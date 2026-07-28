from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
COMPATIBILITY_FACADE = REPO_ROOT / "python" / "testing" / "runtime.py"
EXCLUDED_PREFIXES = (
  "tests/archive/",
  "tools/archive/",
)
EXCLUDED_DIR_PREFIXES = (".git", ".venv", "__pycache__", "build", "dist", "node_modules")


def _iter_maintained_python_paths() -> list[Path]:
  paths: list[Path] = []
  for path in sorted(REPO_ROOT.rglob("*.py")):
    rel = path.relative_to(REPO_ROOT).as_posix()
    if path == COMPATIBILITY_FACADE:
      continue
    if any(rel.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
      continue
    if any(part.startswith(EXCLUDED_DIR_PREFIXES) for part in path.parts):
      continue
    paths.append(path)
  return paths


def _imports_testing_runtime(node: ast.AST) -> bool:
  if isinstance(node, ast.Import):
    return any(
      alias.name == "python.testing.runtime" or alias.name.startswith("python.testing.runtime.")
      for alias in node.names
    )
  if isinstance(node, ast.ImportFrom):
    if node.module == "python.testing.runtime":
      return True
    return (
      node.module == "python.testing"
      and any(alias.name == "runtime" for alias in node.names)
    )
  return False


def test_maintained_python_paths_use_the_canonical_runtime_bootstrap_owner() -> None:
  violations: list[tuple[str, int, str]] = []
  for path in _iter_maintained_python_paths():
    source = path.read_text(encoding="utf-8")
    if "python.testing.runtime" not in source and "from python.testing import runtime" not in source:
      continue
    tree = ast.parse(source, filename=str(path))
    for node in ast.walk(tree):
      if _imports_testing_runtime(node):
        violations.append(
          (
            path.relative_to(REPO_ROOT).as_posix(),
            node.lineno,
            ast.get_source_segment(source, node) or "",
          )
        )

  assert not violations, (
    "maintained callers must import python.runtime_bootstrap directly; "
    f"compatibility facade imports found: {violations}"
  )
