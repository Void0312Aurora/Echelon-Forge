"""Every pytest hook under tests/ must be a deliberate, registered decision.

A ``pytest_collection_modifyitems`` defined in *any* conftest -- however deep
-- receives the whole session's item list, not its own directory's. A leaf
conftest doing per-item filesystem work therefore taxes every collect in the
repository: the runtime_profiles conftest resolved 3,515 paths per session
(~7s on Windows) before 74891c57 cached it per module. Static call-pattern
scanning cannot separate that cached form from the uncached one without false
positives, so this guard pins the inventory instead: adding a conftest or a
hook fails here first, forcing the author through this file's warning.
"""

from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests"

# repo-relative conftest path -> exact set of pytest_* hooks it may define.
REGISTERED_CONFTEST_HOOKS: dict[str, frozenset[str]] = {
  "tests/conftest.py": frozenset({"pytest_configure"}),
  "tests/architecture/runtime_profiles/conftest.py": frozenset(
    {"pytest_collection_modifyitems"}
  ),
}


def _hooks_defined(path: Path) -> set[str]:
  tree = ast.parse(path.read_text(encoding="utf-8"))
  return {
    node.name
    for node in tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and node.name.startswith("pytest_")
  }


def test_conftest_hook_inventory_is_registered() -> None:
  found = {
    path.relative_to(REPO_ROOT).as_posix(): _hooks_defined(path)
    for path in sorted(TESTS_ROOT.rglob("conftest.py"))
  }

  unregistered = sorted(set(found) - set(REGISTERED_CONFTEST_HOOKS))
  assert not unregistered, (
    "new conftest.py files under tests/ must be registered here first. "
    "Before registering, read this module's docstring: collection hooks see "
    f"every session item, not just this directory's. New files: {unregistered}"
  )

  removed = sorted(set(REGISTERED_CONFTEST_HOOKS) - set(found))
  assert not removed, (
    f"registered conftest files disappeared; prune the registry: {removed}"
  )

  for rel_path, hooks in sorted(found.items()):
    allowed = REGISTERED_CONFTEST_HOOKS[rel_path]
    extra = sorted(hooks - allowed)
    assert not extra, (
      f"{rel_path} defines unregistered pytest hooks {extra}. Collection "
      "hooks receive the whole session's items; per-item filesystem work "
      "there taxes every collect in the repository (see 74891c57). Register "
      "the hook here once it follows the cached-per-module pattern."
    )
    missing = sorted(allowed - hooks)
    assert not missing, (
      f"{rel_path} no longer defines {missing}; update the registry."
    )
