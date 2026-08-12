#!/usr/bin/env python3
"""Write retained Stage C component-probability candidate artifacts for A2.

This tool materializes the current Stage C machine-readable candidate surfaces
into stable JSON files under the candidate package directory. The retained pack
is intentionally bounded to candidate, non-authoritative, author-side review
artifacts with a test-local runtime origin. It does not grant stock runtime
authority, validated fragility truth, Pk authority, or deterministic-fuze
authority.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_REPO_ROOT_HINT = str(Path(__file__).resolve().parents[3])
if _REPO_ROOT_HINT not in sys.path:
  sys.path.insert(0, _REPO_ROOT_HINT)

from python.runtime_bootstrap import ensure_repo_imports, repo_root

ensure_repo_imports()

REPO_ROOT = Path(repo_root())

from tools.maintenance.a2_packet_paths import (  # noqa: E402
  CANDIDATE_PACKAGE_DIR as A2_CANDIDATE_PACKAGE_DIR,
)

from tools.maintenance.candidate_artifacts import _retained_pack_common as retained_pack_common
from tools.maintenance.candidate_artifacts import runtime_authority_exercise as authority_pack
from tools.maintenance.candidate_artifacts import (
  component_probability_result_pack as result_pack,
)
from tools.maintenance.candidate_artifacts import (
  component_probability_snapshot as snapshot,
)
from tools.maintenance.candidate_artifacts import (
  component_probability_surface_probe as surface_probe,
)

PACKAGE_ID = (
  "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
  "beam_high_near_miss_0_35m_v0"
)
RETAINED_PACK_SCHEMA_VERSION = "a2.stage_c_component_probability_retained_artifact_pack.v1"
MISSING_PACK_STATUS = "missing_stage_c_component_probability_retained_artifact_pack"
RETAINED_PACK_STATUS = (
  "author_retained_stage_c_component_probability_candidate_artifacts_only"
)
RETENTION_SCOPE = "stage_c_component_probability_author_side_candidate_only"
DEFAULT_OUTPUT_DIR = (
  A2_CANDIDATE_PACKAGE_DIR
  / "retained_artifacts"
  / "stage_c_component_probability_20260530"
)

ARTIFACT_FILENAMES = {
  "runtime_aligned_authority_pack": "runtime_aligned_authority_pack.json",
  "stage_c_component_probability_snapshot": "stage_c_component_probability_snapshot.json",
  "stage_c_component_probability_surface_probe": (
    "stage_c_component_probability_surface_probe.json"
  ),
  "stage_c_component_probability_result_pack": (
    "stage_c_component_probability_result_pack.json"
  ),
}

ARTIFACT_RELEASE_BOUNDARIES = {
  "runtime_aligned_authority_pack": {
    "origin_class": "test_local_runtime_exercise_only",
    "allowed_claim": "test-local runtime-aligned component probability exercise exists",
    "forbidden_claim": (
      "validated fragility truth, stock runtime authority, Pk authority, "
      "or deterministic-fuze authority"
    ),
  },
  "stage_c_component_probability_snapshot": {
    "origin_class": "author_side_candidate_snapshot_only",
    "allowed_claim": "author-side candidate Stage C snapshot and provenance surface exist",
    "forbidden_claim": (
      "validated component fragility truth, stock runtime authority, Pk "
      "authority, or deterministic-fuze authority"
    ),
  },
  "stage_c_component_probability_surface_probe": {
    "origin_class": "author_side_candidate_surface_probe_only",
    "allowed_claim": (
      "author-side candidate Stage C fragility-surface and repeatability snapshot exist"
    ),
    "forbidden_claim": (
      "validated fragility curve, stock runtime authority, Pk authority, or "
      "deterministic-fuze authority"
    ),
  },
  "stage_c_component_probability_result_pack": {
    "origin_class": "author_side_candidate_result_pack_only",
    "allowed_claim": "author-side candidate Stage C result pack and stable hashes exist",
    "forbidden_claim": (
      "validated release result, stock runtime authority, Pk authority, or "
      "deterministic-fuze authority"
    ),
  },
}

RETAINED_ORIGIN_SUMMARY = {
  "runtime_origin": "test_local_runtime_authority_exercise_only",
  "review_surface": "author_side_candidate_snapshot_and_result_pack_only",
  "independent_release_artifact_present": False,
  "stock_runtime_authority_present": False,
}

def _build_artifacts(repo_root: Path) -> dict[str, dict[str, Any]]:
  return {
    "runtime_aligned_authority_pack": authority_pack.generate_runtime_aligned_authority_pack(
      repo_root=repo_root
    ),
    "stage_c_component_probability_snapshot": snapshot.generate_stage_c_component_probability_snapshot(
      repo_root=repo_root
    ),
    "stage_c_component_probability_surface_probe": (
      surface_probe.generate_stage_c_component_probability_surface_probe(
        repo_root=repo_root
      )
    ),
    "stage_c_component_probability_result_pack": (
      result_pack.generate_stage_c_component_probability_result_pack(
        repo_root=repo_root
      )
    ),
  }

def load_retained_artifact_pack_manifest(
  *,
  repo_root: Path = REPO_ROOT,
  output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
  return retained_pack_common.load_pack_manifest(
    repo_root=repo_root,
    output_dir=output_dir,
    package_id=PACKAGE_ID,
    schema_version=RETAINED_PACK_SCHEMA_VERSION,
    missing_status=MISSING_PACK_STATUS,
  )

def generate_retained_artifact_pack(
  *,
  repo_root: Path = REPO_ROOT,
  output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
  return retained_pack_common.write_pack(
    repo_root=repo_root,
    output_dir=output_dir,
    build_artifacts=_build_artifacts,
    artifact_filenames=ARTIFACT_FILENAMES,
    release_boundaries=ARTIFACT_RELEASE_BOUNDARIES,
    package_id=PACKAGE_ID,
    schema_version=RETAINED_PACK_SCHEMA_VERSION,
    status=RETAINED_PACK_STATUS,
    retention_scope=RETENTION_SCOPE,
    retained_origin_summary=dict(RETAINED_ORIGIN_SUMMARY),
  )

def main(argv: list[str] | None = None) -> int:
  return retained_pack_common.run_pack_cli(
    argv,
    description=(
      "Write retained Stage C component-probability candidate artifacts for "
      "the current A2 blast-fragmentation package."
    ),
    default_output_dir=DEFAULT_OUTPUT_DIR,
    generate=generate_retained_artifact_pack,
  )

if __name__ == "__main__":
  raise SystemExit(main())
