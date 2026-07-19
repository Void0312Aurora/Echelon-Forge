"""I12/I27: maintained callers must use ``python.runtime_bootstrap`` directly.

The compatibility facade ``python/testing/runtime.py`` must not gain new
importers. I27 (repair round) removed the content pre-filter that skipped
relative imports (``from . import runtime`` inside ``python/testing/`` carries
no ``python.testing.runtime`` literal), and upgraded detection to the same
collector pattern as the tasking-contracts gate:

- every maintained file is AST-parsed (no literal pre-screening);
- relative imports are resolved per PEP 328 against the file's package;
- ``importlib.import_module`` calls are matched through aliases
  (``from importlib import import_module as load``,
  ``loader = importlib.import_module``,
  ``loader = getattr(importlib, "import_module")``) and ``__import__``,
  with conservative constant folding for concatenated string arguments;
- a file-scoped text combination alarm fires when dynamic-loader capability
  (``getattr(importlib`` / ``__import__(`` / any ``import_module`` mention)
  coexists with a quoted ``"python.testing``-prefixed string anywhere in the
  file. Conservative by design: false positives go through the explicit
  allowlist below; false negatives are not acceptable.
"""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
COMPATIBILITY_FACADE = REPO_ROOT / "python" / "testing" / "runtime.py"
GATE_SELF_RELPATH = "tests/architecture/governance/test_runtime_bootstrap_owner.py"
EXCLUDED_PREFIXES = (
  "tests/archive/",
  "tools/archive/",
)
EXCLUDED_DIR_PREFIXES = (".git", ".venv", "__pycache__", "build", "dist", "node_modules")

TARGET_MODULE = "python.testing.runtime"

# Files allowed to trip the text-level combination alarm (each entry reviewed).
TEXT_COMBINATION_ALLOWLIST = {
  # This gate itself: needles and fixture sources quote the target module string.
  GATE_SELF_RELPATH,
  # import_module("python.testing.contracts") / ("python.runtime_bootstrap"):
  # loads the contracts package and the canonical bootstrap owner, never the
  # runtime facade. The `"python.testing` prefix marker matches the contracts
  # package string.
  "tests/runners/test_contract_batches.py",
  # import_module("python.testing.contracts") for runner dispatch, same as above.
  "tests/runners/test_run_scenario_contract.py",
}


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


def _module_qualname_for_path(path: Path, repo_root: Path) -> tuple[str, bool]:
  rel = path.relative_to(repo_root)
  parts = list(rel.with_suffix("").parts)
  is_package_init = bool(parts and parts[-1] == "__init__")
  if is_package_init:
    parts = parts[:-1]
  return ".".join(parts), is_package_init


def _resolve_import_from_module(
  node: ast.ImportFrom,
  *,
  file_module: str,
  is_package_init: bool,
) -> str | None:
  if node.level <= 0:
    return node.module
  parts = [part for part in file_module.split(".") if part]
  package_parts = list(parts) if is_package_init else parts[:-1]
  drop = node.level - 1
  if drop > len(package_parts):
    return None
  base = package_parts[: len(package_parts) - drop]
  if node.module:
    return ".".join((*base, *node.module.split("."))) if base else node.module
  return ".".join(base) if base else None


def _const_str(node: ast.AST) -> str | None:
  """Conservatively fold string-constant expressions (Constant, +, f-string)."""
  if isinstance(node, ast.Constant) and isinstance(node.value, str):
    return node.value
  if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
    left = _const_str(node.left)
    right = _const_str(node.right)
    if left is not None and right is not None:
      return left + right
    return None
  if isinstance(node, ast.JoinedStr):
    pieces: list[str] = []
    for value in node.values:
      if isinstance(value, ast.Constant) and isinstance(value.value, str):
        pieces.append(value.value)
      else:
        return None
    return "".join(pieces)
  return None


def _dynamic_import_aliases(tree: ast.AST) -> set[str]:
  """Names bound to ``importlib.import_module`` anywhere in the file."""
  aliases: set[str] = set()
  for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom) and node.module == "importlib" and node.level == 0:
      for alias in node.names:
        if alias.name == "import_module":
          aliases.add(alias.asname or alias.name)
    elif isinstance(node, ast.Assign):
      value = node.value
      binds_import_module = (
        isinstance(value, ast.Attribute) and value.attr == "import_module"
      ) or (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == "getattr"
        and len(value.args) >= 2
        and isinstance(value.args[1], ast.Constant)
        and value.args[1].value == "import_module"
      )
      if binds_import_module:
        for target in node.targets:
          if isinstance(target, ast.Name):
            aliases.add(target.id)
  return aliases


def _is_target(module: str | None) -> bool:
  return module is not None and (
    module == TARGET_MODULE or module.startswith(f"{TARGET_MODULE}.")
  )


def _ast_violations(path: Path, source: str, repo_root: Path) -> list[tuple[int, str]]:
  """Every facade import in ``source``, resolved against ``repo_root``."""
  tree = ast.parse(source, filename=str(path))
  file_module, is_package_init = _module_qualname_for_path(path, repo_root)
  aliases = _dynamic_import_aliases(tree)
  hits: list[tuple[int, str]] = []
  for node in ast.walk(tree):
    hit = False
    if isinstance(node, ast.Import):
      hit = any(_is_target(alias.name) for alias in node.names)
    elif isinstance(node, ast.ImportFrom):
      resolved = _resolve_import_from_module(
        node,
        file_module=file_module,
        is_package_init=is_package_init,
      )
      if _is_target(resolved):
        hit = True
      elif resolved == "python.testing" and any(
        alias.name == "runtime" or alias.name.startswith("runtime.")
        for alias in node.names
      ):
        hit = True
    elif isinstance(node, ast.Call):
      func = node.func
      is_dynamic_import = (
        isinstance(func, ast.Name)
        and (func.id in aliases or func.id in ("import_module", "__import__"))
      ) or (isinstance(func, ast.Attribute) and func.attr == "import_module")
      if is_dynamic_import and node.args:
        hit = _is_target(_const_str(node.args[0]))
    if hit:
      hits.append((int(node.lineno), ast.get_source_segment(source, node) or ""))
  return hits


_DYNAMIC_CAPABILITY_MARKERS = ("getattr(importlib", "__import__(", "import_module")
_TARGET_STRING_MARKERS = ('"python.testing', "'python.testing")


def _text_combination_violation(source: str) -> bool:
  """File-scoped combination alarm: dynamic-loader capability anywhere in the
  file + a quoted ``python.testing``-prefixed string anywhere in the file.

  The quoted-prefix match is deliberately conservative (it also catches
  concatenation pieces such as ``"python.testing" + ".runtime"``); reviewed
  false positives belong in TEXT_COMBINATION_ALLOWLIST.
  """
  has_capability = any(marker in source for marker in _DYNAMIC_CAPABILITY_MARKERS)
  if not has_capability:
    return False
  return any(marker in source for marker in _TARGET_STRING_MARKERS)


def test_maintained_python_paths_use_the_canonical_runtime_bootstrap_owner() -> None:
  violations: list[tuple[str, int, str]] = []
  for path in _iter_maintained_python_paths():
    rel = path.relative_to(REPO_ROOT).as_posix()
    source = path.read_text(encoding="utf-8")
    try:
      hits = _ast_violations(path, source, REPO_ROOT)
    except SyntaxError:
      # Unparseable files cannot import the facade at runtime either.
      hits = []
    for lineno, segment in hits:
      violations.append((rel, lineno, segment))
    if rel not in TEXT_COMBINATION_ALLOWLIST and not hits and _text_combination_violation(source):
      violations.append(
        (rel, 0, "dynamic import machinery + quoted python.testing string (combination alarm)")
      )

  assert not violations, (
    "maintained callers must import python.runtime_bootstrap directly; "
    f"compatibility facade imports found: {violations}"
  )


# --- Blind-spot fixture tests (tmp trees; reviewed bypass constructions) ------


def _write_tmp_module(tmp_path: Path, relative: str, source: str) -> Path:
  path = tmp_path / relative
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(textwrap.dedent(source), encoding="utf-8")
  return path


def test_gate_detects_relative_import_inside_python_testing(tmp_path: Path) -> None:
  # Reviewed bypass 1: `from . import runtime` inside python/testing/ carries no
  # "python.testing.runtime" literal, so a literal pre-filter would skip it.
  path = _write_tmp_module(
    tmp_path,
    "python/testing/consumer.py",
    """
    from . import runtime
    """,
  )
  hits = _ast_violations(path, path.read_text(encoding="utf-8"), tmp_path)
  assert hits, "expected `from . import runtime` inside python/testing/ to be flagged"

  sibling = _write_tmp_module(
    tmp_path,
    "python/consumer.py",
    """
    from .testing import runtime
    """,
  )
  hits = _ast_violations(sibling, sibling.read_text(encoding="utf-8"), tmp_path)
  assert hits, "expected `from .testing import runtime` inside python/ to be flagged"


def test_gate_detects_cross_line_getattr_dynamic_import(tmp_path: Path) -> None:
  # Reviewed bypass 2: alias bound via getattr on one line, target string used
  # on a later line through a variable call. AST alias tracking cannot fold the
  # variable argument, so the file-scoped combination alarm must fire.
  path = _write_tmp_module(
    tmp_path,
    "sample.py",
    """
    import importlib

    loader = getattr(importlib, "import_module")

    def load():
        name = "python.testing.runtime"
        return loader(name)
    """,
  )
  source = path.read_text(encoding="utf-8")
  assert _text_combination_violation(source), (
    "expected combination alarm for cross-line getattr(importlib, ...) + target string"
  )


def test_gate_detects_aliased_and_concatenated_import_module(tmp_path: Path) -> None:
  # Aliased loader with constant-concatenated argument must be caught by AST
  # folding (no reliance on the text alarm).
  path = _write_tmp_module(
    tmp_path,
    "sample.py",
    """
    from importlib import import_module as load

    runtime = load("python.testing" + ".runtime")
    """,
  )
  hits = _ast_violations(path, path.read_text(encoding="utf-8"), tmp_path)
  assert hits, "expected aliased import_module with concatenated constant to be flagged"


def test_gate_detects_getattr_bound_alias_with_constant_argument(tmp_path: Path) -> None:
  # getattr-bound alias called with a constant string: AST alias tracking path.
  path = _write_tmp_module(
    tmp_path,
    "sample.py",
    """
    import importlib

    loader = getattr(importlib, "import_module")
    runtime = loader("python.testing.runtime")
    """,
  )
  hits = _ast_violations(path, path.read_text(encoding="utf-8"), tmp_path)
  assert hits, "expected getattr-bound alias with constant argument to be flagged"
