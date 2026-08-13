#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <string_view>
#include <vector>

namespace runtime::cuda_resident::device_consumer {

inline constexpr std::string_view kCudaResidentDeviceLeaseSchemaV1 =
    "cuda_resident.device_observation_lease.v1";
inline constexpr std::string_view kCudaResidentDeviceConsumerSurfaceV1 =
    "cuda_resident.device_consumer_smoke.v1";
inline constexpr std::string_view kCudaResidentDeviceLeaseOwnership = "owned_d2d_snapshot_copy";
inline constexpr std::string_view kCudaResidentDeviceLeaseStream = "legacy_default_stream";
inline constexpr bool kDeviceConsumerMeasuredPathIncludesHostValidationReadback = false;
inline constexpr bool kDeviceConsumerDiagnosticReadbackIsOutsideMeasuredPath = true;
inline constexpr bool kSubmissionMaySynchronizeForDeviceAllocation = true;
inline constexpr bool kInFlightReleaseMaySynchronize = true;

enum class FailureCode : std::uint8_t {
    none,
    invalid_request,
    cuda_unavailable,
    no_committed_window,
    lease_allocation_failed,
    lease_pack_failed,
    lease_event_record_failed,
    invalid_lease,
    stale_epoch,
    device_mismatch,
    stream_mismatch,
    incompatible_layout,
    consumer_allocation_failed,
    consumer_launch_failed,
    consumer_event_record_failed,
    invalid_receipt,
    wait_required,
    wait_failed,
    diagnostic_failed,
};

[[nodiscard]] inline constexpr std::string_view failure_code_id(FailureCode code) noexcept {
    switch (code) {
    case FailureCode::none:
        return "none";
    case FailureCode::invalid_request:
        return "invalid_request";
    case FailureCode::cuda_unavailable:
        return "cuda_unavailable";
    case FailureCode::no_committed_window:
        return "no_committed_window";
    case FailureCode::lease_allocation_failed:
        return "lease_allocation_failed";
    case FailureCode::lease_pack_failed:
        return "lease_pack_failed";
    case FailureCode::lease_event_record_failed:
        return "lease_event_record_failed";
    case FailureCode::invalid_lease:
        return "invalid_lease";
    case FailureCode::stale_epoch:
        return "stale_epoch";
    case FailureCode::device_mismatch:
        return "device_mismatch";
    case FailureCode::stream_mismatch:
        return "stream_mismatch";
    case FailureCode::incompatible_layout:
        return "incompatible_layout";
    case FailureCode::consumer_allocation_failed:
        return "consumer_allocation_failed";
    case FailureCode::consumer_launch_failed:
        return "consumer_launch_failed";
    case FailureCode::consumer_event_record_failed:
        return "consumer_event_record_failed";
    case FailureCode::invalid_receipt:
        return "invalid_receipt";
    case FailureCode::wait_required:
        return "wait_required";
    case FailureCode::wait_failed:
        return "wait_failed";
    case FailureCode::diagnostic_failed:
        return "diagnostic_failed";
    }
    return "unknown";
}

struct LeaseEpoch {
    std::uint64_t allocation_generation = 0;
    std::uint64_t reset_generation = 0;
    std::uint64_t committed_window = 0;
    std::uint64_t source_snapshot = 0;

    [[nodiscard]] bool valid() const noexcept {
        return allocation_generation != 0 && reset_generation != 0 && committed_window != 0 &&
               source_snapshot != 0;
    }
    friend constexpr bool operator==(const LeaseEpoch &, const LeaseEpoch &) = default;
};

struct TensorDescriptor {
    std::vector<std::uint64_t> shape;
    std::vector<std::uint64_t> strides;
    std::string dtype;
    std::string stride_units = "elements";
    std::size_t element_count = 0;

    [[nodiscard]] bool valid() const noexcept {
        return !shape.empty() && shape.size() == strides.size() && !dtype.empty() &&
               stride_units == "elements" && element_count != 0;
    }
};

// This is a private backend seam. The lifetime owner contains the device
// buffers and ready event; the raw pointers are only usable while it is held.
struct ObservationLease {
    std::shared_ptr<void> lifetime;
    const float *values = nullptr;
    const std::uint64_t *ids = nullptr;
    void *ready_event = nullptr;
    int device_ordinal = -1;
    std::uintptr_t producer_stream = 0;
    LeaseEpoch epoch{};
    TensorDescriptor observations{};
    TensorDescriptor ids_tensor{};
    std::string source_request_id;

    [[nodiscard]] bool valid() const noexcept {
        return lifetime != nullptr && values != nullptr && ids != nullptr &&
               ready_event != nullptr && device_ordinal >= 0 && epoch.valid() &&
               observations.valid() && ids_tensor.valid();
    }
};

struct AcquireResult {
    ObservationLease lease{};
    FailureCode failure = FailureCode::none;
    std::string detail;

    [[nodiscard]] bool success() const noexcept {
        return failure == FailureCode::none && lease.valid();
    }
};

struct ConsumerRequest {
    std::string request_id;
    LeaseEpoch expected_epoch{};
    // False keeps the single-value smoke consumer; true submits the CP-6
    // learner-equivalent consumer, which reads every lease element and writes
    // the normalized policy-input tensor.
    bool learner_equivalent = false;
};

struct ConsumerReceipt {
    // The owner deliberately captures the input lease, so the input buffers
    // remain alive until the consumer event has completed and the receipt is
    // released.
    std::shared_ptr<void> lifetime;
    std::shared_ptr<void> completion_state;
    const float *values = nullptr;
    const std::uint64_t *ids = nullptr;
    void *ready_event = nullptr;
    int device_ordinal = -1;
    std::uintptr_t producer_stream = 0;
    std::size_t world_count = 0;
    // One for the smoke consumer, the packed field count for the
    // learner-equivalent consumer.
    std::size_t values_per_world = 0;
    // World-major [world_count, values_per_world] float32 output layout.
    TensorDescriptor outputs{};
    LeaseEpoch source_epoch{};
    std::string request_id;

    [[nodiscard]] bool valid() const noexcept {
        return lifetime != nullptr && completion_state != nullptr && values != nullptr &&
               ids != nullptr && ready_event != nullptr && device_ordinal >= 0 &&
               producer_stream == 0 && world_count != 0 && values_per_world != 0 &&
               outputs.valid() && source_epoch.valid();
    }
};

struct SubmitResult {
    ConsumerReceipt receipt{};
    FailureCode failure = FailureCode::none;
    std::string detail;

    [[nodiscard]] bool success() const noexcept {
        return failure == FailureCode::none && receipt.valid();
    }
};

struct Status {
    FailureCode failure = FailureCode::none;
    std::string detail;

    [[nodiscard]] bool success() const noexcept { return failure == FailureCode::none; }
};

struct DiagnosticMaterialization {
    std::vector<float> values;
    std::vector<std::uint64_t> ids;
    std::size_t values_per_world = 0;
};

struct DiagnosticResult {
    DiagnosticMaterialization materialized{};
    FailureCode failure = FailureCode::none;
    std::string detail;

    [[nodiscard]] bool success() const noexcept {
        return failure == FailureCode::none && !materialized.values.empty() &&
               materialized.values_per_world != 0 &&
               materialized.values.size() ==
                   materialized.ids.size() * materialized.values_per_world;
    }
};

} // namespace runtime::cuda_resident::device_consumer
