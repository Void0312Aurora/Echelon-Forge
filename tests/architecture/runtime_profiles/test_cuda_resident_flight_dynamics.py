from __future__ import annotations

from tests.architecture.helpers import REPO_ROOT


CUDA_RESIDENT_DIR = REPO_ROOT / "src/runtime/facade/internal/cuda_resident"
PHASE_CONTRACT = REPO_ROOT / "src/runtime/contracts/cuda_resident_flight_dynamics_fixture_contract.h"
CUDA_PHASE_TEST = REPO_ROOT / "src/tests/test_cuda_resident_flight_dynamics.cpp"
CPU_PHASE_TEST = REPO_ROOT / "src/tests/test_cuda_resident_flight_dynamics_cpu_reference.cpp"
DEVICE_SOURCE = CUDA_RESIDENT_DIR / "cuda_world_store_cuda_flight_dynamics.cu"
WINDOW_SOURCE = CUDA_RESIDENT_DIR / "cuda_world_store_cuda_window.cu"
STORE_HEADER = CUDA_RESIDENT_DIR / "cuda_world_store.h"
BACKEND_SOURCE = CUDA_RESIDENT_DIR / "cuda_resident_backend.cpp"
FACADE_CONFIG = REPO_ROOT / "src/runtime/facade/runtime_facade_config.cpp"


def test_rb6_flight_dynamics_uses_resident_dynamics_soa_and_split_live_ranges() -> None:
    contract = PHASE_CONTRACT.read_text(encoding="utf-8")
    device = DEVICE_SOURCE.read_text(encoding="utf-8")
    store = STORE_HEADER.read_text(encoding="utf-8")

    assert '"cuda_resident.phase_b.airframe_dynamics.v1"' in contract
    assert "kCudaResidentFlightDynamicsFirstExpected" in contract
    assert "kFlightDynamicsInertiaRollKgM2" in contract
    assert "struct CudaWorldDynamicsState" in store
    for field in (
        "angular rates",
        "control-surface positions",
        "Propulsion spool state",
        "Cached aerodynamic state",
    ):
        assert field in store
    for kernel in (
        "flight_dynamics_forces_kernel",
        "flight_dynamics_aerodynamics_kernel",
        "flight_dynamics_integrate_kernel",
    ):
        assert kernel in device

    window = WINDOW_SOURCE.read_text(encoding="utf-8")
    force_launch = window.index("launch_flight_dynamics_forces")
    aero_launch = window.index("launch_flight_dynamics_aerodynamics")
    integrate_launch = window.index("launch_flight_dynamics_integrate")
    sync = window.index("cudaDeviceSynchronize()")
    assert force_launch < aero_launch < integrate_launch < sync
    assert window[:sync].count("cudaDeviceSynchronize()") == 0
    assert window[:sync].count("cudaMemcpyDeviceToHost") == 0


def test_rb6_cpu_and_cuda_parity_oracles_execute_independently() -> None:
    cpu_test = CPU_PHASE_TEST.read_text(encoding="utf-8")
    cuda_test = CUDA_PHASE_TEST.read_text(encoding="utf-8")

    assert "WorldBatchRuntime" in cpu_test
    for stage in (
        "ClearForces",
        "FlightControl",
        "ComputeAeroState",
        "ComputePropulsion",
        "ComputeForces",
        "AdvanceControlSurfaces",
        "ComputeAerodynamics",
        "RotationalIntegrate",
        "LeapfrogIntegrate",
    ):
        assert f'"{stage}"' in cpu_test
    assert "CudaResidentBackend" not in cpu_test
    assert "WorldBatchRuntime" not in cuda_test
    assert "FlecsCpuBackend" not in cuda_test
    assert "flight_dynamics_forces_kernel_resources" in cuda_test
    assert "flight_dynamics_aerodynamics_kernel_resources" in cuda_test
    assert "flight_dynamics_integrate_kernel_resources" in cuda_test
    assert "fail_next_state_transfer" in cuda_test


def test_rb6_remains_private_and_fail_closed() -> None:
    backend = BACKEND_SOURCE.read_text(encoding="utf-8")
    facade_config = FACADE_CONFIG.read_text(encoding="utf-8")

    assert "kCudaResidentFlightDynamicsBackendId" in backend
    assert "spawn.z >= 100.0" in backend
    assert "spawn.z <= 10000.0" in backend
    assert "reject_unimplemented_operation" in backend
    assert "WorldBatchRuntime" not in backend
    assert "FlecsCpuBackend" not in backend
    assert ".compiled_experimental_backend = false" in facade_config
    assert ".supported_manifest_ids" not in facade_config
