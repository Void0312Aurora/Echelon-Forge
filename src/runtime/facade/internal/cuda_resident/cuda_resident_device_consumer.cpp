#include "runtime/facade/internal/cuda_resident/cuda_resident_device_consumer.h"

#include <atomic>
#include <limits>
#include <memory>
#include <string>
#include <utility>

#include "runtime/facade/internal/cuda_resident/cuda_world_store.h"

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
#include <cuda_runtime_api.h>

#include "runtime/facade/internal/cuda_resident/cuda_world_store_device_api.h"
#endif

namespace runtime::cuda_resident {
namespace {

struct CompletionState {
    std::atomic_bool completed = false;
};

device_consumer::SubmitResult submit_failure(device_consumer::FailureCode failure,
                                             std::string detail) {
    return {.failure = failure, .detail = std::move(detail)};
}

device_consumer::Status status_failure(device_consumer::FailureCode failure, std::string detail) {
    return {.failure = failure, .detail = std::move(detail)};
}

device_consumer::DiagnosticResult diagnostic_failure(device_consumer::FailureCode failure,
                                                     std::string detail) {
    return {.failure = failure, .detail = std::move(detail)};
}

bool layout_is_supported(const device_consumer::ObservationLease &lease) noexcept {
    const auto &observations = lease.observations;
    const auto &ids = lease.ids_tensor;
    if (observations.shape.size() != 2 || observations.strides.size() != 2 ||
        ids.shape.size() != 1 || ids.strides.size() != 1 || observations.dtype != "float32" ||
        ids.dtype != "uint64" || observations.stride_units != "elements" ||
        ids.stride_units != "elements" || observations.shape[0] == 0 ||
        observations.shape[1] == 0 || observations.shape[0] != ids.shape[0] ||
        observations.strides[1] != 1 || observations.strides[0] != observations.shape[1] ||
        ids.strides[0] != 1) {
        return false;
    }
    if (observations.shape[0] > std::numeric_limits<std::size_t>::max() ||
        observations.shape[1] > std::numeric_limits<std::size_t>::max()) {
        return false;
    }
    const auto worlds = static_cast<std::size_t>(observations.shape[0]);
    const auto values_per_world = static_cast<std::size_t>(observations.shape[1]);
    return values_per_world <= std::numeric_limits<std::size_t>::max() / worlds &&
           observations.element_count == worlds * values_per_world && ids.element_count == worlds;
}

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
bool current_device_matches(int expected, std::string *detail) {
    int current = -1;
    const cudaError_t status = cudaGetDevice(&current);
    if (status != cudaSuccess) {
        if (detail != nullptr) {
            *detail = std::string("query CUDA consumer device: ") + cudaGetErrorString(status);
        }
        return false;
    }
    if (current != expected) {
        if (detail != nullptr) *detail = "CUDA consumer receipt device ordinal mismatch";
        return false;
    }
    return true;
}

detail::CudaWorldStoreDeviceConsumerRaw
raw_receipt(const device_consumer::ConsumerReceipt &receipt) noexcept {
    return {
        .first_values = const_cast<float *>(receipt.first_values),
        .ids = const_cast<std::uint64_t *>(receipt.ids),
        .ready_event = receipt.ready_event,
        .device_ordinal = receipt.device_ordinal,
        .world_count = receipt.world_count,
    };
}
#endif

} // namespace

device_consumer::SubmitResult
CudaResidentDeviceConsumer::submit(const device_consumer::ObservationLease &lease,
                                   const device_consumer::ConsumerRequest &request) {
    if (request.request_id.empty() || !request.expected_epoch.valid()) {
        return submit_failure(device_consumer::FailureCode::invalid_request,
                              "CUDA device consumer requires request_id and expected epoch");
    }
    if (!lease.valid()) {
        return submit_failure(device_consumer::FailureCode::invalid_lease,
                              "CUDA device consumer requires a valid observation lease");
    }
    if (request.expected_epoch != lease.epoch) {
        return submit_failure(device_consumer::FailureCode::stale_epoch,
                              "CUDA device consumer expected epoch does not match lease");
    }
    if (lease.producer_stream != 0) {
        return submit_failure(device_consumer::FailureCode::stream_mismatch,
                              "CUDA device consumer supports the declared default stream only");
    }
    if (!layout_is_supported(lease)) {
        return submit_failure(device_consumer::FailureCode::incompatible_layout,
                              "CUDA device consumer observation layout is incompatible");
    }
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    CudaWorldStoreDeviceObservationLeaseRaw raw_lease{
        .values = const_cast<float *>(lease.values),
        .ids = const_cast<std::uint64_t *>(lease.ids),
        .ready_event = lease.ready_event,
        .world_count = static_cast<std::size_t>(lease.observations.shape[0]),
        .values_per_world = static_cast<std::size_t>(lease.observations.shape[1]),
        .device_ordinal = lease.device_ordinal,
        .producer_stream = lease.producer_stream,
        .epoch = lease.epoch,
    };
    detail::CudaWorldStoreDeviceConsumerRaw raw{};
    device_consumer::FailureCode failure = device_consumer::FailureCode::none;
    std::string error;
    const bool fail_allocation = std::exchange(faults_.fail_next_allocation, false);
    const bool fail_launch = std::exchange(faults_.fail_next_launch, false);
    const bool fail_event_record = std::exchange(faults_.fail_next_event_record, false);
    if (!detail::submit_cuda_world_store_device_observation_consumer(
            raw_lease, &raw, fail_allocation, fail_launch, fail_event_record, &failure, &error)) {
        return submit_failure(failure, std::move(error));
    }

    device_consumer::SubmitResult result{};
    auto &receipt = result.receipt;
    receipt.lifetime = std::shared_ptr<void>(
        raw.first_values, [ids = raw.ids, event = raw.ready_event, device = raw.device_ordinal,
                           input_lifetime = lease.lifetime](void *first_values) {
            detail::release_cuda_world_store_device_consumer(first_values, ids, event, device);
            (void)input_lifetime;
        });
    receipt.completion_state = std::make_shared<CompletionState>();
    receipt.first_values = static_cast<const float *>(raw.first_values);
    receipt.ids = static_cast<const std::uint64_t *>(raw.ids);
    receipt.ready_event = raw.ready_event;
    receipt.device_ordinal = raw.device_ordinal;
    receipt.producer_stream = 0;
    receipt.world_count = raw.world_count;
    receipt.source_epoch = lease.epoch;
    receipt.request_id = request.request_id;
    return result;
#else
    (void)lease;
    return submit_failure(device_consumer::FailureCode::cuda_unavailable,
                          "CUDA device consumer requires EF_ENABLE_CUDA_EXPERIMENTS");
#endif
}

device_consumer::Status
CudaResidentDeviceConsumer::await(const device_consumer::ConsumerReceipt &receipt) {
    if (!receipt.valid()) {
        return status_failure(device_consumer::FailureCode::invalid_receipt,
                              "CUDA device consumer wait requires a valid receipt");
    }
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    std::string error;
    if (!current_device_matches(receipt.device_ordinal, &error)) {
        return status_failure(device_consumer::FailureCode::device_mismatch, std::move(error));
    }
    const bool fail_wait = std::exchange(faults_.fail_next_wait, false);
    if (!detail::await_cuda_world_store_device_observation_consumer(raw_receipt(receipt), fail_wait,
                                                                    &error)) {
        return status_failure(device_consumer::FailureCode::wait_failed, std::move(error));
    }
    std::static_pointer_cast<CompletionState>(receipt.completion_state)
        ->completed.store(true, std::memory_order_release);
    return {};
#else
    return status_failure(device_consumer::FailureCode::cuda_unavailable,
                          "CUDA device consumer wait requires EF_ENABLE_CUDA_EXPERIMENTS");
#endif
}

device_consumer::DiagnosticResult CudaResidentDeviceConsumer::materialize_for_diagnostics(
    const device_consumer::ConsumerReceipt &receipt) {
    if (!receipt.valid()) {
        return diagnostic_failure(device_consumer::FailureCode::invalid_receipt,
                                  "CUDA device consumer diagnostic requires a valid receipt");
    }
    if (!std::static_pointer_cast<CompletionState>(receipt.completion_state)
             ->completed.load(std::memory_order_acquire)) {
        return diagnostic_failure(device_consumer::FailureCode::wait_required,
                                  "CUDA device consumer diagnostic requires explicit await");
    }
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    std::string error;
    if (!current_device_matches(receipt.device_ordinal, &error)) {
        return diagnostic_failure(device_consumer::FailureCode::device_mismatch, std::move(error));
    }
    device_consumer::DiagnosticResult result{};
    const bool fail_materialize = std::exchange(faults_.fail_next_materialize, false);
    if (!detail::materialize_cuda_world_store_device_observation_consumer(
            raw_receipt(receipt), &result.materialized.first_values, &result.materialized.ids,
            fail_materialize, &error)) {
        return diagnostic_failure(device_consumer::FailureCode::diagnostic_failed,
                                  std::move(error));
    }
    return result;
#else
    return diagnostic_failure(
        device_consumer::FailureCode::cuda_unavailable,
        "CUDA device consumer diagnostic requires EF_ENABLE_CUDA_EXPERIMENTS");
#endif
}

void testing::CudaResidentDeviceConsumerTestAccess::fail_next_allocation(
    CudaResidentDeviceConsumer &consumer) noexcept {
    consumer.faults_.fail_next_allocation = true;
}

void testing::CudaResidentDeviceConsumerTestAccess::fail_next_launch(
    CudaResidentDeviceConsumer &consumer) noexcept {
    consumer.faults_.fail_next_launch = true;
}

void testing::CudaResidentDeviceConsumerTestAccess::fail_next_event_record(
    CudaResidentDeviceConsumer &consumer) noexcept {
    consumer.faults_.fail_next_event_record = true;
}

void testing::CudaResidentDeviceConsumerTestAccess::fail_next_wait(
    CudaResidentDeviceConsumer &consumer) noexcept {
    consumer.faults_.fail_next_wait = true;
}

void testing::CudaResidentDeviceConsumerTestAccess::fail_next_materialize(
    CudaResidentDeviceConsumer &consumer) noexcept {
    consumer.faults_.fail_next_materialize = true;
}

} // namespace runtime::cuda_resident
