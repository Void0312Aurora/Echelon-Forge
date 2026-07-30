#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include "runtime/facade/internal/cuda_resident/cuda_world_store.h"

namespace runtime::cuda_resident::detail {

struct CudaWorldStoreDeviceAllocation;

struct CudaWorldStoreDeviceFaultInjection {
    bool fail_next_allocation = false;
    bool fail_next_reset_copy = false;
    bool fail_next_release = false;
    bool fail_next_state_transfer = false;
    bool fail_next_barrier_commit = false;
};

struct CudaWorldStoreDeviceSnapshot {
    std::vector<std::uint32_t> seeds;
    std::vector<std::uint64_t> reset_generations;
};

struct CudaWorldStoreDeviceAllocationResult {
    CudaWorldStoreDeviceAllocation *allocation = nullptr;
    std::size_t device_bytes = 0;
    std::string error;
};

[[nodiscard]] bool cuda_world_store_runtime_available(std::string *error);
[[nodiscard]] CudaWorldStoreDeviceAllocationResult
allocate_cuda_world_store_metadata(std::size_t world_capacity,
                                   CudaWorldStoreDeviceFaultInjection *faults);
[[nodiscard]] bool reset_cuda_world_store_metadata(CudaWorldStoreDeviceAllocation *allocation,
                                                   const std::uint32_t *seeds,
                                                   std::size_t world_capacity,
                                                   std::uint64_t reset_generation,
                                                   CudaWorldStoreDeviceFaultInjection *faults,
                                                   std::string *error);
[[nodiscard]] bool read_cuda_world_store_metadata(const CudaWorldStoreDeviceAllocation *allocation,
                                                  std::size_t world_capacity,
                                                  CudaWorldStoreDeviceSnapshot *snapshot,
                                                  std::string *error);
[[nodiscard]] bool setup_cuda_world_store_fixed_air_fixture(
    CudaWorldStoreDeviceAllocation *allocation, const std::vector<CudaFixedAirWorldSetup> &setups,
    CudaWorldStoreDeviceFaultInjection *faults, std::string *error);
[[nodiscard]] bool inject_cuda_world_store_flight_controls(
    CudaWorldStoreDeviceAllocation *allocation,
    const std::vector<CudaWorldFlightControlAssignment> &assignments,
    CudaWorldStoreDeviceFaultInjection *faults, std::string *error);
[[nodiscard]] bool publish_cuda_world_store_stage(CudaWorldStoreDeviceAllocation *allocation,
                                                  CudaWorldStoreDeviceFaultInjection *faults,
                                                  std::string *error);
[[nodiscard]] bool commit_cuda_world_store_window(CudaWorldStoreDeviceAllocation *allocation,
                                                  CudaWorldStoreDeviceFaultInjection *faults,
                                                  std::string *error);
[[nodiscard]] bool read_cuda_world_store_state(const CudaWorldStoreDeviceAllocation *allocation,
                                               CudaWorldStoreStateSnapshot *snapshot,
                                               std::string *error);
[[nodiscard]] bool
query_cuda_world_store_barrier_kernel_resources(CudaBarrierKernelResources *resources,
                                                std::string *error);
[[nodiscard]] bool
query_cuda_world_store_phase_a_kernel_resources(CudaBarrierKernelResources *resources,
                                                std::string *error);
[[nodiscard]] bool
release_cuda_world_store_metadata(CudaWorldStoreDeviceAllocation *&allocation,
                                  CudaWorldStoreDeviceFaultInjection *faults) noexcept;

} // namespace runtime::cuda_resident::detail
