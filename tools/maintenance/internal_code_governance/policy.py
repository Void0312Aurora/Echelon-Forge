"""Detection policy for opaque project-internal codes."""

from __future__ import annotations

import re
from pathlib import PurePosixPath


SOURCE_SUFFIXES = {
  ".c",
  ".cc",
  ".cpp",
  ".cu",
  ".cuh",
  ".h",
  ".hpp",
  ".py",
}
DOCUMENT_SUFFIXES = {".md"}
PRODUCTION_ROOTS = {"gym_envs", "python", "src"}
EXCLUDED_PARTS = {
  ".git",
  "Archive",
  "archive",
  "build",
  "build-coverage",
  "build-workshop",
  "third_party",
}

# These families identify work packages, review batches, or iterations rather
# than stable runtime/domain concepts. Short domain abbreviations such as C2 are
# deliberately excluded because they need semantic ownership, not a global ban.
TRACKING_CODE_PATTERN = (
  r"RB\d+[A-Za-z]?|"
  r"CR\d+(?:[-.]\d+[A-Za-z]?)?|"
  r"WP\d+(?:[-.]\d+[A-Za-z]?)?|"
  r"TM\d+(?:[-.]\d+[A-Za-z]?)?|"
  r"MLF(?:[-.]?\d+[A-Za-z]?)|"
  r"RES\d+(?:[-.]\d+[A-Za-z]?)?|"
  r"I\d{2,}"
)
TRACKING_CODE_RE = re.compile(
  rf"(?<![A-Za-z0-9])(?:{TRACKING_CODE_PATTERN})(?![A-Za-z0-9])",
  re.IGNORECASE,
)
TRACKING_CODE_TOKEN_RE = re.compile(
  rf"^(?:{TRACKING_CODE_PATTERN})$",
  re.IGNORECASE,
)
PHASE_IDENTIFIER_RE = re.compile(
  r"(?<![A-Za-z0-9])(?:"
  r"phase_[a-d](?:_[A-Za-z0-9_]+)?|"
  r"PHASE_[A-D](?:_[A-Za-z0-9_]+)?|"
  r"[kK]?Phase[A-D](?![a-z])(?:[A-Z0-9_][A-Za-z0-9_]*)?|"
  r"phase[A-D](?![a-z])(?:[A-Z0-9_][A-Za-z0-9_]*)?"
  r")",
)
PHASE_PROSE_RE = re.compile(
  r"(?<![A-Za-z0-9])Phase(?:\s+|-)[A-D](?:/[A-D])*(?![A-Za-z0-9])",
  re.IGNORECASE,
)
STRING_LITERAL_RE = re.compile(
  r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
)
COMPATIBILITY_MARKER = "internal-code: compatibility"
POLICY_DOCUMENTS = {
  "docs/standards/governance/internal_code_policy.md",
  "docs/standards/governance/internal_code_policy.zh.md",
}


def normalize_path(path: str) -> str:
  return PurePosixPath(path.replace("\\", "/")).as_posix().lstrip("./")


def is_excluded(path: str) -> bool:
  parts = PurePosixPath(normalize_path(path)).parts
  return any(part in EXCLUDED_PARTS for part in parts)


def is_production_source(path: str) -> bool:
  normalized = normalize_path(path)
  pure_path = PurePosixPath(normalized)
  return (
    bool(pure_path.parts)
    and pure_path.parts[0] in PRODUCTION_ROOTS
    and pure_path.suffix.lower() in SOURCE_SUFFIXES
    and not is_excluded(normalized)
  )


def is_document(path: str) -> bool:
  normalized = normalize_path(path)
  return (
    PurePosixPath(normalized).suffix.lower() in DOCUMENT_SUFFIXES
    and not is_excluded(normalized)
  )
