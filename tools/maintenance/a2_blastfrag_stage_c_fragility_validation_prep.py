#!/usr/bin/env python3
"""Prepare Stage C component-probability fragility review inputs for A2.

This tool converts the current Stage C component-probability candidate artifacts
into a bounded independent-review prep packet. It deliberately does not grant
stock authority: the output is a fragility validation matrix, uncertainty
closeout plan, independence trace and baseline-replacement path for the
right_aileron_actuator candidate only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.candidate_artifacts import component_probability_result_pack as result_pack  # noqa: E402
from tools.maintenance.candidate_artifacts import component_probability_review_readiness as review_gate  # noqa: E402
from tools.maintenance.candidate_artifacts import component_probability_surface_probe as surface_probe  # noqa: E402


PACKAGE_ID = (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
)
PREP_SCHEMA_VERSION = "a2.stage_c_fragility_validation_prep.v1"
PRIMARY_COMPONENT_NAME = "right_aileron_actuator"
PRIMARY_COMPONENT_SYSTEM = "flight_control"
PRIMARY_COMPONENT_REDUNDANCY_GROUP = "lateral_flight_control_actuators"
STAGE_C_PREP_RESIDUALS = ("RES-009", "RES-010", "RES-011", "RES-012")


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _blocking_conditions_by_residual(
    gate_artifact: dict[str, Any],
) -> dict[str, list[dict[str, str]]]:
    by_residual: dict[str, list[dict[str, str]]] = {}
    for row in gate_artifact["blocking_conditions"]:
        residual_id = str(row["residual_id"])
        by_residual.setdefault(residual_id, []).append(row)
    return by_residual


def _residual_gate_results(gate_artifact: dict[str, Any]) -> list[dict[str, Any]]:
    blockers = _blocking_conditions_by_residual(gate_artifact)
    closeout_requirements = {
        "RES-009": (
            "Run and independently review a component fragility curve/benchmark for "
            "right_aileron_actuator; prove the candidate evidence-row mapping is not "
            "a synthetic_sigmoid substitute or a test-local positive path."
        ),
        "RES-010": (
            "Attach the pre-run Stage C criteria to a formal result table, validation "
            "manifest update and independent reviewer signoff."
        ),
        "RES-011": (
            "Close probability uncertainty with calibrated coverage metrics, seed and "
            "scenario spread, and reviewer-accepted uncertainty bounds."
        ),
        "RES-012": (
            "Audit benchmark/input separation at result level and record independent "
            "reviewer confirmation that the benchmark does not circularly reuse model "
            "inputs or tuning rows."
        ),
    }
    prep_outputs = {
        "RES-009": [
            "fragility_validation_matrix",
            "baseline_synthetic_sigmoid_vs_candidate_evidence_row_replacement_path",
        ],
        "RES-010": [
            "fragility_validation_matrix",
            "review_entry_artifact_inventory",
        ],
        "RES-011": [
            "author_side_uncertainty_probe",
            "uncertainty_closeout_plan",
        ],
        "RES-012": [
            "independence_trace",
            "stage_b_dependency_interlock",
        ],
    }
    results: list[dict[str, Any]] = []
    for residual_id in STAGE_C_PREP_RESIDUALS:
        residual_blockers = blockers.get(residual_id, [])
        results.append(
            {
                "residual_id": residual_id,
                "current_gate_result": (
                    "blocked_non_authoritative"
                    if residual_blockers
                    else "not_blocked_by_current_gate"
                ),
                "blocking_condition_ids": [
                    str(row["blocker_id"]) for row in residual_blockers
                ],
                "blocking_summaries": [str(row["summary"]) for row in residual_blockers],
                "prep_outputs_added": prep_outputs[residual_id],
                "required_to_close": closeout_requirements[residual_id],
                "authority_release_effect": (
                    "continues_to_block_stage_c_component_probability_authority"
                ),
            }
        )
    return results


def _fragility_validation_matrix(
    *,
    result_artifact: dict[str, Any],
    surface_artifact: dict[str, Any],
    gate_artifact: dict[str, Any],
) -> list[dict[str, Any]]:
    surface_rows = surface_artifact["surface_probe_rows"]
    probe_row_ids = [str(row["selected_row_id"]) for row in surface_rows]
    probe_probabilities = [
        float(row["component_failure_probability"]) for row in surface_rows
    ]
    return [
        {
            "matrix_id": "FRAG-MAT-CP-001",
            "residual_links": ["RES-009", "RES-010"],
            "review_question": (
                "Does the candidate review surface remain locked to "
                "right_aileron_actuator and its flight-control redundancy group?"
            ),
            "executable_artifact": (
                "tools/maintenance/damage_model_candidate_artifacts.py "
                "component-probability-surface-probe"
            ),
            "current_author_side_result": (
                "pass_candidate_only"
                if surface_artifact["metrics"]["primary_component_identity_stable_pass"]
                else "fail"
            ),
            "evidence_summary": {
                "component_name": PRIMARY_COMPONENT_NAME,
                "component_system": PRIMARY_COMPONENT_SYSTEM,
                "component_redundancy_group_id": PRIMARY_COMPONENT_REDUNDANCY_GROUP,
            },
            "release_interpretation": (
                "component identity is reviewable, but not independently audited truth"
            ),
        },
        {
            "matrix_id": "FRAG-MAT-CP-002",
            "residual_links": ["RES-009", "RES-010"],
            "review_question": (
                "Does each candidate row cover the primary mechanism-load gate band "
                "for the projected component?"
            ),
            "executable_artifact": (
                "tools/maintenance/damage_model_candidate_artifacts.py "
                "component-probability-surface-probe"
            ),
            "current_author_side_result": (
                "pass_candidate_only"
                if surface_artifact["metrics"]["selected_rows_cover_primary_loads_pass"]
                else "fail"
            ),
            "evidence_summary": {
                "probe_labels": [
                    str(row["probe_label"]) for row in surface_rows
                ],
                "selected_row_ids": probe_row_ids,
                "all_selected_rows_cover_primary_loads": all(
                    bool(row["selected_row_covers_primary_loads"])
                    for row in surface_rows
                ),
            },
            "release_interpretation": (
                "load-gate coverage is ready for reviewer audit, not authority release"
            ),
        },
        {
            "matrix_id": "FRAG-MAT-CP-003",
            "residual_links": ["RES-009"],
            "review_question": (
                "Is the baseline still synthetic_sigmoid, and therefore not a "
                "release-grade component fragility curve?"
            ),
            "executable_artifact": (
                "tools/maintenance/damage_model_candidate_artifacts.py "
                "component-probability-result-pack"
            ),
            "current_author_side_result": (
                "blocked_expected_non_authoritative"
                if result_artifact["component_probability_result_summary"][
                    "baseline_component_probability_source"
                ]
                == "synthetic_sigmoid"
                else "unexpected_baseline_source"
            ),
            "evidence_summary": {
                "baseline_component_probability_source": result_artifact[
                    "component_probability_result_summary"
                ]["baseline_component_probability_source"],
                "candidate_component_failure_probability": result_artifact[
                    "component_probability_result_summary"
                ]["candidate_component_failure_probability"],
            },
            "release_interpretation": (
                "synthetic baseline must be replaced only after independent fragility "
                "closeout and descriptor review"
            ),
        },
        {
            "matrix_id": "FRAG-MAT-CP-004",
            "residual_links": ["RES-009", "RES-011"],
            "review_question": (
                "Is the author-side candidate surface monotonic with standoff inside "
                "the narrow near-miss bucket?"
            ),
            "executable_artifact": (
                "tools/maintenance/damage_model_candidate_artifacts.py "
                "component-probability-surface-probe"
            ),
            "current_author_side_result": (
                "pass_candidate_only"
                if surface_artifact["metrics"][
                    "probability_monotonic_decreasing_with_standoff_pass"
                ]
                else "fail"
            ),
            "evidence_summary": {
                "probe_probabilities": probe_probabilities,
                "probe_row_ids": probe_row_ids,
            },
            "release_interpretation": (
                "monotonic candidate behavior is an author-side review input only"
            ),
        },
        {
            "matrix_id": "FRAG-MAT-CP-005",
            "residual_links": ["RES-011"],
            "review_question": (
                "Is the fixed-seed repeatability probe stable enough to hand to an "
                "uncertainty reviewer?"
            ),
            "executable_artifact": (
                "tools/maintenance/damage_model_candidate_artifacts.py "
                "component-probability-surface-probe"
            ),
            "current_author_side_result": (
                "pass_candidate_only"
                if surface_artifact["metrics"]["anchor_seed_window_cv_pass"]
                else "fail"
            ),
            "evidence_summary": {
                "seed_values": surface_artifact["repeatability_summary"]["seed_values"],
                "component_failure_probability_cv": surface_artifact[
                    "repeatability_summary"
                ]["component_failure_probability"]["cv"],
            },
            "release_interpretation": (
                "repeatability exists for the toy candidate probe, but uncertainty "
                "coverage remains open"
            ),
        },
        {
            "matrix_id": "FRAG-MAT-CP-006",
            "residual_links": ["RES-012"],
            "review_question": (
                "Are input/tuning artifacts separated from output/result artifacts in "
                "the review packet?"
            ),
            "executable_artifact": (
                "tools/maintenance/damage_model_candidate_artifacts.py "
                "component-probability-result-pack"
            ),
            "current_author_side_result": (
                "prepared_pending_independent_audit"
                if result_artifact["independence_audit"]
                else "missing_trace"
            ),
            "evidence_summary": {
                "independence_rows": [
                    row["artifact_id"] for row in result_artifact["independence_audit"]
                ],
                "review_gate_has_res012_blocker": "RES-012"
                in gate_artifact["blocking_residual_ids"],
            },
            "release_interpretation": (
                "separation trace is ready to inspect, but independent audit is not closed"
            ),
        },
        {
            "matrix_id": "FRAG-MAT-CP-007",
            "residual_links": ["RES-010", "RES-012"],
            "review_question": (
                "Does Stage C preserve the blocked Stage B effect-scale dependency "
                "instead of promoting component probability independently?"
            ),
            "executable_artifact": (
                "tools/maintenance/damage_model_candidate_artifacts.py "
                "component-probability-review-readiness"
            ),
            "current_author_side_result": (
                "dependency_preserved_as_blocked"
                if result_artifact["upstream_stage_b_dependency_summary"][
                    "dependency_preserved_as_blocked"
                ]
                else "dependency_interlock_missing"
            ),
            "evidence_summary": {
                "stage_b_status": result_artifact[
                    "upstream_stage_b_dependency_summary"
                ]["status"],
                "stage_b_blocking_residual_ids": result_artifact[
                    "upstream_stage_b_dependency_summary"
                ]["blocking_residual_ids"],
            },
            "release_interpretation": (
                "Stage C may prepare review inputs, but cannot outrun blocked Stage B"
            ),
        },
    ]


def _author_side_uncertainty_probe(
    surface_artifact: dict[str, Any],
) -> dict[str, Any]:
    repeatability = surface_artifact["repeatability_summary"]
    metrics = surface_artifact["metrics"]
    return {
        "probe_status": "author_side_repeatability_probe_only",
        "anchor_probe_label": repeatability["anchor_probe_label"],
        "seed_values": repeatability["seed_values"],
        "selected_row_ids": repeatability["selected_row_ids"],
        "component_failure_probability": repeatability[
            "component_failure_probability"
        ],
        "mechanism_load_repeatability": {
            "fragment_areal_density_per_m2": repeatability[
                "fragment_areal_density_per_m2"
            ],
            "fragment_energy_j": repeatability["fragment_energy_j"],
            "penetration_margin": repeatability["penetration_margin"],
            "blast_impulse_kpa_ms": repeatability["blast_impulse_kpa_ms"],
        },
        "current_author_side_result": (
            "repeatability_probe_pass_candidate_only"
            if metrics["anchor_seed_window_cv_pass"]
            else "repeatability_probe_failed"
        ),
        "not_covered": [
            "independent Brier/log-loss or calibration-curve scoring",
            "scenario spread outside the three-point author-side surface probe",
            "reviewer-accepted confidence or coverage interval",
            "release-grade uncertainty budget for stock descriptor admission",
        ],
    }


def _uncertainty_closeout_plan() -> list[dict[str, Any]]:
    return [
        {
            "plan_id": "UNC-CP-001",
            "residual_id": "RES-011",
            "owner_role": "independent_fragility_reviewer",
            "required_input": "frozen Stage C fragility validation matrix and retained prep artifact",
            "required_output": "reviewer-owned uncertainty result table",
            "acceptance_signal": "coverage metrics pass pre-declared Stage C thresholds",
        },
        {
            "plan_id": "UNC-CP-002",
            "residual_id": "RES-011",
            "owner_role": "author_support_only",
            "required_input": "author-side repeatability probe and surface probe rows",
            "required_output": "reviewer-auditable seed/scenario spread ledger",
            "acceptance_signal": (
                "author-side fixed-seed repeatability is reproducible and clearly "
                "separated from release-grade uncertainty claims"
            ),
        },
        {
            "plan_id": "UNC-CP-003",
            "residual_id": "RES-011",
            "owner_role": "release_reviewer",
            "required_input": "candidate evidence-row replacement path",
            "required_output": "explicit decision to retain or reject the evidence-row probabilities",
            "acceptance_signal": (
                "synthetic_sigmoid is not replaced unless uncertainty and fragility "
                "validation both pass"
            ),
        },
    ]


def _independence_trace(
    *,
    result_artifact: dict[str, Any],
    gate_artifact: dict[str, Any],
) -> dict[str, Any]:
    stage_b_dependency = result_artifact["upstream_stage_b_dependency_summary"]
    return {
        "trace_status": "prepared_pending_independent_result_audit",
        "residual_id": "RES-012",
        "input_or_tuning_layer": [
            {
                "artifact_id": "INPUT-CP-001",
                "artifact_kind": "candidate_descriptor_rows",
                "role": "candidate evidence-row inputs only",
                "forbidden_use": "validation benchmark truth or reviewer result",
            },
            {
                "artifact_id": "INPUT-CP-002",
                "artifact_kind": "runtime_aligned_authority_exercise_fixture",
                "role": "test-local positive-path exercise",
                "forbidden_use": "stock descriptor admission evidence",
            },
        ],
        "result_or_review_layer": [
            {
                "artifact_id": "RESULT-CP-001",
                "artifact_kind": "stage_c_component_probability_result_pack",
                "role": "author-side consolidated result snapshot",
                "current_independence_class": "candidate_result_pack_only",
            },
            {
                "artifact_id": "RESULT-CP-002",
                "artifact_kind": "stage_c_fragility_validation_prep",
                "role": "reviewer input matrix and closeout plan",
                "current_independence_class": "prep_packet_only",
            },
        ],
        "existing_independence_audit_rows": result_artifact["independence_audit"],
        "stage_b_dependency_interlock": {
            "dependency_role": stage_b_dependency["dependency_role"],
            "stage_b_status": stage_b_dependency["status"],
            "stage_b_release_target": stage_b_dependency["release_target"],
            "dependency_preserved_as_blocked": stage_b_dependency[
                "dependency_preserved_as_blocked"
            ],
            "stage_b_blocking_residual_ids": stage_b_dependency[
                "blocking_residual_ids"
            ],
            "stage_c_must_not_promote_before_stage_b_release": True,
        },
        "open_independence_blockers": [
            row
            for row in gate_artifact["blocking_conditions"]
            if row["residual_id"] == "RES-012"
        ],
        "required_independent_review_record": (
            "reviewer-owned signoff that benchmark outputs, acceptance thresholds "
            "and descriptor/tuning inputs are separated and non-circular"
        ),
    }


def _baseline_replacement_path(
    *,
    result_artifact: dict[str, Any],
    surface_artifact: dict[str, Any],
) -> dict[str, Any]:
    probability_summary = result_artifact["component_probability_result_summary"]
    surface_rows = surface_artifact["surface_probe_rows"]
    return {
        "path_status": "defined_but_not_authorized",
        "baseline": {
            "component_probability_source": probability_summary[
                "baseline_component_probability_source"
            ],
            "component_name": probability_summary["candidate_component_name"],
            "authority_role": "stock_runtime_baseline_remains_closed",
            "replacement_allowed_now": False,
        },
        "candidate_evidence_row_surface": [
            {
                "probe_label": row["probe_label"],
                "candidate_row_id": row["component_failure_probability_evidence_row_id"],
                "candidate_probability": row["component_failure_probability"],
                "candidate_probability_source": row[
                    "component_failure_probability_source"
                ],
                "candidate_evidence_source_ref": row[
                    "component_failure_probability_evidence_source_ref"
                ],
                "candidate_evidence_provenance": row[
                    "component_failure_probability_evidence_provenance"
                ],
                "component_name": row["component_primary_name"],
                "component_system": row["component_primary_system"],
                "component_redundancy_group_id": row[
                    "component_primary_redundancy_group_id"
                ],
            }
            for row in surface_rows
        ],
        "replacement_sequence": [
            "retain synthetic_sigmoid as non-authoritative stock baseline",
            "run independent fragility validation against the frozen matrix",
            "close RES-009, RES-010, RES-011 and RES-012 with reviewer-owned records",
            "re-check Stage B effect-scale release dependency before Stage C promotion",
            "only then consider a separate stock descriptor admission review",
        ],
        "forbidden_shortcuts": [
            "do not copy the test-local candidate rows into stock descriptors",
            "do not treat component_failure_probability_calibrated=true in a fixture as stock authority",
            "do not promote baseline replacement while Stage B remains blocked",
        ],
    }


def _review_entry_artifact_inventory(
    *,
    result_artifact: dict[str, Any],
    surface_artifact: dict[str, Any],
    gate_artifact: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "artifact_id": "REVIEW-CP-001",
            "artifact_kind": "stage_c_result_pack",
            "tool_ref": (
                "tools/maintenance/damage_model_candidate_artifacts.py "
                "component-probability-result-pack"
            ),
            "current_status": result_artifact["status"],
            "review_role": "author-side current result summary",
        },
        {
            "artifact_id": "REVIEW-CP-002",
            "artifact_kind": "stage_c_surface_probe",
            "tool_ref": (
                "tools/maintenance/damage_model_candidate_artifacts.py "
                "component-probability-surface-probe"
            ),
            "current_status": surface_artifact["status"],
            "review_role": "fragility-surface and repeatability input",
        },
        {
            "artifact_id": "REVIEW-CP-003",
            "artifact_kind": "stage_c_review_readiness_gate",
            "tool_ref": (
                "tools/maintenance/damage_model_candidate_artifacts.py "
                "component-probability-review-readiness"
            ),
            "current_status": gate_artifact["status"],
            "review_role": "blocked authority boundary and residual gate",
        },
        {
            "artifact_id": "REVIEW-CP-004",
            "artifact_kind": "stage_c_fragility_validation_prep",
            "tool_ref": "tools/maintenance/a2_blastfrag_stage_c_fragility_validation_prep.py",
            "current_status": "prep_packet_generated_by_this_tool",
            "review_role": "independent fragility review entry matrix",
        },
    ]


def generate_stage_c_fragility_validation_prep(
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    result_artifact = result_pack.generate_stage_c_component_probability_result_pack(
        repo_root=repo_root
    )
    surface_artifact = surface_probe.generate_stage_c_component_probability_surface_probe(
        repo_root=repo_root
    )
    gate_artifact = review_gate.generate_stage_c_component_probability_review_readiness_gate(
        repo_root=repo_root
    )
    scope = gate_artifact["scope"]
    non_authoritative_guards = gate_artifact["non_authoritative_guards"]
    stage_b_dependency = result_artifact["upstream_stage_b_dependency_summary"]

    authority_guards = {
        "stock_descriptor_created": bool(
            non_authoritative_guards["stock_descriptor_created"]
        ),
        "stock_database_authority_granted": bool(
            non_authoritative_guards["stock_database_authority_granted"]
        ),
        "stock_component_probability_authority": bool(
            non_authoritative_guards["component_failure_probability_authority_in_stock"]
        ),
        "pk_authority": bool(non_authoritative_guards["pk_authority"]),
        "deterministic_fuze_authority": bool(
            non_authoritative_guards["deterministic_fuze_authority"]
        ),
        "stage_c_candidate_bundle_role": non_authoritative_guards[
            "candidate_bundle_role"
        ],
    }

    return {
        "package_id": PACKAGE_ID,
        "schema_version": PREP_SCHEMA_VERSION,
        "status": (
            "prepared_non_authoritative_stage_c_fragility_validation_review_inputs"
        ),
        "readiness_level": (
            "fragility_review_input_packet_ready_but_authority_release_blocked"
        ),
        "scope": {
            "target_type": scope["target_type"],
            "weapon_class": scope["weapon_class"],
            "weapon_family": scope["weapon_family"],
            "aspect_bucket": scope["aspect_bucket"],
            "closure_bucket": scope["closure_bucket"],
            "miss_distance_bucket": scope["miss_distance_bucket"],
            "candidate_scope_label": scope["candidate_scope_label"],
            "component_name": scope["component_name"],
            "component_system": scope["component_system"],
            "component_redundancy_group_id": scope[
                "component_redundancy_group_id"
            ],
        },
        "residual_gate_results": _residual_gate_results(gate_artifact),
        "fragility_validation_matrix": _fragility_validation_matrix(
            result_artifact=result_artifact,
            surface_artifact=surface_artifact,
            gate_artifact=gate_artifact,
        ),
        "author_side_uncertainty_probe": _author_side_uncertainty_probe(
            surface_artifact
        ),
        "uncertainty_closeout_plan": _uncertainty_closeout_plan(),
        "independence_trace": _independence_trace(
            result_artifact=result_artifact,
            gate_artifact=gate_artifact,
        ),
        "baseline_synthetic_sigmoid_vs_candidate_evidence_row_replacement_path": (
            _baseline_replacement_path(
                result_artifact=result_artifact,
                surface_artifact=surface_artifact,
            )
        ),
        "stage_b_dependency_interlock": {
            "dependency_role": stage_b_dependency["dependency_role"],
            "stage_b_status": stage_b_dependency["status"],
            "stage_b_release_target": stage_b_dependency["release_target"],
            "stage_b_readiness_level": stage_b_dependency["readiness_level"],
            "stage_b_blocking_residual_ids": _dedupe_preserve_order(
                list(stage_b_dependency["blocking_residual_ids"])
            ),
            "dependency_preserved_as_blocked": stage_b_dependency[
                "dependency_preserved_as_blocked"
            ],
            "interlock_result": (
                "dependency_preserved_no_stage_c_authority_promotion"
            ),
        },
        "review_entry_artifact_inventory": _review_entry_artifact_inventory(
            result_artifact=result_artifact,
            surface_artifact=surface_artifact,
            gate_artifact=gate_artifact,
        ),
        "authority_guards": authority_guards,
        "review_packet_summary": {
            "ready_to_request_independent_fragility_review": True,
            "independent_fragility_review_closed": False,
            "authority_release_ready": False,
            "residuals_still_blocking_authority": list(STAGE_C_PREP_RESIDUALS),
            "stage_b_dependency_preserved_as_blocked": stage_b_dependency[
                "dependency_preserved_as_blocked"
            ],
            "stock_authority_remains_closed": not authority_guards[
                "stock_component_probability_authority"
            ],
        },
        "explicit_boundaries": [
            "prep packet only; not an independent fragility review result",
            "do not create or update stock runtime descriptors from this artifact",
            "do not promote component probability while Stage B effect-scale is blocked",
            "pk_authority=false and deterministic_fuze_authority=false remain mandatory",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the Stage C component-probability fragility validation prep "
            "packet for the current A2 blast-fragmentation candidate package."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path. Defaults to stdout.",
    )
    args = parser.parse_args()

    artifact = generate_stage_c_fragility_validation_prep()
    payload = _canonical_json(artifact)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
