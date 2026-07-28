#!/usr/bin/env python3
"""Generate a Stage C component-probability candidate validation result pack.

This tool packages the current non-authoritative Stage C component-probability
review artifacts into one machine-readable bundle with stable content hashes and
explicit independence semantics. It remains below runtime authority: the output
is a candidate review artifact and must not be treated as validated fragility
truth, stock runtime authority, Pk, or deterministic-fuze authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


_REPO_ROOT_HINT = str(Path(__file__).resolve().parents[3])
if _REPO_ROOT_HINT not in sys.path:
  sys.path.insert(0, _REPO_ROOT_HINT)

from python.runtime_bootstrap import ensure_repo_imports, repo_root

ensure_repo_imports()
REPO_ROOT = Path(repo_root())
from tools.maintenance.candidate_artifacts import runtime_authority_exercise as authority_pack
from tools.maintenance.release_governance import effect_scale_release_readiness as stage_b_gate
from tools.maintenance.candidate_artifacts import (
  component_probability_snapshot as stage_c_snapshot,
)
from tools.maintenance.candidate_artifacts import (
  component_probability_surface_probe as surface_probe,
)


PACKAGE_ID = (
  "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
  "beam_high_near_miss_0_35m_v0"
)
RESULT_PACK_SCHEMA_VERSION = "a2.stage_c_component_probability_result_pack.v1"


def _canonical_json(payload: dict[str, Any]) -> str:
  return json.dumps(payload, indent=2, sort_keys=True)


def _payload_sha256(payload: dict[str, Any]) -> str:
  canonical = _canonical_json(payload)
  return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _artifact_hash_rows(
  *,
  authority_artifact: dict[str, Any],
  stage_c_snapshot_artifact: dict[str, Any],
  surface_probe_artifact: dict[str, Any],
) -> list[dict[str, Any]]:
  return [
    {
      "artifact_id": "ART-RUNTIME-AUTH-001",
      "artifact_kind": "runtime_aligned_authority_exercise",
      "tool_ref": (
    "tools/maintenance/damage_model.py candidate-artifacts "
        "runtime-authority-exercise"
      ),
      "status": authority_artifact["status"],
      "sha256": _payload_sha256(authority_artifact),
    },
    {
      "artifact_id": "ART-STAGE-C-SNAPSHOT-001",
      "artifact_kind": "stage_c_component_probability_snapshot",
      "tool_ref": (
    "tools/maintenance/damage_model.py candidate-artifacts "
        "component-probability-snapshot"
      ),
      "status": stage_c_snapshot_artifact["status"],
      "sha256": _payload_sha256(stage_c_snapshot_artifact),
    },
    {
      "artifact_id": "ART-STAGE-C-SURFACE-001",
      "artifact_kind": "stage_c_component_probability_surface_probe",
      "tool_ref": (
    "tools/maintenance/damage_model.py candidate-artifacts "
        "component-probability-surface-probe"
      ),
      "status": surface_probe_artifact["status"],
      "sha256": _payload_sha256(surface_probe_artifact),
    },
  ]


def _independence_audit_rows() -> list[dict[str, str]]:
  return [
    {
      "artifact_id": "ART-RUNTIME-AUTH-001",
      "independence_class": "test_local_runtime_exercise_only",
      "current_release_role": "positive_path_runtime_shape_demonstration",
      "allowed_claim": "runtime-aligned component-specific positive path exists",
      "forbidden_claim": "stock runtime authority or independent fragility validation",
      "audit_outcome": "test_local_positive_path_only",
    },
    {
      "artifact_id": "ART-STAGE-C-SNAPSHOT-001",
      "independence_class": "author_side_candidate_snapshot_only",
      "current_release_role": "frozen_author_side_component_probability_snapshot",
      "allowed_claim": "author-side candidate snapshot and provenance surface exist",
      "forbidden_claim": "validated component fragility truth or released probability authority",
      "audit_outcome": "candidate_snapshot_only_not_independent_validation",
    },
    {
      "artifact_id": "ROW-COMPONENT-001",
      "independence_class": "component_specific_candidate_row_only",
      "current_release_role": "component-specific provenance and gate-band demonstration",
      "allowed_claim": "candidate row binds to one projected component with traceable fields",
      "forbidden_claim": "real actuator fragility curve or aircraft-wide failure probability truth",
      "audit_outcome": "candidate_component_specific_only",
    },
  ]


def _dedupe_preserve_order(values: list[str]) -> list[str]:
  return list(dict.fromkeys(values))


def generate_stage_c_component_probability_result_pack(
  *,
  repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
  authority_artifact = authority_pack.generate_runtime_aligned_authority_pack(
    repo_root=repo_root
  )
  stage_c_snapshot_artifact = stage_c_snapshot.generate_stage_c_component_probability_snapshot(
    repo_root=repo_root
  )
  surface_probe_artifact = surface_probe.generate_stage_c_component_probability_surface_probe(
    repo_root=repo_root
  )
  stage_b_gate_artifact = stage_b_gate.generate_stage_b_release_readiness_gate(
    repo_root=repo_root
  )
  artifact_hashes = _artifact_hash_rows(
    authority_artifact=authority_artifact,
    stage_c_snapshot_artifact=stage_c_snapshot_artifact,
    surface_probe_artifact=surface_probe_artifact,
  )
  artifact_hash_map = {row["artifact_id"]: row["sha256"] for row in artifact_hashes}
  baseline = authority_artifact["baseline_event_summary"]
  row = authority_artifact["component_failure_probability_descriptor_candidate"]["rows"][0]
  snapshot_summary = stage_c_snapshot_artifact["summary"]
  surface_summary = surface_probe_artifact["repeatability_summary"]

  return {
    "package_id": PACKAGE_ID,
    "schema_version": RESULT_PACK_SCHEMA_VERSION,
    "status": "candidate_non_authoritative_stage_c_component_probability_result_pack",
    "scope": dict(stage_c_snapshot_artifact["scope"]),
    "artifact_hashes": artifact_hashes,
    "result_table_summary": {
      "all_hard_gates_pass_in_current_snapshot": snapshot_summary[
        "all_hard_gates_pass_in_current_snapshot"
      ],
      "failed_criteria_ids": list(snapshot_summary["failed_criteria_ids"]),
      "reviewed_checks": list(snapshot_summary["reviewed_checks"]),
      "primary_release_scope": snapshot_summary["primary_release_scope"],
      "review_status": "author_result_pack_only_pending_independent_review",
      "evidence_artifact_hashes": {
        "runtime_aligned_authority_exercise": artifact_hash_map[
          "ART-RUNTIME-AUTH-001"
        ],
        "stage_c_snapshot": artifact_hash_map["ART-STAGE-C-SNAPSHOT-001"],
        "stage_c_surface_probe": artifact_hash_map["ART-STAGE-C-SURFACE-001"],
      },
    },
    "component_probability_result_summary": {
      "baseline_component_probability_source": str(
        baseline["component_failure_probability_source"]
      ),
      "baseline_component_probability": float(
        baseline["component_failure_probability"]
      ),
      "candidate_component_name": str(row["component_name"]),
      "candidate_component_system": str(row["component_system"]),
      "candidate_component_redundancy_group_id": str(
        row["component_redundancy_group_id"]
      ),
      "candidate_component_failure_probability": float(
        row["component_failure_probability"]
      ),
      "result_interpretation": (
        "candidate component-specific probability snapshot only; not an "
        "independently reviewed fragility curve or uncertainty boundary"
      ),
    },
    "scope_audit_summary": {
      "projected_component_row_count": len(authority_artifact["baseline_component_rows"]),
      "primary_component_name": str(baseline["component_primary_name"]),
      "gate_band_contains_primary_blast_scaled_distance": (
        float(row["min_blast_scaled_distance_m_kg13"])
        <= float(baseline["component_primary_mechanism_blast_scaled_distance_m_kg13"])
        <= float(row["max_blast_scaled_distance_m_kg13"])
      ),
      "gate_band_contains_primary_fragment_density": (
        float(row["min_fragment_areal_density_per_m2"])
        <= float(
          baseline["component_primary_mechanism_fragment_areal_density_per_m2"]
        )
        <= float(row["max_fragment_areal_density_per_m2"])
      ),
      "gate_band_contains_primary_fragment_energy": (
        float(row["min_fragment_energy_j"])
        <= float(baseline["component_primary_mechanism_fragment_energy_j"])
        <= float(row["max_fragment_energy_j"])
      ),
      "gate_band_contains_primary_penetration_margin": (
        float(row["min_penetration_margin"])
        <= float(baseline["component_primary_mechanism_penetration_margin"])
        <= float(row["max_penetration_margin"])
      ),
      "gate_band_contains_primary_blast_impulse": (
        float(row["min_blast_impulse_kpa_ms"])
        <= float(baseline["component_primary_mechanism_blast_impulse_kpa_ms"])
        <= float(row["max_blast_impulse_kpa_ms"])
      ),
      "gate_band_contains_primary_surface_incidence": (
        float(row["min_surface_incidence_cos"])
        <= float(baseline["component_primary_mechanism_surface_incidence_cos"])
        <= float(row["max_surface_incidence_cos"])
      ),
      "scope_guard_interpretation": (
        "Stage C currently proves only one component-specific candidate row "
        "inside the narrow scope; it does not yet establish wider fragility "
        "coverage or independent probability validation"
      ),
    },
    "fragility_surface_summary": {
      "surface_probe_status": surface_probe_artifact["status"],
      "probe_row_count": len(surface_probe_artifact["surface_probe_rows"]),
      "probe_labels": [
        str(candidate["probe_label"])
        for candidate in surface_probe_artifact["surface_probe_rows"]
      ],
      "runtime_seed_values_are_fixed": surface_probe_artifact[
        "determinism_summary"
      ]["runtime_seed_values_are_fixed"],
      "json_output_uses_sort_keys": surface_probe_artifact[
        "determinism_summary"
      ]["json_output_uses_sort_keys"],
      "primary_component_identity_stable_pass": surface_probe_artifact["metrics"][
        "primary_component_identity_stable_pass"
      ],
      "component_specific_precedence_pass": surface_probe_artifact["metrics"][
        "component_specific_precedence_pass"
      ],
      "selected_rows_cover_primary_loads_pass": surface_probe_artifact["metrics"][
        "selected_rows_cover_primary_loads_pass"
      ],
      "probability_monotonic_decreasing_with_standoff_pass": (
        surface_probe_artifact["metrics"][
          "probability_monotonic_decreasing_with_standoff_pass"
        ]
      ),
      "anchor_seed_window_probability_cv": surface_summary[
        "component_failure_probability"
      ]["cv"],
      "result_interpretation": (
        "candidate fragility-surface and runtime repeatability snapshot only; "
        "not an independently reviewed fragility curve or uncertainty boundary"
      ),
      "stock_baseline_sources_are_synthetic_sigmoid": surface_probe_artifact[
        "stock_baseline_probe_summary"
      ]["all_probability_sources_are_synthetic_sigmoid"],
      "component_scope_locked_to_right_aileron_actuator": surface_probe_artifact[
        "component_scope_audit"
      ]["component_specific_rows_scope_locked_to_primary_component"],
    },
    "upstream_stage_b_dependency_summary": {
      "dependency_role": "separate_upstream_effect_scale_authority_track",
      "status": stage_b_gate_artifact["status"],
      "release_target": stage_b_gate_artifact["release_target"],
      "readiness_level": stage_b_gate_artifact["readiness_level"],
      "blocking_residual_ids": _dedupe_preserve_order(
        list(stage_b_gate_artifact["blocking_residual_ids"])
      ),
      "dependency_preserved_as_blocked": (
        stage_b_gate_artifact["status"]
        == "blocked_non_authoritative_stage_b_release_candidate"
        and stage_b_gate_artifact["release_target"]
        == "effect_scale_authority_only"
      ),
      "stage_c_interlock": (
        "Stage C component-probability packaging remains candidate "
        "review hygiene and cannot be promoted while the separate Stage B "
        "effect-scale release gate is blocked"
      ),
    },
    "independence_audit": _independence_audit_rows(),
    "current_findings": [
      (
        "the current result pack consolidates the runtime-aligned authority "
        "exercise, the Stage C snapshot and the Stage C surface probe under "
        "stable content hashes"
      ),
      (
        "the candidate surface probe now shows monotonic component-specific "
        "row selection inside the narrow near-miss bucket, while the baseline "
        "stock event still reports synthetic component probability"
      ),
      (
        "Stage C still lacks independent fragility validation, uncertainty "
        "closeout and stock authority release"
      ),
    ],
    "non_authoritative_guards": {
      "stock_runtime_authority_granted": False,
      "effect_scale_authority_granted": False,
      "component_failure_probability_authority_granted": False,
      "pk_authority_granted": False,
      "deterministic_fuze_authority_granted": False,
    },
  }


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description=(
      "Generate the Stage C component-probability candidate validation "
      "result pack for the current A2 blast-fragmentation package."
    )
  )
  parser.add_argument(
    "--output",
    type=Path,
    help="Optional JSON output path. Defaults to stdout.",
  )
  args = parser.parse_args(argv)

  artifact = generate_stage_c_component_probability_result_pack()
  payload = _canonical_json(artifact)
  if args.output:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload + "\n", encoding="utf-8")
  else:
    print(payload)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
