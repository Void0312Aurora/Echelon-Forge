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

inline bool runtime_window_is_blank(std::string_view value) {
    return value.empty() || std::all_of(value.begin(), value.end(), [](unsigned char c) {
        return std::isspace(c) != 0;
    });
}

inline bool runtime_window_is_supported_merge_policy(std::string_view policy) {
    return policy == "last_write_wins" || policy == "reject_on_conflict";
}

inline bool runtime_window_has_payload(const RuntimeWindowActionRequest& request) {
    return request.action_intent.has_pilot_action ||
        request.action_intent.has_mission_command;
}

inline bool runtime_window_has_finite_time(double value) {
    return std::isfinite(value) != 0;
}

inline bool runtime_window_is_supported_clock_merge_policy(std::string_view policy) {
    return policy == "nested_slot" || policy == "hold_last" ||
        policy == "interpolate" || policy == "enqueue_event" ||
        policy == "defer_to_next_window" ||
        policy == "reject_on_ambiguous_order";
}

inline bool runtime_window_is_independent_clock_domain_relation(
    std::string_view relation
) {
    return relation == "independent";
}

inline bool runtime_window_has_selected_barrier_order(
    const std::vector<std::string>& barrier_order
) {
    if (barrier_order.empty()) {
        return false;
    }

    const std::array<std::string_view, 3> selected_barriers = {
        kRuntimeWindowBarrierInputInjection,
        kRuntimeWindowBarrierWindowCommit,
        kRuntimeWindowBarrierExport,
    };
    std::size_t next_index = 0;
    for (const auto& barrier_id : barrier_order) {
        const auto it = std::find(
            selected_barriers.begin() + static_cast<std::ptrdiff_t>(next_index),
            selected_barriers.end(),
            barrier_id
        );
        if (it == selected_barriers.end()) {
            return false;
        }
        next_index = static_cast<std::size_t>(
            std::distance(selected_barriers.begin(), it) + 1
        );
    }
    return true;
}

inline std::vector<std::string> runtime_window_selected_barrier_order() {
    return {
        std::string(kRuntimeWindowBarrierInputInjection),
        std::string(kRuntimeWindowBarrierWindowCommit),
        std::string(kRuntimeWindowBarrierExport),
    };
}

inline std::vector<std::string> runtime_window_partial_barrier_order(
    std::initializer_list<std::string_view> barrier_ids
) {
    std::vector<std::string> barrier_order;
    barrier_order.reserve(barrier_ids.size());
    for (const auto barrier_id : barrier_ids) {
        barrier_order.emplace_back(barrier_id);
    }
    return barrier_order;
}

inline std::string runtime_window_input_source_snapshot_version(
    const RuntimeWindowActionRequest& request
) {
    if (!runtime_window_is_blank(
            request.clock_domain_metadata.source_snapshot_version)) {
        return request.clock_domain_metadata.source_snapshot_version;
    }
    return request.input_snapshot_version;
}

inline double runtime_window_input_source_time_s(
    const RuntimeWindowActionRequest& request,
    double fallback_source_time_s
) {
    if (request.clock_domain_metadata.has_source_time &&
        runtime_window_has_finite_time(
            request.clock_domain_metadata.source_time_s)) {
        return request.clock_domain_metadata.source_time_s;
    }
    if (runtime_window_has_finite_time(request.action_intent.effective_time_s)) {
        return request.action_intent.effective_time_s;
    }
    return fallback_source_time_s;
}

inline std::string runtime_window_input_target_window_id(
    const RuntimeWindowActionRequest& request,
    const RuntimeWindowSchedulingContext& context
) {
    if (!runtime_window_is_blank(request.clock_domain_metadata.target_window_id)) {
        return request.clock_domain_metadata.target_window_id;
    }
    return context.window_id;
}

inline std::vector<std::string> runtime_window_input_barrier_order(
    const RuntimeWindowActionRequest& request,
    std::initializer_list<std::string_view> fallback_barriers
) {
    if (!request.clock_domain_metadata.barrier_order.empty()) {
        return request.clock_domain_metadata.barrier_order;
    }
    return runtime_window_partial_barrier_order(fallback_barriers);
}

inline std::string runtime_window_input_clock_merge_policy(
    const RuntimeWindowActionRequest& request,
    std::string_view fallback_policy
) {
    if (!runtime_window_is_blank(request.clock_domain_metadata.clock_merge_policy)) {
        return request.clock_domain_metadata.clock_merge_policy;
    }
    return std::string(fallback_policy);
}

inline bool runtime_window_has_requested_export(
    const RuntimeWindowRequest& request
) {
    return request.export_observation || request.export_engagement ||
        request.export_diagnostics;
}

inline std::string runtime_window_default_id(const RuntimeWindowRequest& request) {
    if (!runtime_window_is_blank(request.window_id)) {
        return request.window_id;
    }
    return "window:" + std::to_string(request.world_id) + ":" +
        std::to_string(request.source_time_s);
}

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

inline void runtime_window_push_unique_world_ref(
    std::vector<WorldEntityRef>* refs,
    std::uint64_t world_index,
    std::uint64_t entity_id
) {
    if (refs == nullptr) {
        return;
    }
    const auto duplicate = std::find_if(
        refs->begin(),
        refs->end(),
        [world_index, entity_id](const WorldEntityRef& ref) {
            return ref.world_index == world_index && ref.entity_id == entity_id;
        }
    );
    if (duplicate == refs->end()) {
        refs->push_back(WorldEntityRef{
            .world_index = world_index,
            .entity_id = entity_id,
        });
    }
}

inline void runtime_window_push_unique_engagement_ref(
    std::vector<EngagementEntityRef>* refs,
    std::uint64_t world_index,
    std::uint64_t entity_id
) {
    if (refs == nullptr) {
        return;
    }
    const auto duplicate = std::find_if(
        refs->begin(),
        refs->end(),
        [world_index, entity_id](const EngagementEntityRef& ref) {
            return ref.world_index == world_index && ref.entity_id == entity_id;
        }
    );
    if (duplicate == refs->end()) {
        refs->push_back(EngagementEntityRef{
            .world_index = world_index,
            .entity_id = entity_id,
        });
    }
}

inline ObservationBatchRequest resolve_runtime_window_observation_request(
    const RuntimeWindowRequest& request,
    const std::vector<RuntimeWindowInputRecord>& accepted_inputs
) {
    ObservationBatchRequest observation_request = request.observation_request;
    if (!observation_request.refs.empty()) {
        return observation_request;
    }
    for (const auto& record : accepted_inputs) {
        runtime_window_push_unique_world_ref(
            &observation_request.refs,
            record.request.action_intent.target.world_index,
            record.request.action_intent.target.entity_id
        );
    }
    return observation_request;
}

inline EngagementBatchRequest resolve_runtime_window_engagement_request(
    const RuntimeWindowRequest& request,
    const std::vector<RuntimeWindowInputRecord>& accepted_inputs
) {
    EngagementBatchRequest engagement_request = request.engagement_request;
    if (engagement_request.refs.empty()) {
        for (const auto& record : accepted_inputs) {
            runtime_window_push_unique_engagement_ref(
                &engagement_request.refs,
                record.request.action_intent.target.world_index,
                record.request.action_intent.target.entity_id
            );
        }
    }
    if (engagement_request.trace_ids.empty()) {
        engagement_request.trace_ids.reserve(engagement_request.refs.size());
        for (std::size_t index = 0; index < engagement_request.refs.size(); ++index) {
            engagement_request.trace_ids.push_back(static_cast<std::uint64_t>(index + 1));
        }
    }
    return engagement_request;
}

inline void runtime_window_advance_barrier(
    RuntimeWindowSchedulingContext* context,
    std::vector<RuntimeWindowBarrierRecord>* barrier_trace,
    std::string_view barrier_id,
    std::string_view node_id = {}
) {
    if (context == nullptr || barrier_trace == nullptr) {
        return;
    }
    ++context->barrier_sequence;
    context->current_barrier_id = std::string(barrier_id);
    barrier_trace->push_back(RuntimeWindowBarrierRecord{
        .sequence = context->barrier_sequence,
        .barrier_id = std::string(barrier_id),
        .node_id = std::string(node_id),
    });
}

inline RuntimeWindowNodeExecutionRecord runtime_window_base_node_execution_record(
    const runtime::scheduler::StageNodeManifest& manifest,
    std::size_t visible_input_count
) {
    return RuntimeWindowNodeExecutionRecord{
        .node_id = manifest.node_id,
        .clock_domain = manifest.clock_domain,
        .read_snapshot_policy = manifest.read_snapshot_policy,
        .write_commit_policy = manifest.write_commit_policy,
        .visible_input_count = visible_input_count,
        .execution_state = "skipped",
        .target_window_id = {},
    };
}

inline RuntimeWindowNodeExecutionRecord runtime_window_fire_control_launch_record(
    const runtime::scheduler::StageNodeManifest& manifest,
    const RuntimeWindowSchedulingContext& context
) {
    RuntimeWindowNodeExecutionRecord record =
        runtime_window_base_node_execution_record(
            manifest,
            context.accepted_inputs.size()
        );
    record.decision_barrier_id = std::string(kRuntimeWindowBarrierInputInjection);
    record.target_window_id = context.window_id;
    record.barrier_order =
        runtime_window_partial_barrier_order({kRuntimeWindowBarrierInputInjection});

    if (!context.accepted_inputs.empty()) {
        const auto& trigger = context.accepted_inputs.front().request;
        record.execution_state = "executed";
        record.decision_reason =
            "maintained fire-control cadence triggered by accepted window input";
        record.trigger_source =
            "input_injection:" + trigger.action_intent.source_id;
        record.clock_merge_policy = runtime_window_input_clock_merge_policy(
            trigger,
            "nested_slot"
        );
        record.source_snapshot_version =
            runtime_window_input_source_snapshot_version(trigger);
        record.source_time_s =
            runtime_window_input_source_time_s(trigger, context.source_time_s);
        record.target_window_id =
            runtime_window_input_target_window_id(trigger, context);
        record.barrier_order = runtime_window_input_barrier_order(
            trigger,
            {kRuntimeWindowBarrierInputInjection}
        );
        return record;
    }

    if (!context.rejected_inputs.empty()) {
        const auto& rejected = context.rejected_inputs.front().request;
        record.execution_state = "rejected";
        record.decision_reason =
            "maintained fire-control cadence rejected candidate trigger input";
        record.trigger_source =
            "input_injection_rejected:" + rejected.action_intent.source_id;
        record.clock_merge_policy = runtime_window_input_clock_merge_policy(
            rejected,
            "reject_on_ambiguous_order"
        );
        record.source_snapshot_version =
            runtime_window_input_source_snapshot_version(rejected);
        record.source_time_s =
            runtime_window_input_source_time_s(rejected, context.source_time_s);
        record.target_window_id =
            runtime_window_input_target_window_id(rejected, context);
        record.barrier_order = runtime_window_input_barrier_order(
            rejected,
            {kRuntimeWindowBarrierInputInjection}
        );
        return record;
    }

    if (!context.deferred_inputs.empty() || !context.expired_inputs.empty()) {
        const auto& deferred = !context.deferred_inputs.empty()
            ? context.deferred_inputs.front().request
            : context.expired_inputs.front().request;
        record.execution_state = "deferred";
        record.decision_reason =
            "maintained fire-control cadence did not fire in the current window";
        record.trigger_source =
            "input_injection_deferred:" + deferred.action_intent.source_id;
        record.clock_merge_policy = runtime_window_input_clock_merge_policy(
            deferred,
            "defer_to_next_window"
        );
        record.source_snapshot_version =
            runtime_window_input_source_snapshot_version(deferred);
        record.source_time_s =
            runtime_window_input_source_time_s(deferred, context.source_time_s);
        record.target_window_id =
            runtime_window_input_target_window_id(deferred, context);
        record.barrier_order = runtime_window_input_barrier_order(
            deferred,
            {kRuntimeWindowBarrierInputInjection}
        );
        return record;
    }

    record.decision_reason =
        "maintained fire-control cadence had no visible trigger at input_injection";
    record.trigger_source = "input_injection:none";
    record.clock_merge_policy = "nested_slot";
    record.source_time_s = context.source_time_s;
    return record;
}

inline RuntimeWindowNodeExecutionRecord runtime_window_effects_damage_record(
    const runtime::scheduler::StageNodeManifest& manifest,
    const RuntimeWindowSchedulingContext& context,
    const RuntimeWindowNodeExecutionRecord& fire_control_record
) {
    RuntimeWindowNodeExecutionRecord record =
        runtime_window_base_node_execution_record(manifest, 0U);
    record.decision_barrier_id = std::string(kRuntimeWindowBarrierWindowCommit);
    record.target_window_id = context.window_id;
    record.barrier_order = runtime_window_partial_barrier_order({
        kRuntimeWindowBarrierInputInjection,
        kRuntimeWindowBarrierWindowCommit,
    });
    record.source_time_s = context.source_time_s;

    if (fire_control_record.execution_state == "executed") {
        record.execution_state = "executed";
        record.decision_reason =
            "maintained effects/damage cadence triggered by the fire-control launch chain";
        record.trigger_source =
            "p7.fire_control_launch.v1:fire_control_and_launch";
        record.clock_merge_policy = "enqueue_event";
        record.source_snapshot_version =
            fire_control_record.source_snapshot_version;
        record.source_time_s = fire_control_record.source_time_s;
        return record;
    }

    if (fire_control_record.execution_state == "rejected") {
        record.execution_state = "rejected";
        record.decision_reason =
            "maintained effects/damage cadence rejected because upstream fire-control trigger failed closed";
        record.trigger_source =
            "p7.fire_control_launch.v1:rejected_upstream_trigger";
        record.clock_merge_policy = "reject_on_ambiguous_order";
        record.source_snapshot_version =
            fire_control_record.source_snapshot_version;
        record.source_time_s = fire_control_record.source_time_s;
        return record;
    }

    if (fire_control_record.execution_state == "deferred") {
        record.execution_state = "deferred";
        record.decision_reason =
            "maintained effects/damage cadence deferred with the upstream fire-control trigger";
        record.trigger_source =
            "p7.fire_control_launch.v1:deferred_upstream_trigger";
        record.clock_merge_policy = "defer_to_next_window";
        record.source_snapshot_version =
            fire_control_record.source_snapshot_version;
        record.source_time_s = fire_control_record.source_time_s;
        return record;
    }

    record.decision_reason =
        "maintained effects/damage cadence had no launch/effects trigger in the current window";
    record.trigger_source = "window_commit:none";
    record.clock_merge_policy = "enqueue_event";
    return record;
}

inline RuntimeWindowNodeExecutionRecord runtime_window_observation_export_record(
    const runtime::scheduler::StageNodeManifest& manifest,
    const RuntimeWindowRequest& request,
    const RuntimeWindowSchedulingContext& context,
    const RuntimeWindowCoordinatorCallbacks& callbacks
) {
    RuntimeWindowNodeExecutionRecord record =
        runtime_window_base_node_execution_record(manifest, 0U);
    record.decision_barrier_id = std::string(kRuntimeWindowBarrierExport);
    record.target_window_id = context.window_id;
    record.barrier_order =
        runtime_window_partial_barrier_order(
            {kRuntimeWindowBarrierWindowCommit, kRuntimeWindowBarrierExport}
        );
    record.clock_merge_policy = "nested_slot";
    record.source_time_s = context.source_time_s;

    if (!runtime_window_has_requested_export(request)) {
        record.decision_reason =
            "maintained observation/export cadence skipped because no facade export was requested";
        record.trigger_source = "export:none";
        return record;
    }

    std::vector<std::string> missing_callbacks;
    if (request.export_observation && !callbacks.export_observation_packet) {
        missing_callbacks.push_back("observation");
    }
    if (request.export_engagement && !callbacks.export_engagement_event_packet) {
        missing_callbacks.push_back("engagement");
    }
    if (request.export_diagnostics && !callbacks.export_diagnostics_traces) {
        missing_callbacks.push_back("diagnostics");
    }
    if (!missing_callbacks.empty()) {
        record.execution_state = "rejected";
        record.decision_reason =
            "maintained observation/export cadence rejected because one or more requested export callbacks are missing";
        record.trigger_source = "export:missing_callback";
        record.clock_merge_policy = "reject_on_ambiguous_order";
        return record;
    }

    record.execution_state = "executed";
    record.decision_reason =
        "maintained observation/export cadence triggered by the export barrier";
    record.trigger_source = "export:maintained_facade_export";
    return record;
}

inline std::string runtime_window_export_snapshot_evidence(
    const RuntimeWindowResult& result
) {
    if (result.observation_packet.snapshot_version != 0) {
        return "observation_packet:" +
            std::to_string(result.observation_packet.snapshot_version);
    }
    if (result.engagement_packet.snapshot_version != 0) {
        return "engagement_packet:" +
            std::to_string(result.engagement_packet.snapshot_version);
    }
    return {};
}

inline RuntimeWindowResult execute_runtime_window(
    const RuntimeWindowRequest& request,
    const RuntimeWindowCoordinatorCallbacks& callbacks
) {
    RuntimeWindowResult result{};
    result.context = classify_runtime_window_inputs(request);
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
        runtime::scheduler::enumerate_wp10_maintained_stage_node_manifests();
    result.executed_nodes.reserve(manifests.size());

    const auto* fire_control_manifest =
        runtime::scheduler::find_stage_node_manifest("p7.fire_control_launch.v1");
    if (fire_control_manifest != nullptr) {
        result.executed_nodes.push_back(runtime_window_fire_control_launch_record(
            *fire_control_manifest,
            result.context
        ));
    }

    const auto* effects_damage_manifest =
        runtime::scheduler::find_stage_node_manifest("p9.effects_damage.v1");
    if (effects_damage_manifest != nullptr && !result.executed_nodes.empty()) {
        result.executed_nodes.push_back(runtime_window_effects_damage_record(
            *effects_damage_manifest,
            result.context,
            result.executed_nodes.front()
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
            callbacks
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
