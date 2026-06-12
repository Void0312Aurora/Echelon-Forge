#pragma once

#include <algorithm>
#include <cctype>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace runtime::scheduler {

inline constexpr bool kWp10ClockDomainAdvisoryOnly = true;

inline constexpr std::string_view kReadSnapshotPolicyPreWindow = "pre_window";
inline constexpr std::string_view kReadSnapshotPolicyPostInjection = "post_injection";
inline constexpr std::string_view kReadSnapshotPolicySameWindow = "same_window";
inline constexpr std::string_view kReadSnapshotPolicyCommitted = "committed";
inline constexpr std::string_view kReadSnapshotPolicyDiagnosticOnly = "diagnostic_only";

inline constexpr std::string_view kWriteCommitPolicyStagePublish = "stage_publish";
inline constexpr std::string_view kWriteCommitPolicyWindowCommit = "window_commit";
inline constexpr std::string_view kWriteCommitPolicyDelayedEvent = "delayed_event";
inline constexpr std::string_view kWriteCommitPolicyExportOnly = "export_only";
inline constexpr std::string_view kWriteCommitPolicyDiagnosticOnly = "diagnostic_only";

inline constexpr std::string_view kFacadeVisibilityInternal = "internal";
inline constexpr std::string_view kFacadeVisibilityMaintainedSurface = "maintained_facade_surface";
inline constexpr std::string_view kFacadeVisibilityMaintainedExport = "maintained_facade_export";
inline constexpr std::string_view kFacadeVisibilityAdapterProjection = "adapter_projection";
inline constexpr std::string_view kFacadeVisibilityDiagnosticsOnly = "diagnostics_only";

struct StageNodeManifest {
    std::string node_id;
    std::vector<std::string> semantic_stage;
    std::string owner_module;
    std::vector<std::string> input_packets;
    std::vector<std::string> output_packets;
    std::vector<std::string> read_state_shards;
    std::vector<std::string> write_state_shards;
    std::string read_snapshot_policy;
    std::string write_commit_policy;
    std::string clock_domain;
    std::string latency_policy;
    std::string sync_policy;
    std::vector<std::string> allowed_same_window_edges;
    std::vector<std::string> required_barriers;
    std::vector<std::string> event_families_emitted;
    std::vector<std::string> diagnostic_trace_obligations;
    std::string facade_visibility;
    bool adapter_projection_allowed = false;
};

struct StageNodeManifestValidationResult {
    bool valid = true;
    std::vector<std::string> errors;

    void add_error(std::string error) {
        valid = false;
        errors.push_back(std::move(error));
    }
};

inline const std::vector<StageNodeManifest>& wp10_stage_node_manifest_registry_seed();

inline bool is_blank(std::string_view value) {
    return std::all_of(value.begin(), value.end(), [](unsigned char c) {
        return std::isspace(c) != 0;
    });
}

inline bool contains_value(
    const std::vector<std::string>& items,
    std::string_view expected
) {
    return std::find(items.begin(), items.end(), expected) != items.end();
}

inline bool declares_same_window_publish(const StageNodeManifest& manifest) {
    return manifest.write_commit_policy == kWriteCommitPolicyStagePublish ||
        manifest.latency_policy.find("same_window") != std::string::npos ||
        contains_value(manifest.required_barriers, "stage_publish");
}

inline bool declares_event_like_outputs(const StageNodeManifest& manifest) {
    return std::any_of(
        manifest.output_packets.begin(),
        manifest.output_packets.end(),
        [](const std::string& packet) {
            constexpr std::string_view kEventSuffix = "Event";
            constexpr std::string_view kReportSuffix = "Report";
            return (packet.size() >= kEventSuffix.size() &&
                    packet.ends_with(kEventSuffix)) ||
                (packet.size() >= kReportSuffix.size() &&
                 packet.ends_with(kReportSuffix));
        }
    );
}

inline bool is_maintained_scheduler_truth(const StageNodeManifest& manifest) {
    return manifest.facade_visibility != kFacadeVisibilityAdapterProjection &&
        manifest.facade_visibility != kFacadeVisibilityDiagnosticsOnly &&
        manifest.write_commit_policy != kWriteCommitPolicyDiagnosticOnly;
}

inline bool is_wp17_selected_slice_strict_clock_domain_node(
    const StageNodeManifest& manifest
) {
    return manifest.node_id == "p7.fire_control_launch.v1" ||
        manifest.node_id == "p9.effects_damage.v1" ||
        manifest.node_id == "p10.observation_export.v1";
}

inline std::vector<const StageNodeManifest*>
enumerate_wp17_selected_slice_strict_clock_domain_manifests() {
    std::vector<const StageNodeManifest*> manifests;
    for (const auto& manifest : wp10_stage_node_manifest_registry_seed()) {
        if (is_wp17_selected_slice_strict_clock_domain_node(manifest)) {
            manifests.push_back(&manifest);
        }
    }
    return manifests;
}

inline StageNodeManifestValidationResult validate_stage_node_manifest(
    const StageNodeManifest& manifest
) {
    StageNodeManifestValidationResult result{};

    if (is_blank(manifest.node_id)) {
        result.add_error("node_id is required");
    }
    if (manifest.semantic_stage.empty()) {
        result.add_error("semantic_stage is required");
    }
    if (is_blank(manifest.owner_module)) {
        result.add_error("owner_module is required");
    }
    if (manifest.input_packets.empty()) {
        result.add_error("input_packets is required for the WP10 slice");
    }
    if (manifest.output_packets.empty()) {
        result.add_error("output_packets is required");
    }
    if (manifest.read_state_shards.empty()) {
        result.add_error("read_state_shards is required");
    }
    if (is_blank(manifest.read_snapshot_policy)) {
        result.add_error("read_snapshot_policy is required");
    }
    if (is_blank(manifest.write_commit_policy)) {
        result.add_error("write_commit_policy is required");
    }
    if (is_blank(manifest.clock_domain)) {
        result.add_error("clock_domain is required");
    }
    if (is_blank(manifest.latency_policy)) {
        result.add_error("latency_policy is required");
    }
    if (is_blank(manifest.sync_policy)) {
        result.add_error("sync_policy is required");
    }
    if (manifest.required_barriers.empty()) {
        result.add_error("required_barriers is required");
    }
    if (manifest.diagnostic_trace_obligations.empty()) {
        result.add_error("diagnostic_trace_obligations is required");
    }
    if (is_blank(manifest.facade_visibility)) {
        result.add_error("facade_visibility is required");
    }

    if (declares_same_window_publish(manifest) &&
        manifest.allowed_same_window_edges.empty()) {
        result.add_error(
            "allowed_same_window_edges is required for same-window publish claims"
        );
    }
    if (manifest.write_commit_policy == kWriteCommitPolicyStagePublish &&
        !contains_value(manifest.required_barriers, "stage_publish")) {
        result.add_error(
            "stage_publish manifests must declare the stage_publish barrier"
        );
    }
    if (manifest.facade_visibility == kFacadeVisibilityAdapterProjection &&
        !manifest.adapter_projection_allowed) {
        result.add_error(
            "adapter_projection visibility requires adapter_projection_allowed"
        );
    }
    if (declares_event_like_outputs(manifest)) {
        if (manifest.event_families_emitted.empty()) {
            result.add_error(
                "event-emitting manifests must declare event_families_emitted"
            );
        }
        if (manifest.diagnostic_trace_obligations.empty()) {
            result.add_error(
                "event-emitting manifests must declare diagnostic_trace_obligations"
            );
        }
    }

    return result;
}

inline StageNodeManifestValidationResult validate_stage_node_manifest_registry(
    const std::vector<StageNodeManifest>& registry
) {
    StageNodeManifestValidationResult result{};
    std::vector<std::string> seen_ids;
    seen_ids.reserve(registry.size());

    for (const auto& manifest : registry) {
        if (contains_value(seen_ids, manifest.node_id)) {
            result.add_error("duplicate node_id: " + manifest.node_id);
            continue;
        }

        seen_ids.push_back(manifest.node_id);
        const StageNodeManifestValidationResult manifest_result =
            validate_stage_node_manifest(manifest);
        for (const auto& error : manifest_result.errors) {
            result.add_error(manifest.node_id + ": " + error);
        }
    }

    if (registry.empty()) {
        result.add_error("registry seed must not be empty");
    }

    return result;
}

inline const std::vector<StageNodeManifest>& wp10_stage_node_manifest_registry_seed() {
    static const std::vector<StageNodeManifest> registry = {
        StageNodeManifest{
            .node_id = "p7.fire_control_launch.v1",
            .semantic_stage = {"P7 FireControlLaunch"},
            .owner_module = "src/core/engine/simulation_kernel_weapon_api.cpp",
            .input_packets = {"LaunchRequest", "TrackPacket"},
            .output_packets = {"LaunchEvent", "DiagnosticsTrace"},
            .read_state_shards = {"track", "engagement", "control", "command"},
            .write_state_shards = {"engagement"},
            .read_snapshot_policy = std::string(kReadSnapshotPolicyPostInjection),
            .write_commit_policy = std::string(kWriteCommitPolicyWindowCommit),
            .clock_domain = "event_driven_or_fire_control_cadence",
            .latency_policy = "window_commit_same_timestamp",
            .sync_policy = "host_owned",
            .allowed_same_window_edges = {},
            .required_barriers = {"input_injection", "window_commit"},
            .event_families_emitted = {"fire_control_and_launch"},
            .diagnostic_trace_obligations = {
                "launch_request_id",
                "launch_event_id",
                "input_snapshot_version",
                "barrier_id",
                "world_id",
            },
            .facade_visibility = std::string(kFacadeVisibilityMaintainedSurface),
            .adapter_projection_allowed = false,
        },
        StageNodeManifest{
            .node_id = "p9.effects_damage.v1",
            .semantic_stage = {"P9 EffectsDamage"},
            .owner_module = "src/core/engine/simulation_kernel_damage_debug_api.cpp",
            .input_packets = {"EffectsEvent", "MunitionLifecyclePacket"},
            .output_packets = {"DamageReport", "DiagnosticsTrace"},
            .read_state_shards = {"engagement", "physics", "damage"},
            .write_state_shards = {"damage"},
            .read_snapshot_policy = std::string(kReadSnapshotPolicyCommitted),
            .write_commit_policy = std::string(kWriteCommitPolicyWindowCommit),
            .clock_domain = "event_driven_effects_resolution",
            .latency_policy = "window_commit_same_timestamp",
            .sync_policy = "host_owned",
            .allowed_same_window_edges = {},
            .required_barriers = {"window_commit"},
            .event_families_emitted = {"effects_and_damage"},
            .diagnostic_trace_obligations = {
                "effects_event_id",
                "damage_report_id",
                "source_snapshot_version",
                "affected_entity_ref",
                "barrier_id",
            },
            .facade_visibility = std::string(kFacadeVisibilityInternal),
            .adapter_projection_allowed = false,
        },
        StageNodeManifest{
            .node_id = "p10.observation_export.v1",
            .semantic_stage = {"P10 ObservationExport"},
            .owner_module = "src/runtime/facade/runtime_facade.cpp",
            .input_packets = {"LaunchEvent", "DamageReport", "DiagnosticsTrace"},
            .output_packets = {"ObservationBatchPacket", "DiagnosticsTrace"},
            .read_state_shards = {"engagement", "damage", "observation"},
            .write_state_shards = {"observation"},
            .read_snapshot_policy = std::string(kReadSnapshotPolicyCommitted),
            .write_commit_policy = std::string(kWriteCommitPolicyExportOnly),
            .clock_domain = "window_export",
            .latency_policy = "export_after_window_commit",
            .sync_policy = "explicit_export",
            .allowed_same_window_edges = {},
            .required_barriers = {"window_commit", "export"},
            .event_families_emitted = {"observation_and_export"},
            .diagnostic_trace_obligations = {
                "source_snapshot_version",
                "export_barrier_id",
                "observation_packet_version",
                "launch_event_id",
                "damage_report_id",
            },
            .facade_visibility = std::string(kFacadeVisibilityMaintainedExport),
            .adapter_projection_allowed = false,
        },
        StageNodeManifest{
            .node_id = "p7.launch_request_adapter_projection.v1",
            .semantic_stage = {"P7 FireControlLaunch"},
            .owner_module = "src/runtime/facade/runtime_facade.cpp",
            .input_packets = {"LaunchRequest"},
            .output_packets = {"DiagnosticsTrace"},
            .read_state_shards = {"engagement"},
            .write_state_shards = {},
            .read_snapshot_policy = std::string(kReadSnapshotPolicyDiagnosticOnly),
            .write_commit_policy = std::string(kWriteCommitPolicyDiagnosticOnly),
            .clock_domain = "adapter_projection_passthrough",
            .latency_policy = "best_effort_diagnostics",
            .sync_policy = "diagnostics_only",
            .allowed_same_window_edges = {},
            .required_barriers = {"input_injection", "export"},
            .event_families_emitted = {},
            .diagnostic_trace_obligations = {
                "source_id",
                "adapter_projection_label",
                "input_snapshot_version",
            },
            .facade_visibility = std::string(kFacadeVisibilityAdapterProjection),
            .adapter_projection_allowed = true,
        },
        StageNodeManifest{
            .node_id = "p10.observation_trace_diagnostics.v1",
            .semantic_stage = {"P10 ObservationExport"},
            .owner_module = "src/runtime/facade/runtime_facade.cpp",
            .input_packets = {"DiagnosticsTrace"},
            .output_packets = {"DiagnosticsTrace"},
            .read_state_shards = {"observation"},
            .write_state_shards = {},
            .read_snapshot_policy = std::string(kReadSnapshotPolicyDiagnosticOnly),
            .write_commit_policy = std::string(kWriteCommitPolicyDiagnosticOnly),
            .clock_domain = "diagnostics_export_slot",
            .latency_policy = "best_effort_diagnostics",
            .sync_policy = "diagnostics_only",
            .allowed_same_window_edges = {},
            .required_barriers = {"export"},
            .event_families_emitted = {},
            .diagnostic_trace_obligations = {
                "trace_id",
                "parent_trace_id",
                "observation_packet_version",
            },
            .facade_visibility = std::string(kFacadeVisibilityDiagnosticsOnly),
            .adapter_projection_allowed = false,
        },
    };
    return registry;
}

inline std::vector<const StageNodeManifest*> enumerate_wp10_maintained_stage_node_manifests() {
    std::vector<const StageNodeManifest*> manifests;
    for (const auto& manifest : wp10_stage_node_manifest_registry_seed()) {
        if (is_maintained_scheduler_truth(manifest)) {
            manifests.push_back(&manifest);
        }
    }
    return manifests;
}

inline const StageNodeManifest* find_stage_node_manifest(std::string_view node_id) {
    const auto& registry = wp10_stage_node_manifest_registry_seed();
    const auto it = std::find_if(
        registry.begin(),
        registry.end(),
        [node_id](const StageNodeManifest& manifest) {
            return manifest.node_id == node_id;
        }
    );
    if (it == registry.end()) {
        return nullptr;
    }
    return &(*it);
}

inline std::optional<StageNodeManifestValidationResult>
validate_wp10_stage_node_manifest_registry_seed() {
    const StageNodeManifestValidationResult result =
        validate_stage_node_manifest_registry(wp10_stage_node_manifest_registry_seed());
    if (result.valid) {
        return std::nullopt;
    }
    return result;
}

}  // namespace runtime::scheduler
