#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace runtime::cuda_resident::detail {

struct CudaWorldStoreDeviceAllocation;

struct CudaWorldStoreDeviceFaultInjection {
    bool fail_next_allocation = false;
    bool fail_next_reset_copy = false;
    bool fail_next_release = false;
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
[[nodiscard]] bool
release_cuda_world_store_metadata(CudaWorldStoreDeviceAllocation *&allocation,
                                  CudaWorldStoreDeviceFaultInjection *faults) noexcept;

} // namespace runtime::cuda_resident::detail
