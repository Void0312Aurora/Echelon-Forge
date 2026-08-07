from __future__ import annotations

from tests.architecture.helpers import REPO_ROOT


CUDA_RESIDENT_DIR = REPO_ROOT / "src/runtime/facade/internal/cuda_resident"
DEVICE_SOURCES = tuple(
    CUDA_RESIDENT_DIR / name
    for name in (
        "cuda_world_store_cuda_internal.cuh",
        "cuda_world_store_cuda_storage.cu",
        "cuda_world_store_cuda_barrier.cu",
        "cuda_world_store_cuda_control_preparation.cu",
        "cuda_world_store_cuda_flight_dynamics.cu",
        "cuda_world_store_cuda_observation_projection.cu",
        "cuda_world_store_cuda_observation.cu",
        "cuda_world_store_cuda_state_readback.cu",
        "cuda_world_store_cuda_window.cu",
    )
)
CMAKE = REPO_ROOT / "CMakeLists.txt"
FACADE_CONFIG = REPO_ROOT / "src/runtime/facade/runtime_facade_config.cpp"
FIXTURE_CONTRACT = REPO_ROOT / "src/runtime/contracts/cuda_resident_fixed_air_fixture_contract.h"
STATE_TEST = REPO_ROOT / "src/tests/test_cuda_resident_backend_state.cpp"
CPU_REFERENCE_TEST = REPO_ROOT / "src/tests/test_cuda_resident_fixed_air_cpu_reference.cpp"


def _device_source() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in DEVICE_SOURCES)


def test_cr2_split_manifest_keeps_private_cuda_translation_units_non_rdc() -> None:
    cmake = CMAKE.read_text(encoding="utf-8")
    source_manifest = cmake.split("set(EF_CUDA_RESIDENT_BACKEND_SOURCES", 1)[1].split(
        "add_library(ef_cuda_resident_backend", 1
    )[0]
    resident_target = cmake.split("add_library(ef_cuda_resident_backend", 1)[1].split(
        "add_library(ef_gpu_experiments", 1
    )[0]
    device_source = _device_source()

    assert "cuda_world_store_cuda.cu" not in source_manifest
    assert "CUDA_SEPARABLE_COMPILATION" not in resident_target
    for path in DEVICE_SOURCES[1:]:
        assert path.name in source_manifest
    assert "#include \"cuda_world_store_cuda_" not in device_source
    assert device_source.count("__global__") == 10
    for kernel in (
        "control_preparation_kernel",
        "flight_dynamics_forces_kernel",
        "flight_dynamics_aerodynamics_kernel",
        "flight_dynamics_integrate_kernel",
        "instrument_projection_kernel",
        "configuration_projection_kernel",
        "episode_projection_kernel",
        "pack_device_observation_kernel",
        "device_observation_consumer_smoke_kernel",
        "apply_barrier_kernel",
    ):
        assert kernel in device_source


def test_rb3_store_is_separate_instance_owned_target() -> None:
    cmake = CMAKE.read_text(encoding="utf-8")
    store_header = (CUDA_RESIDENT_DIR / "cuda_world_store.h").read_text(encoding="utf-8")
    store_source = (CUDA_RESIDENT_DIR / "cuda_world_store.cpp").read_text(encoding="utf-8")
    device_source = _device_source()

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
    device_source = _device_source()
    store_header = (CUDA_RESIDENT_DIR / "cuda_world_store.h").read_text(encoding="utf-8")
    backend_source = (CUDA_RESIDENT_DIR / "cuda_resident_backend.cpp").read_text(encoding="utf-8")
    cmake = CMAKE.read_text(encoding="utf-8")

    assert "CudaWorldStateSlotLayout" in device_source
    assert "control_doubles" in device_source
    assert "kinematics" in device_source
    assert "CudaWorldStateRecord" not in device_source
    assert "__global__ void apply_barrier_kernel" in device_source
    assert "--ptxas-options=-v" in cmake
    assert "partial_sync_commit is disabled for the selected CUDA-resident slice" in (
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
