#include "runtime/facade/internal/cuda_resident/cuda_world_store_host_internal.h"

#include <algorithm>

namespace runtime::cuda_resident {

bool CudaWorldStore::acquire_device_observation_lease_raw(
    CudaWorldStoreDeviceObservationLeaseRaw *raw, device_consumer::FailureCode *failure,
    std::string *error) const {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    if (raw == nullptr) {
        if (failure != nullptr) *failure = device_consumer::FailureCode::invalid_request;
        if (error != nullptr) *error = "device observation lease requires an output";
        return false;
    }
    *raw = {};
    if (failure != nullptr) *failure = device_consumer::FailureCode::none;
    if (impl_->diagnostics.state != CudaWorldStoreState::ready || impl_->allocation == nullptr) {
        if (failure != nullptr) *failure = device_consumer::FailureCode::cuda_unavailable;
        if (error != nullptr) *error = "device observation lease requires a ready allocation";
        return false;
    }
    if (impl_->window_state != Impl::WindowState::awaiting_input ||
        impl_->committed_window_epoch == 0 ||
        std::any_of(impl_->setup_active.begin(), impl_->setup_active.end(),
                    [](std::uint8_t active) { return active == 0; })) {
        if (failure != nullptr) *failure = device_consumer::FailureCode::no_committed_window;
        if (error != nullptr) *error = "device observation lease requires a committed window";
        return false;
    }
    const device_consumer::LeaseEpoch epoch{
        .allocation_generation = impl_->diagnostics.allocation_generation,
        .reset_generation = impl_->diagnostics.reset_generation,
        .committed_window = impl_->committed_window_epoch,
        .source_snapshot = impl_->committed_source_snapshot,
    };
    return detail::acquire_cuda_world_store_device_observation_lease(
        impl_->allocation, epoch, raw, &impl_->faults, failure, error);
#else
    (void)raw;
    if (failure != nullptr) *failure = device_consumer::FailureCode::cuda_unavailable;
    if (error != nullptr) *error = "device observation lease requires CUDA experiments";
    return false;
#endif
}

void testing::CudaWorldStoreTestAccess::fail_next_device_lease_allocation(
    CudaWorldStore &store) noexcept {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    store.impl_->faults.fail_next_device_lease_allocation = true;
#else
    (void)store;
#endif
}

void testing::CudaWorldStoreTestAccess::fail_next_device_lease_event_record(
    CudaWorldStore &store) noexcept {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    store.impl_->faults.fail_next_device_lease_event_record = true;
#else
    (void)store;
#endif
}

} // namespace runtime::cuda_resident
