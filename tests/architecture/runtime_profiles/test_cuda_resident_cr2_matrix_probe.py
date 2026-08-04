from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from tools.diagnostics import cuda_resident_cr2_matrix_probe as matrix


ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "src/runtime/contracts/cuda_resident_matrix_contract.h"
FULL_WINDOW_CONTRACT = ROOT / "src/runtime/contracts/cuda_resident_full_window_contract.h"
PARITY_CONTRACT = ROOT / "src/runtime/contracts/cuda_resident_parity_release_contract.h"
RESOURCE_CONTRACT = ROOT / "src/runtime/contracts/cuda_resident_resource_evidence_contract.h"
SESSION_HEADER = ROOT / "src/tools/experimental/cuda_resident/cuda_resident_cr2_matrix_session.h"
SESSION = ROOT / "src/tools/experimental/cuda_resident/cuda_resident_cr2_matrix_session.cpp"
PROBE = ROOT / "src/tools/experimental/cuda_resident/cuda_resident_cr2_matrix_probe.cpp"
VALIDATOR = ROOT / "tools/diagnostics/cuda_resident_cr2_matrix_probe.py"
CMAKE = ROOT / "CMakeLists.txt"


def _stats(value: float, count: int) -> dict[str, object]:
    return {
        "sample_count": count,
        "p50_ms": value,
        "p95_ms": value,
        "min_ms": value,
        "max_ms": value,
        "mean_ms": value,
        "raw_ms": [value] * count,
    }


def _row(
    lane: str,
    world: int,
    mode: str,
    protocol: dict[str, object],
) -> dict[str, object]:
    host_export, device_consumer, cpu_available = matrix.MODES[mode]
    available = lane == "cuda_resident" or cpu_available
    base = float(world) + (0.1 if host_export else 0.0) + (0.2 if device_consumer else 0.0)
    if not available:
        return {
            "world_count": world,
            "mode_id": mode,
            "host_export": host_export,
            "device_consumer": device_consumer,
            "trace_signature": f"{world:016x}",
            "available": False,
            "unavailable_reason": "cpu_reference_has_no_device_observation_consumer",
            "effective_worker_threads": None,
            "latency": None,
            "reset_determinism": None,
            "consumer_diagnostics": None,
            "device_memory": None,
            "promotion_eligible": False,
        }
    receipts = 0
    if device_consumer:
        receipts = (
            protocol["cold_samples"]
            + protocol["warmup_windows"]
            + protocol["measured_windows"]
            + protocol["rollout_samples"] * protocol["rollout_windows"]
        )
    return {
        "world_count": world,
        "mode_id": mode,
        "host_export": host_export,
        "device_consumer": device_consumer,
        "trace_signature": f"{world:016x}",
        "available": True,
        "unavailable_reason": "",
        "effective_worker_threads": (min(world, 8) if lane == "flecs_cpu_reference" else 1),
        "latency": {
            "setup": _stats(base * 0.2, protocol["cold_samples"]),
            "cold_reset_setup_plus_first_window": _stats(base, protocol["cold_samples"]),
            "cold_first_window": _stats(base * 0.8, protocol["cold_samples"]),
            "warmed_end_to_end": _stats(base, protocol["measured_windows"]),
            "warmed_input_evaluate_advance": _stats(base * 0.75, protocol["measured_windows"]),
            "warmed_collection": _stats(base * 0.25, protocol["measured_windows"]),
            "rollout_total": _stats(base, protocol["rollout_samples"]),
            "rollout_windows": protocol["rollout_windows"],
        },
        "reset_determinism": {
            "checked": True,
            "matched": True,
            "digest": f"{world + 100:016x}",
            "scope": "released_selected_payload_identity_excluded",
            "identity_excluded": True,
            "correctness_export_outside_timer": True,
        },
        "consumer_diagnostics": {
            "receipt_count": receipts,
            "materialized_count": 1 if device_consumer else 0,
            "validation_outside_timer": True,
            "release_outside_timer": True,
            "max_deferred_rollout_receipts": (
                protocol["rollout_windows"] if device_consumer else 0
            ),
        },
        "device_memory": (
            {
                "availability": "candidate_owned_requested_bytes",
                "resident_bytes": world * 1024,
                "state_slot_bytes": world * 512,
            }
            if lane == "cuda_resident"
            else {
                "availability": "not_applicable",
                "resident_bytes": None,
                "state_slot_bytes": None,
            }
        ),
        "promotion_eligible": False,
    }


def _report(lane: str, *, production: bool = True) -> dict[str, object]:
    if production:
        worlds = matrix.WORLD_COUNTS
        protocol = deepcopy(matrix.PRODUCTION_PROTOCOL)
    else:
        worlds = [1, 4]
        protocol = {
            **matrix.PRODUCTION_PROTOCOL,
            "cold_samples": 1,
            "warmup_windows": 1,
            "measured_windows": 2,
            "rollout_samples": 1,
            "rollout_windows": 2,
        }
    return {
        "schema_version": matrix.SCHEMA,
        "profile_id": matrix.PROFILE,
        "lane": lane,
        "backend_id": (
            "flecs_cpu_reference" if lane == "flecs_cpu_reference" else "cuda_resident.rb7_phase_d"
        ),
        "build_config": "Release",
        "production_protocol": production,
        "invocation_surface": matrix.SURFACE,
        "full_window_surface_ref": matrix.FULL_WINDOW_SURFACE,
        "operation_sequence": [
            "inject",
            "evaluate_empty",
            "advance_world_batch",
            "optional_public_export",
            "optional_device_consumer",
        ],
        "selected_payload_schema_ref": matrix.SELECTED_PAYLOAD_SCHEMA_REF,
        "selected_payload_policy_ref": matrix.SELECTED_PAYLOAD_POLICY_REF,
        "selected_payload_policy_trace_profile_ref": (
            matrix.SELECTED_PAYLOAD_POLICY_TRACE_PROFILE_REF
        ),
        "selected_payload_reference_scope": matrix.SELECTED_PAYLOAD_REFERENCE_SCOPE,
        "selected_payload_matrix_profile_released": False,
        "trace_signature_algorithm": "fnv1a64",
        "master_trace_world_count": 256,
        "master_trace_signature": "0000000000000100",
        "world_counts": worlds,
        "modes": [
            {
                "mode_id": mode,
                "host_export": spec[0],
                "device_consumer": spec[1],
                "cpu_available": spec[2],
            }
            for mode, spec in matrix.MODES.items()
        ],
        "protocol": protocol,
        "lane_configuration": (
            {
                "host_worker_request": 0,
                "host_worker_policy": "hardware_concurrency_capped_by_world_count",
                "device_parallelism": "not_applicable",
            }
            if lane == "flecs_cpu_reference"
            else {
                "host_worker_request": 1,
                "host_worker_policy": "single_host_orchestrator",
                "device_parallelism": "world_grid_128_threads_per_block",
            }
        ),
        "cuda_environment": (
            None
            if lane == "flecs_cpu_reference"
            else {
                "device_ordinal": 0,
                "device_name": "test GPU",
                "compute_capability": "8.6",
                "total_global_memory_bytes": 1,
                "driver_version": 1,
                "runtime_version": 1,
            }
        ),
        "rows": [_row(lane, world, mode, protocol) for world in worlds for mode in matrix.MODES],
        "gates": {
            "cr2_4b_selected_payload_parity_required": True,
            "cr2_5_achieved_counter_gate_complete": False,
            "matrix_evidence_complete": False,
            "maintained_claim_allowed": False,
            "public_support_enabled": False,
            "promotion_allowed": False,
            "tuning_authorized": False,
        },
    }


def _replace_world_one_with_bool(report: dict[str, object]) -> None:
    for row in report["rows"]:
        if row["world_count"] == 1:
            row["world_count"] = True


def test_cr2_6a_contract_freezes_world_mode_and_protocol_scope() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    assert matrix.SCHEMA in contract
    assert matrix.PROFILE in contract
    assert matrix.SURFACE in contract
    assert "{1, 4, 16, 64, 256}" in contract
    full_window_contract = FULL_WINDOW_CONTRACT.read_text(encoding="utf-8")
    assert matrix.FULL_WINDOW_SURFACE in full_window_contract
    assert "full_window::kSurfaceId" in contract
    parity_contract = PARITY_CONTRACT.read_text(encoding="utf-8")
    assert matrix.SELECTED_PAYLOAD_SCHEMA_REF in parity_contract
    assert matrix.SELECTED_PAYLOAD_POLICY_REF in parity_contract
    assert matrix.SELECTED_PAYLOAD_POLICY_TRACE_PROFILE_REF in parity_contract
    assert "parity_release::kSchemaV1" in contract
    assert "parity_release::kPolicyId" in contract
    assert "parity_release::kTraceProfileId" in contract
    assert "parity_release::kReleasedNumericFields.size() == 12" in contract
    assert "kSelectedPayloadMatrixProfileReleased = false" in contract
    assert "kFnv1a64OffsetBasis = 14695981039346656037ULL" in contract
    assert "kFnv1a64Prime = 1099511628211ULL" in contract
    assert 'static_assert(fnv1a64("") == 0xcbf29ce484222325ULL)' in contract
    assert 'static_assert(fnv1a64("a") == 0xaf63dc4c8601ec8cULL)' in contract
    assert 'static_assert(fnv1a64("foobar") == 0x85944171f73967e8ULL)' in contract
    for mode, (host_export, device_consumer, cpu_available) in matrix.MODES.items():
        values = ", ".join(
            str(value).lower() for value in (host_export, device_consumer, cpu_available)
        )
        assert f'{{"{mode}", {values}}}' in contract
    for field, value in {
        "cold_samples": 10,
        "warmup_windows": 32,
        "measured_windows": 100,
        "rollout_samples": 10,
        "rollout_windows": 64,
    }.items():
        assert f".{field} = {value}" in contract
    assert "kCpuHostWorkerRequest = 0" in contract
    assert '"hardware_concurrency_capped_by_world_count"' in contract
    assert "kCudaHostWorkerRequest = 1" in contract
    resource_contract = RESOURCE_CONTRACT.read_text(encoding="utf-8")
    assert "kThreadsPerBlock = 128" in resource_contract
    assert "kCudaThreadsPerBlock = resource_evidence::kThreadsPerBlock" in contract
    session = SESSION.read_text(encoding="utf-8")
    assert ".worker_threads = runtime::cuda_resident::matrix::kCpuHostWorkerRequest" in session
    assert ".worker_threads = runtime::cuda_resident::matrix::kCudaHostWorkerRequest" in session
    assert "std::to_string(matrix::kCudaThreadsPerBlock)" in PROBE.read_text(encoding="utf-8")
    for flag in (
        "kMaintainedClaimAllowed = false",
        "kPublicSupportEnabled = false",
        "kPromotionAllowed = false",
        "kTuningAuthorized = false",
    ):
        assert flag in contract


def test_cr2_6a_both_targets_use_one_probe_and_common_backend_spi_sequence() -> None:
    cmake = CMAKE.read_text(encoding="utf-8")
    session = SESSION.read_text(encoding="utf-8")
    probe = PROBE.read_text(encoding="utf-8")
    assert "ef_cuda_resident_cr2_matrix_cuda_probe" in cmake
    assert "ef_cuda_resident_cr2_matrix_cpu_probe" in cmake
    assert cmake.count("cuda_resident_cr2_matrix_probe.cpp") == 2
    assert cmake.count("cuda_resident_cr2_matrix_session.cpp") == 2
    common = session.split("WindowTiming ProbeSession::run_window", 1)[1].split(
        "DrainResult ProbeSession::drain_device_consumers", 1
    )[0]
    assert common.index("backend.inject") < common.index("backend.evaluate")
    assert common.index("backend.evaluate") < common.index("backend.advance")
    assert common.index("backend.advance") < common.index("backend.export_state")
    assert "publish_stage" not in common
    assert "export_snapshot" not in common
    assert "evaluate_empty" in probe
    assert "std::string trace_digest" in probe
    assert "CudaResidentReplayHarness::trace_signature(trace)" in probe
    assert "matrix::fnv1a64(canonical)" in probe
    assert '"master_trace_signature", trace_digest(make_trace(256))' in probe
    contract = CONTRACT.read_text(encoding="utf-8")
    assert '"cuda_resident.cr2.matrix_backend_spi.v1"' in contract
    assert "full_window::kSurfaceId" in contract


def test_cr2_6a_consumer_diagnostics_and_identity_digest_stay_outside_timing() -> None:
    session = SESSION.read_text(encoding="utf-8")
    probe = PROBE.read_text(encoding="utf-8")
    digest = session.split("std::string ProbeSession::released_state_digest", 1)[1].split(
        "double ProbeSession::setup_ms", 1
    )[0]
    assert "kFnv1a64OffsetBasis" in digest
    assert "kFnv1a64Prime" in session
    assert "digest_mix(digest, observation.id)" not in digest
    assert "observation.id != impl_->refs[world].entity_id" in digest
    parity_contract = PARITY_CONTRACT.read_text(encoding="utf-8")
    for field, policy_path in (
        ("observation.sim_time", "agent_observations.sim_time"),
        ("observation.x", "agent_observations.x"),
        ("observation.y", "agent_observations.y"),
        ("observation.z", "agent_observations.z"),
        ("observation.vx", "agent_observations.vx"),
        ("observation.vy", "agent_observations.vy"),
        ("observation.vz", "agent_observations.vz"),
        ("observation.heading", "agent_observations.heading"),
        ("observation.roll", "agent_observations.roll"),
        ("observation.speed", "agent_observations.speed"),
        ("observation.gear_state", "agent_observations.gear_state"),
        ("instrument.throttle_pos", "instrument_states.throttle_pos"),
    ):
        assert field in digest
        assert f'"{policy_path}"' in parity_contract
    cold = probe.split("for (std::size_t sample = 0; sample < args.protocol.cold_samples", 1)[1]
    cold = cold.split("probe::ProbeSession warmed", 1)[0]
    assert cold.index("cold_total_samples.push_back") < cold.index("drain_device_consumers")
    rollout = probe.split("for (std::size_t sample = 0; sample < args.protocol.rollout_samples", 1)[
        1
    ]
    rollout = rollout.split("return {", 1)[0]
    assert rollout.index("rollout_samples.push_back") < rollout.index("drain_device_consumers")


def test_matrix_validator_accepts_complete_production_and_smoke_reports() -> None:
    for lane in ("flecs_cpu_reference", "cuda_resident"):
        matrix.validate_report(_report(lane), require_production=True)
        matrix.validate_report(_report(lane, production=False), require_production=False)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update({"invocation_surface": "private_phase_sequence"}),
        lambda value: value.update({"selected_payload_policy_ref": "invented.policy.v1"}),
        lambda value: value.update({"selected_payload_matrix_profile_released": True}),
        lambda value: value["lane_configuration"].update({"host_worker_request": 1}),
        lambda value: value["lane_configuration"].update({"host_worker_request": False}),
        lambda value: value.update({"master_trace_world_count": 256.0}),
        lambda value: value.update({"master_trace_signature": "f" * 16}),
        lambda value: value["protocol"].update({"fresh_process_cold_available": 0}),
        lambda value: value["modes"][0].update({"host_export": 0}),
        _replace_world_one_with_bool,
        lambda value: value["operation_sequence"].remove("evaluate_empty"),
        lambda value: value["gates"].update({"public_support_enabled": True}),
        lambda value: value["gates"].update({"promotion_allowed": 0}),
        lambda value: value["gates"].update({"matrix_evidence_complete": True}),
        lambda value: value["rows"][0]["latency"]["warmed_end_to_end"]["raw_ms"].pop(),
        lambda value: value["rows"][0]["latency"]["warmed_end_to_end"].update(
            {"sample_count": 100.0}
        ),
        lambda value: value["rows"][0]["latency"].update(
            {"warmed_collection": _stats(0.5, value["protocol"]["measured_windows"])}
        ),
        lambda value: value["rows"][0]["latency"].update(
            {"cold_reset_setup_plus_first_window": _stats(0.5, value["protocol"]["cold_samples"])}
        ),
        lambda value: value["rows"][0]["latency"].update({"rollout_windows": 64.0}),
        lambda value: value["rows"][0]["consumer_diagnostics"].update({"receipt_count": 0.0}),
        lambda value: value["rows"][0]["reset_determinism"].update({"identity_excluded": False}),
        lambda value: value["rows"][0].update({"effective_worker_threads": 0}),
        lambda value: value["rows"][5].update({"effective_worker_threads": 1}),
        lambda value: value["rows"][2].update({"available": True, "unavailable_reason": ""}),
    ],
)
def test_matrix_validator_rejects_surface_timing_or_gate_drift(mutation) -> None:
    report = _report("flecs_cpu_reference")
    mutation(report)
    with pytest.raises(matrix.MatrixProbeError):
        matrix.validate_report(report, require_production=True)


def test_matrix_validator_rejects_consumer_receipt_trace_and_digest_drift() -> None:
    report = _report("cuda_resident")
    report["rows"][2]["consumer_diagnostics"]["receipt_count"] = 0
    with pytest.raises(matrix.MatrixProbeError, match="receipt count"):
        matrix.validate_report(report, require_production=True)

    report = _report("cuda_resident")
    report["rows"][1]["trace_signature"] = "f" * 16
    with pytest.raises(matrix.MatrixProbeError, match="trace differs"):
        matrix.validate_report(report, require_production=True)

    report = _report("cuda_resident")
    report["rows"][1]["reset_determinism"]["digest"] = "f" * 16
    with pytest.raises(matrix.MatrixProbeError, match="reset digest differs"):
        matrix.validate_report(report, require_production=True)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["cuda_environment"].update({"device_ordinal": False}),
        lambda value: value["cuda_environment"].update({"driver_version": 1.0}),
        lambda value: value["rows"][0]["device_memory"].update({"resident_bytes": True}),
        lambda value: value["rows"][1]["device_memory"].update({"resident_bytes": 2048}),
    ],
)
def test_matrix_validator_rejects_cuda_integer_type_aliases(mutation) -> None:
    report = _report("cuda_resident")
    mutation(report)
    with pytest.raises(matrix.MatrixProbeError):
        matrix.validate_report(report, require_production=True)


def test_matrix_json_loader_rejects_duplicate_keys(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.json"
    path.write_text('{"schema_version":"a","schema_version":"b"}', encoding="utf-8")
    with pytest.raises(matrix.MatrixProbeError, match="duplicate JSON key"):
        matrix.load_report(path)


def test_cr2_6a_keeps_historical_rb9_evidence_unchanged() -> None:
    completed = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            "05b05c5a",
            "--",
            "docs/plan/exact_runtime/cuda_resident_rb9_evidence_20260730",
            "src/tools/experimental/cuda_resident/cuda_resident_rb9_probe.cpp",
            "src/tools/experimental/cuda_resident/cuda_resident_rb9_probe_session.cpp",
        ],
        cwd=ROOT,
        check=False,
    )
    assert completed.returncode == 0


def test_cr2_6a_new_modules_remain_below_soft_size_targets() -> None:
    assert len(CONTRACT.read_text(encoding="utf-8").splitlines()) <= 600
    assert len(SESSION_HEADER.read_text(encoding="utf-8").splitlines()) <= 600
    assert len(SESSION.read_text(encoding="utf-8").splitlines()) <= 700
    assert len(PROBE.read_text(encoding="utf-8").splitlines()) <= 700
    assert len(VALIDATOR.read_text(encoding="utf-8").splitlines()) <= 700
    assert len(Path(__file__).read_text(encoding="utf-8").splitlines()) <= 700
