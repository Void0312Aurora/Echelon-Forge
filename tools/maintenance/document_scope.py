"""Shared documentation-maintenance scope rules.

The default maintained surface intentionally excludes archival, scratch, and
local-only source documents.  A maintained document may still link into an
archive; link auditing decides whether that target exists separately.

``classify_document`` is the single source of truth for the four maintained
surface tiers defined by the bilingual documentation policy.  Every Markdown
file under ``docs/`` resolves to exactly one tier; there is no fallthrough.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Literal


DocumentTier = Literal["tier_a", "tier_b", "tier_c", "tier_d"]
DOCUMENT_TIERS: tuple[DocumentTier, ...] = ("tier_a", "tier_b", "tier_c", "tier_d")

# Extension point for path-shaped local-only exclusions. It is empty because
# the previous entries (docs/temp/, docs/plan/results/, and
# docs/plan/architecture/review/) named paths that no longer exist in the tree.
DEFAULT_EXCLUDE_SUBSTRINGS: tuple[str, ...] = ()
DEFAULT_EXCLUDE_DIR_NAMES = {"Archive", "archive"}
# Directory components that put a document in Tier C retention. These are
# matched against the docs-root-relative path, so a workspace that happens to
# be checked out below a directory named "temp" is not misread as scratch.
# ``temp`` covers both the ``docs/temp/`` root and the owner-local
# ``docs/**/temp/`` mirrors the policy places in Tier C.
TIER_C_DIR_NAMES = frozenset({"Archive", "archive", "temp"})
# Owner-local sealed dated evidence packets (Tier D) live under a ``reviews``
# directory component, for example
# ``docs/systems/effects/reviews/<packet>_<YYYYMMDD>/``.
SEALED_EVIDENCE_DIR_NAME = "reviews"
# Docs-root-relative posix paths of work-layer files explicitly promoted into
# the strict bilingual surface. Promotion registers both the English canonical
# file and its .zh.md companion here; see the bilingual documentation policy.
PROMOTED_WORK_DOCUMENTS: frozenset[str] = frozenset()
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
  # Work surfaces are Tier B (English canonical, no bilingual SLA) and stay
  # outside the strict maintained bilingual surface even when they sit under
  # an owner prefix that is otherwise strict, such as operations/. A pair that
  # is explicitly promoted re-enters through PROMOTED_WORK_DOCUMENTS.
  if "work" in relative.split("/")[:-1]:
    return relative in PROMOTED_WORK_DOCUMENTS
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


def is_english_work_doc(path: Path, root: Path) -> bool:
  """English canonical work-layer documents keep default link auditing even
  though they sit outside the strict bilingual surface."""
  if path.name.endswith(".zh.md") or path.name.endswith(".en.md"):
    return False
  relative = path.relative_to(root).as_posix()
  return "work" in relative.split("/")[:-1]


def is_retained_doc(path: Path, root: Path) -> bool:
  """Tier C: archived, scratch, or otherwise local-only retention."""
  parts = path.relative_to(root).as_posix().split("/")
  if any(part in TIER_C_DIR_NAMES for part in parts[:-1]):
    return True
  return is_local_only_doc(path)


def is_sealed_evidence_doc(path: Path, root: Path) -> bool:
  """Tier D: an owner-local sealed dated evidence packet.

  These packets record what was inspected at a point in time and are frequently
  pinned by SHA-256 entries in a retained-artifact manifest, so they are read
  only and carry no bilingual SLA.  Archived copies stay Tier C.
  """
  if is_retained_doc(path, root):
    return False
  parts = path.relative_to(root).as_posix().split("/")
  return SEALED_EVIDENCE_DIR_NAME in parts[:-1]


def classify_document(path: Path, root: Path) -> DocumentTier:
  """Return the single maintained-surface tier that owns ``path``.

  Precedence is deliberate and mirrors ``filter_paths``:

  1. ``tier_c`` -- archive, scratch, and local-only retention wins first, so an
     archived copy of a maintained page never inherits a live SLA.
  2. ``tier_a`` -- the strict bilingual surface, including a work or review
     page an owner explicitly promoted into it.  A registered bilingual pair
     keeps its live SLA instead of decaying into sealed evidence.
  3. ``tier_d`` -- sealed dated evidence under an owner-local ``reviews/``
     subtree.
  4. ``tier_b`` -- everything else: the English-only work and evidence surface.
  """
  if is_retained_doc(path, root):
    return "tier_c"
  if is_strict_bilingual_doc(path, root):
    return "tier_a"
  if is_sealed_evidence_doc(path, root):
    return "tier_d"
  return "tier_b"


def requires_english_companion(path: Path, root: Path) -> bool:
  """Whether a Chinese-only page should be queued for an English canonical peer.

  Only the strict bilingual surface carries that obligation.  Translating a
  sealed evidence page would break the hash pins that make it evidence, and
  Tier B/Tier C pages have no bilingual SLA to satisfy.
  """
  if not path.name.endswith(".zh.md"):
    return False
  return classify_document(path, root) == "tier_a"


def filter_paths(
  paths: Iterable[Path],
  include_local_only: bool,
  *,
  root: Path | None = None,
  strict_bilingual_only: bool = False,
) -> list[Path]:
  """Select the maintained slice of ``paths``.

  With ``root`` the default exclusion is the whole Tier C retention set
  (archive, ``temp`` components relative to the docs root, and local-only
  names), so the filter agrees with ``classify_document``. Without ``root``
  only the root-independent ``is_local_only_doc`` heuristics apply; callers
  that know the docs root should always pass it.
  """
  if include_local_only:
    filtered = sorted(paths)
  elif root is not None:
    filtered = sorted(p for p in paths if not is_retained_doc(p, root))
  else:
    filtered = sorted(p for p in paths if not is_local_only_doc(p))
  if strict_bilingual_only:
    if root is None:
      raise ValueError("root is required when strict_bilingual_only=True")
    filtered = [p for p in filtered if is_strict_bilingual_doc(p, root)]
  return sorted(filtered)
