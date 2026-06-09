from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import a2_blastfrag_uncertainty_review_gate as gate  # noqa: E402


def test_a2_blastfrag_uncertainty_review_gate_splits_stage_b_and_stage_c() -> None:
    artifact = gate.generate_uncertainty_review_gate(repo_root=REPO_ROOT)

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert artifact["schema_version"] == "a2.uncertainty_review_gate.v1"
    assert artifact["status"] == (
        "uncertainty_review_stage_b_narrow_pass_stage_c_blocked_release_blocked"
    )
    assert artifact["review_target"] == "RES-011_uncertainty_review_only"
    assert artifact["missing_evidence"] == []

    stage_b = artifact["stage_b_uncertainty_review"]
    assert stage_b["review_result"] == (
        "narrow_author_side_uncertainty_closeout_complete_release_blocked"
    )
    assert stage_b["author_side_closeout_complete"] is True
    assert stage_b["seed_window_cv_pass"] is True
    assert [row["metric"] for row in stage_b["cv_rows"]] == [
        "fragment_areal_density_per_m2.cv",
        "blast_impulse_kpa_ms_proxy.cv",
        "fragment_energy_j_proxy.cv",
        "penetration_margin_proxy.cv",
    ]
    assert all(row["pass"] for row in stage_b["cv_rows"])
    assert stage_b["release_uncertainty_review_status"] == (
        "blocked_pending_independent_coverage_review"
    )
    assert "independent uncertainty reviewer signoff is absent" in (
        stage_b["not_release_grade_because"]
    )

    stage_c = artifact["stage_c_uncertainty_review"]
    assert stage_c["review_result"] == (
        "blocked_probability_uncertainty_coverage_missing"
    )
    assert stage_c["author_repeatability_review_result"] == "review_passed"
    assert stage_c["uncertainty_closeout_result"] == "blocked"
    assert stage_c["anchor_probe_label"] == "middle"
    assert stage_c["seed_values"] == [20260526, 20260527, 20260528]
    assert stage_c["component_failure_probability_cv"] == 0.0
    assert stage_c["component_result_pack_anchor_cv"] == 0.0
    assert stage_c["blocking_condition_ids"] == ["BLOCK-CP-004"]
    assert "reviewer-accepted confidence or coverage interval" in (
        stage_c["missing_evidence"]
    )
    assert stage_c["closeout_doc_is_review_package_only"] is True


def test_a2_blastfrag_uncertainty_review_gate_keeps_res011_and_authority_blocked(
) -> None:
    artifact = gate.generate_uncertainty_review_gate(repo_root=REPO_ROOT)

    residual = artifact["residual_status"]
    assert residual["residual_id"] == "RES-011"
    assert residual["combined_decision"] == "blocked_release_grade_uncertainty_review"
    assert residual["stage_b_decision"] == "narrow_author_side_pass_release_blocked"
    assert residual["stage_c_decision"] == (
        "blocked_probability_uncertainty_coverage_missing"
    )
    assert residual["residual_register_status_after_gate"] == (
        "remains_open_release_blocked"
    )
    assert "Stage B seed-window CV rows pass current author-side thresholds" in (
        residual["review_passed_items"]
    )
    assert "Stage C calibration or coverage scoring" in (
        residual["missing_release_grade_items"]
    )

    decision = artifact["review_decision"]
    assert decision["stage_b_author_side_uncertainty_closeout_complete"] is True
    assert decision["stage_b_release_grade_uncertainty_complete"] is False
    assert decision["stage_c_author_repeatability_present"] is True
    assert decision["stage_c_release_grade_uncertainty_complete"] is False
    assert decision["res011_release_grade_complete"] is False
    assert decision["release_ready"] is False
    assert decision["release_blocked"] is True

    guards = artifact["authority_guards"]
    assert guards["stock_descriptor_created"] is False
    assert guards["stock_database_authority_granted"] is False
    assert guards["stock_runtime_authority_granted"] is False
    assert guards["effect_scale_authority_granted"] is False
    assert guards["component_failure_probability_authority_granted"] is False
    assert guards["pk_authority_granted"] is False
    assert guards["deterministic_fuze_authority_granted"] is False
    assert guards["formal_validation_manifest_promoted"] is False


def test_a2_blastfrag_uncertainty_review_gate_fails_closed_without_evidence(
    tmp_path: Path,
) -> None:
    artifact = gate.generate_uncertainty_review_gate(
        repo_root=REPO_ROOT,
        package_dir=tmp_path,
    )

    assert artifact["status"] == "uncertainty_review_fail_closed"
    assert artifact["stage_b_uncertainty_review"]["review_result"] == (
        "fail_closed_missing_result_pack"
    )
    assert artifact["residual_status"]["combined_decision"] == (
        "fail_closed_missing_or_incomplete_uncertainty_evidence"
    )
    assert [row["evidence_id"] for row in artifact["missing_evidence"]] == [
        "UNC-STAGE-B-RESULT-PACK",
        "UNC-STAGE-B-CLOSEOUT-DOC",
        "UNC-STAGE-C-RESULT-PACK",
        "UNC-STAGE-C-FRAGILITY-REVIEW",
        "UNC-STAGE-C-FRAGILITY-BENCHMARK",
        "UNC-STAGE-C-CLOSEOUT-DOC",
    ]
    assert artifact["authority_guards"]["pk_authority_granted"] is False
    assert artifact["authority_guards"]["deterministic_fuze_authority_granted"] is False


def test_a2_blastfrag_uncertainty_review_gate_cli_writes_retained_json(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "uncertainty_review_20260531"
    result = subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_uncertainty_review_gate.py",
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
        "uncertainty_review_stage_b_narrow_pass_stage_c_blocked_release_blocked"
    )
    gate_path = output_dir / "uncertainty_review_gate.json"
    manifest_path = output_dir / "manifest.json"
    assert gate_path.is_file()
    assert manifest_path.is_file()

    artifact = json.loads(gate_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert artifact["review_decision"]["res011_release_grade_complete"] is False
    assert manifest["schema_version"] == (
        "a2.uncertainty_review_retained_artifacts.v1"
    )
    assert manifest["status"] == "uncertainty_review_retained_release_blocked"
    assert manifest["artifacts"][0]["artifact_key"] == "uncertainty_review_gate"
    assert manifest["artifacts"][0]["content_sha256"]
    assert manifest["authority_guards"]["component_failure_probability_authority_granted"] is False
