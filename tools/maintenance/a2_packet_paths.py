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

LEGACY_SUBAGENT_USAGE_POLICY_LOGICAL_PATH = (
  "docs/standards/governance/subagent_usage_policy.md"
)
RETAINED_GOVERNANCE_DEPENDENCY_RELATIVE_DIR = (
  PACKET_RELATIVE_DIR / "retained_dependencies" / "governance_20260531"
)
RETAINED_SUBAGENT_USAGE_POLICY_RELATIVE_PATH = (
  RETAINED_GOVERNANCE_DEPENDENCY_RELATIVE_DIR / "subagent_usage_policy.md"
)

# Sealed manifests may pin dependencies outside the retired A2 tree.  Exact
# logical paths map to immutable byte-for-byte snapshots before prefix-based
# A2 translation is considered.  Do not point these entries at maintained
# policy documents: their content may legitimately evolve and invalidate the
# historical manifest hash.
PERSISTED_LOGICAL_PATH_OVERRIDES = {
  LEGACY_SUBAGENT_USAGE_POLICY_LOGICAL_PATH:
    RETAINED_SUBAGENT_USAGE_POLICY_RELATIVE_PATH.as_posix(),
}


def translate_logical_a2_path(recorded: str) -> str:
  """Translate a persisted logical path to its current physical location.

  Sealed evidence manifests record ``relative_path`` values under the retired
  ``docs/task/air_combat/archive/a2_high_fidelity_damage_model`` prefix.
  Some also hash-pin dependencies outside that tree. The sealed bytes are
  immutable; readers call this function to map recorded strings to the live
  packet or to a byte-preserved dependency snapshot before opening a file.

  Unregistered paths outside the legacy packet prefix are returned unchanged.
  """
  override = PERSISTED_LOGICAL_PATH_OVERRIDES.get(recorded)
  if override is not None:
    return override
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
