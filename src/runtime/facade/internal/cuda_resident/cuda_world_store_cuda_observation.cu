#include "runtime/facade/internal/cuda_resident/cuda_world_store_cuda_internal.cuh"
#include "runtime/contracts/cuda_resident_phase_d_fixture_contract.h"

#include <algorithm>
#include <cmath>
#include <memory>
#include <new>
#include <utility>
#include <vector>
namespace runtime::cuda_resident::detail {
namespace {
__device__ inline float phase_d_to_float(double value) {
    if (!isfinite(value)) return 0.0F;
    return static_cast<float>(fmin(fmax(value, -kPhaseDObservationFloatClip),
                                   kPhaseDObservationFloatClip));
}

__global__ void phase_d_pack_observation_kernel(
    std::size_t world_capacity, const double *observations, const std::uint64_t *observation_ids,
    float *values, std::uint64_t *ids) {
    const std::size_t world = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (world >= world_capacity) return;
    const std::size_t base = world * kPhaseDObservationFieldCount;
    for (std::size_t field = 0; field < kPhaseDObservationFieldCount; ++field) {
        values[base + field] =
            phase_d_to_float(observations[field * world_capacity + world]);
    }
    ids[world] = observation_ids[world];
}

__global__ void phase_d_consumer_smoke_kernel(
    const float *values, const std::uint64_t *ids, std::size_t world_capacity,
    std::size_t values_per_world, float *first_values, std::uint64_t *out_ids) {
    const std::size_t world = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (world >= world_capacity) return;
    first_values[world] = values[world * values_per_world];
    out_ids[world] = ids[world];
}

} // namespace

bool export_cuda_world_store_device_observation(
    const CudaWorldStoreDeviceAllocation *allocation, CudaWorldStoreDeviceObservationRaw *raw,
    std::string *error) {
    if (allocation == nullptr || raw == nullptr) {
        if (error != nullptr) *error = "CUDA device observation export requires an allocation";
        return false;
    }
    *raw = {};
    raw->world_count = allocation->world_capacity;
    raw->values_per_world = kPhaseDObservationFieldCount;
    if (allocation->world_capacity == 0) {
        if (error != nullptr) error->clear();
        return true;
    }
    const std::size_t value_count =
        allocation->world_capacity * kPhaseDObservationFieldCount;
    float *values = nullptr;
    std::uint64_t *ids = nullptr;
    cudaError_t status = cudaMalloc(reinterpret_cast<void **>(&values), value_count * sizeof(float));
    if (status == cudaSuccess) {
        status = cudaMalloc(reinterpret_cast<void **>(&ids),
                            allocation->world_capacity * sizeof(std::uint64_t));
    }
    if (status != cudaSuccess) {
        if (values != nullptr) cudaFree(values);
        if (ids != nullptr) cudaFree(ids);
        if (error != nullptr) *error = cuda_error_message("allocate device observation view", status);
        return false;
    }
    constexpr unsigned int threads = 128;
    const unsigned int blocks = static_cast<unsigned int>(
        (allocation->world_capacity + threads - 1) / threads);
    const std::uint8_t *slot = allocation->state_slots[allocation->active_state_slot];
    phase_d_pack_observation_kernel<<<blocks, threads>>>(
        allocation->world_capacity,
        device_field<double>(slot, allocation->state_layout.phase_d_observations),
        device_field<std::uint64_t>(slot, allocation->state_layout.phase_d_observation_ids), values,
        ids);
    status = cudaGetLastError();
    if (status == cudaSuccess) status = cudaDeviceSynchronize();
    std::vector<std::uint64_t> versions(allocation->world_capacity, 0);
    if (status == cudaSuccess) {
        status = cudaMemcpy(versions.data(),
                            device_field<std::uint64_t>(slot, allocation->state_layout.global_versions),
                            versions.size() * sizeof(std::uint64_t), cudaMemcpyDeviceToHost);
    }
    if (status != cudaSuccess || versions.empty() ||
        std::any_of(versions.begin(), versions.end(), [&](std::uint64_t value) {
            return value != versions.front();
        })) {
        if (values != nullptr) cudaFree(values);
        if (ids != nullptr) cudaFree(ids);
        if (error != nullptr) {
            *error = status != cudaSuccess
                         ? cuda_error_message("materialize device observation view", status)
                         : "resident device observation worlds have divergent snapshots";
        }
        return false;
    }
    raw->values = values;
    raw->ids = ids;
    raw->source_snapshot = versions.front();
    if (error != nullptr) error->clear();
    return true;
}

void release_cuda_world_store_device_observation(void *values, void *ids) noexcept {
    if (values != nullptr) cudaFree(values);
    if (ids != nullptr) cudaFree(ids);
}

bool consume_cuda_world_store_device_observation(
    const void *values, const void *ids, std::size_t world_count, std::size_t values_per_world,
    std::vector<float> *first_values, std::vector<std::uint64_t> *ids_out, std::string *error) {
    if (values == nullptr || ids == nullptr || first_values == nullptr || ids_out == nullptr ||
        world_count == 0 || values_per_world == 0) {
        if (error != nullptr) *error = "device observation consumer requires a valid lease";
        return false;
    }
    float *device_first_values = nullptr;
    std::uint64_t *device_ids = nullptr;
    cudaError_t status = cudaMalloc(reinterpret_cast<void **>(&device_first_values),
                                     world_count * sizeof(float));
    if (status == cudaSuccess) {
        status = cudaMalloc(reinterpret_cast<void **>(&device_ids),
                            world_count * sizeof(std::uint64_t));
    }
    if (status == cudaSuccess) {
        constexpr unsigned int threads = 128;
        const unsigned int blocks =
            static_cast<unsigned int>((world_count + threads - 1) / threads);
        phase_d_consumer_smoke_kernel<<<blocks, threads>>>(
            static_cast<const float *>(values), static_cast<const std::uint64_t *>(ids), world_count,
            values_per_world, device_first_values, device_ids);
        status = cudaGetLastError();
    }
    if (status == cudaSuccess) status = cudaDeviceSynchronize();
    std::vector<float> next_values(world_count, 0.0F);
    std::vector<std::uint64_t> next_ids(world_count, 0);
    if (status == cudaSuccess) {
        status = cudaMemcpy(next_values.data(), device_first_values,
                            world_count * sizeof(float), cudaMemcpyDeviceToHost);
    }
    if (status == cudaSuccess) {
        status = cudaMemcpy(next_ids.data(), device_ids, world_count * sizeof(std::uint64_t),
                            cudaMemcpyDeviceToHost);
    }
    if (device_first_values != nullptr) cudaFree(device_first_values);
    if (device_ids != nullptr) cudaFree(device_ids);
    if (status != cudaSuccess) {
        if (error != nullptr) *error = cuda_error_message("consume device observation view", status);
        return false;
    }
    *first_values = std::move(next_values);
    *ids_out = std::move(next_ids);
    if (error != nullptr) error->clear();
    return true;
}

bool query_cuda_world_store_phase_d_pack_kernel_resources(CudaBarrierKernelResources *resources,
                                                          std::string *error) {
    return query_phase_b_kernel_resources(phase_d_pack_observation_kernel,
                                          "phase_d_pack_observation_kernel", resources, error);
}

bool query_cuda_world_store_phase_d_consumer_kernel_resources(
    CudaBarrierKernelResources *resources, std::string *error) {
    return query_phase_b_kernel_resources(phase_d_consumer_smoke_kernel,
                                          "phase_d_consumer_smoke_kernel", resources, error);
}


} // namespace runtime::cuda_resident::detail
