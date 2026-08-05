#pragma once

#include <charconv>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <string>
#include <string_view>
#include <system_error>
#include <vector>

#include "runtime/contracts/cuda_resident_fixed_air_fixture_contract.h"
#include "runtime/contracts/parity_budget_contracts.h"
#include "runtime/contracts/world_batch_contracts.h"

namespace runtime::cuda_resident::replay {

inline constexpr std::string_view kCudaResidentReplayHarnessId = "cuda_resident.rb8.replay_shadow";
inline constexpr std::string_view kCudaResidentReplaySchemaV1 =
    "cuda_resident.replay_shadow_report.v1";
inline constexpr std::string_view kCudaResidentReplayProfileId =
    "resident_state.unmaintained_candidate";
inline constexpr std::string_view kCudaResidentReplayBudgetRef =
    parity::kParityBudgetResidentStateUnmaintainedCandidateV1;
inline constexpr std::string_view kCudaResidentReplayShadowProfileId =
    "shadow_compare.unmaintained_candidate";
inline constexpr std::string_view kCudaResidentReplayShadowBudgetRef =
    parity::kParityBudgetShadowCompareUnmaintainedCandidateV1;

enum class ReplayLaneKind : std::uint8_t {
    cpu_reference,
    cuda_resident,
};

enum class ReplayRunStatus : std::uint8_t {
    passed,
    quarantined,
    rejected,
};

struct ReplayActionWindow {
    std::vector<PilotAction> actions;
    std::string request_id;
};

// A trace owns all input values. Neither lane may retain a pointer into this
// object after its runner returns; runners are expected to construct their own
// backend-local requests from these values.
struct ReplayTrace {
    std::string run_id;
    std::string backend_profile_id = std::string(kCudaResidentReplayProfileId);
    std::string parity_budget_ref = std::string(kCudaResidentReplayBudgetRef);
    std::vector<std::uint32_t> seeds;
    std::vector<WorldSpawnRequest> spawns;
    std::vector<double> time_steps;
    std::vector<ReplayActionWindow> windows;
};

struct ReplayFieldValue {
    std::size_t world_index = 0;
    std::string field_family;
    std::string field_path;
    parity::ParityBudgetValueKind value_kind = parity::ParityBudgetValueKind::structured;
    bool available = false;
    bool numeric = false;
    double numeric_value = 0.0;
    std::string canonical_value;
};

struct ReplayLaneFrame {
    std::size_t window_index = 0;
    std::string barrier_id;
    std::uint64_t source_snapshot_version = 0;
    std::vector<ReplayFieldValue> fields;
};

struct ReplayLaneResult {
    ReplayLaneKind lane = ReplayLaneKind::cpu_reference;
    std::string backend_id;
    std::string trace_signature;
    bool completed = false;
    std::string failure_code;
    std::vector<ReplayLaneFrame> frames;
};

struct ReplayMismatch {
    std::size_t window_index = 0;
    std::size_t world_index = 0;
    std::string barrier_id;
    std::string field_family;
    std::string field_path;
    std::string mismatch_code;
    std::string expected;
    std::string actual;
};

struct ReplayCoverage {
    std::size_t expected_selected_field_count = 0;
    std::size_t consumed_selected_field_count = 0;
    std::size_t expected_field_instances = 0;
    std::size_t expected_field_family_count = 0;
    std::size_t expected_barrier_count = 0;
    std::size_t selected_field_instances = 0;
    std::size_t available_field_instances = 0;
    std::size_t matched_field_instances = 0;
    std::size_t mismatched_field_instances = 0;
    std::size_t unavailable_field_instances = 0;
    std::vector<std::string> consumed_field_families;
    std::vector<std::string> consumed_barriers;
};

struct ReplayComparisonReport {
    std::string schema_version = std::string(kCudaResidentReplaySchemaV1);
    std::string harness_id = std::string(kCudaResidentReplayHarnessId);
    std::string run_id;
    std::string trace_signature;
    std::string backend_profile_id;
    std::string parity_budget_ref;
    int parity_budget_version = 0;
    std::string shadow_profile_id = std::string(kCudaResidentReplayShadowProfileId);
    std::string shadow_parity_budget_ref = std::string(kCudaResidentReplayShadowBudgetRef);
    ReplayRunStatus status = ReplayRunStatus::rejected;
    std::string rejection_reason;
    std::string comparison_reference;
    std::string shadow_run_id;
    std::string compared_profile_id;
    std::string sync_barrier_id;
    std::string mismatch_domain;
    std::string mismatch_summary;
    std::vector<std::uint64_t> reference_source_snapshot_versions;
    std::vector<std::uint64_t> shadow_source_snapshot_versions;
    ReplayCoverage coverage{};
    std::vector<ReplayMismatch> mismatches;
    bool complete_selected_slice = false;
    bool deterministic = false;
    bool quarantined = true;
    bool candidate_promotion_blocked = true;
    bool maintained_claim_allowed = false;
    std::string stable_signature;

    [[nodiscard]] const ReplayMismatch *first_divergence() const noexcept {
        return mismatches.empty() ? nullptr : &mismatches.front();
    }
};

[[nodiscard]] inline std::string replay_canonical_double(double value) {
    if (std::isnan(value)) return "nan";
    if (std::isinf(value)) return value < 0.0 ? "-inf" : "inf";
    char buffer[64]{};
    const auto result =
        std::to_chars(buffer, buffer + sizeof(buffer), value, std::chars_format::general,
                      std::numeric_limits<double>::max_digits10);
    if (result.ec == std::errc{}) return std::string(buffer, result.ptr);
    return "<unrepresentable>";
}

[[nodiscard]] inline std::string replay_canonical_float(float value) {
    return replay_canonical_double(static_cast<double>(value));
}

[[nodiscard]] inline std::string replay_canonical_bool(bool value) {
    return value ? "true" : "false";
}

[[nodiscard]] inline std::string replay_lane_name(ReplayLaneKind lane) {
    return lane == ReplayLaneKind::cpu_reference ? "cpu_reference" : "cuda_resident";
}

} // namespace runtime::cuda_resident::replay
