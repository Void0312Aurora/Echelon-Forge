#!/usr/bin/env python3
"""Canonical filesystem locations for the retained A2 damage-model packet.

The A2 high-fidelity damage-model evidence moved from the retired
``docs/task/air_combat/archive/`` tree to its owner root under
``docs/systems/effects/reviews/`` during the ownership-first documentation
migration. Every tool and test that reads or writes retained A2 evidence
resolves its paths here so a future move updates one module instead of
twenty-seven duplicated path literals.
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

PACKET_ROOT = (
  REPO_ROOT
  / "docs"
  / "systems"
  / "effects"
  / "reviews"
  / "a2_high_fidelity_damage_model_20260602"
)

CANDIDATE_PACKAGE_DIR = (
  PACKET_ROOT
  / "calibration"
  / "vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m"
)

RETAINED_ARTIFACTS_DIR = CANDIDATE_PACKAGE_DIR / "retained_artifacts"

DATA_COLLECTION_DIR = PACKET_ROOT / "data_collection"

MANIFEST_GLOB = "retained_artifacts/**/manifest.json"

# Repository-relative forms, for helpers that receive ``repo_root`` as an
# argument instead of importing the module-level constants.
PACKET_RELATIVE_DIR = Path(
  "docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602"
)
CANDIDATE_PACKAGE_RELATIVE_DIR = (
  PACKET_RELATIVE_DIR
  / "calibration"
  / "vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m"
)


def packet_root(repo_root: Path) -> Path:
  """Return the A2 packet root beneath *repo_root*."""
  return repo_root / PACKET_RELATIVE_DIR


def candidate_package_dir(repo_root: Path) -> Path:
  """Return the A2 candidate package directory beneath *repo_root*."""
  return repo_root / CANDIDATE_PACKAGE_RELATIVE_DIR


def retained_artifact_dir(name: str) -> Path:
  """Return the retained-artifact subdirectory *name* inside the packet."""
  return RETAINED_ARTIFACTS_DIR / name


# ---------------------------------------------------------------------------
# Logical → physical path translation for sealed evidence artifacts
# ---------------------------------------------------------------------------
# Sealed JSON artifacts (hash-pinned retained evidence) record relative paths
# under the *retired* logical prefix below.  Those bytes must not be rewritten
# because the manifests are SHA-256 pinned.  Readers apply
# ``translate_logical_a2_path`` when resolving a recorded string to a live
# filesystem path.

LEGACY_PACKET_LOGICAL_PREFIX = (
  "docs/task/air_combat/archive/a2_high_fidelity_damage_model"
)
PACKET_PHYSICAL_PREFIX = PACKET_RELATIVE_DIR.as_posix()


def translate_logical_a2_path(recorded: str) -> str:
  """Translate a pre-migration logical path to its current physical location.

  Sealed evidence manifests record ``relative_path`` values under the retired
  ``docs/task/air_combat/archive/a2_high_fidelity_damage_model`` prefix.
  The sealed bytes are SHA-256 pinned and must not be modified; readers call
  this function to map the recorded string to the live filesystem location
  before opening the file.

  Paths that do not start with the legacy prefix are returned unchanged.
  """
  if recorded.startswith(LEGACY_PACKET_LOGICAL_PREFIX):
    return PACKET_PHYSICAL_PREFIX + recorded[len(LEGACY_PACKET_LOGICAL_PREFIX) :]
  return recorded


def require_candidate_package_dir() -> Path:
  """Return the candidate package directory, failing closed when it is absent.

  Retained-evidence tools default to a production location. If that location
  is renamed or pruned without updating this module, a glob over the missing
  directory silently yields zero manifests and every integrity counter reads
  zero -- a passing result that verified nothing. Raising here converts that
  fail-open into a hard error.
  """
  if not CANDIDATE_PACKAGE_DIR.is_dir():
    raise FileNotFoundError(
      "retained A2 candidate package directory is missing: "
      f"{CANDIDATE_PACKAGE_DIR}. Update tools/maintenance/a2_packet_paths.py "
      "if the packet moved to a new owner root."
    )
  return CANDIDATE_PACKAGE_DIR
