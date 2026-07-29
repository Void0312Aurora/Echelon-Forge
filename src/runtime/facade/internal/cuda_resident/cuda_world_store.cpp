#include "runtime/facade/internal/cuda_resident/cuda_world_store.h"

#include <limits>
#include <stdexcept>
#include <utility>

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
#include "runtime/facade/internal/cuda_resident/cuda_world_store_device_api.h"
#endif

namespace runtime::cuda_resident {

struct CudaWorldStore::Impl {
    CudaWorldStoreDiagnostics diagnostics{};
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    detail::CudaWorldStoreDeviceAllocation *allocation = nullptr;
    detail::CudaWorldStoreDeviceAllocation *pending_cleanup = nullptr;
    detail::CudaWorldStoreDeviceFaultInjection faults{};
#endif
};

CudaWorldStore::CudaWorldStore() : impl_(std::make_unique<Impl>()) {
    impl_->diagnostics.compiled_with_cuda = compiled_with_cuda();
}

CudaWorldStore::~CudaWorldStore() {
    (void)teardown();
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    // A one-shot teardown failure keeps ownership intact. The destructor gets
    // one final best-effort retry; CUDA context destruction remains the final
    // process-level recovery for a persistent runtime release failure.
    (void)detail::release_cuda_world_store_metadata(impl_->pending_cleanup, &impl_->faults);
    (void)detail::release_cuda_world_store_metadata(impl_->allocation, &impl_->faults);
#endif
}

bool CudaWorldStore::compiled_with_cuda() noexcept {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return true;
#else
    return false;
#endif
}

bool CudaWorldStore::configure(std::size_t world_capacity) {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    if (impl_->diagnostics.allocation_generation == std::numeric_limits<std::uint64_t>::max()) {
        impl_->diagnostics.last_error = "CUDA world store allocation generation exhausted";
        return false;
    }

    std::string availability_error;
    if (!detail::cuda_world_store_runtime_available(&availability_error)) {
        if (impl_->diagnostics.state != CudaWorldStoreState::ready) {
            impl_->diagnostics.state = CudaWorldStoreState::unavailable;
        }
        impl_->diagnostics.runtime_available = false;
        impl_->diagnostics.last_error = std::move(availability_error);
        return false;
    }

    if (!detail::release_cuda_world_store_metadata(impl_->pending_cleanup, &impl_->faults)) {
        impl_->diagnostics.last_error =
            "CUDA world store could not release a pending replacement allocation";
        return false;
    }

    detail::CudaWorldStoreDeviceAllocationResult allocation =
        detail::allocate_cuda_world_store_metadata(world_capacity, &impl_->faults);
    if (allocation.allocation == nullptr) {
        if (impl_->diagnostics.state != CudaWorldStoreState::ready) {
            impl_->diagnostics.state = CudaWorldStoreState::unavailable;
        }
        impl_->diagnostics.runtime_available = true;
        impl_->diagnostics.last_error = std::move(allocation.error);
        return false;
    }

    if (!detail::release_cuda_world_store_metadata(impl_->allocation, &impl_->faults)) {
        if (!detail::release_cuda_world_store_metadata(allocation.allocation, &impl_->faults)) {
            // Keep the replacement owner reachable and block further
            // allocation until a later configure/teardown retries cleanup.
            impl_->pending_cleanup = allocation.allocation;
        }
        impl_->diagnostics.last_error = "CUDA world store could not release the active allocation";
        return false;
    }
    impl_->allocation = allocation.allocation;
    impl_->diagnostics.state = CudaWorldStoreState::ready;
    impl_->diagnostics.runtime_available = true;
    impl_->diagnostics.world_capacity = world_capacity;
    impl_->diagnostics.device_bytes = allocation.device_bytes;
    ++impl_->diagnostics.allocation_generation;
    impl_->diagnostics.last_error.clear();
    return true;
#else
    (void)world_capacity;
    impl_->diagnostics.state = CudaWorldStoreState::unavailable;
    impl_->diagnostics.runtime_available = false;
    impl_->diagnostics.last_error =
        "CUDA resident backend was compiled without EF_ENABLE_CUDA_EXPERIMENTS";
    return false;
#endif
}

bool CudaWorldStore::reset(const std::vector<std::uint32_t> &seeds) {
    if (impl_->diagnostics.state != CudaWorldStoreState::ready) {
        impl_->diagnostics.last_error = "CUDA world store reset requires a ready allocation";
        return false;
    }
    if (!seeds.empty() && seeds.size() != impl_->diagnostics.world_capacity) {
        impl_->diagnostics.last_error =
            "CUDA world store seed count must be empty or equal world capacity";
        return false;
    }

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    if (impl_->diagnostics.reset_generation == std::numeric_limits<std::uint64_t>::max()) {
        impl_->diagnostics.last_error = "CUDA world store reset generation exhausted";
        return false;
    }
    const std::uint64_t next_reset_generation = impl_->diagnostics.reset_generation + 1;
    std::string error;
    if (!detail::reset_cuda_world_store_metadata(
            impl_->allocation, seeds.empty() ? nullptr : seeds.data(),
            impl_->diagnostics.world_capacity, next_reset_generation, &impl_->faults, &error)) {
        impl_->diagnostics.last_error = std::move(error);
        return false;
    }
    impl_->diagnostics.reset_generation = next_reset_generation;
    impl_->diagnostics.last_error.clear();
    return true;
#else
    (void)seeds;
    impl_->diagnostics.last_error =
        "CUDA resident backend was compiled without EF_ENABLE_CUDA_EXPERIMENTS";
    return false;
#endif
}

bool CudaWorldStore::teardown() noexcept {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    if (!detail::release_cuda_world_store_metadata(impl_->pending_cleanup, &impl_->faults) ||
        !detail::release_cuda_world_store_metadata(impl_->allocation, &impl_->faults)) {
        return false;
    }
#endif
    impl_->diagnostics.state = CudaWorldStoreState::unconfigured;
    impl_->diagnostics.runtime_available = false;
    impl_->diagnostics.world_capacity = 0;
    impl_->diagnostics.device_bytes = 0;
    impl_->diagnostics.last_error.clear();
    return true;
}

CudaWorldStoreDiagnostics CudaWorldStore::diagnostics() const {
    return impl_->diagnostics;
}

std::size_t CudaWorldStore::world_capacity() const noexcept {
    return impl_->diagnostics.world_capacity;
}

void testing::CudaWorldStoreTestAccess::fail_next_allocation(CudaWorldStore &store) noexcept {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    store.impl_->faults.fail_next_allocation = true;
#else
    (void)store;
#endif
}

void testing::CudaWorldStoreTestAccess::fail_next_reset_copy(CudaWorldStore &store) noexcept {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    store.impl_->faults.fail_next_reset_copy = true;
#else
    (void)store;
#endif
}

void testing::CudaWorldStoreTestAccess::fail_next_release(CudaWorldStore &store) noexcept {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    store.impl_->faults.fail_next_release = true;
#else
    (void)store;
#endif
}

void testing::CudaWorldStoreTestAccess::set_allocation_generation(
    CudaWorldStore &store, std::uint64_t generation) noexcept {
    store.impl_->diagnostics.allocation_generation = generation;
}

void testing::CudaWorldStoreTestAccess::set_reset_generation(CudaWorldStore &store,
                                                             std::uint64_t generation) noexcept {
    store.impl_->diagnostics.reset_generation = generation;
}

CudaWorldStoreLifecycleSnapshot
testing::CudaWorldStoreTestAccess::readback(const CudaWorldStore &store) {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    detail::CudaWorldStoreDeviceSnapshot device_snapshot;
    std::string error;
    if (!detail::read_cuda_world_store_metadata(store.impl_->allocation,
                                                store.impl_->diagnostics.world_capacity,
                                                &device_snapshot, &error)) {
        throw std::runtime_error("CUDA world store metadata readback failed: " + error);
    }
    return {
        .seeds = std::move(device_snapshot.seeds),
        .reset_generations = std::move(device_snapshot.reset_generations),
    };
#else
    (void)store;
    throw std::logic_error("CUDA world store metadata readback requires CUDA experiments");
#endif
}

} // namespace runtime::cuda_resident
