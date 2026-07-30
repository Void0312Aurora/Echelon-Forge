from __future__ import annotations

from tests.architecture.helpers import REPO_ROOT


CUDA_RESIDENT_DIR = REPO_ROOT / "src/runtime/facade/internal/cuda_resident"
PHASE_CONTRACT = REPO_ROOT / "src/runtime/contracts/cuda_resident_phase_a_fixture_contract.h"
CUDA_PHASE_TEST = REPO_ROOT / "src/tests/test_cuda_resident_phase_a.cpp"
CPU_PHASE_TEST = REPO_ROOT / "src/tests/test_cuda_resident_phase_a_cpu_reference.cpp"
STORE_SOURCE = CUDA_RESIDENT_DIR / "cuda_world_store.cpp"
DEVICE_SOURCE = CUDA_RESIDENT_DIR / "cuda_world_store_cuda.cu"
BACKEND_SOURCE = CUDA_RESIDENT_DIR / "cuda_resident_backend.cpp"
CMAKE = REPO_ROOT / "CMakeLists.txt"


def test_rb5_phase_a_keeps_raw_and_prepared_controls_as_distinct_device_soa() -> None:
    contract = PHASE_CONTRACT.read_text(encoding="utf-8")
    device = DEVICE_SOURCE.read_text(encoding="utf-8")
    store = STORE_SOURCE.read_text(encoding="utf-8")

    assert '"cuda_resident.phase_a.direct_pilot.v1"' in contract
    assert "kCudaResidentPhaseAManualDeadband" in contract
    assert "phase_a_cpu_time_step" in contract
    assert "phase_a_lpf" in contract
    assert "control_doubles" in device
    assert "prepared_doubles" in device
    assert "prepared_flags" in device
    assert "phase_versions" in device
    assert "prepare_phase_a_controls_kernel" in device
    assert "commit_phase_a_stage" in device
    assert "const double raw_pitch = control_doubles[world_index]" in device
    assert "const double raw_roll = control_doubles[world_capacity + world_index]" in device
    assert "phase_a_ready = false" in store
    assert "phase_a_ready = true" in store
    assert "requires a successful Phase A stage publish" in store
    assert ".active = true" in BACKEND_SOURCE.read_text(encoding="utf-8")


def test_rb5_cpu_oracle_is_independent_from_cuda_backend() -> None:
    cpu_test = CPU_PHASE_TEST.read_text(encoding="utf-8")
    cuda_test = CUDA_PHASE_TEST.read_text(encoding="utf-8")

    assert "WorldBatchRuntime" in cpu_test
    assert 'run_exact_stage_direct("FlightControl")' in cpu_test
    assert "CudaResidentBackend" not in cpu_test
    assert "WorldBatchRuntime" not in cuda_test
    assert "FlecsCpuBackend" not in cuda_test
    assert "phase_a_kernel_resources" in cuda_test
    assert "fail_next_state_transfer" in cuda_test
    assert "CHECK_THROWS_AS(backend.advance" in cuda_test


def test_rb5_phase_a_stays_private_and_does_not_promote_backend_support() -> None:
    backend = BACKEND_SOURCE.read_text(encoding="utf-8")
    facade_config = (
        REPO_ROOT / "src/runtime/facade/runtime_facade_config.cpp"
    ).read_text(encoding="utf-8")
    cmake = CMAKE.read_text(encoding="utf-8")

    assert "kCudaResidentRb6BackendId" in backend
    assert "reject_unimplemented_operation" in backend
    assert ".compiled_experimental_backend = false" in facade_config
    assert ".supported_manifest_ids" not in facade_config
    assert "EF_ENABLE_CUDA_EXPERIMENTS" in cmake
    assert "src/tests/test_cuda_resident_phase_a.cpp" in cmake
    assert "WorldBatchRuntime" not in backend
    assert "FlecsCpuBackend" not in backend
