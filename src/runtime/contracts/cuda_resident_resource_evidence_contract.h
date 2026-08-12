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

// v3 describes the CP-5 fused window graph. Unlike v2, this generation is a
// deliberate execution-graph change: the six per-world window-commit launches
// measured by v1/v2 (forces, aerodynamics, integrate, and the three
// projections) are one fused launch, because the CP-4 achieved counters showed
// the split graph is latency-bound on a near-idle device and its launch chain
// is the dominant cost. The captured workload (trace signature) is unchanged;
// the fold table below pins which v2 kernels each v3 kernel absorbed.
inline constexpr std::string_view kSchemaV3 = "cuda_resident.cp.kernel_resource_evidence.v3";
inline constexpr std::string_view kProbeSchemaV3 = "cuda_resident.cp.resource_capture_probe.v3";
inline constexpr std::string_view kProfileIdV3 = "cp.resource.steady_full_window_body.sm86.v3";
inline constexpr std::string_view kProbeSchemaV3Predecessor = kProbeSchemaV2;

// v4 describes the CP-7b launch fold. The kernel SET is unchanged from v3 --
// the same five symbols -- but the stage_publish and window_commit barrier
// launches are per-world epilogues inside their stage kernels, so a captured
// window has five launches and apply_barrier keeps only its input-injection
// launch. The captured workload (trace signature) is unchanged; the
// absorption walk below pins which v3 launches each v4 launch carries.
inline constexpr std::string_view kSchemaV4 = "cuda_resident.cp.kernel_resource_evidence.v4";
inline constexpr std::string_view kProbeSchemaV4 = "cuda_resident.cp.resource_capture_probe.v4";
inline constexpr std::string_view kProfileIdV4 = "cp.resource.steady_full_window_body.sm86.v4";
inline constexpr std::string_view kProbeSchemaV4Predecessor = kProbeSchemaV3;

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

// v2 catalog: the semantic symbols of the pre-fusion binary. Frozen historical
// record since CP-5: the retained v2 static and counter evidence hashes against
// these symbols, so they must not be edited to match the fused sources.
// kKernelSpecsV2Migration below pins the 1:1 correspondence to v1 so the two
// evidence generations stay comparable. kKernelSpecsV3 is the live catalog.
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

// v3 catalog: the symbols actually emitted by the fused .cu sources. The six
// window-commit kernels of v2 are one kernel; barriers, control preparation,
// and the device-observation pair are unchanged.
inline constexpr auto kKernelSpecsV3 = std::to_array<KernelSpec>({
    {"apply_barrier", "apply_barrier_kernel", 3},
    {"control_preparation", "control_preparation_kernel", 1},
    {"window_commit_body", "window_commit_body_kernel", 1},
    {"device_observation_pack", "pack_device_observation_kernel", 1},
    {"device_observation_consumer", "device_observation_consumer_smoke_kernel", 1},
});

struct KernelFoldSpec {
    std::string_view v2_kernel_id;
    std::string_view v3_kernel_id;
};

// Total fold map, not a bijection: every v2 kernel maps to exactly one v3
// kernel, and the six window-commit kernels share one target. This is the
// checked statement of what the fusion absorbed, so a v3 report stays
// comparable to the frozen v2 static and counter evidence kernel-by-kernel.
inline constexpr auto kKernelSpecsV3Fold = std::to_array<KernelFoldSpec>({
    {"apply_barrier", "apply_barrier"},
    {"control_preparation", "control_preparation"},
    {"flight_dynamics_forces", "window_commit_body"},
    {"flight_dynamics_aerodynamics", "window_commit_body"},
    {"flight_dynamics_integrate", "window_commit_body"},
    {"instrument_projection", "window_commit_body"},
    {"configuration_projection", "window_commit_body"},
    {"episode_projection", "window_commit_body"},
    {"device_observation_pack", "device_observation_pack"},
    {"device_observation_consumer", "device_observation_consumer"},
});

// Seven launches: the six-launch window graph of v2 collapses at position 3,
// every launch outside the fold keeps its relative position and stage.
inline constexpr auto kLaunchSequenceV3 = std::to_array<LaunchSpec>({
    {0, "apply_barrier", "input_injection"},
    {1, "control_preparation", "control_preparation"},
    {2, "apply_barrier", "stage_publish"},
    {3, "window_commit_body", "window_commit_body"},
    {4, "apply_barrier", "window_commit"},
    {5, "device_observation_pack", "device_observation_pack"},
    {6, "device_observation_consumer", "device_consumer"},
});

// v4 catalog: same five kernels as v3, but the two in-window barrier launches
// are epilogues of their stage kernels, so apply_barrier launches once.
inline constexpr auto kKernelSpecsV4 = std::to_array<KernelSpec>({
    {"apply_barrier", "apply_barrier_kernel", 1},
    {"control_preparation", "control_preparation_kernel", 1},
    {"window_commit_body", "window_commit_body_kernel", 1},
    {"device_observation_pack", "pack_device_observation_kernel", 1},
    {"device_observation_consumer", "device_observation_consumer_smoke_kernel", 1},
});

// Five launches. The two folded stages carry compound semantic-stage names so
// a v4 report can never be misread as claiming the barriers stopped happening.
inline constexpr auto kLaunchSequenceV4 = std::to_array<LaunchSpec>({
    {0, "apply_barrier", "input_injection"},
    {1, "control_preparation", "control_preparation_and_stage_publish"},
    {2, "window_commit_body", "window_commit_body_and_window_commit"},
    {3, "device_observation_pack", "device_observation_pack"},
    {4, "device_observation_consumer", "device_consumer"},
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

inline constexpr bool kernel_catalog_v3_is_complete() {
    return catalog_is_complete(kKernelSpecsV3, kLaunchSequenceV3);
}

// The fold must be total on v2 and surjective onto v3: every v2 kernel maps to
// exactly one v3 kernel, and every v3 kernel absorbs at least one v2 kernel.
// Without surjectivity a v3 kernel could appear from nowhere and still pass.
inline constexpr bool kernel_fold_is_total_and_surjective() {
    if (kKernelSpecsV3Fold.size() != kKernelSpecsV2.size()) {
        return false;
    }
    for (const auto &kernel : kKernelSpecsV2) {
        std::size_t hits = 0;
        for (const auto &entry : kKernelSpecsV3Fold) {
            if (entry.v2_kernel_id == kernel.kernel_id) {
                ++hits;
            }
        }
        if (hits != 1) {
            return false;
        }
    }
    for (const auto &kernel : kKernelSpecsV3) {
        std::size_t hits = 0;
        for (const auto &entry : kKernelSpecsV3Fold) {
            if (entry.v3_kernel_id == kernel.kernel_id) {
                ++hits;
            }
        }
        if (hits == 0) {
            return false;
        }
    }
    return true;
}

// Launch correspondence across the fold: mapping every v2 launch through the
// fold table and collapsing consecutive runs that land on the same fused v3
// kernel must reproduce the v3 sequence exactly. This is what makes "the six
// window launches became one" a checked claim rather than prose.
inline constexpr bool launch_sequences_correspond_v2_to_v3() {
    constexpr auto fold = [](std::string_view v2_kernel_id) -> std::string_view {
        for (const auto &entry : kKernelSpecsV3Fold) {
            if (entry.v2_kernel_id == v2_kernel_id) {
                return entry.v3_kernel_id;
            }
        }
        return {};
    };
    constexpr auto fold_absorbs_several = [](std::string_view v3_kernel_id) {
        std::size_t hits = 0;
        for (const auto &entry : kKernelSpecsV3Fold) {
            if (entry.v3_kernel_id == v3_kernel_id) {
                ++hits;
            }
        }
        return hits > 1;
    };
    std::size_t v3_index = 0;
    for (std::size_t index = 0; index < kLaunchSequenceV2.size(); ++index) {
        const std::string_view mapped = fold(kLaunchSequenceV2[index].kernel_id);
        if (mapped.empty()) {
            return false;
        }
        const bool continues_fused_run =
            index > 0 && fold_absorbs_several(mapped) &&
            fold(kLaunchSequenceV2[index - 1].kernel_id) == mapped;
        if (continues_fused_run) {
            continue;
        }
        if (v3_index >= kLaunchSequenceV3.size() ||
            kLaunchSequenceV3[v3_index].kernel_id != mapped ||
            kLaunchSequenceV3[v3_index].launch_index != v3_index) {
            return false;
        }
        ++v3_index;
    }
    return v3_index == kLaunchSequenceV3.size();
}

static_assert(kKernelSpecs.size() == 10);
static_assert(kLaunchSequence.size() == 12);
static_assert(kernel_catalog_is_complete());

static_assert(kKernelSpecsV2.size() == 10);
static_assert(kLaunchSequenceV2.size() == 12);
static_assert(kernel_catalog_v2_is_complete());
static_assert(kernel_migration_is_total());
static_assert(launch_sequences_correspond());

static_assert(kKernelSpecsV3.size() == 5);
static_assert(kLaunchSequenceV3.size() == 7);
static_assert(kernel_catalog_v3_is_complete());
static_assert(kernel_fold_is_total_and_surjective());
static_assert(launch_sequences_correspond_v2_to_v3());

inline constexpr bool kernel_catalog_v4_is_complete() {
    return catalog_is_complete(kKernelSpecsV4, kLaunchSequenceV4);
}

// The v3 and v4 catalogs must name the same kernels: CP-7b folded launches,
// not kernels. Only the apply_barrier launch count may differ.
inline constexpr bool kernel_sets_match_v3_to_v4() {
    if (kKernelSpecsV4.size() != kKernelSpecsV3.size()) {
        return false;
    }
    for (std::size_t index = 0; index < kKernelSpecsV3.size(); ++index) {
        if (kKernelSpecsV4[index].kernel_id != kKernelSpecsV3[index].kernel_id ||
            kKernelSpecsV4[index].symbol_fragment != kKernelSpecsV3[index].symbol_fragment) {
            return false;
        }
    }
    return true;
}

// Launch absorption: walking the v3 sequence and merging each barrier launch
// whose stage is stage_publish or window_commit into the launch immediately
// before it must reproduce the v4 sequence exactly, with the compound stage
// name recording both halves. This is the checked statement of "the barriers
// still happen, inside the preceding stage's launch".
inline constexpr bool launch_sequences_correspond_v3_to_v4() {
    std::size_t v4_index = 0;
    for (std::size_t index = 0; index < kLaunchSequenceV3.size(); ++index) {
        const auto &launch = kLaunchSequenceV3[index];
        const bool absorbed_barrier =
            launch.kernel_id == std::string_view("apply_barrier") &&
            (launch.semantic_stage == std::string_view("stage_publish") ||
             launch.semantic_stage == std::string_view("window_commit"));
        if (absorbed_barrier) {
            // The barrier folds into the previous v4 row, whose compound stage
            // must end with this barrier's stage name.
            if (v4_index == 0 || index == 0) {
                return false;
            }
            const auto &host_row = kLaunchSequenceV4[v4_index - 1];
            const auto stage = host_row.semantic_stage;
            const auto barrier_stage = launch.semantic_stage;
            if (stage.size() <= barrier_stage.size() ||
                stage.substr(stage.size() - barrier_stage.size()) != barrier_stage) {
                return false;
            }
            // And that previous row must be the launch that directly precedes
            // this barrier in v3.
            if (host_row.kernel_id != kLaunchSequenceV3[index - 1].kernel_id) {
                return false;
            }
            continue;
        }
        if (v4_index >= kLaunchSequenceV4.size()) {
            return false;
        }
        const auto &v4_row = kLaunchSequenceV4[v4_index];
        if (v4_row.launch_index != v4_index || v4_row.kernel_id != launch.kernel_id) {
            return false;
        }
        // Non-folded launches keep their stage name; folded hosts prefix it.
        const auto stage = v4_row.semantic_stage;
        if (stage.substr(0, launch.semantic_stage.size()) != launch.semantic_stage) {
            return false;
        }
        ++v4_index;
    }
    return v4_index == kLaunchSequenceV4.size();
}

static_assert(kKernelSpecsV4.size() == 5);
static_assert(kLaunchSequenceV4.size() == 5);
static_assert(kernel_catalog_v4_is_complete());
static_assert(kernel_sets_match_v3_to_v4());
static_assert(launch_sequences_correspond_v3_to_v4());

inline constexpr bool kSetupOutsideCapture = true;
inline constexpr bool kPublicExportInsideCapture = true;
inline constexpr bool kDeviceConsumerInsideCapture = true;
inline constexpr bool kDiagnosticMaterializationInsideCapture = false;
inline constexpr bool kMaintainedClaimAllowed = false;
inline constexpr bool kPublicSupportEnabled = false;
inline constexpr bool kPromotionAllowed = false;
inline constexpr bool kTuningAuthorized = false;

} // namespace runtime::cuda_resident::resource_evidence
