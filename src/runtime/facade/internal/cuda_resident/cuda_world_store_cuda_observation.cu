#include "runtime/facade/internal/cuda_resident/cuda_world_store_cuda_internal.cuh"
#include "runtime/contracts/cuda_resident_learner_consumption_contract.h"
#include "runtime/contracts/cuda_resident_observation_projection_fixture_contract.h"

#include <algorithm>
#include <cmath>
#include <memory>
#include <new>
#include <utility>
#include <vector>
namespace runtime::cuda_resident::detail {
namespace {
__device__ inline float observation_projection_to_float(double value) {
    if (!isfinite(value)) return 0.0F;
    return static_cast<float>(fmin(fmax(value, -kObservationProjectionObservationFloatClip),
                                   kObservationProjectionObservationFloatClip));
}

__global__ void pack_device_observation_kernel(std::size_t world_capacity,
                                               const double *observations,
                                               const std::uint64_t *observation_ids, float *values,
                                               std::uint64_t *ids) {
    const std::size_t world = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (world >= world_capacity) return;
    const std::size_t base = world * kObservationProjectionObservationFieldCount;
    for (std::size_t field = 0; field < kObservationProjectionObservationFieldCount; ++field) {
        values[base + field] =
            observation_projection_to_float(observations[field * world_capacity + world]);
    }
    ids[world] = observation_ids[world];
}

__global__ void
device_observation_consumer_smoke_kernel(const float *values, const std::uint64_t *ids,
                                         std::size_t world_capacity, std::size_t values_per_world,
                                         float *out_values, std::uint64_t *out_ids) {
    const std::size_t world = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (world >= world_capacity) return;
    out_values[world] = values[world * values_per_world];
    out_ids[world] = ids[world];
}

static_assert(learner_consumption::kLearnerConsumptionFeatureCount ==
                  kObservationProjectionObservationFieldCount,
              "learner-equivalent consumption covers exactly the packed observation layout");

// Kernel-parameter copy of the contract-owned normalization table. Passing the
// constants by value keeps the contract the single owner without a device
// symbol to keep synchronized.
struct LearnerNormalizationValues {
    float offsets[learner_consumption::kLearnerConsumptionFeatureCount];
    float scales[learner_consumption::kLearnerConsumptionFeatureCount];
};

[[nodiscard]] LearnerNormalizationValues learner_normalization_values() noexcept {
    LearnerNormalizationValues values{};
    for (std::size_t field = 0; field < learner_consumption::kLearnerConsumptionFeatureCount;
         ++field) {
        values.offsets[field] = learner_consumption::kLearnerNormalization[field].offset;
        values.scales[field] = learner_consumption::kLearnerNormalization[field].scale;
    }
    return values;
}

// Learner-equivalent consumer: reads every element of the lease tensor,
// applies the contract-owned per-field affine normalization, and writes the
// device-resident policy input buffer in the lease payload's world-major
// [world_count, feature_count] float layout. Ids pass through unchanged.
__global__ void learner_equivalent_consumer_kernel(const float *values, const std::uint64_t *ids,
                                                   std::size_t world_capacity,
                                                   std::size_t values_per_world,
                                                   LearnerNormalizationValues normalization,
                                                   float *policy_inputs, std::uint64_t *out_ids) {
    const std::size_t world = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (world >= world_capacity) return;
    const std::size_t base = world * values_per_world;
    for (std::size_t field = 0; field < values_per_world; ++field) {
        policy_inputs[base + field] =
            (values[base + field] - normalization.offsets[field]) * normalization.scales[field];
    }
    out_ids[world] = ids[world];
}

} // namespace

bool export_cuda_world_store_device_observation(const CudaWorldStoreDeviceAllocation *allocation,
                                                CudaWorldStoreDeviceObservationRaw *raw,
                                                std::string *error) {
    if (allocation == nullptr || raw == nullptr) {
        if (error != nullptr) *error = "CUDA device observation export requires an allocation";
        return false;
    }
    *raw = {};
    raw->world_count = allocation->world_capacity;
    raw->values_per_world = kObservationProjectionObservationFieldCount;
    if (allocation->world_capacity == 0) {
        if (error != nullptr) error->clear();
        return true;
    }
    const std::size_t value_count =
        allocation->world_capacity * kObservationProjectionObservationFieldCount;
    float *values = nullptr;
    std::uint64_t *ids = nullptr;
    cudaError_t status =
        cudaMalloc(reinterpret_cast<void **>(&values), value_count * sizeof(float));
    if (status == cudaSuccess) {
        status = cudaMalloc(reinterpret_cast<void **>(&ids),
                            allocation->world_capacity * sizeof(std::uint64_t));
    }
    if (status != cudaSuccess) {
        if (values != nullptr) cudaFree(values);
        if (ids != nullptr) cudaFree(ids);
        if (error != nullptr)
            *error = cuda_error_message("allocate device observation view", status);
        return false;
    }
    constexpr unsigned int threads = 128;
    const unsigned int blocks =
        static_cast<unsigned int>((allocation->world_capacity + threads - 1) / threads);
    const std::uint8_t *slot = allocation->state_slots[allocation->active_state_slot];
    pack_device_observation_kernel<<<blocks, threads>>>(
        allocation->world_capacity,
        device_field<double>(slot, allocation->state_layout.projected_observations),
        device_field<std::uint64_t>(slot, allocation->state_layout.projected_observation_ids),
        values, ids);
    status = cudaGetLastError();
    if (status == cudaSuccess) status = cudaDeviceSynchronize();
    std::vector<std::uint64_t> versions(allocation->world_capacity, 0);
    if (status == cudaSuccess) {
        status =
            cudaMemcpy(versions.data(),
                       device_field<std::uint64_t>(slot, allocation->state_layout.global_versions),
                       versions.size() * sizeof(std::uint64_t), cudaMemcpyDeviceToHost);
    }
    if (status != cudaSuccess || versions.empty() ||
        std::any_of(versions.begin(), versions.end(),
                    [&](std::uint64_t value) { return value != versions.front(); })) {
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

namespace {

void set_lease_failure(device_consumer::FailureCode *failure,
                       device_consumer::FailureCode value) noexcept {
    if (failure != nullptr) *failure = value;
}

void release_async_device_buffers(void *values, void *ids, cudaEvent_t ready_event,
                                  int device_ordinal, bool synchronize_stream) noexcept {
    int previous_device = -1;
    (void)cudaGetDevice(&previous_device);
    if (device_ordinal >= 0 && previous_device != device_ordinal) {
        (void)cudaSetDevice(device_ordinal);
    }
    if (synchronize_stream) {
        (void)cudaDeviceSynchronize();
    } else if (ready_event != nullptr) {
        (void)cudaEventSynchronize(ready_event);
    }
    if (ready_event != nullptr) (void)cudaEventDestroy(ready_event);
    if (values != nullptr) (void)cudaFree(values);
    if (ids != nullptr) (void)cudaFree(ids);
    if (device_ordinal >= 0 && previous_device >= 0 && previous_device != device_ordinal) {
        (void)cudaSetDevice(previous_device);
    }
}

} // namespace

bool acquire_cuda_world_store_device_observation_lease(
    const CudaWorldStoreDeviceAllocation *allocation, const device_consumer::LeaseEpoch &epoch,
    CudaWorldStoreDeviceObservationLeaseRaw *raw, CudaWorldStoreDeviceFaultInjection *faults,
    device_consumer::FailureCode *failure, std::string *error) {
    if (raw == nullptr || allocation == nullptr || !epoch.valid() ||
        allocation->world_capacity == 0) {
        set_lease_failure(failure, device_consumer::FailureCode::invalid_request);
        if (error != nullptr) *error = "CUDA observation lease requires a non-empty allocation";
        return false;
    }
    *raw = {};
    set_lease_failure(failure, device_consumer::FailureCode::none);
    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_device_lease_allocation)) {
        set_lease_failure(failure, device_consumer::FailureCode::lease_allocation_failed);
        if (error != nullptr) *error = "injected CUDA observation lease allocation failure";
        return false;
    }

    int device_ordinal = -1;
    cudaError_t status = cudaGetDevice(&device_ordinal);
    float *values = nullptr;
    std::uint64_t *ids = nullptr;
    cudaEvent_t ready_event = nullptr;
    const std::size_t value_count =
        allocation->world_capacity * kObservationProjectionObservationFieldCount;
    if (status == cudaSuccess) {
        status = cudaMalloc(reinterpret_cast<void **>(&values), value_count * sizeof(float));
    }
    if (status == cudaSuccess) {
        status = cudaMalloc(reinterpret_cast<void **>(&ids),
                            allocation->world_capacity * sizeof(std::uint64_t));
    }
    if (status == cudaSuccess) {
        status = cudaEventCreateWithFlags(&ready_event, cudaEventDisableTiming);
    }
    if (status != cudaSuccess) {
        release_async_device_buffers(values, ids, ready_event, device_ordinal, true);
        set_lease_failure(failure, device_consumer::FailureCode::lease_allocation_failed);
        if (error != nullptr) *error = cuda_error_message("allocate observation lease", status);
        return false;
    }

    constexpr unsigned int threads = 128;
    const unsigned int blocks =
        static_cast<unsigned int>((allocation->world_capacity + threads - 1) / threads);
    const std::uint8_t *slot = allocation->state_slots[allocation->active_state_slot];
    pack_device_observation_kernel<<<blocks, threads>>>(
        allocation->world_capacity,
        device_field<double>(slot, allocation->state_layout.projected_observations),
        device_field<std::uint64_t>(slot, allocation->state_layout.projected_observation_ids),
        values, ids);
    status = cudaGetLastError();
    if (status != cudaSuccess) {
        release_async_device_buffers(values, ids, ready_event, device_ordinal, true);
        set_lease_failure(failure, device_consumer::FailureCode::lease_pack_failed);
        if (error != nullptr) *error = cuda_error_message("launch observation lease pack", status);
        return false;
    }
    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_device_lease_event_record)) {
        release_async_device_buffers(values, ids, ready_event, device_ordinal, true);
        set_lease_failure(failure, device_consumer::FailureCode::lease_event_record_failed);
        if (error != nullptr) *error = "injected CUDA observation lease event-record failure";
        return false;
    }
    status = cudaEventRecord(ready_event, nullptr);
    if (status != cudaSuccess) {
        release_async_device_buffers(values, ids, ready_event, device_ordinal, true);
        set_lease_failure(failure, device_consumer::FailureCode::lease_event_record_failed);
        if (error != nullptr) *error = cuda_error_message("record observation lease event", status);
        return false;
    }
    raw->values = values;
    raw->ids = ids;
    raw->ready_event = reinterpret_cast<void *>(ready_event);
    raw->world_count = allocation->world_capacity;
    raw->values_per_world = kObservationProjectionObservationFieldCount;
    raw->device_ordinal = device_ordinal;
    raw->producer_stream = 0;
    raw->epoch = epoch;
    if (error != nullptr) error->clear();
    return true;
}

void release_cuda_world_store_device_observation_lease(void *values, void *ids, void *ready_event,
                                                       int device_ordinal) noexcept {
    release_async_device_buffers(values, ids, reinterpret_cast<cudaEvent_t>(ready_event),
                                 device_ordinal, false);
}

bool submit_cuda_world_store_device_observation_consumer(
    const CudaWorldStoreDeviceObservationLeaseRaw &lease, CudaWorldStoreDeviceConsumerRaw *raw,
    bool learner_equivalent, bool fail_allocation, bool fail_launch, bool fail_event_record,
    device_consumer::FailureCode *failure, std::string *error) {
    if (raw == nullptr || lease.values == nullptr || lease.ids == nullptr ||
        lease.ready_event == nullptr || lease.world_count == 0 || lease.values_per_world == 0 ||
        lease.device_ordinal < 0 || lease.producer_stream != 0) {
        set_lease_failure(failure, device_consumer::FailureCode::invalid_lease);
        if (error != nullptr) *error = "CUDA observation consumer requires a valid lease";
        return false;
    }
    if (learner_equivalent &&
        lease.values_per_world != learner_consumption::kLearnerConsumptionFeatureCount) {
        set_lease_failure(failure, device_consumer::FailureCode::incompatible_layout);
        if (error != nullptr) {
            *error = "learner-equivalent consumption requires the fifteen-field lease layout";
        }
        return false;
    }
    *raw = {};
    set_lease_failure(failure, device_consumer::FailureCode::none);
    // The smoke consumer proves the boundary with one value per world; the
    // learner-equivalent consumer writes the full policy-input tensor.
    const std::size_t values_per_world = learner_equivalent ? lease.values_per_world : 1;
    int current_device = -1;
    cudaError_t status = cudaGetDevice(&current_device);
    if (status == cudaSuccess && current_device != lease.device_ordinal) {
        set_lease_failure(failure, device_consumer::FailureCode::device_mismatch);
        if (error != nullptr) *error = "CUDA observation consumer device ordinal mismatch";
        return false;
    }
    if (status == cudaSuccess) {
        status = cudaStreamWaitEvent(nullptr, reinterpret_cast<cudaEvent_t>(lease.ready_event), 0);
    }
    float *values = nullptr;
    std::uint64_t *ids = nullptr;
    cudaEvent_t ready_event = nullptr;
    if (status == cudaSuccess && fail_allocation) {
        status = cudaErrorMemoryAllocation;
    }
    if (status == cudaSuccess) {
        status = cudaMalloc(reinterpret_cast<void **>(&values),
                            lease.world_count * values_per_world * sizeof(float));
    }
    if (status == cudaSuccess) {
        status =
            cudaMalloc(reinterpret_cast<void **>(&ids), lease.world_count * sizeof(std::uint64_t));
    }
    if (status == cudaSuccess)
        status = cudaEventCreateWithFlags(&ready_event, cudaEventDisableTiming);
    if (status != cudaSuccess) {
        release_async_device_buffers(values, ids, ready_event, lease.device_ordinal, true);
        set_lease_failure(failure, device_consumer::FailureCode::consumer_allocation_failed);
        if (error != nullptr)
            *error = cuda_error_message("allocate device consumer output", status);
        return false;
    }
    constexpr unsigned int threads = 128;
    const unsigned int blocks =
        static_cast<unsigned int>((lease.world_count + threads - 1) / threads);
    if (fail_launch) {
        release_async_device_buffers(values, ids, ready_event, lease.device_ordinal, true);
        set_lease_failure(failure, device_consumer::FailureCode::consumer_launch_failed);
        if (error != nullptr) *error = "injected CUDA device consumer launch failure";
        return false;
    }
    if (learner_equivalent) {
        learner_equivalent_consumer_kernel<<<blocks, threads>>>(
            static_cast<const float *>(lease.values), static_cast<const std::uint64_t *>(lease.ids),
            lease.world_count, lease.values_per_world, learner_normalization_values(), values, ids);
    } else {
        device_observation_consumer_smoke_kernel<<<blocks, threads>>>(
            static_cast<const float *>(lease.values), static_cast<const std::uint64_t *>(lease.ids),
            lease.world_count, lease.values_per_world, values, ids);
    }
    status = cudaGetLastError();
    if (status != cudaSuccess) {
        release_async_device_buffers(values, ids, ready_event, lease.device_ordinal, true);
        set_lease_failure(failure, device_consumer::FailureCode::consumer_launch_failed);
        if (error != nullptr) *error = cuda_error_message("launch device consumer", status);
        return false;
    }
    if (fail_event_record) {
        release_async_device_buffers(values, ids, ready_event, lease.device_ordinal, true);
        set_lease_failure(failure, device_consumer::FailureCode::consumer_event_record_failed);
        if (error != nullptr) *error = "injected CUDA device consumer event-record failure";
        return false;
    }
    status = cudaEventRecord(ready_event, nullptr);
    if (status != cudaSuccess) {
        release_async_device_buffers(values, ids, ready_event, lease.device_ordinal, true);
        set_lease_failure(failure, device_consumer::FailureCode::consumer_event_record_failed);
        if (error != nullptr) *error = cuda_error_message("record device consumer event", status);
        return false;
    }
    raw->values = values;
    raw->ids = ids;
    raw->ready_event = reinterpret_cast<void *>(ready_event);
    raw->device_ordinal = lease.device_ordinal;
    raw->world_count = lease.world_count;
    raw->values_per_world = values_per_world;
    if (error != nullptr) error->clear();
    return true;
}

bool await_cuda_world_store_device_observation_consumer(const CudaWorldStoreDeviceConsumerRaw &raw,
                                                        bool fail_wait, std::string *error) {
    if (raw.ready_event == nullptr || raw.world_count == 0) {
        if (error != nullptr) *error = "CUDA device consumer wait requires a valid receipt";
        return false;
    }
    if (fail_wait) {
        if (error != nullptr) *error = "injected CUDA device consumer wait failure";
        return false;
    }
    const cudaError_t status = cudaEventSynchronize(reinterpret_cast<cudaEvent_t>(raw.ready_event));
    if (status != cudaSuccess) {
        if (error != nullptr) *error = cuda_error_message("wait for device consumer", status);
        return false;
    }
    if (error != nullptr) error->clear();
    return true;
}

bool materialize_cuda_world_store_device_observation_consumer(
    const CudaWorldStoreDeviceConsumerRaw &raw, std::vector<float> *values,
    std::vector<std::uint64_t> *ids, bool fail_materialize, std::string *error) {
    if (raw.values == nullptr || raw.ids == nullptr || raw.world_count == 0 ||
        raw.values_per_world == 0 || values == nullptr || ids == nullptr) {
        if (error != nullptr) *error = "CUDA device consumer diagnostic requires a valid receipt";
        return false;
    }
    if (fail_materialize) {
        if (error != nullptr) *error = "injected CUDA device consumer diagnostic failure";
        return false;
    }
    values->assign(raw.world_count * raw.values_per_world, 0.0F);
    ids->assign(raw.world_count, 0);
    cudaError_t status =
        cudaMemcpy(values->data(), raw.values,
                   raw.world_count * raw.values_per_world * sizeof(float), cudaMemcpyDeviceToHost);
    if (status == cudaSuccess) {
        status = cudaMemcpy(ids->data(), raw.ids, raw.world_count * sizeof(std::uint64_t),
                            cudaMemcpyDeviceToHost);
    }
    if (status != cudaSuccess) {
        values->clear();
        ids->clear();
        if (error != nullptr) *error = cuda_error_message("materialize device consumer", status);
        return false;
    }
    if (error != nullptr) error->clear();
    return true;
}

void release_cuda_world_store_device_consumer(void *values, void *ids, void *ready_event,
                                              int device_ordinal) noexcept {
    release_async_device_buffers(values, ids, reinterpret_cast<cudaEvent_t>(ready_event),
                                 device_ordinal, false);
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
    cudaError_t status =
        cudaMalloc(reinterpret_cast<void **>(&device_first_values), world_count * sizeof(float));
    if (status == cudaSuccess) {
        status =
            cudaMalloc(reinterpret_cast<void **>(&device_ids), world_count * sizeof(std::uint64_t));
    }
    if (status == cudaSuccess) {
        constexpr unsigned int threads = 128;
        const unsigned int blocks =
            static_cast<unsigned int>((world_count + threads - 1) / threads);
        device_observation_consumer_smoke_kernel<<<blocks, threads>>>(
            static_cast<const float *>(values), static_cast<const std::uint64_t *>(ids),
            world_count, values_per_world, device_first_values, device_ids);
        status = cudaGetLastError();
    }
    if (status == cudaSuccess) status = cudaDeviceSynchronize();
    std::vector<float> next_values(world_count, 0.0F);
    std::vector<std::uint64_t> next_ids(world_count, 0);
    if (status == cudaSuccess) {
        status = cudaMemcpy(next_values.data(), device_first_values, world_count * sizeof(float),
                            cudaMemcpyDeviceToHost);
    }
    if (status == cudaSuccess) {
        status = cudaMemcpy(next_ids.data(), device_ids, world_count * sizeof(std::uint64_t),
                            cudaMemcpyDeviceToHost);
    }
    if (device_first_values != nullptr) cudaFree(device_first_values);
    if (device_ids != nullptr) cudaFree(device_ids);
    if (status != cudaSuccess) {
        if (error != nullptr)
            *error = cuda_error_message("consume device observation view", status);
        return false;
    }
    *first_values = std::move(next_values);
    *ids_out = std::move(next_ids);
    if (error != nullptr) error->clear();
    return true;
}

bool query_cuda_world_store_device_observation_pack_kernel_resources(
    CudaBarrierKernelResources *resources, std::string *error) {
    return query_cuda_kernel_resources(pack_device_observation_kernel,
                                       "pack_device_observation_kernel", resources, error);
}

bool query_cuda_world_store_device_observation_consumer_kernel_resources(
    CudaBarrierKernelResources *resources, std::string *error) {
    return query_cuda_kernel_resources(device_observation_consumer_smoke_kernel,
                                       "device_observation_consumer_smoke_kernel", resources,
                                       error);
}

bool query_cuda_world_store_learner_consumer_kernel_resources(CudaBarrierKernelResources *resources,
                                                              std::string *error) {
    return query_cuda_kernel_resources(learner_equivalent_consumer_kernel,
                                       "learner_equivalent_consumer_kernel", resources, error);
}

} // namespace runtime::cuda_resident::detail
