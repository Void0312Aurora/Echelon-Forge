#pragma once

#include "runtime/facade/internal/cuda_resident/cuda_world_store.h"

#if defined(EF_ENABLE_CUDA_RESIDENT_BACKEND)
#include "runtime/facade/internal/cuda_resident/cuda_world_store_device_api.h"
#endif

namespace runtime::cuda_resident {

struct CudaWorldStore::Impl {
    enum class WindowState : std::uint8_t {
        awaiting_input,
        input_injected,
        stage_published,
    };

    CudaWorldStoreDiagnostics diagnostics{};
    WindowState window_state = WindowState::awaiting_input;
#if defined(EF_ENABLE_CUDA_RESIDENT_BACKEND)
    detail::CudaWorldStoreDeviceAllocation *allocation = nullptr;
    detail::CudaWorldStoreDeviceAllocation *pending_cleanup = nullptr;
    detail::CudaWorldStoreDeviceFaultInjection faults{};
    std::vector<std::uint32_t> entity_generations;
    std::vector<std::uint8_t> setup_active;
    std::vector<std::uint64_t> entity_ids;
    bool control_preparation_ready = false;
    std::uint64_t committed_window_epoch = 0;
    std::uint64_t committed_source_snapshot = 0;
#endif
};

} // namespace runtime::cuda_resident
