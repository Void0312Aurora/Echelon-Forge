#!/usr/bin/env python3
"""Write retained Stage B effect-scale candidate artifacts for A2.

This tool materializes the current author-side Stage B candidate artifacts into
stable files under the candidate package directory. It remains non-authoritative:
the retained pack only preserves current candidate evidence surfaces and does not
grant runtime authority or independent validation status.
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
from tools.maintenance.candidate_artifacts import scope_boundary_probe as scope_probe
from tools.maintenance.candidate_artifacts import effect_scale_snapshot as stage_b_snapshot
from tools.maintenance.candidate_artifacts import effect_scale_result_pack as result_pack
from tools.maintenance.candidate_artifacts import validation_scaffold as scaffold

PACKAGE_ID = (
  "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
  "beam_high_near_miss_0_35m_v0"
)
RETAINED_PACK_SCHEMA_VERSION = "a2.stage_b_retained_artifact_pack.v1"
MISSING_PACK_STATUS = "missing_retained_artifact_pack"
RETAINED_PACK_STATUS = "author_retained_candidate_artifacts_only"
RETENTION_SCOPE = "stage_b_effect_scale_author_side_candidate_only"
DEFAULT_OUTPUT_DIR = (
  A2_CANDIDATE_PACKAGE_DIR
  / "retained_artifacts"
  / "stage_b_effect_scale_20260530"
)

ARTIFACT_FILENAMES = {
  "validation_scaffold_snapshot": "validation_scaffold_snapshot.json",
  "scope_boundary_probe_snapshot": "scope_boundary_probe_snapshot.json",
  "stage_b_effect_scale_snapshot": "stage_b_effect_scale_snapshot.json",
  "stage_b_validation_result_pack": "stage_b_validation_result_pack.json",
}

ARTIFACT_RELEASE_BOUNDARIES = {
  "validation_scaffold_snapshot": {
    "origin_class": "author_side_validation_scaffold_snapshot_only",
    "allowed_claim": "candidate validation scaffold inputs and non-authoritative guards are retained",
    "forbidden_claim": (
      "independent validation, stock runtime authority, component-probability "
      "release, Pk authority, or deterministic-fuze authority"
    ),
  },
  "scope_boundary_probe_snapshot": {
    "origin_class": "author_side_scope_boundary_probe_only",
    "allowed_claim": "candidate near-miss and closure scope probe surface is retained",
    "forbidden_claim": (
      "reviewed closure physics, stock runtime authority, component-probability "
      "release, Pk authority, or deterministic-fuze authority"
    ),
  },
  "stage_b_effect_scale_snapshot": {
    "origin_class": "author_side_stage_b_hard_gate_snapshot_only",
    "allowed_claim": "author-side Stage B hard-gate snapshot is retained",
    "forbidden_claim": (
      "release readiness, stock runtime authority, component-probability "
      "release, Pk authority, or deterministic-fuze authority"
    ),
  },
  "stage_b_validation_result_pack": {
    "origin_class": "author_side_stage_b_result_pack_only",
    "allowed_claim": "author-side Stage B result pack and stable hashes are retained",
    "forbidden_claim": (
      "independent validation result, stock runtime authority, "
      "component-probability release, Pk authority, or deterministic-fuze authority"
    ),
  },
}

RETAINED_ORIGIN_SUMMARY = {
  "runtime_origin": "no_stock_runtime_descriptor_author_side_artifacts_only",
  "review_surface": "author_side_stage_b_effect_scale_candidate_only",
  "independent_release_artifact_present": False,
  "stock_runtime_authority_present": False,
  "stage_c_component_probability_artifacts_present": False,
}

def _build_artifacts(repo_root: Path) -> dict[str, dict[str, Any]]:
  return {
    "validation_scaffold_snapshot": scaffold.generate_validation_scaffold(
      repo_root=repo_root
    ),
    "scope_boundary_probe_snapshot": scope_probe.generate_scope_boundary_probe(
      repo_root=repo_root
    ),
    "stage_b_effect_scale_snapshot": stage_b_snapshot.generate_stage_b_effect_scale_snapshot(
      repo_root=repo_root
    ),
    "stage_b_validation_result_pack": result_pack.generate_stage_b_validation_result_pack(
      repo_root=repo_root
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
      "Write retained Stage B effect-scale candidate artifacts for the "
      "current A2 blast-fragmentation package."
    ),
    default_output_dir=DEFAULT_OUTPUT_DIR,
    generate=generate_retained_artifact_pack,
  )

if __name__ == "__main__":
  raise SystemExit(main())
