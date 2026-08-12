from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.benchmark_cuda_resident_rb9 import (
    COMPACT_TRACE_ALGORITHM,
    EXPECTED_PROTOCOL,
    MODES,
    RAW_TRACE_ALGORITHM,
    WORLD_COUNTS,
    build_summary,
    compact_report,
)


ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "src/runtime/contracts/cuda_resident_performance_contract.h"
PROBE = ROOT / "src/tools/experimental/cuda_resident/cuda_resident_rb9_probe.cpp"
PROBE_SESSION = (
    ROOT / "src/tools/experimental/cuda_resident/cuda_resident_rb9_probe_session.cpp"
)
CUDA_RESIDENT_DIR = ROOT / "src/runtime/facade/internal/cuda_resident"
DEVICE_SOURCES = tuple(
    CUDA_RESIDENT_DIR / name
    for name in (
        "cuda_world_store_cuda_barrier.cu",
        "cuda_world_store_cuda_control_preparation.cu",
        "cuda_world_store_cuda_observation.cu",
        "cuda_world_store_cuda_window.cu",
        "cuda_world_store_cuda_window_body.cu",
    )
)
WINDOW_SOURCE = CUDA_RESIDENT_DIR / "cuda_world_store_cuda_window.cu"
CMAKE = ROOT / "CMakeLists.txt"
EVIDENCE = ROOT / "docs/plan/exact_runtime/cuda_resident_rb9_evidence_20260730"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _device_text() -> str:
    return "\n".join(_text(path) for path in DEVICE_SOURCES)


def _stats(value: float, sample_count: int) -> dict[str, float | int | list[float]]:
    return {
        "sample_count": sample_count,
        "p50_ms": value,
        "p95_ms": value * 1.1,
        "min_ms": value * 0.9,
        "max_ms": value * 1.1,
        "mean_ms": value,
        "raw_ms": [value] * sample_count,
    }


def _report(lane: str) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for world in WORLD_COUNTS:
        for mode in MODES:
            device = "device_consumer" in mode
            available = not (lane == "flecs_cpu_reference" and device)
            base = float(world) if lane == "flecs_cpu_reference" else float(world) * 0.7
            rows.append(
                {
                    "world_count": world,
                    "mode_id": mode,
                    "host_snapshot": mode.startswith("host_export_"),
                    "device_consumer": device,
                    "trace_signature": f"{world:064x}",
                    "master_trace_prefix_world_count": 256,
                    "available": available,
                    "unavailable_reason": (
                        "cpu_reference_has_no_device_observation_consumer" if not available else ""
                    ),
                    "learner_equivalent": False,
                    "parity_status": "rb8_selected_slice_quarantined",
                    "promotion_eligible": False,
                    "latency": None if not available else {
                        "setup": _stats(base, EXPECTED_PROTOCOL["cold_samples"]),
                        "cold_reset_setup_plus_first_window": _stats(
                            base, EXPECTED_PROTOCOL["cold_samples"]
                        ),
                        "cold_first_window": _stats(base, EXPECTED_PROTOCOL["cold_samples"]),
                        "warmed_end_to_end": _stats(
                            base, EXPECTED_PROTOCOL["measured_windows"]
                        ),
                        "warmed_advance": _stats(base, EXPECTED_PROTOCOL["measured_windows"]),
                        "warmed_collection": _stats(
                            base, EXPECTED_PROTOCOL["measured_windows"]
                        ),
                        "rollout_total": _stats(
                            base * 128.0, EXPECTED_PROTOCOL["rollout_samples"]
                        ),
                        "rollout_windows": EXPECTED_PROTOCOL["rollout_windows"],
                    },
                    "determinism": None if not available else {
                        "checked": True,
                        "matched": False,
                        "scope": "identity_inclusive_reset_diagnostic",
                        "identity_inclusive": True,
                        "mismatch_reason": "reset_allocates_fresh_entity_ids",
                    },
                    "device_memory": {
                        "availability": (
                            "candidate_owned_requested_bytes"
                            if lane == "cuda_resident"
                            else "not_applicable"
                        ),
                    },
                }
            )
    return {
        "schema_version": "cuda_resident.performance_evidence.v1",
        "profile_id": "resident_state.unmaintained_candidate",
        "parity_budget_ref": "parity_budget.resident_state.unmaintained_candidate.v1",
        "lane": lane,
        "trace_signature_algorithm": COMPACT_TRACE_ALGORITHM,
        "world_counts": WORLD_COUNTS,
        "build_config": "Release",
        "complete_rollout_collection_available": True,
        "promotion_allowed": False,
        "required_metrics_complete": False,
        "break_even_eligible": False,
        "learner_consumption_available": False,
        "maintained_claim": False,
        "master_trace_signature": f"{256:064x}",
        "protocol": EXPECTED_PROTOCOL,
        "invocation_surface": (
            "backend_spi_world_batch"
            if lane == "flecs_cpu_reference"
            else "backend_private_phase_sequence"
        ),
        "full_facade_available": False,
        "rows": rows,
        "achieved_hardware_counters": {
            "availability": "not_applicable"
            if lane == "flecs_cpu_reference"
            else "unavailable",
            "reason": "cpu_reference_lane" if lane == "flecs_cpu_reference" else "ERR_NVGPUCTRPERM",
            "achieved_occupancy": None,
            "branch_divergence": None,
            "global_memory_traffic": None,
            "local_memory_traffic": None,
            "shared_memory_traffic": None,
        },
    }


def test_rb9_probe_keeps_cpu_and_cuda_release_targets_separate() -> None:
    cmake = _text(CMAKE)
    assert "ef_cuda_resident_rb9_cpu_probe" in cmake
    assert "ef_cuda_resident_rb9_cuda_probe" in cmake
    cuda_target = cmake.split("add_executable(ef_cuda_resident_rb9_cuda_probe", 1)[1].split(
        "else()", 1
    )[0]
    assert "ef_cuda_resident_backend" in cuda_target
    assert "ef_core" not in cuda_target
    assert "ef_facade" not in cuda_target
    cpu_target = cmake.split("add_executable(ef_cuda_resident_rb9_cpu_probe", 1)[1].split(
        "endif()", 1
    )[0]
    assert "ef_facade" in cpu_target
    assert cmake.count("cuda_resident_rb9_probe_session.cpp") == 2


def test_rb9_freezes_private_invocation_and_complete_world_mode_matrix() -> None:
    contract = _text(CONTRACT)
    probe = _text(PROBE)
    session = _text(PROBE_SESSION)
    assert '"backend_private_phase_sequence"' in contract
    assert "{1, 4, 16, 64, 256}" in probe
    for mode in MODES:
        assert f'"{mode}"' in probe
    run_window = session.split("WindowTiming ProbeSession::run_window", 1)[1]
    private_sequence = run_window.split("#else", 1)[1].split("const auto advanced", 1)[0]
    # CP-3 removed the session's explicit publish_stage call: advance() owns
    # the publish when the window is input_injected. The measured sequence is
    # inject -> advance, and no explicit publish call may reappear here.
    assert private_sequence.index("impl_->backend.inject") < private_sequence.index(
        "impl_->backend.advance"
    )
    assert "publish_stage" not in private_sequence
    assert '{"full_facade_available", false}' in probe
    assert '{"promotion_allowed", false}' in probe
    assert '{"break_even_eligible", false}' in probe


def test_rb9_probe_session_split_stays_structural_and_below_soft_limit() -> None:
    probe = _text(PROBE)
    session = _text(PROBE_SESSION)
    assert "class ProbeSession final" not in probe
    assert '#include "tools/experimental/cuda_resident/cuda_resident_rb9_probe_session.h"' in probe
    assert len(probe.splitlines()) <= 700
    assert len(session.splitlines()) <= 700


def test_rb9_static_ledger_matches_current_cuda_execution_graph() -> None:
    contract = _text(CONTRACT)
    device = _device_text()
    execution_window = _text(WINDOW_SOURCE)
    # Three resident-window launches are the base path after the CP-5 fusion
    # and the CP-7b barrier fold; the legacy diagnostic and CR2-3 measured
    # wrappers each contain pack/consumer call sites.
    assert device.count("<<<blocks, threads>>>") == 7
    assert execution_window.count("launch_window_commit_body") == 1
    assert "launch_flight_dynamics_" not in execution_window
    assert "launch_instrument_projection" not in execution_window
    assert "finalize_staged_barrier" not in execution_window
    assert "kFlightControlH2dBytesPerWorld = 55" in contract
    assert ".kernel_launch_count = 3" in contract
    assert "ledger.kernel_launch_count += 2" in contract
    assert ".synchronization_count = 3" in contract
    assert "pack_device_observation_kernel" in device
    assert "device_observation_consumer_smoke_kernel" in device
    assert "device_consumer_includes_host_validation_d2h" in contract
    assert "ledger.device_consumer_measured_path_d2h_copy_count = 0" in contract
    assert "ledger.device_consumer_diagnostic_d2h_copy_count = 2" in contract
    assert "ledger.device_consumer_event_wait_count = 1" in contract
    assert "ledger.device_consumer_allocation_may_synchronize = true" in contract
    assert "ledger.device_consumer_release_outside_measured_path = true" in contract


def test_cp7a_small_batch_selection_rule_is_frozen_policy_not_a_selector() -> None:
    """CP-7a freezes the world-1 disposition of gate G-F as explicit policy.

    The rule must exist with its measured content (resident-lane advisory
    minimum at the smallest measured-winning world count, sub-minimum counts
    routed to the CPU reference, maintained default unchanged, crossover
    review owned by CP-8), and it must stay documentation-grade: no runtime
    translation unit may consume the constants, so freezing the rule cannot
    smuggle in a public backend selector.
    """
    contract = _text(CONTRACT)
    assert '"cp7.small_batch_selection_rule.v1"' in contract
    assert "kResidentLaneAdvisoryMinimumWorldCount = 4" in contract
    assert "kWorldCountsBelowMinimumRouteToCpuReference = true" in contract
    assert "kMaintainedDefaultRemainsCpuReference = true" in contract
    assert '"cp8.rematrix"' in contract
    assert "static_assert(kResidentLaneAdvisoryMinimumWorldCount > 1" in contract

    # Documentation-grade means zero runtime consumers: the constants may be
    # referenced only by the contract itself and by tests.
    rule_symbols = (
        "kSmallBatchSelectionRuleId",
        "kResidentLaneAdvisoryMinimumWorldCount",
        "kWorldCountsBelowMinimumRouteToCpuReference",
    )
    src_root = ROOT / "src"
    offenders: list[str] = []
    for path in src_root.rglob("*"):
        if path.suffix not in {".cpp", ".cu", ".cuh", ".h"}:
            continue
        if path == CONTRACT:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(symbol in text for symbol in rule_symbols):
            offenders.append(path.relative_to(ROOT).as_posix())
    allowed = {"src/tests/test_cuda_resident_performance.cpp"}
    unexpected = sorted(set(offenders) - allowed)
    assert not unexpected, (
        f"the small-batch rule must stay documentation-grade policy; runtime "
        f"consumers found: {unexpected}"
    )

    # Freezing the rule must leave the maintained default untouched.
    facade = _text(ROOT / "src/runtime/facade/runtime_facade_config.cpp")
    assert ".compiled_experimental_backend = false" in facade
    assert "supports_resident_state = false" in facade


def test_rb9_comparison_remains_held_even_when_internal_speedup_exceeds_target() -> None:
    summary = build_summary(_report("flecs_cpu_reference"), _report("cuda_resident"), cpu_sha256="a", cuda_sha256="b")
    assert summary["matrix_complete"] is True
    assert summary["provisional_internal_threshold_world_count"] == 1
    assert summary["threshold_is_promotion_gate"] is False
    assert summary["required_metrics_complete"] is False
    assert summary["break_even_eligible"] is False
    assert summary["promotion_allowed"] is False
    assert summary["decision_input"] == "hold_required"


def test_rb9_trace_compaction_keeps_samples_and_content_addresses_trace() -> None:
    raw = _report("flecs_cpu_reference")
    raw["trace_signature_algorithm"] = RAW_TRACE_ALGORITHM
    raw["master_trace_signature"] = "canonical:256:" + "x" * 4096
    for row in raw["rows"]:
        row["trace_signature"] = (
            raw["master_trace_signature"]
            if row["world_count"] == 256
            else f"canonical:{row['world_count']}:" + "x" * row["world_count"]
        )
    before_samples = deepcopy(raw["rows"][0]["latency"]["warmed_end_to_end"]["raw_ms"])
    compact = compact_report(raw)
    assert compact["trace_signature_algorithm"] == COMPACT_TRACE_ALGORITHM
    assert len(compact["master_trace_signature"]) == 64
    assert compact["master_trace_signature"] == compact["rows"][-4]["trace_signature"]
    assert compact["rows"][0]["latency"]["warmed_end_to_end"]["raw_ms"] == before_samples
    assert len(json.dumps(compact)) < len(json.dumps(raw))


@pytest.mark.parametrize(
    ("lane", "mutation", "message"),
    [
        ("cuda_resident", lambda report: report.__setitem__("parity_budget_ref", "tampered"), "parity budget"),
        (
            "cuda_resident",
            lambda report: report["rows"][0].__setitem__("trace_signature", "tampered"),
            "trace",
        ),
        (
            "flecs_cpu_reference",
            lambda report: report.__setitem__("invocation_surface", "tampered"),
            "invocation",
        ),
        (
            "flecs_cpu_reference",
            lambda report: report["rows"][2].update(
                {
                    "available": True,
                    "unavailable_reason": "",
                    "latency": report["rows"][0]["latency"],
                    "determinism": report["rows"][0]["determinism"],
                }
            ),
            "availability",
        ),
        (
            "cuda_resident",
            lambda report: report["rows"][2].update(
                {"available": False, "latency": None, "unavailable_reason": "tampered"}
            ),
            "availability",
        ),
        (
            "cuda_resident",
            lambda report: report["rows"][0].__setitem__("promotion_eligible", True),
            "promotion",
        ),
    ],
)
def test_rb9_comparison_rejects_matrix_and_admission_mutations(
    lane: str, mutation, message: str
) -> None:
    cpu = _report("flecs_cpu_reference")
    cuda = _report("cuda_resident")
    target = cpu if lane == "flecs_cpu_reference" else cuda
    mutation(target)
    with pytest.raises(ValueError, match=message):
        build_summary(cpu, cuda, cpu_sha256="a", cuda_sha256="b")


def test_rb9_unavailable_achieved_counters_cannot_be_filled_with_zero() -> None:
    cpu = _report("flecs_cpu_reference")
    cuda = deepcopy(_report("cuda_resident"))
    counters = cuda["achieved_hardware_counters"]
    assert isinstance(counters, dict)
    counters["achieved_occupancy"] = 0.0
    with pytest.raises(ValueError, match="must be null"):
        build_summary(cpu, cuda, cpu_sha256="a", cuda_sha256="b")


def test_rb9_does_not_promote_runtime_facade_support() -> None:
    config = _text(ROOT / "src/runtime/facade/runtime_facade_config.cpp")
    assert ".compiled_experimental_backend = false" in config
    assert ".supports_resident_state = false" in config
    assert ".supports_device_observation_view = false" in config


def test_rb9_committed_evidence_is_complete_but_held() -> None:
    cpu = json.loads((EVIDENCE / "cpu_lane.json").read_text(encoding="utf-8"))
    cuda = json.loads((EVIDENCE / "cuda_lane.json").read_text(encoding="utf-8"))
    comparison = json.loads((EVIDENCE / "comparison.json").read_text(encoding="utf-8"))
    assert cpu["build_config"] == "Release"
    assert cuda["build_config"] == "Release"
    assert cpu["world_counts"] == WORLD_COUNTS
    assert cuda["world_counts"] == WORLD_COUNTS
    assert len(cpu["rows"]) == len(cuda["rows"]) == 20
    assert comparison["matrix_complete"] is True
    assert comparison["required_metrics_complete"] is False
    assert comparison["break_even_eligible"] is False
    assert comparison["promotion_allowed"] is False
    assert comparison["decision_input"] == "hold_required"
    assert cpu["trace_signature_algorithm"] == COMPACT_TRACE_ALGORITHM
    assert cuda["trace_signature_algorithm"] == COMPACT_TRACE_ALGORITHM
    assert comparison["determinism_diagnostic"]["identity_inclusive"] is True
    evidence_paths = [
        EVIDENCE / "cpu_lane.json",
        EVIDENCE / "cuda_lane.json",
        EVIDENCE / "comparison.json",
    ]
    english_log = _text(
        ROOT / "docs/plan/exact_runtime/cuda_resident_backend_iteration_log_20260729.md"
    )
    chinese_log = _text(
        ROOT / "docs/plan/exact_runtime/cuda_resident_backend_iteration_log_20260729.zh.md"
    )
    for path in evidence_paths:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest in english_log
        assert digest in chinese_log
    assert sum(path.stat().st_size for path in evidence_paths) < 400_000
    assert all(len(row["trace_signature"]) == 64 for row in cpu["rows"])
    assert all(len(row["trace_signature"]) == 64 for row in cuda["rows"])
    attributes = _text(ROOT / ".gitattributes")
    assert "cuda_resident_rb9_evidence_20260730/** -text" in attributes
