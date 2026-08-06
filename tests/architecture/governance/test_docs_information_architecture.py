from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TARGET_ROOTS = {
  "architecture",
  "domains",
  "engineering",
  "learning",
  "operations",
  "project",
  "research",
  "systems",
}
TRANSITIONAL_ROOTS = {
  "Archive",
  "evaluation",
  "forward",
  "log",
  "manual",
  "plan",
  "standards",
  "task",
}


def _tracked_docs_paths() -> list[str]:
  result = subprocess.run(
    ["git", "ls-files", "--", "docs"],
    cwd=REPO_ROOT,
    check=True,
    capture_output=True,
    text=True,
  )
  return [line for line in result.stdout.splitlines() if line]


def test_tracked_docs_use_registered_top_level_roots() -> None:
  tracked = _tracked_docs_paths()
  roots = {
    parts[1]
    for path in tracked
    if len(parts := Path(path).parts) > 2
  }

  assert TARGET_ROOTS <= roots
  assert roots <= TARGET_ROOTS | TRANSITIONAL_ROOTS
  assert {"agent", "book", "archive"}.isdisjoint(roots)


def test_legacy_manual_contains_archives_only() -> None:
  legacy_manual = [
    path for path in _tracked_docs_paths() if path.startswith("docs/manual/")
  ]

  assert legacy_manual
  assert all(path.startswith("docs/manual/archive/") for path in legacy_manual)
