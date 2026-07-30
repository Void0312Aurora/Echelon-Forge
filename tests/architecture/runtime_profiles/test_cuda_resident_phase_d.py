from __future__ import annotations

from tests.architecture.helpers import REPO_ROOT


CUDA_RESIDENT_DIR = REPO_ROOT / "src/runtime/facade/internal/cuda_resident"
CONTRACT = REPO_ROOT / "src/runtime/contracts/cuda_resident_phase_d_fixture_contract.h"
DEVICE_SOURCE = CUDA_RESIDENT_DIR / "cuda_world_store_cuda.cu"
STORE_HEADER = CUDA_RESIDENT_DIR / "cuda_world_store.h"
BACKEND_HEADER = CUDA_RESIDENT_DIR / "cuda_resident_backend.h"
BACKEND_SOURCE = CUDA_RESIDENT_DIR / "cuda_resident_backend.cpp"
CUDA_TEST = REPO_ROOT / "src/tests/test_cuda_resident_phase_d.cpp"
CPU_TEST = REPO_ROOT / "src/tests/test_cuda_resident_phase_d_cpu_reference.cpp"
FACADE_CONFIG = REPO_ROOT / "src/runtime/facade/runtime_facade_config.cpp"


def test_rb7_phase_d_contract_and_split_kernels_are_present() -> None:
  contract = CONTRACT.read_text(encoding="utf-8")
  device = DEVICE_SOURCE.read_text(encoding="utf-8")
  store = STORE_HEADER.read_text(encoding="utf-8")

  assert '"cuda_resident.phase_d.projection.v1"' in contract
  assert '"cuda_resident.fixed_air_snapshot.v3"' in contract
  assert '"cuda_resident.rb7.explicit_d2d_ownership_copy"' in contract
  assert "struct CudaWorldInstrumentState" in store
  assert "struct CudaWorldObservationState" in store
  assert "struct CudaWorldRewardState" in store
  assert "CudaWorldTerminationState" in store
  for kernel in (
    "phase_d_instruments_kernel",
    "phase_d_configuration_kernel",
    "phase_d_episode_kernel",
    "phase_d_pack_observation_kernel",
  ):
    assert kernel in device

  window = device.split("bool commit_phase_b_window", 1)[1].split("} // namespace", 1)[0]
  for launch in (
    "phase_b_forces_kernel<<<",
    "phase_b_aerodynamics_kernel<<<",
    "phase_b_integrate_kernel<<<",
    "phase_d_instruments_kernel<<<",
    "phase_d_configuration_kernel<<<",
    "phase_d_episode_kernel<<<",
  ):
    assert launch in window
  sync = window.index("cudaDeviceSynchronize()")
  assert window[:sync].count("cudaDeviceSynchronize()") == 0
  assert window[:sync].count("cudaMemcpyDeviceToHost") == 0


def test_rb7_cpu_and_cuda_projection_oracles_are_separate() -> None:
  cpu = CPU_TEST.read_text(encoding="utf-8")
  cuda = CUDA_TEST.read_text(encoding="utf-8")
  assert "CudaResidentBackend" not in cpu
  assert "WorldBatchRuntime" not in cpu
  assert "flecs" not in cpu.lower()
  assert "CudaResidentBackend" in cuda
  assert "phase_d_projection_kernel_resources" in cuda
  assert "phase_d_instruments_kernel_resources" in cuda
  assert "phase_d_configuration_kernel_resources" in cuda
  assert "consume_device_observation_view" in cuda
  assert "kPhaseDSurvivalReward" in cuda


def test_rb7_device_view_is_explicitly_lease_scoped_and_private() -> None:
  header = BACKEND_HEADER.read_text(encoding="utf-8")
  backend = BACKEND_SOURCE.read_text(encoding="utf-8")
  facade = FACADE_CONFIG.read_text(encoding="utf-8")
  assert "CudaResidentDeviceObservationView" in header
  assert "std::shared_ptr<void> lifetime" in (STORE_HEADER.read_text(encoding="utf-8"))
  assert "ownership_copy_d2d" in backend
  assert "not_zero_copy" in backend
  assert "kCudaResidentRb7BackendId" in backend
  assert "WorldBatchRuntime" not in backend
  assert "FlecsCpuBackend" not in backend
  assert ".compiled_experimental_backend = false" in facade
  assert ".supported_manifest_ids" not in facade
