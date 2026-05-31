from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import a2_blastfrag_scope_bucket_independent_review_gate as gate


def _residuals_by_id(artifact: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        row["residual_id"]: row
        for row in artifact["residual_statuses"]  # type: ignore[index]
    }


def test_a2_blastfrag_scope_bucket_independent_review_gate_narrow_passes_only(
) -> None:
    artifact, probe = gate.generate_scope_bucket_independent_review_gate(
        repo_root=REPO_ROOT
    )

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert artifact["schema_version"] == "a2.scope_bucket_independent_review_gate.v1"
    assert artifact["status"] == "scope_bucket_independent_review_passed_release_blocked"
    assert artifact["review_target"] == "RES-007_RES-008_scope_bucket_independent_review_only"
    assert artifact["release_target"] == "none_review_gate_record_only"
    assert probe["status"] == "candidate_non_authoritative_scope_probe_results"

    decision = artifact["review_decision"]
    assert decision["res007_scope_bucket_review_complete"] is True
    assert decision["res008_scope_bucket_review_complete"] is True
    assert decision["narrow_stage_b_scope_only_acceptance"] is True
    assert decision["release_ready"] is False
    assert decision["release_blocked"] is True
    assert decision["release_blocked_by_residual_ids"] == [
        "RES-001",
        "RES-002",
        "RES-003",
        "RES-004",
        "RES-005",
        "RES-006",
        "RES-013/014-boundary",
    ]
    assert decision["missing_review_evidence_count"] == 0
    assert artifact["missing_review_evidence"] == []
    assert artifact["fail_closed_blockers"] == []

    residuals = _residuals_by_id(artifact)
    assert list(residuals) == ["RES-007", "RES-008"]
    assert residuals["RES-007"]["scope_bucket_review_status"] == (
        "narrow_stage_b_scope_review_complete"
    )
    assert residuals["RES-007"]["decision"] == "narrow_pass_stage_b_scope_only"
    assert residuals["RES-007"]["residual_register_status_after_gate"] == (
        "remains_open_release_blocked"
    )
    assert residuals["RES-008"]["scope_bucket_review_status"] == (
        "narrow_stage_b_scope_review_complete"
    )
    assert residuals["RES-008"]["decision"] == "narrow_pass_stage_b_scope_only"
    assert residuals["RES-008"]["residual_register_status_after_gate"] == (
        "remains_open_release_blocked"
    )
    assert all(row["pass"] for row in residuals["RES-007"]["checks"])
    assert all(row["pass"] for row in residuals["RES-008"]["checks"])

    coverage = artifact["probe_coverage_summary"]
    assert coverage["standoff_rows_m"] == [0.25, 0.35, 0.45]
    assert coverage["miss_distance_row_count"] == 3
    assert coverage["miss_distance_anchor_present"] is True
    assert coverage["runtime_bucket_consistent"] is True
    assert coverage["closure_rows_mps"] == [700.0, 900.0, 1100.0]
    assert coverage["closure_row_count"] == 3
    assert coverage["closure_response_active"] is True

    rejection = artifact["boundary_rejection_coverage"]
    assert rejection["accepted_scope_labels"] == ["beam"]
    assert rejection["all_required_rejections_observed"] is True
    assert rejection["missing_rejected_scope_labels"] == []
    assert rejection["required_rejected_scope_labels"] == [
        "head_on",
        "tail_chase",
        "high_off_boresight",
        "direct_hit",
        "closure_bucket != high",
        "weapon_family != blast_fragmentation",
    ]

    closure_review = artifact["closure_response_review_status"]
    assert closure_review["probe_response_active"] is True
    assert closure_review["probe_self_review_complete"] is False
    assert closure_review["independent_review_complete"] is True
    assert closure_review["decision"] == "review_complete_for_stage_b_scope_only"

    guards = artifact["authority_guards"]
    assert guards["stock_descriptor_created"] is False
    assert guards["stock_database_authority_granted"] is False
    assert guards["stock_runtime_authority_granted"] is False
    assert guards["effect_scale_authority_granted"] is False
    assert guards["effect_scale_authority_in_stock"] is False
    assert guards["component_failure_probability_authority_granted"] is False
    assert guards["component_failure_probability_authority_in_stock"] is False
    assert guards["pk_authority_granted"] is False
    assert guards["deterministic_fuze_authority_granted"] is False
    assert guards["formal_validation_manifest_promoted"] is False
    assert guards["hard_gate_pass_is_release"] is False


def test_a2_blastfrag_scope_bucket_independent_review_gate_fails_closed_without_evidence(
    tmp_path: Path,
) -> None:
    artifact, _ = gate.generate_scope_bucket_independent_review_gate(
        repo_root=REPO_ROOT,
        package_dir=tmp_path,
    )

    assert artifact["status"] == "scope_bucket_independent_review_fail_closed"
    assert artifact["review_decision"]["narrow_stage_b_scope_only_acceptance"] is False
    assert artifact["review_decision"]["res007_scope_bucket_review_complete"] is False
    assert artifact["review_decision"]["res008_scope_bucket_review_complete"] is False
    assert artifact["review_decision"]["release_ready"] is False
    assert artifact["review_decision"]["release_blocked"] is True

    missing = artifact["missing_review_evidence"]
    assert [row["evidence_id"] for row in missing] == [
        "EVID-SCOPE-MANIFEST-001",
        "EVID-RESULT-PACK-001",
        "EVID-INDEPENDENT-REVIEW-001",
        "EVID-INDEPENDENT-REVIEW-MANIFEST-001",
        "EVID-INDEPENDENT-REVIEW-DOC-001",
    ]
    assert all("missing" in row["blocker"] for row in missing)

    blockers = artifact["fail_closed_blockers"]
    blocker_ids = {row["check_id"] for row in blockers}
    assert "RESULT-PACK-001" in blocker_ids
    assert "INDEPENDENT-REVIEW-001" in blocker_ids
    assert "REVIEW-DOC-001" in blocker_ids
    assert "REVIEW-MANIFEST-001" in blocker_ids

    residuals = _residuals_by_id(artifact)
    assert residuals["RES-007"]["decision"] == "fail_closed"
    assert residuals["RES-008"]["decision"] == "fail_closed"
    assert residuals["RES-007"]["residual_register_status_after_gate"] == (
        "remains_open_release_blocked"
    )
    assert residuals["RES-008"]["residual_register_status_after_gate"] == (
        "remains_open_release_blocked"
    )
    assert artifact["authority_guards"]["stock_runtime_authority_granted"] is False
    assert artifact["authority_guards"]["pk_authority_granted"] is False
    assert artifact["authority_guards"]["deterministic_fuze_authority_granted"] is False


def test_a2_blastfrag_scope_bucket_independent_review_gate_cli_writes_retained_json(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "scope_bucket_independent_review_20260531"
    result = subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_scope_bucket_independent_review_gate.py",
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
        "scope_bucket_independent_review_passed_release_blocked"
    )
    gate_path = output_dir / "scope_bucket_independent_review_gate.json"
    probe_path = output_dir / "scope_boundary_probe_rerun.json"
    manifest_path = output_dir / "manifest.json"
    assert gate_path.is_file()
    assert probe_path.is_file()
    assert manifest_path.is_file()

    artifact = json.loads(gate_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert artifact["review_decision"]["narrow_stage_b_scope_only_acceptance"] is True
    assert manifest["schema_version"] == (
        "a2.scope_bucket_independent_review_retained_artifacts.v1"
    )
    assert manifest["status"] == "scope_bucket_independent_review_retained_release_blocked"
    assert [row["artifact_key"] for row in manifest["artifacts"]] == [
        "scope_bucket_independent_review_gate",
        "scope_boundary_probe_rerun",
    ]
    assert all(row["content_sha256"] for row in manifest["artifacts"])
    assert manifest["authority_guards"]["component_failure_probability_authority_granted"] is False
