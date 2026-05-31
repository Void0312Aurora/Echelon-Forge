from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import a2_blastfrag_stage_b_independent_review_gate as gate


def test_a2_blastfrag_stage_b_independent_review_gate_passes_review_not_release(
) -> None:
    artifact = gate.generate_stage_b_independent_review_gate(repo_root=REPO_ROOT)

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert artifact["schema_version"] == "a2.stage_b_independent_review_gate.v1"
    assert artifact["status"] == "independent_review_passed_release_blocked"
    assert artifact["reviewer_role"] == "A2-RC-STAGE-B-INDEPENDENT-REVIEW"
    assert artifact["review_target"] == "stage_b_effect_scale_independent_review_only"
    assert artifact["release_target"] == "effect_scale_authority_only"
    assert artifact["focused_residual_ids"] == [
        "RES-007",
        "RES-008",
        "RES-010",
        "RES-011",
        "RES-012",
    ]

    review = artifact["review_decision"]
    assert review["independent_review_complete"] is True
    assert review["focused_review_passed"] is True
    assert review["review_passed_residual_ids"] == [
        "RES-007",
        "RES-008",
        "RES-010",
        "RES-011",
        "RES-012",
    ]
    assert review["review_blocked_residual_ids"] == []
    assert review["hard_gate_pass_is_release"] is False
    assert review["formal_validation_manifest_promoted"] is False
    assert review["stock_runtime_authority_granted"] is False

    release = artifact["release_decision"]
    assert release["release_ready"] is False
    assert release["release_blocked"] is True
    assert release["current_hard_gate_snapshot_pass"] is True
    assert release["hard_gate_pass_is_release"] is False
    assert release["blocked_even_when_hard_gates_pass"] is True
    assert release["release_blocked_by_residual_ids"] == [
        "RES-001",
        "RES-002",
        "RES-003",
        "RES-004",
        "RES-005",
        "RES-006",
        "RES-013/014-boundary",
    ]
    assert release["stage_c_component_probability_release_included"] is False
    assert release["stock_runtime_authority_granted"] is False

    residuals = {
        row["residual_id"]: row
        for row in artifact["residual_review_gate_results"]
    }
    assert list(residuals) == [
        "RES-007",
        "RES-008",
        "RES-010",
        "RES-011",
        "RES-012",
    ]
    assert all(row["review_gate_result"] == "review_passed" for row in residuals.values())
    assert all(row["all_review_checks_pass"] is True for row in residuals.values())
    assert all(
        row["register_status_after_review"] == "remains_open_release_blocked"
        for row in residuals.values()
    )
    assert residuals["RES-010"]["release_gate_result"] == (
        "blocked_formal_validation_promotion"
    )
    assert residuals["RES-008"]["release_gate_result"] == (
        "blocked_by_mechanism_source_residuals"
    )

    blockers = artifact["release_blocking_conditions"]
    assert [row["blocker_id"] for row in blockers] == [
        "BLOCK-IR-001",
        "BLOCK-IR-002",
        "BLOCK-IR-003",
        "BLOCK-IR-004",
        "BLOCK-IR-005",
        "BLOCK-IR-006",
        "BLOCK-IR-007",
    ]
    assert any("source provenance" in row["summary"] for row in blockers)
    assert any("surrogate identity" in row["summary"] for row in blockers)
    assert any("target geometry" in row["summary"] for row in blockers)
    assert any("warhead class" in row["summary"] for row in blockers)
    assert any("fragment mechanism" in row["summary"] for row in blockers)
    assert any("blast mechanism" in row["summary"] for row in blockers)
    assert any("stock runtime" in row["summary"] for row in blockers)


def test_a2_blastfrag_stage_b_independent_review_gate_audits_focused_surfaces(
) -> None:
    artifact = gate.generate_stage_b_independent_review_gate(repo_root=REPO_ROOT)

    near_miss = artifact["near_miss_bucket_review"]
    assert near_miss["review_gate_result"] == "review_passed"
    assert near_miss["release_gate_result"] == "blocked_by_upstream_release_dependencies"
    assert near_miss["standoff_probe_m"] == [0.25, 0.35, 0.45]
    assert near_miss["runtime_bucket"] == "near_miss"
    assert [row["check_id"] for row in near_miss["checks"]] == [
        "IR-RES007-001",
        "IR-RES007-002",
        "IR-RES007-003",
        "IR-RES007-004",
        "IR-RES007-005",
        "IR-RES007-006",
        "IR-RES007-007",
    ]
    assert all(row["pass"] for row in near_miss["checks"])

    beam_high = artifact["beam_high_scope_leakage_review"]
    assert beam_high["review_gate_result"] == "review_passed"
    assert beam_high["release_gate_result"] == "blocked_by_mechanism_source_residuals"
    assert beam_high["closure_probe_mps"] == [700.0, 900.0, 1100.0]
    assert beam_high["accepted_scope_labels"] == ["beam"]
    assert "direct_hit" in beam_high["rejected_scope_labels"]
    assert "closure_bucket != high" in beam_high["rejected_scope_labels"]
    assert all(row["pass"] for row in beam_high["checks"])

    validation = artifact["validation_result_promotion_review"]
    assert validation["review_gate_result"] == "review_passed"
    assert validation["release_gate_result"] == "blocked_formal_validation_promotion"
    assert validation["criteria_counts"]["criteria_count"] == 18
    assert validation["criteria_counts"]["failed_criteria_ids"] == []
    assert validation["artifact_hash_count"] == 3
    assert validation["validation_manifest_status"] == "not_promoted_to_validated"
    assert validation["formal_validation_promotion_result"] == "blocked"
    assert validation["formal_validation_promotion_blocked_by"] == [
        "RES-001",
        "RES-002",
        "RES-003",
        "RES-004",
        "RES-005",
        "RES-006",
    ]

    uncertainty = artifact["uncertainty_review"]
    assert uncertainty["review_gate_result"] == "review_passed"
    assert uncertainty["release_gate_result"] == "blocked_uncertainty_coverage_release"
    assert uncertainty["seed_window_cv_pass"] is True
    assert all(row["pass"] for row in uncertainty["cv_rows"])
    assert uncertainty["coverage_release_result"] == "blocked"
    assert uncertainty["coverage_release_blocked_by"] == [
        "RES-001",
        "RES-002",
        "RES-003",
        "RES-004",
        "RES-005",
        "RES-006",
    ]

    independence = artifact["benchmark_input_independence_review"]
    assert independence["review_gate_result"] == "review_passed"
    assert independence["release_gate_result"] == (
        "blocked_by_provenance_identity_and_source_residuals"
    )
    bm005 = next(
        row
        for row in independence["benchmark_independence_rows"]
        if row["benchmark_id"] == "BFM-BM-005"
    )
    assert bm005["independence_class"] == "not_independent_real_validation"
    assert bm005["audit_outcome"] == "candidate_hygiene_only_not_independent_validation"
    assert "authority release" in bm005["forbidden_claim"]
    assert all(row["pass"] for row in independence["checks"])

    readiness = artifact["readiness_gate_snapshot"]
    assert readiness["status"] == "blocked_non_authoritative_stage_b_release_candidate"
    assert readiness["hard_gate_pass_is_release"] is False
    assert "RES-001" in readiness["blocking_residual_ids"]
    assert "RES-002" in readiness["blocking_residual_ids"]
    assert "RES-010" in readiness["blocking_residual_ids"]

    guards = artifact["non_authoritative_guards"]
    assert guards["stock_descriptor_created"] is False
    assert guards["stock_database_authority_granted"] is False
    assert guards["stock_runtime_authority_granted"] is False
    assert guards["effect_scale_authority_granted"] is False
    assert guards["effect_scale_authority_in_stock"] is False
    assert guards["component_failure_probability_authority_granted"] is False
    assert guards["component_failure_probability_authority_in_stock"] is False
    assert guards["pk_authority_granted"] is False
    assert guards["deterministic_fuze_authority_granted"] is False


def test_a2_blastfrag_stage_b_independent_review_gate_cli_writes_json(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "a2_stage_b_independent_review_gate.json"
    subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_stage_b_independent_review_gate.py",
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    assert artifact["status"] == "independent_review_passed_release_blocked"
    assert artifact["release_decision"]["hard_gate_pass_is_release"] is False
    assert artifact["residual_review_gate_results"][0]["residual_id"] == "RES-007"
