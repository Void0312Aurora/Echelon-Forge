from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.governance_audit


ROOT = Path(__file__).resolve().parents[3]
DECISION_PATH = (
    ROOT / "tests/fixtures/runtime_profiles/cuda_resident_program_2/cuda_resident_rb10_hold_decision_20260731.json"
)
EVIDENCE = ROOT / "tests/fixtures/runtime_profiles/cuda_resident_program_2/cuda_resident_rb9_evidence_20260730"
RB9_COMMIT = "c21757908bcd4c7c323215bba2e8c3afbbfa7e2c"


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_rb10_hold_is_bound_to_the_accepted_rb9_evidence() -> None:
    decision = _json(DECISION_PATH)
    comparison = _json(EVIDENCE / "comparison.json")
    evidence = decision["evidence"]
    assert isinstance(evidence, dict)

    assert decision["schema_version"] == "cuda_resident.continuation_decision.v1"
    assert decision["decision_id"] == "rb10.hold.cuda_resident.20260731"
    assert decision["status"] == "hold"
    assert decision["decision_basis"] == (
        "mechanical_application_of_frozen_rb10_gates_to_rb9_evidence"
    )
    assert decision["human_promotion_approval_recorded"] is False
    assert evidence["rb9_commit"] == RB9_COMMIT
    assert evidence["comparison_sha256"] == _sha256(EVIDENCE / "comparison.json")
    assert evidence["cpu_lane_sha256"] == _sha256(EVIDENCE / "cpu_lane.json")
    assert evidence["cuda_lane_sha256"] == _sha256(EVIDENCE / "cuda_lane.json")
    assert comparison["inputs"]["cpu_sha256"] == evidence["cpu_lane_sha256"]
    assert comparison["inputs"]["cuda_sha256"] == evidence["cuda_lane_sha256"]
    assert DECISION_PATH.stat().st_size < 10_000


def test_rb10_failed_gates_can_only_select_hold_and_rb11_closure() -> None:
    decision = _json(DECISION_PATH)
    comparison = _json(EVIDENCE / "comparison.json")
    cpu_lane = _json(EVIDENCE / "cpu_lane.json")
    cuda_lane = _json(EVIDENCE / "cuda_lane.json")
    gates = decision["required_gates"]
    outcome = decision["decision"]
    observations = decision["observations"]
    assert isinstance(gates, dict)
    assert isinstance(outcome, dict)
    assert isinstance(observations, dict)

    assert set(gates) == {
        "full_facade_window_available",
        "invocation_surfaces_equivalent",
        "learner_consumption_available",
        "required_metrics_complete",
        "selected_slice_parity_promotable",
        "small_batch_no_regression",
    }
    assert all(value is False for value in gates.values())
    assert observations == {
        "decision_input": "hold_required",
        "provisional_internal_threshold_world_count": 4,
        "threshold_is_promotion_gate": False,
        "world_1_regresses": True,
    }
    assert comparison["decision_input"] == observations["decision_input"]
    assert comparison["provisional_internal_threshold_world_count"] == 4
    assert comparison["threshold_is_promotion_gate"] is False
    assert comparison["required_metrics_complete"] is False
    assert comparison["break_even_eligible"] is False
    assert comparison["promotion_allowed"] is False
    assert comparison["full_facade_available"] is False
    assert comparison["learner_consumption_available"] is False
    assert comparison["invocation_surfaces"] == {
        "cpu": "backend_spi_world_batch",
        "cuda": "backend_private_phase_sequence",
    }
    counters = cuda_lane["achieved_hardware_counters"]
    assert counters["availability"] == "unavailable"
    assert counters["reason"] == "ERR_NVGPUCTRPERM"
    assert all(
        counters[metric] is None
        for metric in (
            "achieved_occupancy",
            "branch_divergence",
            "global_memory_traffic",
            "local_memory_traffic",
            "shared_memory_traffic",
        )
    )
    hold_reasons = set(comparison["hold_reasons"])
    assert "cuda_candidate_not_on_full_runtime_facade_window" in hold_reasons
    assert "learner_consumption_unavailable" in hold_reasons
    assert "achieved_gpu_counters_unavailable:ERR_NVGPUCTRPERM" in hold_reasons
    assert "rb8_selected_slice_parity_remains_quarantined" in hold_reasons
    assert all(
        value < 0
        for row in comparison["comparisons"]
        if row["world_count"] == 1
        for value in (
            row["provisional_p50_speedup_fraction"],
            row["provisional_p95_speedup_fraction"],
            row["provisional_rollout_speedup_fraction"],
        )
    )
    assert all(
        row["available"] is False
        for row in cpu_lane["rows"]
        if "device_consumer" in row["mode_id"]
    )
    assert all(row["available"] is True for row in cuda_lane["rows"])
    assert all(row["parity_status"] == "rb8_selected_slice_quarantined" for row in cuda_lane["rows"])

    assert outcome == {
        "continuation_option": "hold_backend",
        "kernel_or_launch_tuning_authorized": False,
        "maintained_profile_change_allowed": False,
        "promotion_allowed": False,
        "rb11_disposition": "closure_without_promotion",
        "semantic_expansion_authorized": False,
        "support_projection_change_allowed": False,
    }
    assert decision["allowed_actions"] == [
        "preserve_branch_local_candidate_and_rb9_evidence",
        "perform_rb11_closure_audit_without_promotion",
    ]
    assert set(decision["forbidden_actions"]) == {
        "runtime_facade_promotion",
        "capability_manifest_expansion",
        "support_flag_change",
        "kernel_or_launch_tuning_under_current_workline",
        "spatial_sensor_or_communications_slice",
        "cpu_fallback_inside_cuda_window",
    }


def test_rb10_hold_keeps_maintained_runtime_and_bilingual_record_unchanged() -> None:
    decision = _json(DECISION_PATH)
    maintained = decision["maintained_state"]
    assert maintained == {
        "cpu_backend_remains_default": True,
        "cuda_candidate_remains_unmaintained": True,
        "public_abi_changed": False,
        "runtime_support_flags_changed": False,
    }

    config = (
        ROOT / "src/runtime/facade/runtime_facade_config.cpp"
    ).read_text(encoding="utf-8")
    assert ".compiled_experimental_backend = false" in config
    assert ".supports_resident_state = false" in config
    assert ".supports_device_observation_view = false" in config

    english = (
        ROOT / "tests/fixtures/runtime_profiles/cuda_resident_program_2/cuda_resident_rb10_hold_decision_20260731.md"
    ).read_text(encoding="utf-8")
    chinese = (
        ROOT / "tests/fixtures/runtime_profiles/cuda_resident_program_2/cuda_resident_rb10_hold_decision_20260731.zh.md"
    ).read_text(encoding="utf-8")
    for text in (english, chinese):
        assert "rb10.hold.cuda_resident.20260731" in text
        assert "cuda_resident_rb10_hold_decision_20260731.json" in text
        assert RB9_COMMIT in text
    assert "without promotion" in english
    assert "无晋级" in chinese
    assert "cuda_resident_rb10_hold_decision_20260731.md" in (
        ROOT / "tests/fixtures/runtime_profiles/cuda_resident_program_2/README.md"
    ).read_text(encoding="utf-8")
    assert "cuda_resident_rb10_hold_decision_20260731.zh.md" in (
        ROOT / "tests/fixtures/runtime_profiles/cuda_resident_program_2/README.zh.md"
    ).read_text(encoding="utf-8")
    program_english = (
        ROOT / "tests/fixtures/runtime_profiles/cuda_resident_program_2/cuda_resident_backend_program_20260729.md"
    ).read_text(encoding="utf-8")
    program_chinese = (
        ROOT / "tests/fixtures/runtime_profiles/cuda_resident_program_2/cuda_resident_backend_program_20260729.zh.md"
    ).read_text(encoding="utf-8")
    log_english = (
        ROOT / "tests/fixtures/runtime_profiles/cuda_resident_program_2/cuda_resident_backend_iteration_log_20260729.md"
    ).read_text(encoding="utf-8")
    log_chinese = (
        ROOT / "tests/fixtures/runtime_profiles/cuda_resident_program_2/cuda_resident_backend_iteration_log_20260729.zh.md"
    ).read_text(encoding="utf-8")
    assert "RB0 through RB11 are accepted" in program_english
    assert "closed without promotion" in program_english
    assert "RB0 至 RB11" in program_chinese
    assert "无晋级关闭" in program_chinese
    assert "RB10 accepted" in log_english
    assert "RB10 accepted" in log_chinese
