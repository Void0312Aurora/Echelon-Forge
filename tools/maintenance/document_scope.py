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
STRICT_OWNER_DOCUMENTS = {
  "architecture/README.md",
  "architecture/README.zh.md",
  "domains/README.md",
  "domains/README.zh.md",
  "domains/air/README.md",
  "domains/air/README.zh.md",
  "domains/ground/README.md",
  "domains/ground/README.zh.md",
  "domains/naval/README.md",
  "domains/naval/README.zh.md",
  "engineering/README.md",
  "engineering/README.zh.md",
  "engineering/automation/README.md",
  "engineering/automation/README.zh.md",
  "engineering/testing/README.md",
  "engineering/testing/README.zh.md",
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
  "systems/environment/README.md",
  "systems/environment/README.zh.md",
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
    relative.startswith("engineering/automation/rules/")
    or relative.startswith("engineering/automation/prompts/")
    or relative.startswith("engineering/automation/standards/")
    or relative.startswith("architecture/standards/")
    or relative.startswith("architecture/reference/")
    or relative.startswith("engineering/documentation/")
    or relative.startswith("engineering/release/")
    or relative.startswith("domains/air/standards/")
    or relative.startswith("domains/air/reference/")
    or relative.startswith("domains/ground/standards/")
    or relative.startswith("domains/joint/")
    or relative.startswith("domains/naval/reference/")
    or relative.startswith("domains/naval/standards/")
    or relative.startswith("learning/standards/")
    or relative.startswith("operations/")
    or relative.startswith("research/standards/")
    or relative.startswith("research/sources/")
    or relative.startswith("engineering/testing/reference/")
    or relative.startswith("systems/command-tasking/reference/")
    or relative.startswith("systems/standards/")
  ):
    return True
  if relative in STRICT_OWNER_DOCUMENTS:
    return True
  if relative in {
    "reference_artifacts.md",
    "reference_artifacts.zh.md",
  }:
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
