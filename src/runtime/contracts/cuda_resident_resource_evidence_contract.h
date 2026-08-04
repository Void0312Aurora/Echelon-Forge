#pragma once

#include <array>
#include <cstddef>
#include <string_view>

namespace runtime::cuda_resident::resource_evidence {

inline constexpr std::string_view kSchemaV1 =
    "cuda_resident.cr2.kernel_resource_evidence.v1";
inline constexpr std::string_view kProbeSchemaV1 =
    "cuda_resident.cr2.resource_capture_probe.v1";
inline constexpr std::string_view kProfileId =
    "cr2.resource.steady_full_window_body.sm86.v1";
inline constexpr std::string_view kCaptureRange = "cudaProfilerApi";
inline constexpr std::string_view kBuildConfig = "Release";
inline constexpr std::string_view kCudaArchitecture = "sm_86";
inline constexpr std::string_view kTraceSignatureAlgorithm = "fnv1a64";
inline constexpr std::string_view kTraceSignatureDigest = "cb31675ee34e5015";
inline constexpr std::size_t kTraceSignatureBytes = 80469;
inline constexpr std::size_t kWorldCount = 256;
inline constexpr std::size_t kThreadsPerBlock = 128;
inline constexpr std::size_t kBlocks = 2;

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

inline constexpr auto kKernelSpecs = std::to_array<KernelSpec>({
    {"apply_barrier", "apply_barrier_kernel", 3},
    {"phase_a_controls", "prepare_phase_a_controls_kernel", 1},
    {"phase_b_forces", "phase_b_forces_kernel", 1},
    {"phase_b_aerodynamics", "phase_b_aerodynamics_kernel", 1},
    {"phase_b_integrate", "phase_b_integrate_kernel", 1},
    {"phase_d_instruments", "phase_d_instruments_kernel", 1},
    {"phase_d_configuration", "phase_d_configuration_kernel", 1},
    {"phase_d_projection", "phase_d_episode_kernel", 1},
    {"phase_d_pack", "phase_d_pack_observation_kernel", 1},
    {"phase_d_consumer", "phase_d_consumer_smoke_kernel", 1},
});

inline constexpr auto kLaunchSequence = std::to_array<LaunchSpec>({
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

inline constexpr bool kernel_catalog_is_complete() {
    for (const auto &kernel : kKernelSpecs) {
        std::size_t count = 0;
        for (const auto &launch : kLaunchSequence) {
            if (launch.kernel_id == kernel.kernel_id) {
                ++count;
            }
        }
        if (count != kernel.expected_launch_count) {
            return false;
        }
    }
    return true;
}

static_assert(kKernelSpecs.size() == 10);
static_assert(kLaunchSequence.size() == 12);
static_assert(kernel_catalog_is_complete());

inline constexpr bool kSetupOutsideCapture = true;
inline constexpr bool kPublicExportInsideCapture = true;
inline constexpr bool kDeviceConsumerInsideCapture = true;
inline constexpr bool kDiagnosticMaterializationInsideCapture = false;
inline constexpr bool kMaintainedClaimAllowed = false;
inline constexpr bool kPublicSupportEnabled = false;
inline constexpr bool kPromotionAllowed = false;
inline constexpr bool kTuningAuthorized = false;

} // namespace runtime::cuda_resident::resource_evidence
