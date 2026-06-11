#!/usr/bin/env python3
"""Generate a Stage C component-probability candidate snapshot for A2.

This tool freezes the current author-side Stage C component-probability surface
for the narrow A2 blast-fragmentation candidate package. It stays explicitly
non-authoritative: the output documents the current test-local positive path
for component-specific probability authority, but it does not grant stock
runtime authority, validated fragility truth, Pk, or deterministic-fuze
authority.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.candidate_artifacts import runtime_authority_exercise as authority_pack
from tools.maintenance.candidate_artifacts import (
    component_probability_surface_probe as surface_probe,
)


PACKAGE_ID = (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
)
SNAPSHOT_SCHEMA_VERSION = "a2.stage_c_component_probability_snapshot.v1"


def _lookup(root: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = root
    for part in path:
        value = value[part]
    return value


def _criteria_rows(artifact: dict[str, Any]) -> list[dict[str, Any]]:
    descriptor = artifact["component_failure_probability_descriptor_candidate"]
    row = descriptor["rows"][0]
    baseline = artifact["baseline_event_summary"]
    primary_rows = [
        candidate
        for candidate in artifact["baseline_component_rows"]
        if candidate["component_name"] == baseline["component_primary_name"]
    ]
    if not primary_rows:
        raise AssertionError("Stage C snapshot expected one primary projected component row")
    primary_row = primary_rows[0]

    checks: list[dict[str, Any]] = [
        {
            "criteria_id": "BFM-CRIT-CP-001",
            "field_path": ("baseline_event_summary", "component_primary_name"),
            "expected": "right_aileron_actuator",
        },
        {
            "criteria_id": "BFM-CRIT-CP-002",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "source_kind",
            ),
            "expected": "validated_physics_surrogate",
        },
        {
            "criteria_id": "BFM-CRIT-CP-003",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "calibration_status",
            ),
            "expected": "calibrated",
        },
        {
            "criteria_id": "BFM-CRIT-CP-004",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "effect_scale_authority",
            ),
            "expected": False,
        },
        {
            "criteria_id": "BFM-CRIT-CP-005",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "component_failure_probability_authority",
            ),
            "expected": True,
        },
        {
            "criteria_id": "BFM-CRIT-CP-006",
            "field_path": ("component_failure_probability_descriptor_candidate", "pk_authority"),
            "expected": False,
        },
        {
            "criteria_id": "BFM-CRIT-CP-007",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "deterministic_fuze_authority",
            ),
            "expected": False,
        },
        {
            "criteria_id": "BFM-CRIT-CP-008",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "rows",
                "0",
                "component_name",
            ),
            "expected": "right_aileron_actuator",
        },
        {
            "criteria_id": "BFM-CRIT-CP-009",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "rows",
                "0",
                "component_system",
            ),
            "expected": "flight_control",
        },
        {
            "criteria_id": "BFM-CRIT-CP-010",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "rows",
                "0",
                "component_redundancy_group_id",
            ),
            "expected": "lateral_flight_control_actuators",
        },
        {
            "criteria_id": "BFM-CRIT-CP-011",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "rows",
                "0",
                "component_failure_probability",
            ),
            "expected": "0<=x<=1",
        },
        {
            "criteria_id": "BFM-CRIT-CP-012",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "rows",
                "0",
                "min_blast_scaled_distance_m_kg13",
            ),
            "expected": "<=primary_row.blast_scaled_distance",
        },
        {
            "criteria_id": "BFM-CRIT-CP-013",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "rows",
                "0",
                "max_blast_scaled_distance_m_kg13",
            ),
            "expected": ">=primary_row.blast_scaled_distance",
        },
        {
            "criteria_id": "BFM-CRIT-CP-014",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "rows",
                "0",
                "min_fragment_areal_density_per_m2",
            ),
            "expected": "<=primary_row.fragment_density",
        },
        {
            "criteria_id": "BFM-CRIT-CP-015",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "rows",
                "0",
                "max_fragment_areal_density_per_m2",
            ),
            "expected": ">=primary_row.fragment_density",
        },
        {
            "criteria_id": "BFM-CRIT-CP-016",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "rows",
                "0",
                "min_surface_incidence_cos",
            ),
            "expected": "<=primary_row.surface_incidence",
        },
        {
            "criteria_id": "BFM-CRIT-CP-017",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "rows",
                "0",
                "max_surface_incidence_cos",
            ),
            "expected": ">=primary_row.surface_incidence",
        },
        {
            "criteria_id": "BFM-CRIT-CP-018",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "rows",
                "0",
                "min_fragment_energy_j",
            ),
            "expected": "<=primary_row.fragment_energy",
        },
        {
            "criteria_id": "BFM-CRIT-CP-019",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "rows",
                "0",
                "max_fragment_energy_j",
            ),
            "expected": ">=primary_row.fragment_energy",
        },
        {
            "criteria_id": "BFM-CRIT-CP-020",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "rows",
                "0",
                "min_penetration_margin",
            ),
            "expected": "<=primary_row.penetration_margin",
        },
        {
            "criteria_id": "BFM-CRIT-CP-021",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "rows",
                "0",
                "max_penetration_margin",
            ),
            "expected": ">=primary_row.penetration_margin",
        },
        {
            "criteria_id": "BFM-CRIT-CP-022",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "rows",
                "0",
                "min_blast_impulse_kpa_ms",
            ),
            "expected": "<=primary_row.blast_impulse",
        },
        {
            "criteria_id": "BFM-CRIT-CP-023",
            "field_path": (
                "component_failure_probability_descriptor_candidate",
                "rows",
                "0",
                "max_blast_impulse_kpa_ms",
            ),
            "expected": ">=primary_row.blast_impulse",
        },
    ]

    rows: list[dict[str, Any]] = []
    for check in checks:
        field_path = check["field_path"]
        if "rows" in field_path:
            actual = row[field_path[-1]]
        else:
            actual = _lookup(artifact, field_path)
        expected = check["expected"]
        passed = False
        if expected in (True, False):
            passed = bool(actual) is bool(expected)
        elif expected == "0<=x<=1":
            passed = 0.0 <= float(actual) <= 1.0
        elif expected == "<=primary_row.blast_scaled_distance":
            passed = float(actual) <= float(primary_row["mechanism_blast_scaled_distance_m_kg13"])
        elif expected == ">=primary_row.blast_scaled_distance":
            passed = float(actual) >= float(primary_row["mechanism_blast_scaled_distance_m_kg13"])
        elif expected == "<=primary_row.fragment_density":
            passed = float(actual) <= float(primary_row["mechanism_fragment_areal_density_per_m2"])
        elif expected == ">=primary_row.fragment_density":
            passed = float(actual) >= float(primary_row["mechanism_fragment_areal_density_per_m2"])
        elif expected == "<=primary_row.surface_incidence":
            passed = float(actual) <= float(primary_row["mechanism_surface_incidence_cos"])
        elif expected == ">=primary_row.surface_incidence":
            passed = float(actual) >= float(primary_row["mechanism_surface_incidence_cos"])
        elif expected == "<=primary_row.fragment_energy":
            passed = float(actual) <= float(primary_row["mechanism_fragment_energy_j"])
        elif expected == ">=primary_row.fragment_energy":
            passed = float(actual) >= float(primary_row["mechanism_fragment_energy_j"])
        elif expected == "<=primary_row.penetration_margin":
            passed = float(actual) <= float(primary_row["mechanism_penetration_margin"])
        elif expected == ">=primary_row.penetration_margin":
            passed = float(actual) >= float(primary_row["mechanism_penetration_margin"])
        elif expected == "<=primary_row.blast_impulse":
            passed = float(actual) <= float(primary_row["mechanism_blast_impulse_kpa_ms"])
        elif expected == ">=primary_row.blast_impulse":
            passed = float(actual) >= float(primary_row["mechanism_blast_impulse_kpa_ms"])
        else:
            passed = str(actual) == str(expected)
        rows.append(
            {
                "criteria_id": check["criteria_id"],
                "field": ".".join(field_path),
                "expected": expected,
                "actual": actual,
                "pass": passed,
            }
        )
    return rows


def generate_stage_c_component_probability_snapshot(
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    artifact = authority_pack.generate_runtime_aligned_authority_pack(repo_root=repo_root)
    surface_probe_artifact = surface_probe.generate_stage_c_component_probability_surface_probe(
        repo_root=repo_root
    )
    criteria_rows = _criteria_rows(artifact)
    failed_ids = [row["criteria_id"] for row in criteria_rows if not row["pass"]]
    baseline = artifact["baseline_event_summary"]
    descriptor = artifact["component_failure_probability_descriptor_candidate"]
    row = descriptor["rows"][0]

    return {
        "package_id": PACKAGE_ID,
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "status": "candidate_non_authoritative_stage_c_component_probability_snapshot",
        "artifact_provenance": {
            "source_kind": "candidate_stage_c_component_probability_snapshot",
            "runtime_aligned_authority_pack_ref": (
                "tools/maintenance/damage_model_candidate_artifacts.py "
                "runtime-authority-exercise"
            ),
            "surface_probe_ref": (
                "tools/maintenance/damage_model_candidate_artifacts.py "
                "component-probability-surface-probe"
            ),
            "scope_definition_ref": (
                "docs/task/air_combat/archive/a2_high_fidelity_damage_model/"
                "narrow_scope_authority_loop_aim120c_blastfrag_f16c_block50_20260529.zh.md"
            ),
            "component_effects_acceptance_ref": (
                "docs/task/air_combat/archive/a2_high_fidelity_damage_model/component_effects/"
                "acceptance_tests_and_non_authoritative_boundaries_20260528.zh.md"
            ),
        },
        "scope": {
            "target_type": artifact["scope"]["target_type"],
            "weapon_class": artifact["scope"]["weapon_class"],
            "weapon_family": artifact["scope"]["weapon_family"],
            "aspect_bucket": artifact["scope"]["aspect_bucket"],
            "closure_bucket": artifact["scope"]["closure_bucket"],
            "candidate_scope_label": artifact["scope"]["candidate_scope_label"],
            "runtime_miss_distance_bucket": artifact["scope"]["runtime_miss_distance_bucket"],
            "component_name": str(row["component_name"]),
            "component_system": str(row["component_system"]),
            "component_redundancy_group_id": str(row["component_redundancy_group_id"]),
        },
        "criteria_evaluation": criteria_rows,
        "summary": {
            "all_hard_gates_pass_in_current_snapshot": not failed_ids,
            "failed_criteria_ids": failed_ids,
            "reviewed_checks": [
                "runtime_projected_component_row_present",
                "descriptor_authority_flags",
                "component_provenance_fields",
                "mechanism_load_gate_band_contains_primary_row",
                "component_probability_surface_probe",
            ],
            "primary_release_scope": "component_failure_probability_authority_only",
            "review_status": "author_snapshot_only_pending_independent_review",
        },
        "baseline_event_summary": {
            "component_primary_name": baseline["component_primary_name"],
            "component_primary_system": baseline["component_primary_system"],
            "component_primary_redundancy_group_id": baseline[
                "component_primary_redundancy_group_id"
            ],
            "component_failure_probability": baseline["component_failure_probability"],
            "component_failure_probability_source": baseline[
                "component_failure_probability_source"
            ],
            "component_primary_mechanism_blast_scaled_distance_m_kg13": baseline[
                "component_primary_mechanism_blast_scaled_distance_m_kg13"
            ],
            "component_primary_mechanism_fragment_areal_density_per_m2": baseline[
                "component_primary_mechanism_fragment_areal_density_per_m2"
            ],
            "component_primary_mechanism_fragment_energy_j": baseline[
                "component_primary_mechanism_fragment_energy_j"
            ],
            "component_primary_mechanism_penetration_margin": baseline[
                "component_primary_mechanism_penetration_margin"
            ],
            "component_primary_mechanism_blast_impulse_kpa_ms": baseline[
                "component_primary_mechanism_blast_impulse_kpa_ms"
            ],
            "component_primary_mechanism_surface_incidence_cos": baseline[
                "component_primary_mechanism_surface_incidence_cos"
            ],
        },
        "component_probability_snapshot": {
            "descriptor_status": "test_local_component_specific_probability_candidate",
            "dataset_id": descriptor["dataset_id"],
            "source_kind": descriptor["source_kind"],
            "calibration_status": descriptor["calibration_status"],
            "component_failure_probability_authority": descriptor[
                "component_failure_probability_authority"
            ],
            "row": row,
        },
        "surface_probe_summary": {
            "status": surface_probe_artifact["status"],
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
            "selected_row_ids": [
                str(candidate["selected_row_id"])
                for candidate in surface_probe_artifact["surface_probe_rows"]
            ],
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
            "anchor_seed_window_probability_cv": surface_probe_artifact[
                "repeatability_summary"
            ]["component_failure_probability"]["cv"],
            "stock_baseline_sources_are_synthetic_sigmoid": surface_probe_artifact[
                "stock_baseline_probe_summary"
            ]["all_probability_sources_are_synthetic_sigmoid"],
            "stock_baseline_calibrated_probability_present": surface_probe_artifact[
                "stock_baseline_probe_summary"
            ]["any_calibrated_component_probability"],
            "component_specific_rows_scope_locked_to_right_aileron_actuator": (
                surface_probe_artifact["component_scope_audit"][
                    "component_specific_rows_scope_locked_to_primary_component"
                ]
            ),
            "selected_rows_scope_locked_to_right_aileron_actuator": (
                surface_probe_artifact["component_scope_audit"][
                    "selected_rows_scope_locked_to_primary_component"
                ]
            ),
        },
        "current_findings": [
            (
                "the current runtime-aligned Stage C candidate can bind a "
                "component-specific probability row to the projected primary "
                "component within the narrow blast-fragmentation scope"
            ),
            (
                "the same narrow scope now also exposes a three-point candidate "
                "component-probability surface probe with monotonic inner-to-outer "
                "row selection"
            ),
            (
                "the baseline stock event still reports synthetic component "
                "probability, while the descriptor candidate demonstrates only a "
                "test-local authority surface"
            ),
            (
                "this snapshot does not validate fragility truth, independence, "
                "or stock component-probability authority release"
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
            "Generate the current author-side Stage C component-probability "
            "candidate snapshot for the A2 blast-fragmentation package."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path. Defaults to stdout.",
    )
    args = parser.parse_args(argv)

    artifact = generate_stage_c_component_probability_snapshot()
    payload = json.dumps(artifact, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
