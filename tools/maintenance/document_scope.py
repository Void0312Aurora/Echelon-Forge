"""Shared documentation-maintenance scope rules.

The default maintained surface intentionally excludes archival, scratch, and
local-only source documents.  A maintained document may still link into an
archive; link auditing decides whether that target exists separately.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


DEFAULT_EXCLUDE_SUBSTRINGS = (
  "docs/temp/",
  "docs/plan/results/",
  "docs/plan/architecture/review/",
)
DEFAULT_EXCLUDE_DIR_NAMES = {"Archive", "archive"}
STRICT_PLAN_SUBTREES = {
  "architecture",
  "cooperative",
  "repository_consolidation",
  "runtime_facade",
  "unified_architecture_program",
}
STRICT_TASK_SECOND_LEVEL_READMES = {"flight_dynamics"}
STRICT_OWNER_DOCUMENTS = {
  "architecture/README.md",
  "architecture/README.zh.md",
  "domains/README.md",
  "domains/README.zh.md",
  "engineering/README.md",
  "engineering/README.zh.md",
  "learning/README.md",
  "learning/README.zh.md",
  "project/README.md",
  "project/README.zh.md",
  "project/documentation_architecture.md",
  "project/documentation_architecture.zh.md",
  "research/README.md",
  "research/README.zh.md",
  "systems/README.md",
  "systems/README.zh.md",
}


def is_local_only_doc(path: Path) -> bool:
  normalized = path.as_posix()
  if any(part in normalized for part in DEFAULT_EXCLUDE_SUBSTRINGS):
    return True
  name_lower = path.name.lower()
  if name_lower.startswith("temp-") or name_lower.startswith("scratch-"):
    return True
  return any(part in DEFAULT_EXCLUDE_DIR_NAMES for part in path.parts)


def is_strict_bilingual_doc(path: Path, root: Path) -> bool:
  relative = path.relative_to(root).as_posix()
  if relative in {"README.md", "README.zh.md"}:
    return True
  if (
    relative.startswith("engineering/automation/")
    or relative.startswith("engineering/documentation/")
    or relative.startswith("engineering/release/")
    or relative.startswith("domains/joint/")
    or relative.startswith("operations/")
    or relative.startswith("research/sources/")
    or relative.startswith("standards/")
  ):
    return True
  if relative in STRICT_OWNER_DOCUMENTS:
    return True
  if relative in {
    "plan/README.md",
    "plan/README.zh.md",
    "reference_artifacts.md",
    "reference_artifacts.zh.md",
    "task/README.md",
    "task/README.zh.md",
    "task/task_archive_convergence_plan_20260518.md",
    "task/task_archive_convergence_plan_20260518.zh.md",
  }:
    return True

  parts = relative.split("/")
  if len(parts) >= 2 and parts[0] == "plan" and parts[1] in STRICT_PLAN_SUBTREES:
    return True
  if len(parts) == 3 and parts[0] == "task" and parts[2] in {"README.md", "README.zh.md"}:
    return True
  if (
    len(parts) == 4
    and parts[0] == "task"
    and parts[1] in STRICT_TASK_SECOND_LEVEL_READMES
    and parts[3] in {"README.md", "README.zh.md"}
  ):
    return True
  return False


def filter_paths(
  paths: Iterable[Path],
  include_local_only: bool,
  *,
  root: Path | None = None,
  strict_bilingual_only: bool = False,
) -> list[Path]:
  if include_local_only:
    filtered = sorted(paths)
  else:
    filtered = sorted(p for p in paths if not is_local_only_doc(p))
  if strict_bilingual_only:
    if root is None:
      raise ValueError("root is required when strict_bilingual_only=True")
    filtered = [p for p in filtered if is_strict_bilingual_doc(p, root)]
  return sorted(filtered)
