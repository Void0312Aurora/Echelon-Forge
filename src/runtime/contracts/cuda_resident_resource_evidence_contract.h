#pragma once

#include <array>
#include <cstddef>
#include <string_view>

namespace runtime::cuda_resident::resource_evidence {

// v1 describes the pre-semantic-rename binary of the first static capture. Its
// values are frozen historical record: the retained resource and counter
// evidence JSON hashes against them, so they must never be edited to match
// renamed sources. A fresh claim uses the v2 identifiers below.
inline constexpr std::string_view kSchemaV1 = "cuda_resident.cr2.kernel_resource_evidence.v1";
inline constexpr std::string_view kProbeSchemaV1 = "cuda_resident.cr2.resource_capture_probe.v1";
inline constexpr std::string_view kProfileId = "cr2.resource.steady_full_window_body.sm86.v1";

// v2 is the CP-4 recapture against the semantic kernel catalog. The captured
// execution graph is unchanged -- ten kernels, twelve launches, identical grid,
// block, and world count -- so v2 evidence stays directly comparable to the
// frozen v1 capture. Only the kernel symbol names differ.
inline constexpr std::string_view kSchemaV2 = "cuda_resident.cp.kernel_resource_evidence.v2";
inline constexpr std::string_view kProbeSchemaV2 = "cuda_resident.cp.resource_capture_probe.v2";
inline constexpr std::string_view kProfileIdV2 = "cp.resource.steady_full_window_body.sm86.v2";
inline constexpr std::string_view kProbeSchemaV2Predecessor = kProbeSchemaV1;

inline constexpr std::string_view kCaptureRange = "cudaProfilerApi";
inline constexpr std::string_view kBuildConfig = "Release";
inline constexpr std::string_view kCudaArchitecture = "sm_86";
inline constexpr std::string_view kTraceSignatureAlgorithm = "fnv1a64";

// The replay trace signature is built from run_id, seeds, spawns, time steps,
// and pilot actions only (see CudaResidentReplayHarness::trace_signature); no
// kernel or stage identifier participates. The rename therefore cannot move it,
// and v2 deliberately reuses the v1 digest as a cross-version equivalence check
// that the captured workload is the one the frozen v1 capture measured.
inline constexpr std::string_view kTraceSignatureDigest = "cb31675ee34e5015";
inline constexpr std::size_t kTraceSignatureBytes = 80469;
inline constexpr std::size_t kWorldCount = 256;
inline constexpr std::size_t kThreadsPerBlock = 128;
inline constexpr std::size_t kBlocks = 2;

// The v1 capture probe stays retired. v2 does not revive it; it supersedes it.
inline constexpr bool kCaptureProbeV1Retired = true;
inline constexpr std::string_view kCaptureProbeV1RetirementReason =
    "semantic kernel catalog requires a versioned resource-evidence recapture";

struct KernelSpec {
    std::string_view kernel_id;
    std::string_view symbol_fragment;
    std::size_t expected_launch_count;
};

struct LaunchSpec {
    std::size_t launch_index;
    std::string_view kernel_id;
    std::string_view semantic_stage;
};

// v1 catalog: frozen historical symbols of the pre-rename binary. Retained so
// the retained static-capture evidence remains verifiable against the contract
// that produced it. Do not rename these to match current sources.
inline constexpr auto kKernelSpecs = std::to_array<KernelSpec>({
    // internal-code: compatibility -- frozen v1 kernel catalog. These
    // phase-lettered ids and symbols are the provenance keys of the retained
    // static-capture evidence JSON. Renaming them to semantic names would
    // invalidate that evidence rather than improve it; kKernelSpecsV2 below is
    // the semantic catalog for new captures.
    {"apply_barrier", "apply_barrier_kernel", 3},
    // internal-code: compatibility -- frozen evidence provenance key
    {"phase_a_controls", "prepare_phase_a_controls_kernel", 1},
    // internal-code: compatibility -- frozen evidence provenance key
    {"phase_b_forces", "phase_b_forces_kernel", 1},
    // internal-code: compatibility -- frozen evidence provenance key
    {"phase_b_aerodynamics", "phase_b_aerodynamics_kernel", 1},
    // internal-code: compatibility -- frozen evidence provenance key
    {"phase_b_integrate", "phase_b_integrate_kernel", 1},
    // internal-code: compatibility -- frozen evidence provenance key
    {"phase_d_instruments", "phase_d_instruments_kernel", 1},
    // internal-code: compatibility -- frozen evidence provenance key
    {"phase_d_configuration", "phase_d_configuration_kernel", 1},
    // internal-code: compatibility -- frozen evidence provenance key
    {"phase_d_projection", "phase_d_episode_kernel", 1},
    // internal-code: compatibility -- frozen evidence provenance key
    {"phase_d_pack", "phase_d_pack_observation_kernel", 1},
    // internal-code: compatibility -- frozen evidence provenance key
    {"phase_d_consumer", "phase_d_consumer_smoke_kernel", 1},
});

// v2 catalog: the semantic symbols actually emitted by the current .cu sources.
// kernel_id values also move to semantic names so a v2 report never carries a
// phase-lettered identifier. kKernelSpecsV2Migration below pins the 1:1
// correspondence to v1 so the two evidence generations stay comparable.
inline constexpr auto kKernelSpecsV2 = std::to_array<KernelSpec>({
    {"apply_barrier", "apply_barrier_kernel", 3},
    {"control_preparation", "control_preparation_kernel", 1},
    {"flight_dynamics_forces", "flight_dynamics_forces_kernel", 1},
    {"flight_dynamics_aerodynamics", "flight_dynamics_aerodynamics_kernel", 1},
    {"flight_dynamics_integrate", "flight_dynamics_integrate_kernel", 1},
    {"instrument_projection", "instrument_projection_kernel", 1},
    {"configuration_projection", "configuration_projection_kernel", 1},
    {"episode_projection", "episode_projection_kernel", 1},
    {"device_observation_pack", "pack_device_observation_kernel", 1},
    {"device_observation_consumer", "device_observation_consumer_smoke_kernel", 1},
});

struct KernelMigrationSpec {
    std::string_view v1_kernel_id;
    std::string_view v2_kernel_id;
};

// Pure 1:1 relabel. This is the evidence that a v2 capture measures the same
// execution graph the frozen v1 capture measured, not a different one.
inline constexpr auto kKernelSpecsV2Migration = std::to_array<KernelMigrationSpec>({
    {"apply_barrier", "apply_barrier"},
    // internal-code: compatibility -- v1 side of the rename map
    {"phase_a_controls", "control_preparation"},
    // internal-code: compatibility -- v1 side of the rename map
    {"phase_b_forces", "flight_dynamics_forces"},
    // internal-code: compatibility -- v1 side of the rename map
    {"phase_b_aerodynamics", "flight_dynamics_aerodynamics"},
    // internal-code: compatibility -- v1 side of the rename map
    {"phase_b_integrate", "flight_dynamics_integrate"},
    // internal-code: compatibility -- v1 side of the rename map
    {"phase_d_instruments", "instrument_projection"},
    // internal-code: compatibility -- v1 side of the rename map
    {"phase_d_configuration", "configuration_projection"},
    // internal-code: compatibility -- v1 side of the rename map
    {"phase_d_projection", "episode_projection"},
    // internal-code: compatibility -- v1 side of the rename map
    {"phase_d_pack", "device_observation_pack"},
    // internal-code: compatibility -- v1 side of the rename map
    {"phase_d_consumer", "device_observation_consumer"},
});

inline constexpr auto kLaunchSequence = std::to_array<LaunchSpec>({
    // internal-code: compatibility -- frozen v1 launch sequence, paired with
    // kKernelSpecs above. See kLaunchSequenceV2 for the semantic form.
    {0, "apply_barrier", "input_injection"},
    {1, "phase_a_controls", "phase_a_controls"},
    {2, "apply_barrier", "stage_publish"},
    {3, "phase_b_forces", "phase_b_forces"},
    {4, "phase_b_aerodynamics", "phase_b_aerodynamics"},
    {5, "phase_b_integrate", "phase_b_integrate"},
    {6, "phase_d_instruments", "phase_d_instruments"},
    {7, "phase_d_configuration", "phase_d_configuration"},
    {8, "phase_d_projection", "phase_d_projection"},
    {9, "apply_barrier", "window_commit"},
    {10, "phase_d_pack", "device_observation_pack"},
    {11, "phase_d_consumer", "device_consumer"},
});

// v2 launch order is identical to v1; only the kernel and stage identifiers are
// semantic. Twelve launches, same positions, same barrier placement.
inline constexpr auto kLaunchSequenceV2 = std::to_array<LaunchSpec>({
    {0, "apply_barrier", "input_injection"},
    {1, "control_preparation", "control_preparation"},
    {2, "apply_barrier", "stage_publish"},
    {3, "flight_dynamics_forces", "flight_dynamics_forces"},
    {4, "flight_dynamics_aerodynamics", "flight_dynamics_aerodynamics"},
    {5, "flight_dynamics_integrate", "flight_dynamics_integrate"},
    {6, "instrument_projection", "instrument_projection"},
    {7, "configuration_projection", "configuration_projection"},
    {8, "episode_projection", "episode_projection"},
    {9, "apply_barrier", "window_commit"},
    {10, "device_observation_pack", "device_observation_pack"},
    {11, "device_observation_consumer", "device_consumer"},
});

template <std::size_t KernelCount, std::size_t LaunchCount>
inline constexpr bool
catalog_is_complete(const std::array<KernelSpec, KernelCount> &kernels,
                    const std::array<LaunchSpec, LaunchCount> &launches) {
    std::size_t matched_launches = 0;
    for (const auto &kernel : kernels) {
        std::size_t count = 0;
        for (const auto &launch : launches) {
            if (launch.kernel_id == kernel.kernel_id) {
                ++count;
            }
        }
        if (count != kernel.expected_launch_count) {
            return false;
        }
        matched_launches += count;
    }
    // Every launch must belong to a declared kernel, not merely every kernel to
    // some launch. Without this an unknown launch_id would pass silently.
    return matched_launches == LaunchCount;
}

inline constexpr bool kernel_catalog_is_complete() {
    return catalog_is_complete(kKernelSpecs, kLaunchSequence);
}

inline constexpr bool kernel_catalog_v2_is_complete() {
    return catalog_is_complete(kKernelSpecsV2, kLaunchSequenceV2);
}

// The migration table must be a total bijection between the two catalogs, or a
// v2 report could not be compared field-by-field against the v1 capture.
inline constexpr bool kernel_migration_is_total() {
    if (kKernelSpecsV2Migration.size() != kKernelSpecs.size()) {
        return false;
    }
    for (const auto &kernel : kKernelSpecs) {
        std::size_t hits = 0;
        for (const auto &entry : kKernelSpecsV2Migration) {
            if (entry.v1_kernel_id == kernel.kernel_id) {
                ++hits;
            }
        }
        if (hits != 1) {
            return false;
        }
    }
    for (const auto &kernel : kKernelSpecsV2) {
        std::size_t hits = 0;
        for (const auto &entry : kKernelSpecsV2Migration) {
            if (entry.v2_kernel_id == kernel.kernel_id) {
                ++hits;
            }
        }
        if (hits != 1) {
            return false;
        }
    }
    return true;
}

// Launch-for-launch equivalence: position i in v2 must map to position i in v1
// through the migration table. This is what makes "same execution graph, new
// names" a checked claim rather than an assertion in prose.
inline constexpr bool launch_sequences_correspond() {
    if (kLaunchSequenceV2.size() != kLaunchSequence.size()) {
        return false;
    }
    for (std::size_t index = 0; index < kLaunchSequence.size(); ++index) {
        const auto &v1 = kLaunchSequence[index];
        const auto &v2 = kLaunchSequenceV2[index];
        if (v1.launch_index != index || v2.launch_index != index) {
            return false;
        }
        bool mapped = false;
        for (const auto &entry : kKernelSpecsV2Migration) {
            if (entry.v1_kernel_id == v1.kernel_id && entry.v2_kernel_id == v2.kernel_id) {
                mapped = true;
            }
        }
        if (!mapped) {
            return false;
        }
    }
    return true;
}

static_assert(kKernelSpecs.size() == 10);
static_assert(kLaunchSequence.size() == 12);
static_assert(kernel_catalog_is_complete());

static_assert(kKernelSpecsV2.size() == 10);
static_assert(kLaunchSequenceV2.size() == 12);
static_assert(kernel_catalog_v2_is_complete());
static_assert(kernel_migration_is_total());
static_assert(launch_sequences_correspond());

inline constexpr bool kSetupOutsideCapture = true;
inline constexpr bool kPublicExportInsideCapture = true;
inline constexpr bool kDeviceConsumerInsideCapture = true;
inline constexpr bool kDiagnosticMaterializationInsideCapture = false;
inline constexpr bool kMaintainedClaimAllowed = false;
inline constexpr bool kPublicSupportEnabled = false;
inline constexpr bool kPromotionAllowed = false;
inline constexpr bool kTuningAuthorized = false;

} // namespace runtime::cuda_resident::resource_evidence
