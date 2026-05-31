from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_stage_c_fragility_validation_prep as prep,
)


def test_a2_blastfrag_stage_c_fragility_validation_prep_blocks_target_residuals(
) -> None:
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


def test_a2_blastfrag_stage_c_fragility_validation_prep_matrix_and_closeout_plan(
) -> None:
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


def test_a2_blastfrag_stage_c_fragility_validation_prep_interlocks_authority(
) -> None:
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


def test_a2_blastfrag_stage_c_fragility_validation_prep_cli_writes_json(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "a2_stage_c_fragility_validation_prep.json"
    subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_stage_c_fragility_validation_prep.py",
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    artifact = json.loads(output_path.read_text(encoding="utf-8"))
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
