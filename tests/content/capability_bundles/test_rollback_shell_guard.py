"""T11 pilot (this iteration): rollback-shell drift gate.

The content capability-bundle machinery must stay removable without touching
the reference path: deleting ``python/content`` (and its tests) must leave
``spawn_unit`` / ``WorldSpawnRequest`` behaviour byte-identical. This gate
pins the isolation:

1. Zero references to the new machinery anywhere in the maintained default
   surfaces (``python/**`` outside ``python/content``, ``gym_envs/**``,
   ``src/**``, ``tools/**``).
2. The content face never imports runtime bindings (``ef_py``) at module
   level; only the explicitly-parameterized ``bindings_adapter`` touches
   binding shapes, and even it receives the module as an argument.
3. Registration stays opt-in: the package ``__init__`` does not import the
   submarine pilot module, and a fresh registry instance is empty.
4. The canonical scenario materialization still enters through
   ``sim.spawn_unit`` (the reference path is intact).
"""

from __future__ import annotations

from pathlib import Path

from python.content.capability_bundles import CapabilityBundleFamilyRegistry

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT_PACKAGE = REPO_ROOT / "python" / "content"

# Tokens that only the new machinery introduces. "capability_bundle"
# (singular) is deliberately NOT listed: it is the pre-existing WP14-A
# runtime vocabulary (CapabilityBundle, capability_bundle_fields.py).
FORBIDDEN_TOKENS = (
  "capability_bundles",
  "content_capability_bundle",
)

DEFAULT_PATH_SCAN = (
  ("python", (".py",)),
  ("gym_envs", (".py",)),
  ("src", (".h", ".cpp", ".inc")),
  ("tools", (".py",)),
)


def _iter_scan_files():
  for root, suffixes in DEFAULT_PATH_SCAN:
    base = REPO_ROOT / root
    for path in sorted(base.rglob("*")):
      if not path.is_file() or path.suffix not in suffixes:
        continue
      if CONTENT_PACKAGE in path.parents:
        continue
      if "__pycache__" in path.parts:
        continue
      yield path


def test_default_path_has_zero_references_to_the_content_bundle_machinery() -> None:
  offenders = []
  for path in _iter_scan_files():
    text = path.read_text(encoding="utf-8", errors="replace")
    for token in FORBIDDEN_TOKENS:
      if token in text:
        offenders.append((str(path.relative_to(REPO_ROOT)), token))
  assert offenders == [], (
    "maintained default-path surfaces must not reference the opt-in content "
    f"capability-bundle machinery (rollback shell): {offenders}"
  )


def test_content_face_never_imports_runtime_bindings_at_module_level() -> None:
  offenders = []
  for path in sorted(CONTENT_PACKAGE.rglob("*.py")):
    text = path.read_text(encoding="utf-8")
    if "import ef_py" in text:
      offenders.append(str(path.relative_to(REPO_ROOT)))
  assert offenders == [], (
    f"content-face modules must stay standard-library only: {offenders}"
  )


def _imported_module_names(source_path: Path) -> set:
  import ast

  names = set()
  tree = ast.parse(source_path.read_text(encoding="utf-8"))
  for node in ast.walk(tree):
    if isinstance(node, ast.Import):
      names.update(alias.name for alias in node.names)
    elif isinstance(node, ast.ImportFrom) and node.module:
      names.add(node.module)
      names.update(f"{node.module}.{alias.name}" for alias in node.names)
  return names


def test_family_registration_stays_opt_in() -> None:
  pilot_module = "python.content.capability_bundles.submarine"
  for module_name in ("__init__.py", "schema.py", "registry.py", "bindings_adapter.py"):
    imports = _imported_module_names(
      CONTENT_PACKAGE / "capability_bundles" / module_name
    )
    assert pilot_module not in imports, (
      f"{module_name} must not import the pilot module; importing "
      "the family module is the caller's opt-in (G5)"
    )

  assert CapabilityBundleFamilyRegistry().registered_families() == ()


def test_reference_path_still_materializes_through_spawn_unit() -> None:
  kernel_apply = (
    REPO_ROOT / "python" / "scenario" / "runtime" / "kernel_apply.py"
  ).read_text(encoding="utf-8")
  assert "sim.spawn_unit(" in kernel_apply
