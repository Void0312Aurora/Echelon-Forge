from __future__ import annotations

from tests.architecture.helpers import REPO_ROOT


CUDA_DIR = REPO_ROOT / "src/runtime/facade/internal/cuda_resident"
CONTRACT = REPO_ROOT / "src/runtime/contracts/cuda_resident_device_consumer_contract.h"
BACKEND = CUDA_DIR / "cuda_resident_backend.cpp"
STORE_LEASE = CUDA_DIR / "cuda_world_store_device_lease.cpp"
CONSUMER = CUDA_DIR / "cuda_resident_device_consumer.cpp"
CONSUMER_HEADER = CUDA_DIR / "cuda_resident_device_consumer.h"
DEVICE = CUDA_DIR / "cuda_world_store_cuda_observation.cu"
PROBE_SESSION = (
    REPO_ROOT / "src/tools/experimental/cuda_resident/cuda_resident_rb9_probe_session.cpp"
)
PERFORMANCE = REPO_ROOT / "src/runtime/contracts/cuda_resident_performance_contract.h"
CPP_TEST = REPO_ROOT / "src/tests/test_cuda_resident_device_consumer.cpp"
CMAKE = REPO_ROOT / "CMakeLists.txt"
FACADE_CONFIG = REPO_ROOT / "src/runtime/facade/runtime_facade_config.cpp"


def _text(path) -> str:
    return path.read_text(encoding="utf-8")


def _function(text: str, name: str, next_name: str) -> str:
    return text.split(name, 1)[1].split(next_name, 1)[0]


def test_cr2_3_lease_contract_freezes_ownership_layout_epoch_and_failure_ids() -> None:
    contract = _text(CONTRACT)
    for marker in (
        '"cuda_resident.device_observation_lease.v1"',
        '"cuda_resident.device_consumer_smoke.v1"',
        '"owned_d2d_snapshot_copy"',
        '"legacy_default_stream"',
        "allocation_generation",
        "reset_generation",
        "committed_window",
        "source_snapshot",
        'stride_units = "elements"',
        "std::shared_ptr<void> completion_state",
        "lease_event_record_failed",
        "consumer_event_record_failed",
        "wait_required",
        "diagnostic_failed",
    ):
        assert marker in contract
    assert "kDeviceConsumerMeasuredPathIncludesHostValidationReadback = false" in contract
    assert "kDeviceConsumerDiagnosticReadbackIsOutsideMeasuredPath = true" in contract
    assert "kSubmissionMaySynchronizeForDeviceAllocation = true" in contract
    assert "kInFlightReleaseMaySynchronize = true" in contract


def test_cr2_3_acquisition_uses_host_epoch_and_has_no_success_path_readback() -> None:
    store = _text(STORE_LEASE)
    backend = _text(BACKEND)
    device = _text(DEVICE)
    acquisition = _function(
        device,
        "bool acquire_cuda_world_store_device_observation_lease(",
        "void release_cuda_world_store_device_observation_lease(",
    )
    assert "committed_window_epoch == 0" in store
    assert "state_snapshot" not in store
    assert "global_versions" not in store
    assert "acquire_device_observation_lease_raw" in backend
    assert "state_snapshot" not in _function(
        backend,
        "CudaResidentBackend::acquire_device_observation_lease(",
        "void CudaResidentBackend::reject_unimplemented_operation",
    )
    assert "pack_device_observation_kernel<<<blocks, threads>>>" in acquisition
    assert "cudaEventRecord" in acquisition
    assert "cudaMemcpyDeviceToHost" not in acquisition
    assert "cudaDeviceSynchronize" not in acquisition


def test_cr2_3_submit_wait_and_diagnostic_have_separate_transfer_boundaries() -> None:
    device = _text(DEVICE)
    submit = _function(
        device,
        "bool submit_cuda_world_store_device_observation_consumer(",
        "bool await_cuda_world_store_device_observation_consumer(",
    )
    wait = _function(
        device,
        "bool await_cuda_world_store_device_observation_consumer(",
        "bool materialize_cuda_world_store_device_observation_consumer(",
    )
    diagnostic = _function(
        device,
        "bool materialize_cuda_world_store_device_observation_consumer(",
        "void release_cuda_world_store_device_consumer(",
    )
    assert "device_observation_consumer_smoke_kernel<<<blocks, threads>>>" in submit
    assert "cudaEventRecord" in submit
    assert "cudaMemcpyDeviceToHost" not in submit
    assert "cudaDeviceSynchronize" not in submit
    assert "cudaEventSynchronize" in wait
    assert "cudaMemcpyDeviceToHost" not in wait
    assert "cudaDeviceSynchronize" not in wait
    assert diagnostic.count("cudaMemcpy(") == 2
    assert diagnostic.count("cudaMemcpyDeviceToHost") == 2
    assert "cudaDeviceSynchronize" not in diagnostic


def test_cr2_3_probe_stops_all_timers_before_deferred_diagnostic_readback() -> None:
    session = _text(PROBE_SESSION)
    window = _function(
        session,
        "WindowTiming ProbeSession::run_window",
        "void ProbeSession::validate_pending_device_consumers",
    )
    acquisition = window.index("acquire_device_observation_lease")
    submit = window.index("device_consumer.submit")
    wait = window.index("device_consumer.await")
    collected = window.index("const auto collected = Clock::now();", wait)
    retain = window.index("pending_device_consumer_receipts.push_back", collected)
    assert acquisition < submit < wait < collected < retain
    assert "materialize_for_diagnostics" not in window
    assert "export_device_observation_view" not in window
    assert "consume_device_observation_view" not in window
    drain = _function(
        session,
        "void ProbeSession::validate_pending_device_consumers",
        "std::string ProbeSession::state_digest",
    )
    assert "materialize_for_diagnostics" in drain

    probe = _text(REPO_ROOT / "src/tools/experimental/cuda_resident/cuda_resident_rb9_probe.cpp")
    cold = probe.split("for (std::size_t sample = 0; sample < args.cold_samples", 1)[1]
    cold = cold.split("ProbeSession warmed", 1)[0]
    assert cold.index("cold_total_samples.push_back") < cold.index(
        "validate_pending_device_consumers"
    )
    rollout = probe.split("for (std::size_t rollout = 0; rollout < args.rollout_samples", 1)[1]
    rollout = rollout.split("ProbeSession deterministic", 1)[0]
    assert rollout.index("rollout_samples.push_back") < rollout.index(
        "validate_pending_device_consumers"
    )
    assert "(mode.device_consumer ? args.rollout_windows : std::size_t{1})" in probe
    assert '"deferred_device_consumer_receipts"' in probe
    assert '"deferred_after_sample_timer"' in probe
    assert '"learner_facing_device_lease_available"' in probe


def test_cr2_3_performance_ledger_excludes_diagnostic_d2h_but_records_wait_and_alloc_risk() -> None:
    contract = _text(PERFORMANCE)
    assert "ledger.device_consumer_measured_path_d2h_copy_count = 0" in contract
    assert "ledger.device_consumer_diagnostic_d2h_copy_count = 2" in contract
    assert "ledger.device_consumer_event_wait_count = 1" in contract
    assert "ledger.synchronization_count += 1" in contract
    assert "ledger.device_consumer_allocation_may_synchronize = true" in contract
    assert "ledger.device_consumer_release_outside_measured_path = true" in contract
    assert "ledger.device_consumer_includes_host_validation_d2h = true" not in contract


def test_cr2_3_failure_lifetime_and_private_support_guards_are_wired() -> None:
    test = _text(CPP_TEST)
    consumer = _text(CONSUMER)
    header = _text(CONSUMER_HEADER)
    cmake = _text(CMAKE)
    facade = _text(FACADE_CONFIG)
    for marker in (
        "fail_next_device_lease_allocation",
        "fail_next_device_lease_event_record",
        "fail_next_allocation",
        "fail_next_launch",
        "fail_next_event_record",
        "fail_next_wait",
        "fail_next_materialize",
        "consume-after-reset",
        "consume-repeat",
    ):
        assert marker in test
    assert "input_lifetime = lease.lifetime" in consumer
    assert "std::atomic_bool completed" in consumer
    assert "private cr2 consumer seam" in header.lower()
    assert "cuda_resident_device_consumer.cpp" in cmake
    assert "cuda_world_store_device_lease.cpp" in cmake
    assert "test_cuda_resident_device_consumer.cpp" in cmake
    assert ".compiled_experimental_backend = false" in facade
    assert ".supported_manifest_ids" not in facade


def test_cr2_3_new_modules_remain_below_soft_size_limits() -> None:
    limits = {
        CONTRACT: 600,
        CONSUMER_HEADER: 600,
        STORE_LEASE: 700,
        CONSUMER: 700,
        DEVICE: 700,
        CPP_TEST: 700,
    }
    for path, limit in limits.items():
        assert len(_text(path).splitlines()) <= limit, path
