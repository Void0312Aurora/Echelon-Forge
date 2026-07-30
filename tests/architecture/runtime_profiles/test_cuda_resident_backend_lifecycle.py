from __future__ import annotations

from tests.architecture.helpers import REPO_ROOT


CUDA_RESIDENT_DIR = REPO_ROOT / "src/runtime/facade/internal/cuda_resident"
CMAKE = REPO_ROOT / "CMakeLists.txt"
FACADE_CONFIG = REPO_ROOT / "src/runtime/facade/runtime_facade_config.cpp"
FIXTURE_CONTRACT = REPO_ROOT / "src/runtime/contracts/cuda_resident_fixed_air_fixture_contract.h"
STATE_TEST = REPO_ROOT / "src/tests/test_cuda_resident_backend_state.cpp"
CPU_REFERENCE_TEST = REPO_ROOT / "src/tests/test_cuda_resident_fixed_air_cpu_reference.cpp"


def test_rb3_store_is_separate_instance_owned_target() -> None:
    cmake = CMAKE.read_text(encoding="utf-8")
    store_header = (CUDA_RESIDENT_DIR / "cuda_world_store.h").read_text(encoding="utf-8")
    store_source = (CUDA_RESIDENT_DIR / "cuda_world_store.cpp").read_text(encoding="utf-8")
    device_source = (CUDA_RESIDENT_DIR / "cuda_world_store_cuda.cu").read_text(encoding="utf-8")

    assert "add_library(ef_cuda_resident_backend STATIC" in cmake
    assert "std::unique_ptr<Impl> impl_" in store_header
    assert "CudaWorldStore(const CudaWorldStore &) = delete" in store_header
    assert "CudaWorldStore(CudaWorldStore &&) = delete" in store_header
    assert "release_cuda_world_store_metadata(impl_->allocation, &impl_->faults)" in store_source
    assert "CudaWorldStoreDeviceAllocation *allocation" in device_source
    assert "active_lifecycle_slot" in device_source
    assert "active_state_slot" in device_source
    assert "read_cuda_world_store_metadata" in device_source
    assert "fail_next_release" in device_source
    assert "g_cache" not in store_source
    assert "g_cache" not in device_source
    assert "static CudaWorldStore" not in store_source
    assert "static CudaWorldStoreDeviceAllocation" not in device_source


def test_rb3_shell_remains_fail_closed_and_does_not_advertise_manifest() -> None:
    backend_header = (CUDA_RESIDENT_DIR / "cuda_resident_backend.h").read_text(encoding="utf-8")
    backend_source = (CUDA_RESIDENT_DIR / "cuda_resident_backend.cpp").read_text(encoding="utf-8")
    facade_config = FACADE_CONFIG.read_text(encoding="utf-8")

    assert "class CudaResidentBackend final : public IWorldBatchBackend" in backend_header
    assert "reject_unimplemented_operation" in backend_source
    assert "cuda_resident.air_execution.fixed_step.v1" not in backend_header
    assert "cuda_resident.air_execution.fixed_step.v1" not in backend_source
    assert ".compiled_experimental_backend = false" in facade_config
    assert ".supported_manifest_ids" not in facade_config
    assert "supports_resident_state = false" in facade_config
    assert "supports_exact_gpu_backend = false" in facade_config
    assert "supports_device_observation_view = false" in facade_config


def test_rb4_state_layout_is_device_owned_soa_with_narrow_barrier_kernel() -> None:
    device_source = (CUDA_RESIDENT_DIR / "cuda_world_store_cuda.cu").read_text(encoding="utf-8")
    store_header = (CUDA_RESIDENT_DIR / "cuda_world_store.h").read_text(encoding="utf-8")
    backend_source = (CUDA_RESIDENT_DIR / "cuda_resident_backend.cpp").read_text(encoding="utf-8")
    cmake = CMAKE.read_text(encoding="utf-8")

    assert "CudaWorldStateSlotLayout" in device_source
    assert "control_doubles" in device_source
    assert "kinematics" in device_source
    assert "CudaWorldStateRecord" not in device_source
    assert "__global__ void apply_barrier_kernel" in device_source
    assert "--ptxas-options=-v" in cmake
    assert "partial_sync_commit is disabled for the RB2 selected slice" in (
        CUDA_RESIDENT_DIR / "cuda_world_store.cpp"
    ).read_text(encoding="utf-8")
    assert "required_visible_shards" in backend_source
    assert "materialized_shards" in backend_source
    assert "contract_satisfied && rule->host_truth_available" in backend_source
    assert "CUDA resident state readback requires every fixed-air world to be setup" in (
        CUDA_RESIDENT_DIR / "cuda_world_store.cpp"
    ).read_text(encoding="utf-8")
    assert "state_snapshot() const;" in store_header.split("private:", maxsplit=1)[1]
    assert "FlecsCpuBackend" not in backend_source
    assert "WorldBatchRuntime" not in backend_source
    assert "step_batch" not in backend_source


def test_rb4_cpu_and_cuda_paths_consume_one_fixed_fixture_identity_contract() -> None:
    contract = FIXTURE_CONTRACT.read_text(encoding="utf-8")
    state_test = STATE_TEST.read_text(encoding="utf-8")
    cpu_test = CPU_REFERENCE_TEST.read_text(encoding="utf-8")

    assert "kFixedAirFixtureEntityBaseId = 581" in contract
    assert "fixed_air_fixture_entity_id" in state_test
    assert "fixed_air_fixture_entity_id" in cpu_test
    assert "FlecsCpuBackend" not in state_test
    assert "CudaResidentBackend" not in cpu_test
