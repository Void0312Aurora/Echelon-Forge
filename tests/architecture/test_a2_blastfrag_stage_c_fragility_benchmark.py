from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_stage_c_fragility_benchmark as benchmark,
)


def test_a2_blastfrag_stage_c_fragility_benchmark_blocks_residuals_without_truth(
) -> None:
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


def test_a2_blastfrag_stage_c_fragility_benchmark_compares_candidate_to_synthetic_sigmoid(
) -> None:
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


def test_a2_blastfrag_stage_c_fragility_benchmark_uncertainty_and_independence_fail_closed(
) -> None:
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
    assert (
        independence["independent_truth_layer"]["artifact_present"] is False
    )
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


def test_a2_blastfrag_stage_c_fragility_benchmark_cli_writes_retained_artifacts(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "a2_stage_c_fragility_benchmark.json"
    retained_dir = tmp_path / "retained"
    subprocess.run(
        [
            sys.executable,
            "tools/maintenance/a2_blastfrag_stage_c_fragility_benchmark.py",
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
        (retained_dir / "stage_c_fragility_benchmark.json").read_text(
            encoding="utf-8"
        )
    )
    comparison_artifact = json.loads(
        (retained_dir / "candidate_vs_synthetic_sigmoid_comparison.json").read_text(
            encoding="utf-8"
        )
    )
    manifest = json.loads(
        (retained_dir / "manifest.json").read_text(encoding="utf-8")
    )

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
