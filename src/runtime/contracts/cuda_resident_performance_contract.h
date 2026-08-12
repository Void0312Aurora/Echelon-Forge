#pragma once

#include <cstddef>
#include <cstdint>
#include <string_view>

namespace runtime::cuda_resident::performance {

inline constexpr std::string_view kCudaResidentPerformanceHarnessId =
    "cuda_resident.rb9.performance_evidence";
inline constexpr std::string_view kCudaResidentPerformanceSchemaV1 =
    "cuda_resident.performance_evidence.v1";
inline constexpr std::string_view kCudaResidentPerformanceProfileId =
    "resident_state.unmaintained_candidate";
inline constexpr std::string_view kCudaResidentPerformanceBudgetRef =
    "parity_budget.resident_state.unmaintained_candidate.v1";
inline constexpr std::string_view kCudaResidentPerformanceInvocationSurface =
    "backend_private_phase_sequence";
inline constexpr std::string_view kCudaResidentPerformanceUnavailableCountersReason =
    "ERR_NVGPUCTRPERM";

// --- CP-7a: frozen small-batch selection rule (gate G-F disposition) --------
//
// CR2-6b measured the resident lane losing to the CPU reference at world 1 by
// 7-36x and recorded a routing ADVISORY. The CP-5 post-fusion campaigns and
// the world-1 timeline attribution turned the advisory's cause into
// measurement: the fused window body is ~65.5 us of single-thread serial-chain
// device time at world 1 while the CPU lane finishes the whole step in
// ~18-31 us, so no host-side skeleton fix can close world 1. This rule
// freezes that disposition so the world-1 regression is explicit policy
// rather than a silent measurement footnote.
//
// The rule is documentation-grade policy, not a runtime selector: the
// maintained default remains the Flecs CPU reference for every world count,
// and no runtime translation unit may consume these constants (an
// architecture gate enforces that). The exact resident-lane crossover between
// world counts 1 and 4 is unmeasured -- the frozen matrix has no world-2/3
// row -- so the advisory minimum is the smallest measured-winning count and
// its value is a named CP-8 re-matrix review item.
inline constexpr std::string_view kSmallBatchSelectionRuleId =
    "cp7.small_batch_selection_rule.v1";
inline constexpr std::size_t kResidentLaneAdvisoryMinimumWorldCount = 4;
inline constexpr bool kWorldCountsBelowMinimumRouteToCpuReference = true;
inline constexpr bool kMaintainedDefaultRemainsCpuReference = true;
inline constexpr std::string_view kSmallBatchCrossoverReviewOwner = "cp8.rematrix";

static_assert(kResidentLaneAdvisoryMinimumWorldCount > 1,
              "the rule exists to route sub-minimum world counts to the CPU reference");
static_assert(kWorldCountsBelowMinimumRouteToCpuReference &&
                  kMaintainedDefaultRemainsCpuReference,
              "freezing the rule must not weaken the maintained CPU default");

// These constants describe the fixed-air device layout and the operations in
// the split cuda_world_store_cuda_* translation units. They are a diagnostic
// ledger, not a claim that the candidate is a full RuntimeFacade backend. The
// architecture test keeps this ledger synchronized with the declared phase
// sequence.
inline constexpr std::size_t kFlightControlH2dBytesPerWorld = 55;
inline constexpr std::size_t kLifecycleRecordBytesPerWorld = 16;
inline constexpr std::size_t kObservationFieldsPerWorld = 15;

struct WindowTransferLedger {
    std::size_t h2d_copy_count = 0;
    std::size_t h2d_bytes = 0;
    std::size_t d2h_copy_count = 0;
    std::size_t d2h_bytes = 0;
    std::size_t d2d_copy_count = 0;
    std::size_t d2d_bytes = 0;
    std::size_t kernel_launch_count = 0;
    std::size_t synchronization_count = 0;
    std::size_t device_observation_pack_bytes = 0;
    std::size_t device_observation_consumer_bytes = 0;
    std::size_t device_observation_view_bytes = 0;
    std::size_t device_consumer_measured_path_d2h_copy_count = 0;
    std::size_t device_consumer_diagnostic_d2h_copy_count = 0;
    std::size_t device_consumer_event_wait_count = 0;
    bool host_snapshot_includes_full_state_d2h = false;
    bool device_consumer_includes_host_validation_d2h = false;
    bool device_consumer_allocation_may_synchronize = false;
    bool device_consumer_release_outside_measured_path = false;
};

[[nodiscard]] inline WindowTransferLedger modeled_window_ledger(std::size_t world_count,
                                                                std::size_t state_slot_bytes,
                                                                bool host_snapshot,
                                                                bool device_consumer) noexcept {
    // CP-5 fused the six window-commit launches into one; CP-7b folded the
    // stage_publish and window_commit barriers into their stage kernels. The
    // base window is three launches (input-injection barrier, control
    // preparation, fused window body), each with one synchronization and one
    // four-byte status readback. The staging copies are unchanged.
    WindowTransferLedger ledger{
        .h2d_copy_count = 3,
        .h2d_bytes = world_count * kFlightControlH2dBytesPerWorld,
        .d2h_copy_count = 3,
        .d2h_bytes = 3 * sizeof(std::uint32_t),
        .d2d_copy_count = 3,
        .d2d_bytes = 3 * state_slot_bytes,
        .kernel_launch_count = 3,
        .synchronization_count = 3,
    };
    const auto add_state_snapshot_readback = [&]() {
        // state_snapshot() reconstructs the host-visible state and also reads
        // the lifecycle metadata. Both copies are synchronous D2H operations.
        ledger.d2h_copy_count += 2;
        ledger.d2h_bytes += state_slot_bytes + world_count * kLifecycleRecordBytesPerWorld;
    };
    if (host_snapshot) {
        add_state_snapshot_readback();
        ledger.host_snapshot_includes_full_state_d2h = true;
    }
    if (device_consumer) {
        const std::size_t observation_values =
            world_count * kObservationFieldsPerWorld * sizeof(float);
        const std::size_t observation_ids = world_count * sizeof(std::uint64_t);
        const std::size_t consumer_values = world_count * sizeof(float);
        const std::size_t consumer_ids = world_count * sizeof(std::uint64_t);
        ledger.kernel_launch_count += 2;   // pack + consumer smoke
        ledger.synchronization_count += 1; // explicit receipt event wait
        ledger.device_consumer_event_wait_count = 1;
        ledger.device_consumer_measured_path_d2h_copy_count = 0;
        ledger.device_consumer_diagnostic_d2h_copy_count = 2;
        ledger.d2h_copy_count += 0; // diagnostics are explicitly outside the measured path
        ledger.d2h_bytes += 0;
        ledger.device_observation_pack_bytes = observation_values + observation_ids;
        ledger.device_observation_consumer_bytes = consumer_values + consumer_ids;
        ledger.device_observation_view_bytes = ledger.device_observation_pack_bytes;
        ledger.device_consumer_allocation_may_synchronize = true;
        ledger.device_consumer_release_outside_measured_path = true;
    }
    return ledger;
}

} // namespace runtime::cuda_resident::performance
