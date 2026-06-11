from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.architecture.helpers import REPO_ROOT, ensure_repo_root_on_sys_path, read_json
from tests.architecture.damage_model.helpers import run_maintenance_cli

ensure_repo_root_on_sys_path()

from tools.maintenance.candidate_artifacts import component_probability_review_readiness as readiness_gate  # noqa: E402
from tools.maintenance import (  # noqa: E402
    a2_blastfrag_stage_c_fragility_benchmark as benchmark,
)
from tools.maintenance import (  # noqa: E402
    a2_blastfrag_stage_c_fragility_review_gate as review_gate,
)
from tools.maintenance import (  # noqa: E402
    a2_blastfrag_stage_c_fragility_validation_prep as prep,
)


def test_component_probability_review_readiness_gate_is_blocked() -> None:
    artifact = readiness_gate.generate_stage_c_component_probability_review_readiness_gate(
        repo_root=REPO_ROOT
    )

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert (
        artifact["schema_version"]
        == "a2.stage_c_component_probability_review_readiness_gate.v1"
    )
    assert artifact["status"] == "blocked_non_authoritative_stage_c_review_candidate"
    assert artifact["review_target"] == "component_failure_probability_authority_only"
    assert (
        artifact["readiness_level"]
        == "author_side_component_candidate_ready_but_not_fragility_review_closed"
    )

    scope = artifact["scope"]
    assert scope["target_type"] == "F-16C_Block50"
    assert scope["weapon_class"] == "AIM-120C-class"
    assert scope["weapon_family"] == "blast_fragmentation"
    assert scope["aspect_bucket"] == "beam"
    assert scope["closure_bucket"] == "high"
    assert scope["miss_distance_bucket"] == "near_miss"
    assert scope["candidate_scope_label"] == "near_miss_0_35m"
    assert scope["component_name"] == "right_aileron_actuator"
    assert scope["component_system"] == "flight_control"
    assert scope["component_redundancy_group_id"] == "lateral_flight_control_actuators"

    upstream = artifact["upstream_stage_b_dependency_summary"]
    assert upstream["dependency_role"] == (
        "separate_upstream_effect_scale_authority_track"
    )
    assert upstream["status"] == "blocked_non_authoritative_stage_b_release_candidate"
    assert upstream["release_target"] == "effect_scale_authority_only"
    assert upstream["dependency_preserved_as_blocked"] is True
    assert "RES-010" in upstream["blocking_residual_ids"]

    retained = artifact["retained_artifact_pack_summary"]
    assert (
        retained["status"]
        == "author_retained_stage_c_component_probability_candidate_artifacts_only"
    )
    assert retained["manifest_exists"] is True
    assert retained["retained_artifact_count"] == 4
    assert retained["all_artifacts_exist"] is True
    assert (
        retained["retention_scope"]
        == "stage_c_component_probability_author_side_candidate_only"
    )

    shared = artifact["shared_provenance_identity_gate_summary"]
    assert (
        shared["status"]
        == "blocked_non_authoritative_package_provenance_identity_candidate"
    )
    assert (
        shared["readiness_level"]
        == "author_side_pin_and_identity_surface_present_but_not_release_grade"
    )
    assert shared["satisfied_condition_count"] == 5
    assert shared["blocking_condition_count"] == 4
    assert shared["blocking_residual_ids"] == [
        "RES-001",
        "RES-002",
        "RES-013/014-boundary",
    ]

    candidate = artifact["candidate_row_summary"]
    assert candidate["component_name"] == "right_aileron_actuator"
    assert candidate["component_system"] == "flight_control"
    assert candidate["component_redundancy_group_id"] == "lateral_flight_control_actuators"
    assert candidate["component_failure_probability"] == 0.67
    assert candidate["baseline_component_probability_source"] == "synthetic_sigmoid"

    satisfied = artifact["satisfied_conditions"]
    assert [row["condition_id"] for row in satisfied] == [
        "READY-CP-001",
        "READY-CP-002",
        "READY-CP-003",
        "READY-CP-004",
        "READY-CP-005",
        "READY-CP-006",
        "READY-CP-007",
    ]

    blockers = artifact["blocking_conditions"]
    assert [row["blocker_id"] for row in blockers] == [
        "BLOCK-CP-001",
        "BLOCK-CP-002",
        "BLOCK-CP-003",
        "BLOCK-CP-004",
        "BLOCK-CP-005",
        "BLOCK-CP-008",
        "BLOCK-CP-009",
        "BLOCK-CP-011",
    ]
    assert artifact["blocking_residual_ids"] == [
        "RES-012",
        "RES-010",
        "RES-009",
        "RES-011",
        "RES-003",
        "RES-005",
        "RES-006",
        "RES-013/014-boundary",
    ]
    assert artifact["open_residual_ids"] == []
    assert artifact["authority_blocked_residual_ids"] == [
        "RES-003",
        "RES-004",
        "RES-005",
        "RES-006",
        "RES-009",
        "RES-010",
        "RES-011",
        "RES-012",
        "RES-013",
        "RES-014",
    ]
    assert any("independent fragility review" in row["summary"] for row in blockers)
    assert any("validation manifest still stays at not_run" in row["summary"] for row in blockers)
    assert any("synthetic_sigmoid" in row["summary"] for row in blockers)
    assert any("uncertainty coverage" in row["summary"] for row in blockers)
    assert any("geometry truth remain candidate-only" in row["summary"] for row in blockers)
    assert any("fragment mechanism residual" in row["summary"] for row in blockers)
    assert any("blast mechanism residual" in row["summary"] for row in blockers)
    assert any("pk authority and deterministic fuze authority remain explicitly closed" in row["summary"] for row in blockers)

    boundaries = artifact["explicit_boundaries"]
    assert "do not treat this gate as independent fragility review" in boundaries
    assert "do not release pk or deterministic fuze from this Stage C gate" in boundaries

    guards = artifact["non_authoritative_guards"]
    assert guards["stock_descriptor_created"] is False
    assert guards["stock_database_authority_granted"] is False
    assert guards["effect_scale_authority_in_stock"] is False
    assert guards["component_failure_probability_authority_in_stock"] is False
    assert guards["pk_authority"] is False
    assert guards["deterministic_fuze_authority"] is False


def test_component_probability_review_readiness_gate_cli_writes_json(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "a2_stage_c_component_probability_review_gate.json"
    run_maintenance_cli(
        "damage_model_candidate_artifacts.py",
        "component-probability-review-readiness",
        "--output",
        output_path,
        capture_output=False,
    )

    artifact = read_json(output_path)
    assert artifact["status"] == "blocked_non_authoritative_stage_c_review_candidate"
    assert artifact["review_target"] == "component_failure_probability_authority_only"
    assert artifact["blocking_conditions"][0]["blocker_id"] == "BLOCK-CP-001"


def test_fragility_validation_prep_blocks_target_residuals() -> None:
    artifact = prep.generate_stage_c_fragility_validation_prep(repo_root=REPO_ROOT)

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert artifact["schema_version"] == "a2.stage_c_fragility_validation_prep.v1"
    assert (
        artifact["status"]
        == "prepared_non_authoritative_stage_c_fragility_validation_review_inputs"
    )
    assert (
        artifact["readiness_level"]
        == "fragility_review_input_packet_ready_but_authority_release_blocked"
    )

    scope = artifact["scope"]
    assert scope["target_type"] == "F-16C_Block50"
    assert scope["weapon_family"] == "blast_fragmentation"
    assert scope["aspect_bucket"] == "beam"
    assert scope["closure_bucket"] == "high"
    assert scope["candidate_scope_label"] == "near_miss_0_35m"
    assert scope["component_name"] == "right_aileron_actuator"
    assert scope["component_system"] == "flight_control"
    assert scope["component_redundancy_group_id"] == (
        "lateral_flight_control_actuators"
    )

    residuals = {
        row["residual_id"]: row for row in artifact["residual_gate_results"]
    }
    assert list(residuals) == ["RES-009", "RES-010", "RES-011", "RES-012"]
    assert all(
        row["current_gate_result"] == "blocked_non_authoritative"
        for row in residuals.values()
    )
    assert residuals["RES-009"]["blocking_condition_ids"] == ["BLOCK-CP-003"]
    assert residuals["RES-010"]["blocking_condition_ids"] == ["BLOCK-CP-002"]
    assert residuals["RES-011"]["blocking_condition_ids"] == ["BLOCK-CP-004"]
    assert residuals["RES-012"]["blocking_condition_ids"] == ["BLOCK-CP-001"]
    assert "baseline_synthetic_sigmoid_vs_candidate_evidence_row_replacement_path" in (
        residuals["RES-009"]["prep_outputs_added"]
    )
    assert residuals["RES-010"]["authority_release_effect"] == (
        "continues_to_block_stage_c_component_probability_authority"
    )


def test_fragility_validation_prep_matrix_and_closeout_plan() -> None:
    artifact = prep.generate_stage_c_fragility_validation_prep(repo_root=REPO_ROOT)

    matrix = artifact["fragility_validation_matrix"]
    assert [row["matrix_id"] for row in matrix] == [
        "FRAG-MAT-CP-001",
        "FRAG-MAT-CP-002",
        "FRAG-MAT-CP-003",
        "FRAG-MAT-CP-004",
        "FRAG-MAT-CP-005",
        "FRAG-MAT-CP-006",
        "FRAG-MAT-CP-007",
    ]
    assert matrix[0]["current_author_side_result"] == "pass_candidate_only"
    assert matrix[1]["evidence_summary"]["all_selected_rows_cover_primary_loads"] is True
    assert matrix[2]["current_author_side_result"] == (
        "blocked_expected_non_authoritative"
    )
    assert matrix[2]["evidence_summary"]["baseline_component_probability_source"] == (
        "synthetic_sigmoid"
    )
    assert matrix[3]["evidence_summary"]["probe_row_ids"] == [
        "component-inner",
        "component-middle",
        "component-outer",
    ]
    assert matrix[3]["evidence_summary"]["probe_probabilities"] == [
        0.52,
        0.37,
        0.21,
    ]
    assert matrix[5]["current_author_side_result"] == (
        "prepared_pending_independent_audit"
    )
    assert matrix[6]["current_author_side_result"] == (
        "dependency_preserved_as_blocked"
    )

    uncertainty = artifact["author_side_uncertainty_probe"]
    assert uncertainty["probe_status"] == "author_side_repeatability_probe_only"
    assert uncertainty["anchor_probe_label"] == "middle"
    assert uncertainty["seed_values"] == [20260526, 20260527, 20260528]
    assert uncertainty["selected_row_ids"] == [
        "component-middle",
        "component-middle",
        "component-middle",
    ]
    assert uncertainty["component_failure_probability"]["cv"] == 0.0
    assert uncertainty["current_author_side_result"] == (
        "repeatability_probe_pass_candidate_only"
    )
    assert "reviewer-accepted confidence or coverage interval" in (
        uncertainty["not_covered"]
    )

    plan = artifact["uncertainty_closeout_plan"]
    assert [row["plan_id"] for row in plan] == [
        "UNC-CP-001",
        "UNC-CP-002",
        "UNC-CP-003",
    ]
    assert all(row["residual_id"] == "RES-011" for row in plan)


def test_fragility_validation_prep_interlocks_authority() -> None:
    artifact = prep.generate_stage_c_fragility_validation_prep(repo_root=REPO_ROOT)

    replacement = artifact[
        "baseline_synthetic_sigmoid_vs_candidate_evidence_row_replacement_path"
    ]
    assert replacement["path_status"] == "defined_but_not_authorized"
    assert replacement["baseline"]["component_probability_source"] == "synthetic_sigmoid"
    assert replacement["baseline"]["replacement_allowed_now"] is False
    assert [row["candidate_row_id"] for row in replacement["candidate_evidence_row_surface"]] == [
        "component-inner",
        "component-middle",
        "component-outer",
    ]
    assert all(
        row["candidate_probability_source"] == "vulnerability_evidence_row"
        for row in replacement["candidate_evidence_row_surface"]
    )
    assert "do not copy the test-local candidate rows into stock descriptors" in (
        replacement["forbidden_shortcuts"]
    )

    independence = artifact["independence_trace"]
    assert independence["trace_status"] == "prepared_pending_independent_result_audit"
    assert independence["residual_id"] == "RES-012"
    assert independence["stage_b_dependency_interlock"]["stage_b_status"] == (
        "blocked_non_authoritative_stage_b_release_candidate"
    )
    assert (
        independence["stage_b_dependency_interlock"][
            "stage_c_must_not_promote_before_stage_b_release"
        ]
        is True
    )
    assert independence["open_independence_blockers"][0]["blocker_id"] == (
        "BLOCK-CP-001"
    )

    stage_b = artifact["stage_b_dependency_interlock"]
    assert stage_b["stage_b_release_target"] == "effect_scale_authority_only"
    assert stage_b["dependency_preserved_as_blocked"] is True
    assert stage_b["interlock_result"] == (
        "dependency_preserved_no_stage_c_authority_promotion"
    )
    assert "RES-010" in stage_b["stage_b_blocking_residual_ids"]

    guards = artifact["authority_guards"]
    assert guards["stock_descriptor_created"] is False
    assert guards["stock_database_authority_granted"] is False
    assert guards["stock_component_probability_authority"] is False
    assert guards["pk_authority"] is False
    assert guards["deterministic_fuze_authority"] is False

    summary = artifact["review_packet_summary"]
    assert summary["ready_to_request_independent_fragility_review"] is True
    assert summary["independent_fragility_review_closed"] is False
    assert summary["authority_release_ready"] is False
    assert summary["residuals_still_blocking_authority"] == [
        "RES-009",
        "RES-010",
        "RES-011",
        "RES-012",
    ]
    assert summary["stage_b_dependency_preserved_as_blocked"] is True
    assert summary["stock_authority_remains_closed"] is True


def test_fragility_validation_prep_cli_writes_json(tmp_path: Path) -> None:
    output_path = tmp_path / "a2_stage_c_fragility_validation_prep.json"
    run_maintenance_cli(
        "a2_blastfrag_stage_c_fragility_validation_prep.py",
        "--output",
        output_path,
        capture_output=False,
    )

    artifact = read_json(output_path)
    assert (
        artifact["status"]
        == "prepared_non_authoritative_stage_c_fragility_validation_review_inputs"
    )
    assert artifact["residual_gate_results"][0]["residual_id"] == "RES-009"
    assert artifact["authority_guards"]["pk_authority"] is False
    assert artifact["authority_guards"]["deterministic_fuze_authority"] is False
    assert (
        artifact["stage_b_dependency_interlock"]["dependency_preserved_as_blocked"]
        is True
    )


def test_fragility_review_gate_blocks_residuals() -> None:
    artifact = review_gate.generate_stage_c_fragility_review_gate(repo_root=REPO_ROOT)

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert artifact["schema_version"] == "a2.stage_c_fragility_review_gate.v1"
    assert (
        artifact["status"]
        == "blocked_non_authoritative_stage_c_fragility_review_gate"
    )
    assert artifact["review_target"] == (
        "right_aileron_actuator_component_fragility_review_only"
    )
    assert (
        artifact["readiness_level"]
        == "bounded_review_checks_passed_but_residuals_and_authority_blocked"
    )
    assert artifact["focused_residual_ids"] == [
        "RES-009",
        "RES-010",
        "RES-011",
        "RES-012",
    ]

    residuals = {
        row["residual_id"]: row for row in artifact["residual_gate_results"]
    }
    assert list(residuals) == ["RES-009", "RES-010", "RES-011", "RES-012"]
    assert all(row["review_gate_result"] == "blocked" for row in residuals.values())
    assert residuals["RES-009"]["blocking_condition_ids"] == ["BLOCK-CP-003"]
    assert residuals["RES-010"]["blocking_condition_ids"] == ["BLOCK-CP-002"]
    assert residuals["RES-011"]["blocking_condition_ids"] == ["BLOCK-CP-004"]
    assert residuals["RES-012"]["blocking_condition_ids"] == ["BLOCK-CP-001"]
    assert residuals["RES-009"]["blocker_owner"] == (
        "independent_fragility_reviewer"
    )
    assert residuals["RES-009"]["retained_benchmark_artifact_status"] == (
        "present_retained_candidate_vs_synthetic_delta_evidence"
    )
    assert (
        residuals["RES-009"]["candidate_vs_synthetic_delta_evidence_present"]
        is True
    )
    assert residuals["RES-009"]["delta_evidence_status"] == (
        "present_author_side_candidate_vs_synthetic_only"
    )
    assert residuals["RES-009"]["independent_truth_present"] is False
    assert residuals["RES-009"]["replacement_allowed"] is False
    assert residuals["RES-009"]["comparison_point_count"] == 3
    assert "retained candidate-vs-synthetic delta evidence" in (
        residuals["RES-009"]["review_passed_items"]
    )
    assert "independent component fragility curve or benchmark" in (
        residuals["RES-009"]["missing_evidence"]
    )
    assert "reviewer-owned comparison of candidate evidence rows against independent fragility truth" in (
        residuals["RES-009"]["missing_evidence"]
    )
    assert residuals["RES-010"]["blocker_owner"] == (
        "validation_integrator_and_independent_reviewer"
    )
    assert "validated/passed validation manifest state" in (
        residuals["RES-010"]["missing_evidence"]
    )
    assert residuals["RES-011"]["blocker_owner"] == (
        "independent_uncertainty_reviewer"
    )
    assert "reviewer-accepted uncertainty bounds" in (
        residuals["RES-011"]["missing_evidence"]
    )
    assert residuals["RES-012"]["blocker_owner"] == (
        "independent_independence_reviewer"
    )
    assert "non-circular benchmark/input separation signoff" in (
        residuals["RES-012"]["missing_evidence"]
    )


def test_fragility_review_gate_passes_only_review_subchecks() -> None:
    artifact = review_gate.generate_stage_c_fragility_review_gate(repo_root=REPO_ROOT)

    retained_benchmark = artifact["retained_benchmark_artifact_review"]
    assert retained_benchmark["review_result"] == "blocked"
    assert retained_benchmark["artifact_read_status"] == (
        "present_retained_candidate_vs_synthetic_delta_evidence"
    )
    assert retained_benchmark["candidate_vs_synthetic_delta_evidence_present"] is True
    assert retained_benchmark["delta_evidence_status"] == (
        "present_author_side_candidate_vs_synthetic_only"
    )
    assert retained_benchmark["comparison_point_count"] == 3
    assert retained_benchmark["comparison_probe_labels"] == [
        "inner",
        "middle",
        "outer",
    ]
    assert retained_benchmark["benchmark_sha256_verified"] is True
    assert retained_benchmark["comparison_sha256_verified"] is True
    assert retained_benchmark["independent_truth_present"] is False
    assert retained_benchmark["truth_status"] == (
        "missing_independent_right_aileron_actuator_fragility_truth"
    )
    assert retained_benchmark["replacement_allowed"] is False
    assert retained_benchmark["retained_artifact_claims_replacement_allowed"] is False
    assert retained_benchmark["stage_b_dependency_preserved_as_blocked"] is True

    matrix = artifact["fragility_matrix_review"]
    assert matrix["review_result"] == "review_passed"
    assert [row["check_id"] for row in matrix["review_rows"]] == [
        "FRAG-REVIEW-001",
        "FRAG-REVIEW-002",
        "FRAG-REVIEW-003",
        "FRAG-REVIEW-004",
        "FRAG-REVIEW-005",
        "FRAG-REVIEW-006",
        "FRAG-REVIEW-007",
    ]
    assert all(
        row["review_result"] == "review_passed" for row in matrix["review_rows"]
    )
    baseline_row = matrix["review_rows"][2]
    assert baseline_row["source_matrix_id"] == "FRAG-MAT-CP-003"
    assert baseline_row["release_effect"] == (
        "blocks replacement until independent fragility closeout"
    )
    assert "right_aileron_actuator" in matrix["review_rows"][0]["reviewed_finding"]
    assert matrix["review_rows"][6]["release_effect"] == (
        "Stage B remains an upstream authority blocker"
    )

    replacement = artifact["baseline_replacement_review"]
    assert replacement["review_result"] == "review_passed"
    assert replacement["replacement_result"] == "blocked"
    assert replacement["baseline_component_probability_source"] == "synthetic_sigmoid"
    assert replacement["replacement_allowed_now"] is False
    assert replacement["retained_benchmark_delta_evidence_present"] is True
    assert replacement["independent_truth_present"] is False
    assert replacement["replacement_allowed"] is False
    assert replacement["candidate_row_ids"] == [
        "component-inner",
        "component-middle",
        "component-outer",
    ]
    assert replacement["candidate_probability_sources"] == [
        "vulnerability_evidence_row",
        "vulnerability_evidence_row",
        "vulnerability_evidence_row",
    ]
    assert "independent right_aileron_actuator fragility curve" in (
        replacement["minimum_evidence_path"][0]
    )


def test_fragility_review_gate_closeout_boundaries() -> None:
    artifact = review_gate.generate_stage_c_fragility_review_gate(repo_root=REPO_ROOT)

    formal = artifact["formal_result_closeout_review"]
    assert formal["review_result"] == "blocked"
    assert formal["author_result_pack_present"] is True
    assert formal["fragility_prep_packet_present"] is True
    assert formal["validation_manifest_promoted"] is False
    assert formal["independent_reviewer_signoff_present"] is False
    assert formal["blocking_conditions"][0]["blocker_id"] == "BLOCK-CP-002"

    uncertainty = artifact["uncertainty_review"]
    assert uncertainty["author_repeatability_review_result"] == "review_passed"
    assert uncertainty["uncertainty_closeout_result"] == "blocked"
    assert uncertainty["anchor_probe_label"] == "middle"
    assert uncertainty["seed_values"] == [20260526, 20260527, 20260528]
    assert uncertainty["component_failure_probability_cv"] == 0.0
    assert "reviewer-accepted confidence or coverage interval" in (
        uncertainty["not_covered"]
    )

    independence = artifact["independence_review"]
    assert independence["author_trace_review_result"] == "review_passed"
    assert independence["independent_result_audit_result"] == "blocked"
    assert independence["trace_status"] == (
        "prepared_pending_independent_result_audit"
    )
    assert independence["input_or_tuning_artifact_ids"] == [
        "INPUT-CP-001",
        "INPUT-CP-002",
    ]
    assert independence["result_or_review_artifact_ids"] == [
        "RESULT-CP-001",
        "RESULT-CP-002",
    ]
    assert independence["open_independence_blockers"][0]["blocker_id"] == (
        "BLOCK-CP-001"
    )

    stage_b = artifact["stage_b_dependency_interlock_review"]
    assert stage_b["review_result"] == "review_passed"
    assert stage_b["stage_b_status"] == (
        "blocked_non_authoritative_stage_b_release_candidate"
    )
    assert stage_b["stage_b_release_target"] == "effect_scale_authority_only"
    assert stage_b["dependency_preserved_as_blocked"] is True
    assert stage_b["still_blocks_stage_c_authority"] is True
    assert stage_b["stage_c_authority_promotion_allowed"] is False
    assert "RES-010" in stage_b["stage_b_blocking_residual_ids"]

    authority = artifact["authority_decision"]
    assert authority["review_gate_release_ready"] is False
    assert authority["stage_c_component_probability_authority_ready"] is False
    assert authority["stage_b_upstream_dependency_still_blocking"] is True
    assert authority["blocked_residual_ids"] == [
        "RES-009",
        "RES-010",
        "RES-011",
        "RES-012",
    ]
    assert authority["stock_component_probability_authority"] is False
    assert authority["pk_authority"] is False
    assert authority["deterministic_fuze_authority"] is False
    assert authority["candidate_vs_synthetic_delta_evidence_present"] is True
    assert authority["independent_fragility_truth_present"] is False
    assert authority["replacement_allowed"] is False

    guards = artifact["authority_guards"]
    assert guards["stock_descriptor_created"] is False
    assert guards["stock_database_authority_granted"] is False
    assert guards["stock_component_probability_authority"] is False
    assert guards["pk_authority"] is False
    assert guards["deterministic_fuze_authority"] is False
    assert guards["replacement_allowed"] is False


def test_fragility_review_gate_cli_writes_json_and_retained(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "a2_stage_c_fragility_review_gate.json"
    retained_dir = tmp_path / "retained"
    run_maintenance_cli(
        "a2_blastfrag_stage_c_fragility_review_gate.py",
        "--output",
        output_path,
        "--retained-dir",
        retained_dir,
        capture_output=False,
    )

    artifact = read_json(output_path)
    retained_artifact = read_json(retained_dir / "stage_c_fragility_review_gate.json")
    manifest = read_json(retained_dir / "manifest.json")
    assert (
        artifact["status"]
        == "blocked_non_authoritative_stage_c_fragility_review_gate"
    )
    assert retained_artifact == artifact
    assert manifest["schema_version"] == (
        "a2.stage_c_fragility_review_retained_manifest.v1"
    )
    assert manifest["artifact_count"] == 1
    assert manifest["artifacts"][0]["artifact_id"] == (
        "stage_c_fragility_review_gate"
    )
    assert manifest["stock_component_probability_authority"] is False
    assert manifest["pk_authority"] is False
    assert manifest["deterministic_fuze_authority"] is False
    assert manifest["stage_b_dependency_preserved_as_blocked"] is True
    assert manifest["candidate_vs_synthetic_delta_evidence_present"] is True
    assert manifest["independent_truth_present"] is False
    assert manifest["replacement_allowed"] is False


def test_fragility_benchmark_blocks_residuals_without_truth() -> None:
    artifact = benchmark.generate_stage_c_fragility_benchmark(repo_root=REPO_ROOT)

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert artifact["schema_version"] == "a2.stage_c_fragility_benchmark.v1"
    assert (
        artifact["status"]
        == "blocked_non_authoritative_stage_c_fragility_benchmark"
    )
    assert artifact["benchmark_target"] == (
        "right_aileron_actuator_fragility_benchmark_only"
    )
    assert artifact["focused_residual_ids"] == [
        "RES-009",
        "RES-010",
        "RES-011",
        "RES-012",
    ]

    scope = artifact["scope"]
    assert scope["target_type"] == "F-16C_Block50"
    assert scope["weapon_family"] == "blast_fragmentation"
    assert scope["aspect_bucket"] == "beam"
    assert scope["closure_bucket"] == "high"
    assert scope["candidate_scope_label"] == "near_miss_0_35m"
    assert scope["component_name"] == "right_aileron_actuator"
    assert scope["component_system"] == "flight_control"
    assert scope["component_redundancy_group_id"] == (
        "lateral_flight_control_actuators"
    )

    truth = artifact["truth_inventory"]
    assert truth["external_truth_present"] is False
    assert truth["blocked_benchmark_manifest_required"] is True
    assert truth["truth_status"] == (
        "missing_independent_right_aileron_actuator_fragility_truth"
    )
    assert "synthetic_sigmoid is a stock baseline model" in truth[
        "not_authority_reason"
    ]

    residuals = {
        row["residual_id"]: row
        for row in artifact["residual_benchmark_evidence_status"]
    }
    assert list(residuals) == ["RES-009", "RES-010", "RES-011", "RES-012"]
    assert all(row["gate_result"] == "blocked" for row in residuals.values())
    assert all(row["replacement_allowed"] is False for row in residuals.values())
    assert residuals["RES-009"]["benchmark_evidence_status"] == (
        "blocked_missing_independent_fragility_truth"
    )
    assert residuals["RES-009"]["blocking_condition_ids"] == ["BLOCK-CP-003"]
    assert residuals["RES-010"]["benchmark_evidence_status"] == (
        "blocked_pending_formal_result_closeout_and_signoff"
    )
    assert residuals["RES-010"]["blocking_condition_ids"] == ["BLOCK-CP-002"]
    assert residuals["RES-011"]["benchmark_evidence_status"] == (
        "blocked_missing_truth_labels_and_uncertainty_bounds"
    )
    assert residuals["RES-011"]["blocking_condition_ids"] == ["BLOCK-CP-004"]
    assert residuals["RES-012"]["benchmark_evidence_status"] == (
        "blocked_pending_independent_result_level_audit"
    )
    assert residuals["RES-012"]["blocking_condition_ids"] == ["BLOCK-CP-001"]


def test_fragility_benchmark_compares_candidate_to_synthetic_sigmoid() -> None:
    artifact = benchmark.generate_stage_c_fragility_benchmark(repo_root=REPO_ROOT)

    curve = artifact["benchmark_candidate_curve"]
    assert curve["curve_id"] == "RIGHT-AILERON-ACTUATOR-STAGE-C-CANDIDATE-001"
    assert curve["curve_kind"] == (
        "author_side_three_point_piecewise_linear_candidate"
    )
    assert curve["point_count"] == 3
    assert curve["monotonic_decreasing_with_standoff"] is True
    assert curve["benchmark_candidate_status"] == (
        "candidate_curve_available_but_truth_benchmark_missing"
    )
    assert [point["candidate_row_id"] for point in curve["points"]] == [
        "component-inner",
        "component-middle",
        "component-outer",
    ]
    assert [point["candidate_probability"] for point in curve["points"]] == [
        0.52,
        0.37,
        0.21,
    ]
    assert all(
        point["truth_role"] == "candidate_input_not_independent_fragility_truth"
        for point in curve["points"]
    )

    comparison = artifact["candidate_vs_synthetic_sigmoid_comparison"]
    assert comparison["comparison_status"] == (
        "author_side_delta_available_but_not_truth_benchmark"
    )
    assert comparison["replacement_allowed"] is False
    assert comparison["replacement_decision"] == (
        "blocked_no_independent_fragility_truth"
    )
    rows = comparison["rows"]
    assert [row["probe_label"] for row in rows] == ["inner", "middle", "outer"]
    assert [row["candidate_row_id"] for row in rows] == [
        "component-inner",
        "component-middle",
        "component-outer",
    ]
    assert [row["candidate_probability"] for row in rows] == [0.52, 0.37, 0.21]
    assert [row["synthetic_sigmoid_probability"] for row in rows] == pytest.approx(
        [0.001437651677663019, 0.001077334322735288, 0.0009847075557964436]
    )
    assert all(
        row["synthetic_sigmoid_probability_source"] == "synthetic_sigmoid"
        for row in rows
    )
    assert all(row["synthetic_sigmoid_calibrated"] is False for row in rows)
    assert all(
        row["replacement_conclusion"]
        == "replacement_blocked_no_independent_truth"
        for row in rows
    )
    assert rows[0]["candidate_minus_synthetic_sigmoid"] == pytest.approx(
        0.518562348322337
    )
    assert rows[2]["candidate_to_synthetic_sigmoid_ratio"] == pytest.approx(
        213.26128632185564
    )

    metrics = comparison["metrics"]
    assert metrics["point_count"] == 3
    assert metrics["metric_role"] == (
        "candidate_vs_synthetic_baseline_delta_only_not_calibration_truth"
    )
    assert metrics["all_candidate_probabilities_exceed_synthetic_sigmoid"] is True
    assert metrics["mean_candidate_probability"] == pytest.approx(
        0.3666666666666667
    )
    assert metrics["mean_synthetic_sigmoid_probability"] == pytest.approx(
        0.0011665645187315837
    )
    assert metrics["mean_absolute_difference_vs_synthetic_sigmoid"] == pytest.approx(
        0.3655001021479351
    )
    assert metrics["replacement_allowed"] is False
    assert "cannot prove accuracy" in metrics["calibration_interpretation"]


def test_fragility_benchmark_uncertainty_and_independence_fail_closed() -> None:
    artifact = benchmark.generate_stage_c_fragility_benchmark(repo_root=REPO_ROOT)

    uncertainty = artifact["uncertainty_calibration_metrics"]
    assert uncertainty["metric_status"] == (
        "blocked_calibration_truth_missing_author_side_metrics_only"
    )
    repeatability = uncertainty["author_side_repeatability"]
    assert repeatability["anchor_probe_label"] == "middle"
    assert repeatability["seed_values"] == [20260526, 20260527, 20260528]
    assert repeatability["seed_count"] == 3
    assert repeatability["component_failure_probability_cv"] == 0.0
    assert repeatability["repeatability_result"] == "pass_candidate_only"
    assert [row["metric_id"] for row in uncertainty["calibration_scores"]] == [
        "CAL-FRAG-001",
        "CAL-FRAG-002",
        "CAL-FRAG-003",
    ]
    assert all(
        row["status"] == "not_computed"
        for row in uncertainty["calibration_scores"]
    )
    assert "no independent damage/no-damage labels" in uncertainty[
        "coverage_limits"
    ]
    assert uncertainty["authority_effect"] == (
        "continues_to_block_res011_and_replacement"
    )

    independence = artifact["independence_trace"]
    assert independence["trace_status"] == (
        "candidate_inputs_and_synthetic_baseline_separated_but_truth_missing"
    )
    assert independence["candidate_input_layer"][0]["artifact_id"] == (
        "INPUT-FRAG-BENCH-001"
    )
    assert independence["candidate_input_layer"][0]["forbidden_use"] == (
        "independent benchmark truth"
    )
    assert independence["synthetic_baseline_layer"][0]["artifact_id"] == (
        "BASELINE-FRAG-BENCH-001"
    )
    assert independence["synthetic_baseline_layer"][0]["role"] == (
        "delta comparator only"
    )
    assert independence["independent_truth_layer"]["artifact_present"] is False
    assert independence["independent_result_audit_result"] == "blocked"
    assert "not scored against themselves" in independence["circularity_guard"]
    assert independence["authority_effect"] == "continues_to_block_res012"

    stage_b = artifact["stage_b_dependency_interlock"]
    assert stage_b["stage_b_status"] == (
        "blocked_non_authoritative_stage_b_release_candidate"
    )
    assert stage_b["stage_b_release_target"] == "effect_scale_authority_only"
    assert stage_b["dependency_preserved_as_blocked"] is True
    assert stage_b["still_blocks_stage_c_authority"] is True
    assert stage_b["stage_c_authority_promotion_allowed"] is False

    authority = artifact["authority_decision"]
    assert authority["benchmark_gate_result"] == "blocked"
    assert authority["replacement_allowed"] is False
    assert authority["stage_c_component_probability_authority_ready"] is False
    assert authority["stock_component_probability_authority"] is False
    assert authority["pk_authority"] is False
    assert authority["deterministic_fuze_authority"] is False
    assert authority["blocked_residual_ids"] == [
        "RES-009",
        "RES-010",
        "RES-011",
        "RES-012",
    ]

    guards = artifact["authority_guards"]
    assert guards["stock_descriptor_created"] is False
    assert guards["stock_database_authority_granted"] is False
    assert guards["stock_component_probability_authority"] is False
    assert guards["pk_authority"] is False
    assert guards["deterministic_fuze_authority"] is False
    assert guards["replacement_allowed"] is False


def test_fragility_benchmark_cli_writes_retained_artifacts(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "a2_stage_c_fragility_benchmark.json"
    retained_dir = tmp_path / "retained"
    run_maintenance_cli(
        "a2_blastfrag_stage_c_fragility_benchmark.py",
        "--output",
        output_path,
        "--retained-dir",
        retained_dir,
        capture_output=False,
    )

    artifact = read_json(output_path)
    retained_artifact = read_json(retained_dir / "stage_c_fragility_benchmark.json")
    comparison_artifact = read_json(
        retained_dir / "candidate_vs_synthetic_sigmoid_comparison.json"
    )
    manifest = read_json(retained_dir / "manifest.json")

    assert retained_artifact == artifact
    assert comparison_artifact["schema_version"] == (
        "a2.stage_c_fragility_benchmark_comparison.v1"
    )
    assert comparison_artifact["status"] == (
        "blocked_author_side_candidate_vs_synthetic_sigmoid_comparison"
    )
    assert comparison_artifact["comparison"] == (
        artifact["candidate_vs_synthetic_sigmoid_comparison"]
    )
    assert comparison_artifact["authority_guards"] == artifact["authority_guards"]

    assert manifest["schema_version"] == (
        "a2.stage_c_fragility_benchmark_retained_manifest.v1"
    )
    assert manifest["status"] == "blocked_stage_c_fragility_benchmark_manifest_only"
    assert manifest["artifact_count"] == 2
    assert [row["artifact_id"] for row in manifest["artifacts"]] == [
        "stage_c_fragility_benchmark",
        "candidate_vs_synthetic_sigmoid_comparison",
    ]
    assert all(len(row["sha256"]) == 64 for row in manifest["artifacts"])
    assert manifest["authority_granted"] is False
    assert manifest["replacement_allowed"] is False
    assert manifest["stock_component_probability_authority"] is False
    assert manifest["pk_authority"] is False
    assert manifest["deterministic_fuze_authority"] is False
    assert manifest["stage_b_dependency_preserved_as_blocked"] is True
    assert manifest["external_truth_present"] is False
