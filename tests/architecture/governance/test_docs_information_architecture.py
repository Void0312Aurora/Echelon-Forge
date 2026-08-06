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
ACTIVE_LEGACY_ROOTS = {
  "plan",
  "standards",
  "task",
}
ARCHIVE_ONLY_ROOTS = {
  "Archive",
  "evaluation",
  "manual",
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
  assert roots <= TARGET_ROOTS | ACTIVE_LEGACY_ROOTS | ARCHIVE_ONLY_ROOTS
  assert {"agent", "archive", "book", "forward", "log"}.isdisjoint(roots)


def test_archive_only_legacy_roots_contain_archives_only() -> None:
  tracked = _tracked_docs_paths()

  for root in ("evaluation", "manual"):
    legacy_paths = [
      path for path in tracked if path.startswith(f"docs/{root}/")
    ]
    assert legacy_paths
    assert all(path.startswith(f"docs/{root}/archive/") for path in legacy_paths)


def test_owner_local_work_and_reviews_declare_minimum_metadata() -> None:
  governed = [
    path
    for path in _tracked_docs_paths()
    if path.endswith(".md")
    and Path(path).parts[1] in TARGET_ROOTS
    and ("/work/issues/" in path or "/reviews/" in path)
  ]

  assert governed
  for relative in governed:
    text = (REPO_ROOT / relative).read_text(encoding="utf-8")
    for field in (
      "Document kind:",
      "Lifecycle:",
      "Canonical:",
      "Owner:",
      "Last verified:",
    ):
      assert field in text, f"{relative} is missing {field}"
