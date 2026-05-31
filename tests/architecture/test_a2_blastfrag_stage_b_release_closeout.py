from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import a2_blastfrag_stage_b_release_closeout as closeout


def test_a2_blastfrag_stage_b_release_closeout_preserves_blocked_release() -> None:
    artifact = closeout.generate_stage_b_release_closeout(repo_root=REPO_ROOT)

    assert artifact["package_id"] == (
        "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
        "beam_high_near_miss_0_35m_v0"
    )
    assert artifact["schema_version"] == "a2.stage_b_release_closeout.v1"
    assert (
        artifact["status"]
        == "author_side_stage_b_release_closeout_complete_release_blocked"
    )
    assert artifact["release_target"] == "effect_scale_authority_only"
    assert artifact["focused_residual_ids"] == [
        "RES-007",
        "RES-008",
        "RES-010",
        "RES-011",
        "RES-012",
    ]

    release = artifact["release_decision"]
    assert release["current_hard_gate_snapshot_pass"] is True
    assert release["hard_gate_pass_is_release"] is False
    assert release["blocked_even_when_hard_gates_pass"] is True
    assert release["release_ready"] is False
    assert release["release_blocked"] is True
    assert release["stage_c_component_probability_release_included"] is False
    assert release["stock_runtime_authority_granted"] is False

    run_manifest = artifact["validation_run_manifest"]
    assert run_manifest["run_id"] == "STAGE-B-ES-RUN-20260531-001"
    assert run_manifest["run_status"] == "author_side_executed_non_authoritative"
    assert run_manifest["seed"] == 20260529
    assert run_manifest["sample_count"] == 4096
    assert run_manifest["scope_probe_standoffs_m"] == [0.25, 0.35, 0.45]
    assert run_manifest["scope_probe_closures_mps"] == [700.0, 900.0, 1100.0]

    execution = artifact["benchmark_result_execution_record"]
    assert execution["execution_status"] == "author_side_hard_gates_passed_non_release"
    assert execution["criteria_counts"] == {
        "criteria_count": 18,
        "passed_criteria_count": 18,
        "failed_criteria_count": 0,
        "failed_criteria_ids": [],
        "all_hard_gates_pass": True,
    }
    assert execution["hard_gate_pass_is_release"] is False
    assert len(execution["criteria_results"]) == 18
    assert all(row["pass"] for row in execution["criteria_results"])
    assert len(execution["artifact_hashes"]) == 3

    residuals = {
        row["residual_id"]: row
        for row in artifact["residual_gate_results"]
    }
    assert list(residuals) == [
        "RES-007",
        "RES-008",
        "RES-010",
        "RES-011",
        "RES-012",
    ]
    assert residuals["RES-007"]["gate_result"] == (
        "author_scope_closeout_passed_pending_independent_review"
    )
    assert residuals["RES-008"]["gate_result"] == (
        "author_scope_closeout_passed_pending_independent_review"
    )
    assert residuals["RES-010"]["gate_result"] == (
        "author_execution_record_passed_pending_independent_review"
    )
    assert residuals["RES-011"]["gate_result"] == (
        "author_uncertainty_closeout_passed_pending_independent_review"
    )
    assert residuals["RES-012"]["gate_result"] == (
        "author_independence_trace_complete_pending_independent_review"
    )
    assert all(row["author_side_closeout_complete"] is True for row in residuals.values())
    assert all(row["release_blocked"] is True for row in residuals.values())

    near_miss = artifact["near_miss_bucket_closeout"]
    assert near_miss["author_side_closeout_complete"] is True
    assert [row["standoff_m"] for row in near_miss["rows"]] == [0.25, 0.35, 0.45]
    assert near_miss["metrics"]["blast_scaled_distance_monotonic_increasing_pass"] is True
    assert near_miss["metrics"]["fragment_areal_density_monotonic_decreasing_pass"] is True
    assert near_miss["metrics"]["runtime_bucket_consistent_pass"] is True

    beam_high = artifact["beam_high_scope_closeout"]
    assert beam_high["author_side_closeout_complete"] is True
    assert [row["closure_mps"] for row in beam_high["closure_probe"]["rows"]] == [
        700.0,
        900.0,
        1100.0,
    ]
    closure_metrics = beam_high["closure_probe"]["metrics"]
    assert closure_metrics["mechanism_response_active"] is True
    assert closure_metrics["res008_closed_by_probe"] is False
    assert closure_metrics["independent_review_complete"] is False
    assert "direct_hit" in beam_high["aspect_guard"]["rejected_scope_labels"]

    uncertainty = artifact["uncertainty_closeout"]
    assert uncertainty["author_side_closeout_complete"] is True
    assert uncertainty["seed_window_cv_pass"] is True
    assert all(row["pass"] for row in uncertainty["cv_rows"])

    independence = artifact["independence_review_dependency_trace"]
    assert independence["author_side_closeout_complete"] is True
    bm005 = next(
        row
        for row in independence["benchmark_independence_rows"]
        if row["benchmark_id"] == "BFM-BM-005"
    )
    assert bm005["independence_class"] == "not_independent_real_validation"
    assert bm005["audit_outcome"] == "candidate_hygiene_only_not_independent_validation"
    assert independence["review_dependency_trace"][0]["owner"] == "independent_reviewer"
    assert independence["review_dependency_trace"][0]["status"] == "missing"

    dependencies = {
        row["dependency"]: row
        for row in artifact["remaining_release_dependencies"]
    }
    assert dependencies["independent_review"]["status"] == "blocked"
    assert dependencies["release_grade_provenance_identity"]["status"] == "blocked"
    assert dependencies["stock_runtime_descriptor"]["status"] == "forbidden"

    guards = artifact["non_authoritative_guards"]
    assert guards["stock_descriptor_created"] is False
    assert guards["stock_runtime_authority_granted"] is False
    assert guards["effect_scale_authority_granted"] is False
    assert guards["component_failure_probability_authority_granted"] is False
    assert guards["pk_authority_granted"] is False
    assert guards["deterministic_fuze_authority_granted"] is False


def test_a2_blastfrag_stage_b_release_closeout_cli_writes_json(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "a2_stage_b_release_closeout.json"
    subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_stage_b_release_closeout.py",
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    assert (
        artifact["status"]
        == "author_side_stage_b_release_closeout_complete_release_blocked"
    )
    assert artifact["release_decision"]["hard_gate_pass_is_release"] is False
    assert artifact["residual_gate_results"][0]["residual_id"] == "RES-007"
