#pragma once

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <functional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "runtime/contracts/stage_node_manifest_registry.h"
#include "runtime/facade/runtime_facade_types.h"

inline constexpr std::string_view kRuntimeWindowBarrierInputInjection =
    "input_injection";
inline constexpr std::string_view kRuntimeWindowBarrierStagePublish =
    "stage_publish";
inline constexpr std::string_view kRuntimeWindowBarrierWindowCommit =
    "window_commit";
inline constexpr std::string_view kRuntimeWindowBarrierExport = "export";
inline constexpr std::string_view kRuntimeWindowCadenceDomainPolicy = "policy";
inline constexpr std::string_view kRuntimeWindowCadenceDomainControl = "control";
inline constexpr std::string_view kRuntimeWindowCadenceDomainPhysics = "physics";
inline constexpr std::string_view kRuntimeWindowCadenceDomainExport = "export";
// Maintained-slice lineage stays anchored to enumerate_wp10_maintained_stage_node_manifests()
// even though WP17 narrows execution to enumerate_wp17_selected_slice_strict_clock_domain_manifests().

struct RuntimeWindowCoordinatorCallbacks {
    std::function<void(const std::vector<WorldPilotActionAssignment>&)>
        apply_pilot_actions;
    std::function<void(const std::vector<WorldMissionCommandAssignment>&)>
        apply_mission_commands;
    std::function<void()> step_window;
    std::function<ObservationBatchPacket(const ObservationBatchRequest&)>
        export_observation_packet;
    std::function<EngagementEventPacket(const EngagementBatchRequest&)>
        export_engagement_event_packet;
    std::function<std::vector<DiagnosticsTrace>(const EngagementBatchRequest&)>
        export_diagnostics_traces;
};

#include "runtime/facade/runtime_window_coordinator_helpers.h"
#include "runtime/facade/runtime_window_coordinator_selection_helpers.h"
#include "runtime/facade/runtime_window_coordinator_callback_helpers.h"
#include "runtime/facade/runtime_window_coordinator_cadence_trace_helpers.h"
#include "runtime/facade/runtime_window_coordinator_execution_helpers.h"

inline bool runtime_window_requests_conflict(
    const RuntimeWindowActionRequest& lhs,
    const RuntimeWindowActionRequest& rhs
) {
    return lhs.action_intent.target.world_index == rhs.action_intent.target.world_index &&
        lhs.action_intent.target.entity_id == rhs.action_intent.target.entity_id &&
        lhs.action_intent.action_family == rhs.action_intent.action_family;
}

inline RuntimeWindowSchedulingContext classify_runtime_window_inputs(
    const RuntimeWindowRequest& request
) {
    RuntimeWindowSchedulingContext context{};
    context.window_id = runtime_window_default_id(request);
    context.world_id = request.world_id;
    context.source_time_s = request.source_time_s;

    for (const auto& action_request : request.action_requests) {
        RuntimeWindowInputRecord record{
            .request = action_request,
            .reason = "accepted_for_current_window",
        };
        const auto& intent = action_request.action_intent;

        if (!runtime_window_has_finite_time(request.source_time_s) ||
            !runtime_window_has_finite_time(intent.effective_time_s) ||
            (intent.valid_until_s != 0.0 &&
             !runtime_window_has_finite_time(intent.valid_until_s))) {
            record.reason = "non_finite_time_metadata";
            context.rejected_inputs.push_back(record);
            continue;
        }
        if (runtime_window_is_blank(action_request.source_layer)) {
            record.reason = "source_layer is required";
            context.rejected_inputs.push_back(record);
            continue;
        }
        if (runtime_window_is_blank(action_request.input_snapshot_version)) {
            record.reason = "input_snapshot_version is required";
            context.rejected_inputs.push_back(record);
            continue;
        }
        if (runtime_window_is_blank(intent.source_id)) {
            record.reason = "source_id is required";
            context.rejected_inputs.push_back(record);
            continue;
        }
        if (runtime_window_is_blank(intent.action_family)) {
            record.reason = "action_family is required";
            context.rejected_inputs.push_back(record);
            continue;
        }
        if (!runtime_window_is_supported_merge_policy(intent.merge_policy)) {
            record.reason = "merge_policy is not supported by the WP10-B window coordinator";
            context.rejected_inputs.push_back(record);
            continue;
        }
        if (!runtime_window_is_blank(
                action_request.clock_domain_metadata.clock_merge_policy) &&
            !runtime_window_is_supported_clock_merge_policy(
                action_request.clock_domain_metadata.clock_merge_policy)) {
            record.reason =
                "clock_domain_metadata.clock_merge_policy is not supported by the WP16-B cadence gate";
            context.rejected_inputs.push_back(record);
            continue;
        }
        if (runtime_window_is_independent_clock_domain_relation(
                action_request.clock_domain_metadata.relation)) {
            if (action_request.clock_domain_metadata.diagnostics_only) {
                record.reason =
                    action_request.clock_domain_metadata.diagnostics_reason.empty()
                    ? "independent_clock_domain diagnostics-only inputs cannot enter the maintained slice"
                    : action_request.clock_domain_metadata.diagnostics_reason;
                context.rejected_inputs.push_back(record);
                continue;
            }
            if (runtime_window_is_blank(
                    action_request.clock_domain_metadata.clock_merge_policy)) {
                record.reason =
                    "independent_clock_domain inputs require clock_merge_policy";
                context.rejected_inputs.push_back(record);
                continue;
            }
            if (!runtime_window_has_finite_time(
                    action_request.clock_domain_metadata.source_time_s) ||
                !action_request.clock_domain_metadata.has_source_time) {
                record.reason =
                    "independent_clock_domain inputs require finite source_time_s";
                context.rejected_inputs.push_back(record);
                continue;
            }
            if (runtime_window_is_blank(
                    action_request.clock_domain_metadata.source_snapshot_version)) {
                record.reason =
                    "independent_clock_domain inputs require source_snapshot_version";
                context.rejected_inputs.push_back(record);
                continue;
            }
            if (runtime_window_is_blank(
                    action_request.clock_domain_metadata.target_window_id)) {
                record.reason =
                    "independent_clock_domain inputs require target_window_id";
                context.rejected_inputs.push_back(record);
                continue;
            }
            if (!runtime_window_has_selected_barrier_order(
                    action_request.clock_domain_metadata.barrier_order)) {
                record.reason =
                    "independent_clock_domain inputs require deterministic selected-slice barrier_order metadata";
                context.rejected_inputs.push_back(record);
                continue;
            }
            if (action_request.clock_domain_metadata.target_window_id !=
                context.window_id) {
                record.reason =
                    "independent_clock_domain input targets a different scheduling window";
                context.deferred_inputs.push_back(record);
                continue;
            }
        }
        if (intent.target.entity_id == 0) {
            record.reason = "target.entity_id is required";
            context.rejected_inputs.push_back(record);
            continue;
        }
        if (intent.target.world_index != request.world_id) {
            record.reason = "target.world_index does not match the scheduling window world_id";
            context.rejected_inputs.push_back(record);
            continue;
        }
        if (!runtime_window_has_payload(action_request)) {
            record.reason = "at least one action payload is required";
            context.rejected_inputs.push_back(record);
            continue;
        }
        if (intent.valid_until_s != 0.0 &&
            intent.valid_until_s < intent.effective_time_s) {
            record.reason = "valid_until_s must be greater than or equal to effective_time_s";
            context.rejected_inputs.push_back(record);
            continue;
        }
        if (intent.valid_until_s != 0.0 &&
            intent.valid_until_s < request.source_time_s) {
            record.reason = "request validity window expired before the current scheduling window";
            context.expired_inputs.push_back(record);
            continue;
        }
        if (intent.effective_time_s > request.source_time_s) {
            record.reason = "request becomes visible in a future scheduling window";
            context.deferred_inputs.push_back(record);
            continue;
        }
        context.accepted_inputs.push_back(record);
    }

    if (context.accepted_inputs.size() < 2) {
        return context;
    }

    std::vector<RuntimeWindowInputRecord> conflict_free_inputs;
    conflict_free_inputs.reserve(context.accepted_inputs.size());
    for (std::size_t index = 0; index < context.accepted_inputs.size(); ++index) {
        bool conflicted = false;
        for (std::size_t other = 0; other < context.accepted_inputs.size(); ++other) {
            if (index == other) {
                continue;
            }
            if (runtime_window_requests_conflict(
                    context.accepted_inputs[index].request,
                    context.accepted_inputs[other].request)) {
                conflicted = true;
                break;
            }
        }

        if (conflicted) {
            auto rejected = context.accepted_inputs[index];
            rejected.reason =
                "same-window merge resolution is not maintained; conflicting requests fail closed";
            context.rejected_inputs.push_back(rejected);
            continue;
        }

        conflict_free_inputs.push_back(context.accepted_inputs[index]);
    }

    context.accepted_inputs = std::move(conflict_free_inputs);
    return context;
}

inline RuntimeWindowResult execute_runtime_window(
    const RuntimeWindowRequest& request,
    const RuntimeWindowCoordinatorCallbacks& callbacks
) {
    RuntimeWindowResult result{};
    result.context = classify_runtime_window_inputs(request);
    result.cadence_config = normalize_runtime_window_cadence_config(request);
    result.cadence_trace = build_runtime_window_cadence_trace(
        request,
        result.context,
        result.cadence_config,
        callbacks
    );
    result.visibility_trace.push_back(RuntimeWindowVisibilityRecord{
        .barrier_id = "collect",
        .visible_input_count = 0,
    });

    std::vector<WorldPilotActionAssignment> pilot_assignments;
    std::vector<WorldMissionCommandAssignment> mission_assignments;
    pilot_assignments.reserve(result.context.accepted_inputs.size());
    mission_assignments.reserve(result.context.accepted_inputs.size());

    for (const auto& record : result.context.accepted_inputs) {
        const auto& intent = record.request.action_intent;
        if (intent.has_pilot_action) {
            pilot_assignments.push_back(WorldPilotActionAssignment{
                .world_index = intent.target.world_index,
                .entity_id = intent.target.entity_id,
                .action = intent.pilot_action,
            });
        }
        if (intent.has_mission_command) {
            mission_assignments.push_back(WorldMissionCommandAssignment{
                .world_index = intent.target.world_index,
                .entity_id = intent.target.entity_id,
                .command = intent.mission_command,
            });
        }
    }

    runtime_window_advance_barrier(
        &result.context,
        &result.barrier_trace,
        kRuntimeWindowBarrierInputInjection
    );
    result.injected_inputs = result.context.accepted_inputs;
    result.visibility_trace.push_back(RuntimeWindowVisibilityRecord{
        .barrier_id = result.context.current_barrier_id,
        .visible_input_count = result.injected_inputs.size(),
    });

    if (!pilot_assignments.empty() && callbacks.apply_pilot_actions) {
        callbacks.apply_pilot_actions(pilot_assignments);
    }
    if (!mission_assignments.empty() && callbacks.apply_mission_commands) {
        callbacks.apply_mission_commands(mission_assignments);
    }

    const auto manifests =
        runtime::scheduler::enumerate_wp17_selected_slice_strict_clock_domain_manifests();
    result.executed_nodes.reserve(manifests.size());

    const auto* fire_control_manifest =
        runtime::scheduler::find_stage_node_manifest("p7.fire_control_launch.v1");
    if (fire_control_manifest != nullptr) {
        result.executed_nodes.push_back(runtime_window_fire_control_launch_record(
            *fire_control_manifest,
            result.context,
            result.cadence_trace
        ));
    }

    const auto* effects_damage_manifest =
        runtime::scheduler::find_stage_node_manifest("p9.effects_damage.v1");
    if (effects_damage_manifest != nullptr && !result.executed_nodes.empty()) {
        result.executed_nodes.push_back(runtime_window_effects_damage_record(
            *effects_damage_manifest,
            result.context,
            result.executed_nodes.front(),
            result.cadence_trace
        ));
    }

    if (callbacks.step_window) {
        callbacks.step_window();
    }

    for (const auto* manifest : manifests) {
        if (manifest == nullptr) {
            continue;
        }
        const bool stage_publish_required =
            manifest->write_commit_policy ==
                runtime::scheduler::kWriteCommitPolicyStagePublish ||
            runtime::scheduler::contains_value(
                manifest->required_barriers,
                std::string(kRuntimeWindowBarrierStagePublish)
            );
        if (!stage_publish_required) {
            continue;
        }
        runtime_window_advance_barrier(
            &result.context,
            &result.barrier_trace,
            kRuntimeWindowBarrierStagePublish,
            manifest->node_id
        );
    }

    runtime_window_advance_barrier(
        &result.context,
        &result.barrier_trace,
        kRuntimeWindowBarrierWindowCommit
    );

    const auto* export_manifest =
        runtime::scheduler::find_stage_node_manifest("p10.observation_export.v1");
    RuntimeWindowNodeExecutionRecord export_record{};
    bool export_record_present = false;
    if (export_manifest != nullptr) {
        export_record = runtime_window_observation_export_record(
            *export_manifest,
            request,
            result.context,
            callbacks,
            result.cadence_trace
        );
        export_record_present = true;
    }

    const ObservationBatchRequest observation_request =
        resolve_runtime_window_observation_request(request, result.injected_inputs);
    const EngagementBatchRequest engagement_request =
        resolve_runtime_window_engagement_request(request, result.injected_inputs);

    if (export_record_present && export_record.execution_state == "executed" &&
        request.export_observation && callbacks.export_observation_packet) {
        result.observation_packet =
            callbacks.export_observation_packet(observation_request);
    }
    if (export_record_present && export_record.execution_state == "executed" &&
        request.export_engagement && callbacks.export_engagement_event_packet) {
        result.engagement_packet =
            callbacks.export_engagement_event_packet(engagement_request);
    }
    if (export_record_present && export_record.execution_state == "executed" &&
        request.export_diagnostics && callbacks.export_diagnostics_traces) {
        result.diagnostics_traces =
            callbacks.export_diagnostics_traces(engagement_request);
    }

    if (export_record_present) {
        export_record.source_snapshot_version =
            runtime_window_export_snapshot_evidence(result);
        result.executed_nodes.push_back(std::move(export_record));
    }

    runtime_window_advance_barrier(
        &result.context,
        &result.barrier_trace,
        kRuntimeWindowBarrierExport
    );
    return result;
}
