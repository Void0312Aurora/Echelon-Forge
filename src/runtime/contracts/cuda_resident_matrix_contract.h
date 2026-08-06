#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

#include "runtime/contracts/cuda_resident_full_window_contract.h"
#include "runtime/contracts/cuda_resident_parity_release_contract.h"
#include "runtime/contracts/cuda_resident_resource_evidence_contract.h"

namespace runtime::cuda_resident::matrix {

inline constexpr std::string_view kProbeSchema = "cuda_resident.cr2.production_matrix_probe.v1";
inline constexpr std::string_view kProfileId = "cr2.production_matrix.fixed_air.v1";
inline constexpr std::string_view kInvocationSurface = "cuda_resident.cr2.matrix_backend_spi.v1";
inline constexpr std::string_view kFullWindowSurfaceRef = full_window::kSurfaceId;
inline constexpr std::string_view kTraceSignatureAlgorithm = "fnv1a64";
inline constexpr std::string_view kSelectedPayloadSchemaRef = parity_release::kSchemaV1;
inline constexpr std::string_view kSelectedPayloadPolicyRef = parity_release::kPolicyId;
inline constexpr std::string_view kSelectedPayloadPolicyTraceProfileRef =
    parity_release::kTraceProfileId;
inline constexpr std::string_view kSelectedPayloadReferenceScope =
    "field_projection_for_same_lane_reset_only";
inline constexpr bool kSelectedPayloadMatrixProfileReleased = false;
inline constexpr std::uint64_t kFnv1a64OffsetBasis = 14695981039346656037ULL;
inline constexpr std::uint64_t kFnv1a64Prime = 1099511628211ULL;

constexpr std::uint64_t fnv1a64(std::string_view value) noexcept {
    std::uint64_t digest = kFnv1a64OffsetBasis;
    for (const char raw_byte : value) {
        digest ^= static_cast<unsigned char>(raw_byte);
        digest *= kFnv1a64Prime;
    }
    return digest;
}

static_assert(fnv1a64("") == 0xcbf29ce484222325ULL);
static_assert(fnv1a64("a") == 0xaf63dc4c8601ec8cULL);
static_assert(fnv1a64("foobar") == 0x85944171f73967e8ULL);
static_assert(parity_release::kReleasedNumericFields.size() == 12);
static_assert(kSelectedPayloadPolicyTraceProfileRef != kProfileId);

inline constexpr std::array<std::size_t, 5> kWorldCounts{{1, 4, 16, 64, 256}};

struct ModeSpec {
    std::string_view id;
    bool host_export;
    bool device_consumer;
    bool cpu_available;
};

inline constexpr std::array<ModeSpec, 4> kModes{{
    {"no_export_no_device", false, false, true},
    {"host_export_no_device", true, false, true},
    {"no_export_device_consumer", false, true, false},
    {"host_export_device_consumer", true, true, false},
}};

struct Protocol {
    std::size_t cold_samples;
    std::size_t warmup_windows;
    std::size_t measured_windows;
    std::size_t rollout_samples;
    std::size_t rollout_windows;
};

inline constexpr Protocol kProductionProtocol{
    .cold_samples = 10,
    .warmup_windows = 32,
    .measured_windows = 100,
    .rollout_samples = 10,
    .rollout_windows = 64,
};

inline constexpr std::size_t kCpuHostWorkerRequest = 0;
inline constexpr std::string_view kCpuHostWorkerPolicy =
    "hardware_concurrency_capped_by_world_count";
inline constexpr std::size_t kCudaHostWorkerRequest = 1;
inline constexpr std::string_view kCudaHostWorkerPolicy = "single_host_orchestrator";
inline constexpr std::size_t kCudaThreadsPerBlock = resource_evidence::kThreadsPerBlock;

consteval bool mode_ids_are_unique() {
    for (std::size_t left = 0; left < kModes.size(); ++left) {
        if (kModes[left].id.empty() || kModes[left].cpu_available == kModes[left].device_consumer) {
            return false;
        }
        for (std::size_t right = left + 1; right < kModes.size(); ++right) {
            if (kModes[left].id == kModes[right].id) return false;
        }
    }
    return true;
}

static_assert(mode_ids_are_unique());

inline constexpr bool kEvaluationRequestIsEmpty = true;
inline constexpr bool kDeviceConsumerValidationOutsideTimer = true;
inline constexpr bool kDeviceConsumerReleaseOutsideTimer = true;
inline constexpr bool kResetDigestExcludesAllocatorIdentity = true;
inline constexpr bool kFreshProcessColdAvailable = false;
inline constexpr bool kMaintainedClaimAllowed = false;
inline constexpr bool kPublicSupportEnabled = false;
inline constexpr bool kPromotionAllowed = false;
inline constexpr bool kTuningAuthorized = false;

} // namespace runtime::cuda_resident::matrix
