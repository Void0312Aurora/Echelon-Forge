from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_res011012_independent_review_closeout_gate as gate,
)


def test_res011012_closeout_gate_closes_stage_b_effect_scale_only() -> None:
    artifact = gate.generate_res011012_independent_review_closeout_gate(
        repo_root=REPO_ROOT
    )

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert artifact["schema_version"] == (
        "a2.res011012_independent_review_closeout_gate.v1"
    )
    assert artifact["status"] == (
        "res011012_stage_b_effect_scale_closeout_pass_stage_c_blocked_release_blocked"
    )
    assert artifact["review_target"] == (
        "RES-011_RES-012_independent_review_closeout_gate"
    )
    assert artifact["release_target"] == "stage_b_effect_scale_review_closeout_only"
    assert artifact["missing_evidence"] == []
    assert len(artifact["consumed_evidence"]) == 14

    reviewer = artifact["reviewer_identity"]
    assert reviewer["worker_id"] == "A2-RES011012-INDEPENDENT-REVIEW-CLOSEOUT"
    assert reviewer["nickname"] == "res011012-closeout-reviewer"
    assert reviewer["independence_class"] == "project_internal_independent_review_worker"
    assert reviewer["external_validation_claimed"] is False

    stage_b = artifact["stage_b_effect_scale_closeout"]
    assert stage_b["decision"] == (
        "closeable_for_stage_b_effect_scale_independent_review_only"
    )
    assert stage_b["closeout_allowed"] is True
    assert stage_b["res011_stage_b_effect_scale_closeout"] is True
    assert stage_b["res012_stage_b_effect_scale_closeout"] is True
    assert stage_b["res011_basis"]["seed_window_cv_pass"] is True
    assert stage_b["res011_basis"]["release_grade_uncertainty_complete"] is False
    assert stage_b["res012_basis"]["review_gate_result"] == "review_passed"
    assert stage_b["res012_basis"]["external_validation_claimed"] is False
    assert stage_b["stage_c_component_probability_included"] is False
    assert all(row["pass"] for row in stage_b["checks"])
    assert "external validation claim" in stage_b["forbidden_promotions"]

    closeout = artifact["closeout_decision"]
    assert closeout["stage_b_effect_scale_res011012_closeout_complete"] is True
    assert closeout["stage_b_effect_scale_closeout_is_release_authority"] is False
    assert closeout["stage_c_res011012_closeout_complete"] is False
    assert closeout["res011012_package_release_grade_complete"] is False
    assert closeout["release_ready"] is False
    assert closeout["release_blocked"] is True

    residuals = artifact["residual_closeout_decisions"]
    assert residuals["RES-011"]["stage_b_effect_scale"] == (
        "closed_for_bounded_independent_review_closeout"
    )
    assert residuals["RES-012"]["stage_b_effect_scale"] == (
        "closed_for_bounded_independent_review_closeout"
    )
    assert residuals["RES-011"]["stage_c_component_probability"] == "blocked"
    assert residuals["RES-012"]["stage_c_component_probability"] == "blocked"
    assert residuals["RES-011"]["package_release_grade"] == (
        "remains_open_release_blocked"
    )
    assert residuals["RES-012"]["residual_register_edit_required_by_this_gate"] is False


def test_res011012_closeout_gate_keeps_stage_c_and_provenance_blocked() -> None:
    artifact = gate.generate_res011012_independent_review_closeout_gate(
        repo_root=REPO_ROOT
    )

    stage_c = artifact["stage_c_component_probability_closeout"]
    assert stage_c["decision"] == (
        "blocked_probability_uncertainty_fragility_truth_and_independence_missing"
    )
    assert stage_c["closeout_allowed"] is False
    assert stage_c["res011_stage_c_closeout"] is False
    assert stage_c["res012_stage_c_closeout"] is False
    assert stage_c["blocked_residual_ids"] == [
        "RES-009",
        "RES-010",
        "RES-011",
        "RES-012",
    ]
    blocking = stage_c["blocking_evidence"]
    assert blocking["probability_uncertainty_release_grade_complete"] is False
    assert blocking["author_repeatability_present"] is True
    assert blocking["component_failure_probability_cv"] == 0.0
    assert blocking["independent_fragility_truth_present"] is False
    assert blocking["replacement_allowed"] is False
    assert blocking["result_level_independence_audit_complete"] is False
    assert all(row["pass"] for row in stage_c["checks"])
    assert "probability uncertainty coverage with reviewer-accepted bounds" in (
        stage_c["minimum_evidence_to_unblock"]
    )

    provenance = artifact["provenance_interlock"]
    assert provenance["decision"] == "provenance_interlocks_preserved_release_blocked"
    assert provenance["release_ready"] is False
    assert provenance["release_blocked"] is True
    assert provenance["blocking_residual_ids"] == [
        "RES-001",
        "RES-002",
        "RES-003",
        "RES-004",
        "RES-005",
        "RES-006",
    ]
    assert all(row["pass"] for row in provenance["checks"])

    guards = artifact["authority_guards"]
    assert guards["stock_descriptor_created"] is False
    assert guards["stock_database_authority_granted"] is False
    assert guards["stock_runtime_authority_granted"] is False
    assert guards["effect_scale_authority_granted"] is False
    assert guards["component_failure_probability_authority_granted"] is False
    assert guards["component_failure_probability_authority_in_stock"] is False
    assert guards["stock_component_probability_authority"] is False
    assert guards["pk_authority_granted"] is False
    assert guards["deterministic_fuze_authority_granted"] is False
    assert guards["replacement_allowed"] is False


def test_res011012_closeout_gate_fails_closed_without_evidence(
    tmp_path: Path,
) -> None:
    artifact = gate.generate_res011012_independent_review_closeout_gate(
        repo_root=REPO_ROOT,
        package_dir=tmp_path,
    )

    assert artifact["status"] == "res011012_independent_review_closeout_fail_closed"
    assert artifact["stage_b_effect_scale_closeout"]["decision"] == (
        "fail_closed_stage_b_res011012_evidence_incomplete"
    )
    assert artifact["stage_b_effect_scale_closeout"]["closeout_allowed"] is False
    assert artifact["closeout_decision"][
        "stage_b_effect_scale_res011012_closeout_complete"
    ] is False
    assert artifact["residual_closeout_decisions"]["RES-011"]["stage_b_effect_scale"] == (
        "fail_closed"
    )
    assert [row["evidence_id"] for row in artifact["missing_evidence"]] == [
        "stage_b_independent_review_gate",
        "stage_b_independent_review_manifest",
        "stage_b_release_closeout",
        "uncertainty_review_gate",
        "uncertainty_review_manifest",
        "stage_c_fragility_review_gate",
        "stage_c_fragility_review_manifest",
        "stage_c_fragility_validation_prep",
        "stage_c_fragility_validation_prep_manifest",
        "stage_c_fragility_benchmark",
        "provenance_identity_review_gate",
        "geometry_warhead_row_provenance_gate",
        "mechanism_source_closeout_gate",
        "source_rights_output_policy_gate",
    ]
    assert artifact["authority_guards"]["pk_authority_granted"] is False
    assert artifact["authority_guards"]["deterministic_fuze_authority_granted"] is False


def test_res011012_closeout_gate_cli_writes_retained_json(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "res011012_independent_review_closeout_20260531"
    result = subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_res011012_independent_review_closeout_gate.py",
            "--output-dir",
            str(output_dir),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    command_summary = json.loads(result.stdout)
    assert command_summary["status"] == (
        "res011012_stage_b_effect_scale_closeout_pass_stage_c_blocked_release_blocked"
    )
    gate_path = output_dir / "res011012_independent_review_closeout_gate.json"
    manifest_path = output_dir / "manifest.json"
    assert gate_path.is_file()
    assert manifest_path.is_file()

    artifact = json.loads(gate_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert artifact["closeout_decision"][
        "stage_b_effect_scale_res011012_closeout_complete"
    ] is True
    assert artifact["closeout_decision"]["stage_c_res011012_closeout_complete"] is False
    assert manifest["schema_version"] == (
        "a2.res011012_independent_review_closeout_retained_manifest.v1"
    )
    assert manifest["status"] == (
        "res011012_independent_review_closeout_retained_release_blocked"
    )
    assert manifest["artifacts"][0]["artifact_key"] == (
        "res011012_independent_review_closeout_gate"
    )
    assert manifest["artifacts"][0]["content_sha256"]
    assert manifest["reviewer_identity"]["external_validation_claimed"] is False
    assert manifest["authority_guards"][
        "component_failure_probability_authority_granted"
    ] is False
