from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SHIM_MODULE_PATH = "python.rl.runtime.world_batch_vec_env"
SHIM_FILE = REPO_ROOT / "python" / "rl" / "runtime" / "world_batch_vec_env.py"
SCAN_ROOTS = ("python", "gym_envs", "tools", "tests")
EXCLUDED_PATH_PARTS = (".git", ".venv", "__pycache__", "build", "dist", "node_modules", "archive", "temp")


def _iter_maintained_python_files() -> list[Path]:
  files: list[Path] = []
  for root_name in SCAN_ROOTS:
    root = REPO_ROOT / root_name
    if not root.is_dir():
      continue
    for path in sorted(root.rglob("*.py")):
      if any(part.startswith(EXCLUDED_PATH_PARTS) for part in path.parts):
        continue
      files.append(path)
  return files


def _shim_import_violations(path: Path) -> list[tuple[int, str]]:
  tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
  violations: list[tuple[int, str]] = []

  for node in ast.walk(tree):
    if isinstance(node, ast.Import):
      for alias in node.names:
        if alias.name == SHIM_MODULE_PATH:
          violations.append((node.lineno, f"import {alias.name}"))
    elif isinstance(node, ast.ImportFrom):
      if node.module == SHIM_MODULE_PATH:
        names = ", ".join(alias.name for alias in node.names)
        violations.append((node.lineno, f"from {node.module} import {names}"))
      elif node.module == "python.rl.runtime":
        for alias in node.names:
          if alias.name == "world_batch_vec_env":
            violations.append((node.lineno, "from python.rl.runtime import world_batch_vec_env"))

  return violations


def test_maintained_python_paths_do_not_import_world_batch_vec_env_shim() -> None:
  """The `world_batch_vec_env` compat shell is legacy-only; maintained callers under
  python/, gym_envs/, tools/ (non-archive), and tests/ (non-archive) must import the
  canonical `python.rl.runtime.world_batch.vec_env` (and, for
  `compute_execution_observation_batch`, `python.rl.runtime.world_batch._observation_mixin`)
  implementation modules directly instead of the historical shim path.
  """
  violations: dict[str, list[tuple[int, str]]] = {}

  for path in _iter_maintained_python_files():
    if path == SHIM_FILE:
      continue
    found = _shim_import_violations(path)
    if found:
      violations[path.relative_to(REPO_ROOT).as_posix()] = found

  assert not violations, (
    "maintained callers must import python.rl.runtime.world_batch.vec_env directly instead of "
    f"the world_batch_vec_env compatibility shim: {violations}"
  )


def test_world_batch_vec_env_shim_stays_a_thin_reexport_shell() -> None:
  """Once maintained callers no longer monkeypatch the shim module object, the shim
  should not need the historical mutable-forwarding module class. This keeps the shim
  from silently regrowing compatibility complexity that has no remaining consumer.
  """
  source = SHIM_FILE.read_text(encoding="utf-8")

  assert "compatibility-only" in source.lower() or "compatibility only" in source.lower()
  assert "_WorldBatchVecEnvCompatModule" not in source
  assert "_FORWARDED_MUTABLE_EXPORTS" not in source
  assert "__setattr__" not in source
  assert "sys.modules[__name__].__class__" not in source
  assert "from python.rl.runtime.world_batch.vec_env import" in source
  assert "from python.rl.runtime.world_batch._observation_mixin import compute_execution_observation_batch" in source


def test_world_batch_vec_env_shim_all_matches_canonical_reexports() -> None:
  tree = ast.parse(SHIM_FILE.read_text(encoding="utf-8"), filename=str(SHIM_FILE))
  imported_names: set[str] = set()
  all_names: list[str] | None = None

  for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("python.rl.runtime.world_batch"):
      for alias in node.names:
        imported_names.add(alias.asname or alias.name)
    if (
      isinstance(node, ast.Assign)
      and len(node.targets) == 1
      and isinstance(node.targets[0], ast.Name)
      and node.targets[0].id == "__all__"
      and isinstance(node.value, (ast.List, ast.Tuple))
    ):
      all_names = [element.value for element in node.value.elts if isinstance(element, ast.Constant)]

  assert all_names, "expected a literal __all__ list in the world_batch_vec_env shim"
  assert set(all_names) == imported_names, (
    "world_batch_vec_env __all__ has drifted from its canonical re-exports: "
    f"__all__ only={sorted(set(all_names) - imported_names)}, "
    f"imports only={sorted(imported_names - set(all_names))}"
  )
