from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_stage_c_fragility_review_gate as gate,
)


def test_a2_blastfrag_stage_c_fragility_review_gate_blocks_residuals() -> None:
    artifact = gate.generate_stage_c_fragility_review_gate(repo_root=REPO_ROOT)

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
        row["review_gate_result"] == "blocked" for row in residuals.values()
    )
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


def test_a2_blastfrag_stage_c_fragility_review_gate_passes_only_review_subchecks(
) -> None:
    artifact = gate.generate_stage_c_fragility_review_gate(repo_root=REPO_ROOT)

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


def test_a2_blastfrag_stage_c_fragility_review_gate_closeout_boundaries(
) -> None:
    artifact = gate.generate_stage_c_fragility_review_gate(repo_root=REPO_ROOT)

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


def test_a2_blastfrag_stage_c_fragility_review_gate_cli_writes_json_and_retained(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "a2_stage_c_fragility_review_gate.json"
    retained_dir = tmp_path / "retained"
    subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_stage_c_fragility_review_gate.py",
            "--output",
            str(output_path),
            "--retained-dir",
            str(retained_dir),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    retained_artifact = json.loads(
        (retained_dir / "stage_c_fragility_review_gate.json").read_text(
            encoding="utf-8"
        )
    )
    manifest = json.loads(
        (retained_dir / "manifest.json").read_text(encoding="utf-8")
    )
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
