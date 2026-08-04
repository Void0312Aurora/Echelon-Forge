#pragma once

#include <array>
#include <cstddef>
#include <string_view>

namespace runtime::cuda_resident::counter_evidence {

inline constexpr std::string_view kSchemaVersion =
    "cuda_resident.cr2.achieved_counter_evidence.v1";
inline constexpr std::string_view kProfileId =
    "cr2.resource.steady_full_window_body.sm86.v1";
inline constexpr std::string_view kPermissionBlockerCode = "ERR_NVGPUCTRPERM";
inline constexpr std::size_t kRequiredLaunchCount = 12;

struct CounterFamilySpec {
    std::string_view id;
    std::string_view unit;
};

inline constexpr std::array<CounterFamilySpec, 5> kCounterFamilies{{
    {"achieved_occupancy", "ratio"},
    {"branch_divergence", "ratio"},
    {"global_memory_traffic", "bytes"},
    {"local_memory_traffic", "bytes"},
    {"shared_memory_traffic", "bytes"},
}};

inline constexpr std::array<std::string_view, 3> kAttemptStates{{
    "available",
    "external_blocked",
    "collection_failed",
}};

consteval bool counter_family_ids_are_unique() {
    for (std::size_t left = 0; left < kCounterFamilies.size(); ++left) {
        if (kCounterFamilies[left].id.empty() || kCounterFamilies[left].unit.empty()) {
            return false;
        }
        for (std::size_t right = left + 1; right < kCounterFamilies.size(); ++right) {
            if (kCounterFamilies[left].id == kCounterFamilies[right].id) {
                return false;
            }
        }
    }
    return true;
}

static_assert(counter_family_ids_are_unique());

inline constexpr bool kTheoreticalOccupancyMaySubstituteAchieved = false;
inline constexpr bool kMissingCounterMayDefaultToZero = false;
inline constexpr bool kMaintainedClaimAllowed = false;
inline constexpr bool kPublicSupportEnabled = false;
inline constexpr bool kPromotionAllowed = false;
inline constexpr bool kTuningAuthorized = false;

} // namespace runtime::cuda_resident::counter_evidence
