#!/usr/bin/env python3
"""Reproducible source dependency inventory for the maintained code tree.

The inventory records source-level imports/includes and syntactic project
CMake links. It does not resolve nonliteral dynamic Python imports,
preprocessor branches, or conditional CMake configuration.
"""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from tools.architecture import cmake_target_graph, cpp_include_graph

REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_ROOTS = ("python", "gym_envs", "_world_model_train_impl", "tests", "tools", "examples", "scripts")
PYTHON_ENTRYPOINTS = ("train.py", "evaluate.py", "world_model_train.py")


@dataclass(frozen=True, order=True)
class DependencyEdge:
  kind: str
  source: str
  target: str
  path: str
  line: int
  scope: str = "module"

  def identity(self) -> tuple[str, str, str]:
    return self.kind, self.source, self.target


@dataclass(frozen=True)
class Inventory:
  python_modules: dict[str, str]
  python_edges: tuple[DependencyEdge, ...]
  cpp_files: tuple[str, ...]
  cpp_edges: tuple[DependencyEdge, ...]
  cmake_edges: tuple[cmake_target_graph.CMakeTargetEdge, ...]
  unresolved_python_imports: tuple[dict[str, object], ...]


def _python_files(root: Path) -> list[Path]:
  files = [path for name in PYTHON_ROOTS for path in (root / name).rglob("*.py")]
  files.extend(root / name for name in PYTHON_ENTRYPOINTS if (root / name).is_file())
  return sorted(path for path in files if "__pycache__" not in path.parts)


def _module_name(path: Path, root: Path) -> str:
  parts = list(path.relative_to(root).with_suffix("").parts)
  if parts[-1] == "__init__":
    parts.pop()
  return ".".join(parts)


def _absolute_from_base(source: str, source_is_package: bool, level: int, module: str | None) -> str:
  if level == 0:
    return module or ""
  package = source.split(".") if source_is_package else source.split(".")[:-1]
  if level > len(package):
    return ""
  prefix = package[: len(package) - level + 1]
  return ".".join([*prefix, *([module] if module else [])])


class _ImportVisitor(ast.NodeVisitor):
  def __init__(self, source: str, path: str, is_package: bool, modules: dict[str, str]):
    self.source = source
    self.path = path
    self.is_package = is_package
    self.modules = modules
    self.scope = "module"
    self.edges: list[DependencyEdge] = []
    self.unresolved: list[dict[str, object]] = []

  def _record(self, spelling: str, line: int, *, dynamic: bool = False, strict: bool = True) -> None:
    target = spelling if spelling in self.modules else None
    if target is None:
      if strict and (spelling.startswith(("python.", "gym_envs.")) or spelling in {"python", "gym_envs"}):
        self.unresolved.append({"path": self.path, "line": line, "import": spelling})
      return
    self.edges.append(DependencyEdge("python_dynamic" if dynamic else "python_import", self.source, target, self.path, line, self.scope))

  def visit_Import(self, node: ast.Import) -> None:
    for alias in node.names:
      self._record(alias.name, node.lineno, strict=alias.name.startswith(("python.", "gym_envs.")))

  def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
    base = _absolute_from_base(self.source, self.is_package, node.level, node.module)
    if not base:
      self.unresolved.append({"path": self.path, "line": node.lineno, "import": "." * node.level + (node.module or "")})
      return
    # A package may export attributes as well as child modules. Prefer the
    # child only when it exists; otherwise the package/module owns the import.
    for alias in node.names:
      child = f"{base}.{alias.name}"
      self._record(child if child in self.modules else base, node.lineno, strict=base.startswith(("python", "gym_envs")))

  def visit_Call(self, node: ast.Call) -> None:
    func = node.func
    is_import = (
      isinstance(func, ast.Name) and func.id == "__import__"
    ) or (
      isinstance(func, ast.Attribute)
      and isinstance(func.value, ast.Name)
      and func.value.id == "importlib"
      and func.attr == "import_module"
    )
    if is_import and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
      self._record(node.args[0].value, node.lineno, dynamic=True, strict=False)
    self.generic_visit(node)

  def _visit_deferred(self, node: ast.AST) -> None:
    previous = self.scope
    self.scope = "deferred" if previous == "module" else previous
    self.generic_visit(node)
    self.scope = previous

  visit_FunctionDef = _visit_deferred
  visit_AsyncFunctionDef = _visit_deferred

  def visit_If(self, node: ast.If) -> None:
    is_type_checking = (
      isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING"
    ) or (
      isinstance(node.test, ast.Attribute) and node.test.attr == "TYPE_CHECKING"
    )
    previous = self.scope
    if is_type_checking:
      self.scope = "type_checking"
    for item in node.body:
      self.visit(item)
    self.scope = previous
    for item in node.orelse:
      self.visit(item)


def python_inventory(root: Path) -> tuple[dict[str, str], tuple[DependencyEdge, ...], tuple[dict[str, object], ...]]:
  files = _python_files(root)
  modules = {_module_name(path, root): path.relative_to(root).as_posix() for path in files}
  edges: list[DependencyEdge] = []
  unresolved: list[dict[str, object]] = []
  for path in files:
    source = _module_name(path, root)
    visitor = _ImportVisitor(source, modules[source], path.name == "__init__.py", modules)
    visitor.visit(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))
    edges.extend(visitor.edges)
    unresolved.extend(visitor.unresolved)
  return modules, tuple(sorted(set(edges))), tuple(sorted(unresolved, key=lambda row: (str(row["path"]), int(row["line"]), str(row["import"]))))


def build_inventory(root: Path = REPO_ROOT) -> Inventory:
  modules, python_edges, unresolved = python_inventory(root)
  cpp_root = root / "src"
  files = cpp_include_graph.iter_source_files(cpp_root)
  includes = cpp_include_graph.build_edges(files, src_root=cpp_root, repo_root=root)
  cpp_edges = tuple(sorted(
    DependencyEdge("cpp_include", edge.from_path, edge.to_path, edge.from_path, edge.line)
    for edge in includes
  ))
  cmake_edges = cmake_target_graph.build_edges(root / "CMakeLists.txt")
  return Inventory(
    python_modules=modules,
    python_edges=python_edges,
    cpp_files=tuple(path.relative_to(root).as_posix() for path in files),
    cpp_edges=cpp_edges,
    cmake_edges=cmake_edges,
    unresolved_python_imports=unresolved,
  )


def strongly_connected_components(edges: tuple[DependencyEdge, ...]) -> list[list[str]]:
  graph: dict[str, set[str]] = defaultdict(set)
  for edge in edges:
    graph[edge.source].add(edge.target)
  index = 0
  indices: dict[str, int] = {}
  lowlinks: dict[str, int] = {}
  stack: list[str] = []
  active: set[str] = set()
  components: list[list[str]] = []

  def visit(node: str) -> None:
    nonlocal index
    indices[node] = lowlinks[node] = index
    index += 1
    stack.append(node)
    active.add(node)
    for target in sorted(graph[node]):
      if target not in indices:
        visit(target)
        lowlinks[node] = min(lowlinks[node], lowlinks[target])
      elif target in active:
        lowlinks[node] = min(lowlinks[node], indices[target])
    if lowlinks[node] == indices[node]:
      component: list[str] = []
      while True:
        member = stack.pop()
        active.remove(member)
        component.append(member)
        if member == node:
          break
      if len(component) > 1:
        components.append(sorted(component))

  for node in sorted(graph):
    if node not in indices:
      visit(node)
  return sorted(components)


def summary(inventory: Inventory) -> dict[str, object]:
  python_pairs = {edge.identity() for edge in inventory.python_edges}
  cpp_pairs = {edge.identity() for edge in inventory.cpp_edges}
  package_edges = Counter((edge.source.split(".")[0], edge.target.split(".")[0]) for edge in inventory.python_edges)
  return {
    "scope": {
      "python_roots": list(PYTHON_ROOTS),
      "python_entrypoints": list(PYTHON_ENTRYPOINTS),
      "cpp_root": "src",
      "python_edges": "statically resolved AST import sites plus literal importlib.import_module/__import__ calls",
      "cpp_edges": "quoted includes resolved relative to the source file or src root",
      "cmake_edges": "project target_link_libraries calls; syntactic union of conditional branches",
      "excluded": "nonliteral dynamic imports, preprocessor expansion, third-party imports/includes, CMake generator expression evaluation",
    },
    "python_modules": len(inventory.python_modules),
    "python_import_sites": len(inventory.python_edges),
    "python_module_edges": len(python_pairs),
    "python_multi_module_scc": strongly_connected_components(inventory.python_edges),
    "python_package_edges": {f"{a} -> {b}": count for (a, b), count in sorted(package_edges.items())},
    "cpp_files": len(inventory.cpp_files),
    "cpp_include_sites": len(inventory.cpp_edges),
    "cpp_file_edges": len(cpp_pairs),
    "cpp_multi_file_scc": strongly_connected_components(inventory.cpp_edges),
    "cmake_target_link_sites": len(inventory.cmake_edges),
    "cmake_target_edges": len({(edge.source, edge.target) for edge in inventory.cmake_edges}),
    "cmake_target_multi_target_scc": cmake_target_graph.strongly_connected_components(inventory.cmake_edges),
    "unresolved_internal_python_imports": list(inventory.unresolved_python_imports),
  }


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--format", choices=("summary", "json"), default="summary")
  args = parser.parse_args()
  inventory = build_inventory()
  report = summary(inventory)
  if args.format == "json":
    report["python_edges"] = [asdict(edge) for edge in inventory.python_edges]
    report["cpp_edges"] = [asdict(edge) for edge in inventory.cpp_edges]
    report["cmake_edges"] = [asdict(edge) for edge in inventory.cmake_edges]
  print(json.dumps(report, indent=2, ensure_ascii=True, sort_keys=True))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
