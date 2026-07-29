#include "runtime/facade/internal/cuda_resident/cuda_world_store_device_api.h"

#include <cuda_runtime_api.h>

#include <limits>
#include <memory>
#include <new>
#include <utility>
#include <vector>

namespace runtime::cuda_resident::detail {

namespace {

struct alignas(16) CudaWorldLifecycleRecord {
    std::uint64_t reset_generation = 0;
    std::uint32_t seed = 0;
    std::uint32_t reserved = 0;
};

static_assert(sizeof(CudaWorldLifecycleRecord) == 16);

std::string cuda_error_message(const char *operation, cudaError_t status) {
    return std::string(operation) + ": " + cudaGetErrorString(status);
}

bool consume_fault(bool *fault) noexcept {
    if (fault == nullptr || !*fault) {
        return false;
    }
    *fault = false;
    return true;
}

} // namespace

struct CudaWorldStoreDeviceAllocation {
    CudaWorldLifecycleRecord *records = nullptr;
    std::size_t world_capacity = 0;
    std::uint8_t active_slot = 0;
};

bool cuda_world_store_runtime_available(std::string *error) {
    int device_count = 0;
    const cudaError_t status = cudaGetDeviceCount(&device_count);
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("cudaGetDeviceCount", status);
        }
        return false;
    }
    if (device_count <= 0) {
        if (error != nullptr) {
            *error = "cudaGetDeviceCount returned no CUDA devices";
        }
        return false;
    }
    if (error != nullptr) {
        error->clear();
    }
    return true;
}

CudaWorldStoreDeviceAllocationResult
allocate_cuda_world_store_metadata(std::size_t world_capacity,
                                   CudaWorldStoreDeviceFaultInjection *faults) {
    CudaWorldStoreDeviceAllocationResult result{};
    std::unique_ptr<CudaWorldStoreDeviceAllocation> allocation(
        new (std::nothrow) CudaWorldStoreDeviceAllocation{});
    if (!allocation) {
        result.error = "failed to allocate CUDA world store host owner";
        return result;
    }
    allocation->world_capacity = world_capacity;

    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_allocation)) {
        result.error = "injected CUDA world store allocation failure";
        return result;
    }

    if (world_capacity != 0) {
        constexpr std::size_t slot_count = 2;
        if (world_capacity > std::numeric_limits<std::size_t>::max() /
                                 (slot_count * sizeof(CudaWorldLifecycleRecord))) {
            result.error = "CUDA world store metadata size overflow";
            return result;
        }
        result.device_bytes = world_capacity * slot_count * sizeof(CudaWorldLifecycleRecord);
        const cudaError_t status =
            cudaMalloc(reinterpret_cast<void **>(&allocation->records), result.device_bytes);
        if (status != cudaSuccess) {
            result.error = cuda_error_message("cudaMalloc(lifecycle_records)", status);
            result.device_bytes = 0;
            return result;
        }
    }

    // No potentially-throwing operation follows the successful cudaMalloc;
    // ownership transfers directly into the opaque result.
    result.allocation = allocation.release();
    return result;
}

bool reset_cuda_world_store_metadata(CudaWorldStoreDeviceAllocation *allocation,
                                     const std::uint32_t *seeds, std::size_t world_capacity,
                                     std::uint64_t reset_generation,
                                     CudaWorldStoreDeviceFaultInjection *faults,
                                     std::string *error) {
    if (allocation == nullptr || allocation->world_capacity != world_capacity) {
        if (error != nullptr) {
            *error = "CUDA world store reset allocation/capacity mismatch";
        }
        return false;
    }
    if (world_capacity == 0) {
        allocation->active_slot ^= 1U;
        if (error != nullptr) {
            error->clear();
        }
        return true;
    }

    // Construct the complete next epoch before touching device memory. One
    // copy targets the inactive slot, so a host allocation failure or CUDA
    // copy failure cannot expose mixed seed/generation epochs.
    std::vector<CudaWorldLifecycleRecord> next_records;
    try {
        next_records.resize(world_capacity);
    } catch (const std::bad_alloc &) {
        if (error != nullptr) {
            *error = "failed to allocate CUDA world store reset staging metadata";
        }
        return false;
    }
    for (std::size_t index = 0; index < world_capacity; ++index) {
        next_records[index].reset_generation = reset_generation;
        next_records[index].seed = seeds == nullptr ? 0 : seeds[index];
    }

    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_reset_copy)) {
        if (error != nullptr) {
            *error = "injected CUDA world store reset metadata copy failure";
        }
        return false;
    }

    const std::uint8_t next_slot = allocation->active_slot ^ 1U;
    CudaWorldLifecycleRecord *destination =
        allocation->records + (static_cast<std::size_t>(next_slot) * world_capacity);
    const cudaError_t status =
        cudaMemcpy(destination, next_records.data(),
                   world_capacity * sizeof(CudaWorldLifecycleRecord), cudaMemcpyHostToDevice);
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("reset lifecycle metadata", status);
        }
        return false;
    }

    allocation->active_slot = next_slot;
    if (error != nullptr) {
        error->clear();
    }
    return true;
}

bool read_cuda_world_store_metadata(const CudaWorldStoreDeviceAllocation *allocation,
                                    std::size_t world_capacity,
                                    CudaWorldStoreDeviceSnapshot *snapshot, std::string *error) {
    if (allocation == nullptr || allocation->world_capacity != world_capacity ||
        snapshot == nullptr) {
        if (error != nullptr) {
            *error = "CUDA world store readback allocation/capacity mismatch";
        }
        return false;
    }

    std::vector<CudaWorldLifecycleRecord> records(world_capacity);
    if (world_capacity != 0) {
        const CudaWorldLifecycleRecord *source =
            allocation->records +
            (static_cast<std::size_t>(allocation->active_slot) * world_capacity);
        const cudaError_t status =
            cudaMemcpy(records.data(), source, world_capacity * sizeof(CudaWorldLifecycleRecord),
                       cudaMemcpyDeviceToHost);
        if (status != cudaSuccess) {
            if (error != nullptr) {
                *error = cuda_error_message("read lifecycle metadata", status);
            }
            return false;
        }
    }

    CudaWorldStoreDeviceSnapshot next_snapshot;
    next_snapshot.seeds.reserve(world_capacity);
    next_snapshot.reset_generations.reserve(world_capacity);
    for (const CudaWorldLifecycleRecord &record : records) {
        next_snapshot.seeds.push_back(record.seed);
        next_snapshot.reset_generations.push_back(record.reset_generation);
    }
    *snapshot = std::move(next_snapshot);
    if (error != nullptr) {
        error->clear();
    }
    return true;
}

bool release_cuda_world_store_metadata(CudaWorldStoreDeviceAllocation *&allocation,
                                       CudaWorldStoreDeviceFaultInjection *faults) noexcept {
    if (allocation == nullptr) {
        return true;
    }
    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_release)) {
        return false;
    }
    if (allocation->records != nullptr) {
        // Surface pending asynchronous failures before cudaFree. If either
        // operation fails, retain the owner and device pointer for a retry.
        if (cudaDeviceSynchronize() != cudaSuccess) {
            return false;
        }
        if (cudaFree(allocation->records) != cudaSuccess) {
            return false;
        }
        allocation->records = nullptr;
    }
    delete allocation;
    allocation = nullptr;
    return true;
}

} // namespace runtime::cuda_resident::detail
