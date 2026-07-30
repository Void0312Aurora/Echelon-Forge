#include "runtime/facade/internal/cuda_resident/cuda_world_store.h"

#include <algorithm>
#include <exception>
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
    std::vector<std::uint32_t> entity_generations;
    std::vector<std::uint8_t> setup_active;
    std::vector<std::uint64_t> entity_ids;
    bool phase_a_ready = false;
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

    std::vector<std::uint32_t> next_entity_generations;
    std::vector<std::uint8_t> next_setup_active;
    std::vector<std::uint64_t> next_entity_ids;
    try {
        next_entity_generations.resize(world_capacity, 0);
        next_setup_active.resize(world_capacity, 0);
        next_entity_ids.resize(world_capacity, 0);
    } catch (const std::exception &) {
        impl_->diagnostics.last_error = "CUDA world store host metadata size is not representable";
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
    impl_->entity_generations.swap(next_entity_generations);
    impl_->setup_active.swap(next_setup_active);
    impl_->entity_ids.swap(next_entity_ids);
    impl_->phase_a_ready = false;
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
    std::vector<std::uint32_t> next_entity_generations = impl_->entity_generations;
    std::vector<std::uint8_t> next_setup_active(impl_->setup_active.size(), 0);
    std::vector<std::uint64_t> next_entity_ids(impl_->entity_ids.size(), 0);
    for (std::size_t world = 0; world < impl_->setup_active.size(); ++world) {
        if (impl_->setup_active[world] == 0) {
            continue;
        }
        if (next_entity_generations[world] == std::numeric_limits<std::uint32_t>::max()) {
            impl_->diagnostics.last_error = "CUDA fixed-air fixture entity generation exhausted";
            return false;
        }
        ++next_entity_generations[world];
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
    impl_->entity_generations.swap(next_entity_generations);
    impl_->setup_active.swap(next_setup_active);
    impl_->entity_ids.swap(next_entity_ids);
    impl_->phase_a_ready = false;
    return true;
#else
    (void)seeds;
    impl_->diagnostics.last_error =
        "CUDA resident backend was compiled without EF_ENABLE_CUDA_EXPERIMENTS";
    return false;
#endif
}

bool CudaWorldStore::setup_fixed_air_fixture(std::vector<CudaFixedAirWorldSetup> *setups) {
    if (setups == nullptr || setups->size() != impl_->diagnostics.world_capacity) {
        impl_->diagnostics.last_error =
            "CUDA fixed-air setup count must equal configured world capacity";
        return false;
    }
    if (impl_->diagnostics.state != CudaWorldStoreState::ready) {
        impl_->diagnostics.last_error = "CUDA fixed-air setup requires a ready allocation";
        return false;
    }
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    if (std::any_of(impl_->setup_active.begin(), impl_->setup_active.end(),
                    [](std::uint8_t active) { return active != 0; })) {
        impl_->diagnostics.last_error =
            "CUDA fixed-air setup requires reset before replacing active entities";
        return false;
    }

    std::vector<CudaFixedAirWorldSetup> next_setups = *setups;
    for (std::size_t world = 0; world < next_setups.size(); ++world) {
        if (next_setups[world].world_index != world) {
            impl_->diagnostics.last_error =
                "CUDA fixed-air setup worlds must be canonical and contiguous";
            return false;
        }
        next_setups[world].entity_generation = impl_->entity_generations[world];
        next_setups[world].entity_id =
            fixed_air_fixture_entity_id(impl_->entity_generations[world]);
    }

    std::string error;
    if (!detail::setup_cuda_world_store_fixed_air_fixture(impl_->allocation, next_setups,
                                                          &impl_->faults, &error)) {
        impl_->diagnostics.last_error = std::move(error);
        return false;
    }
    for (std::size_t world = 0; world < next_setups.size(); ++world) {
        impl_->setup_active[world] = 1;
        impl_->entity_ids[world] = next_setups[world].entity_id;
    }
    *setups = std::move(next_setups);
    impl_->phase_a_ready = false;
    impl_->diagnostics.last_error.clear();
    return true;
#else
    impl_->diagnostics.last_error =
        "CUDA resident backend was compiled without EF_ENABLE_CUDA_EXPERIMENTS";
    return false;
#endif
}

bool CudaWorldStore::inject_flight_controls(
    const std::vector<CudaWorldFlightControlAssignment> &assignments) {
    if (impl_->diagnostics.state != CudaWorldStoreState::ready) {
        impl_->diagnostics.last_error = "CUDA flight-control injection requires a ready allocation";
        return false;
    }
    if (assignments.size() != impl_->diagnostics.world_capacity) {
        impl_->diagnostics.last_error =
            "CUDA flight-control assignment count must equal world capacity";
        return false;
    }
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    for (std::size_t world = 0; world < assignments.size(); ++world) {
        if (impl_->setup_active[world] == 0 || assignments[world].world_index != world ||
            assignments[world].entity_id != impl_->entity_ids[world]) {
            impl_->diagnostics.last_error =
                "CUDA flight-control assignment identity does not match fixed-air state";
            return false;
        }
    }
    std::string error;
    if (!detail::inject_cuda_world_store_flight_controls(impl_->allocation, assignments,
                                                         &impl_->faults, &error)) {
        impl_->diagnostics.last_error = std::move(error);
        return false;
    }
    impl_->phase_a_ready = false;
    impl_->diagnostics.last_error.clear();
    return true;
#else
    impl_->diagnostics.last_error =
        "CUDA resident backend was compiled without EF_ENABLE_CUDA_EXPERIMENTS";
    return false;
#endif
}

bool CudaWorldStore::publish_stage() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    if (std::any_of(impl_->setup_active.begin(), impl_->setup_active.end(),
                    [](std::uint8_t active) { return active == 0; })) {
        impl_->diagnostics.last_error =
            "CUDA stage publish requires every fixed-air world to be setup";
        return false;
    }
    std::string error;
    if (!detail::publish_cuda_world_store_stage(impl_->allocation, &impl_->faults, &error)) {
        impl_->diagnostics.last_error = std::move(error);
        return false;
    }
    impl_->phase_a_ready = true;
    impl_->diagnostics.last_error.clear();
    return true;
#else
    impl_->diagnostics.last_error =
        "CUDA resident backend was compiled without EF_ENABLE_CUDA_EXPERIMENTS";
    return false;
#endif
}

bool CudaWorldStore::partial_sync_commit() {
    impl_->diagnostics.last_error = "partial_sync_commit is disabled for the RB2 selected slice";
    return false;
}

bool CudaWorldStore::commit_window() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    if (std::any_of(impl_->setup_active.begin(), impl_->setup_active.end(),
                    [](std::uint8_t active) { return active == 0; })) {
        impl_->diagnostics.last_error =
            "CUDA window commit requires every fixed-air world to be setup";
        return false;
    }
    if (!impl_->phase_a_ready) {
        impl_->diagnostics.last_error =
            "CUDA window commit requires a successful Phase A stage publish";
        return false;
    }
    std::string error;
    if (!detail::commit_cuda_world_store_window(impl_->allocation, &impl_->faults, &error)) {
        impl_->diagnostics.last_error = std::move(error);
        return false;
    }
    impl_->phase_a_ready = false;
    impl_->diagnostics.last_error.clear();
    return true;
#else
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
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    impl_->entity_generations.clear();
    impl_->setup_active.clear();
    impl_->entity_ids.clear();
    impl_->phase_a_ready = false;
#endif
    return true;
}

CudaWorldStoreDiagnostics CudaWorldStore::diagnostics() const {
    return impl_->diagnostics;
}

std::size_t CudaWorldStore::world_capacity() const noexcept {
    return impl_->diagnostics.world_capacity;
}

CudaWorldStoreStateSnapshot CudaWorldStore::state_snapshot() const {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    if (impl_->diagnostics.state != CudaWorldStoreState::ready) {
        throw std::logic_error("CUDA resident state readback requires a ready allocation");
    }
    if (std::any_of(impl_->setup_active.begin(), impl_->setup_active.end(),
                    [](std::uint8_t active) { return active == 0; })) {
        throw std::logic_error(
            "CUDA resident state readback requires every fixed-air world to be setup");
    }
    CudaWorldStoreStateSnapshot snapshot;
    std::string error;
    if (!detail::read_cuda_world_store_state(impl_->allocation, &snapshot, &error)) {
        throw std::runtime_error("CUDA resident state readback failed: " + error);
    }
    return snapshot;
#else
    throw std::logic_error("CUDA resident state readback requires CUDA experiments");
#endif
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

void testing::CudaWorldStoreTestAccess::fail_next_state_transfer(CudaWorldStore &store) noexcept {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    store.impl_->faults.fail_next_state_transfer = true;
#else
    (void)store;
#endif
}

void testing::CudaWorldStoreTestAccess::fail_next_barrier_commit(CudaWorldStore &store) noexcept {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    store.impl_->faults.fail_next_barrier_commit = true;
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

CudaWorldStoreStateSnapshot
testing::CudaWorldStoreTestAccess::read_state(const CudaWorldStore &store) {
    return store.state_snapshot();
}

CudaBarrierKernelResources testing::CudaWorldStoreTestAccess::barrier_kernel_resources() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    CudaBarrierKernelResources resources;
    std::string error;
    if (!detail::query_cuda_world_store_barrier_kernel_resources(&resources, &error)) {
        throw std::runtime_error("CUDA barrier kernel resource query failed: " + error);
    }
    return resources;
#else
    throw std::logic_error("CUDA barrier kernel resource query requires CUDA experiments");
#endif
}

CudaBarrierKernelResources testing::CudaWorldStoreTestAccess::phase_a_kernel_resources() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    CudaBarrierKernelResources resources;
    std::string error;
    if (!detail::query_cuda_world_store_phase_a_kernel_resources(&resources, &error)) {
        throw std::runtime_error("CUDA Phase A kernel resource query failed: " + error);
    }
    return resources;
#else
    throw std::logic_error("CUDA Phase A kernel resource query requires CUDA experiments");
#endif
}

CudaBarrierKernelResources testing::CudaWorldStoreTestAccess::phase_b_forces_kernel_resources() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    CudaBarrierKernelResources resources;
    std::string error;
    if (!detail::query_cuda_world_store_phase_b_forces_kernel_resources(&resources, &error)) {
        throw std::runtime_error("CUDA Phase B forces kernel resource query failed: " + error);
    }
    return resources;
#else
    throw std::logic_error("CUDA Phase B forces kernel resource query requires CUDA experiments");
#endif
}

CudaBarrierKernelResources
testing::CudaWorldStoreTestAccess::phase_b_aerodynamics_kernel_resources() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    CudaBarrierKernelResources resources;
    std::string error;
    if (!detail::query_cuda_world_store_phase_b_aerodynamics_kernel_resources(&resources, &error)) {
        throw std::runtime_error("CUDA Phase B aerodynamics kernel resource query failed: " +
                                 error);
    }
    return resources;
#else
    throw std::logic_error(
        "CUDA Phase B aerodynamics kernel resource query requires CUDA experiments");
#endif
}

CudaBarrierKernelResources testing::CudaWorldStoreTestAccess::phase_b_integrate_kernel_resources() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    CudaBarrierKernelResources resources;
    std::string error;
    if (!detail::query_cuda_world_store_phase_b_integrate_kernel_resources(&resources, &error)) {
        throw std::runtime_error("CUDA Phase B integrate kernel resource query failed: " + error);
    }
    return resources;
#else
    throw std::logic_error(
        "CUDA Phase B integrate kernel resource query requires CUDA experiments");
#endif
}

} // namespace runtime::cuda_resident
