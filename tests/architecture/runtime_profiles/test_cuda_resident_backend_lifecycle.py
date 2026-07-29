from __future__ import annotations

from tests.architecture.helpers import REPO_ROOT


CUDA_RESIDENT_DIR = REPO_ROOT / "src/runtime/facade/internal/cuda_resident"
CMAKE = REPO_ROOT / "CMakeLists.txt"
FACADE_CONFIG = REPO_ROOT / "src/runtime/facade/runtime_facade_config.cpp"


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
    assert "active_slot" in device_source
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
