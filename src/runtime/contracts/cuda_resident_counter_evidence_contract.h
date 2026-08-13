#pragma once

#include <array>
#include <cstddef>
#include <string_view>

#include "runtime/contracts/cuda_resident_resource_evidence_contract.h"

namespace runtime::cuda_resident::counter_evidence {

inline constexpr std::string_view kSchemaVersion = "cuda_resident.cr2.achieved_counter_evidence.v1";
inline constexpr std::string_view kProfileId = "cr2.resource.steady_full_window_body.sm86.v1";
inline constexpr std::string_view kPermissionBlockerCode = "ERR_NVGPUCTRPERM";

// A counter capture must profile every launch of the window graph of the
// resource-evidence generation it binds to. The counts are therefore derived
// from the launch sequences the resource contract owns, never declared as an
// independent constant: a new execution-graph generation extends the counter
// chain by extending the resource contract, not by editing this header.
inline constexpr std::size_t kRequiredLaunchCountV1 = resource_evidence::kLaunchSequence.size();
inline constexpr std::size_t kRequiredLaunchCountV2 = resource_evidence::kLaunchSequenceV2.size();
inline constexpr std::size_t kRequiredLaunchCountV3 = resource_evidence::kLaunchSequenceV3.size();
inline constexpr std::size_t kRequiredLaunchCountV4 = resource_evidence::kLaunchSequenceV4.size();

// Frozen artifact pins: the retained v1 blocked attempt and the v2 achieved
// capture both recorded 12; the CP-5 fused window graph launches 7; the CP-7b
// barrier fold launches 5. These assert the derivation still matches the
// evidence already on disk.
static_assert(kRequiredLaunchCountV1 == 12);
static_assert(kRequiredLaunchCountV2 == 12);
static_assert(kRequiredLaunchCountV3 == 7);
static_assert(kRequiredLaunchCountV4 == 5);

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
