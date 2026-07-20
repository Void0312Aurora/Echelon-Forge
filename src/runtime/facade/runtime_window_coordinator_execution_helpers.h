#pragma once

#include <string>
#include <string_view>
#include <utility>
#include <vector>

// Internal helper split for runtime_window_coordinator.h.
// Include this companion after the cadence-trace companion.

inline void runtime_window_advance_barrier(RuntimeWindowSchedulingContext *context,
                                           std::vector<RuntimeWindowBarrierRecord> *barrier_trace,
                                           std::string_view barrier_id,
                                           std::string_view node_id = {}) {
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

inline RuntimeWindowNodeExecutionRecord
runtime_window_base_node_execution_record(const runtime::scheduler::StageNodeManifest &manifest,
                                          std::size_t visible_input_count) {
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
    const runtime::scheduler::StageNodeManifest &manifest,
    const RuntimeWindowSchedulingContext &context,
    const std::vector<RuntimeWindowCadenceTraceRecord> &cadence_trace) {
    RuntimeWindowNodeExecutionRecord record =
        runtime_window_base_node_execution_record(manifest, context.accepted_inputs.size());
    record.decision_barrier_id = std::string(kRuntimeWindowBarrierInputInjection);
    record.target_window_id = context.window_id;
    record.barrier_order =
        runtime_window_partial_barrier_order({kRuntimeWindowBarrierInputInjection});

    const RuntimeWindowCadenceTraceRecord *control_it =
        runtime_window_preferred_cadence_trace_record(
            cadence_trace, kRuntimeWindowCadenceDomainControl, "fire_control_launch.v1");
    if (control_it != nullptr) {
        record.execution_state = control_it->decision == "triggered"      ? "executed"
                                 : control_it->decision == "held"         ? "held"
                                 : control_it->decision == "interpolated" ? "diagnostics_only"
                                                                          : control_it->decision;
        record.decision_reason = control_it->decision_reason;
        if (control_it->source.empty() || control_it->source == "none") {
            record.trigger_source = "input_injection:none";
        } else if (control_it->decision == "rejected") {
            record.trigger_source = "input_injection_rejected:" + control_it->source;
        } else if (control_it->decision == "deferred") {
            record.trigger_source = "input_injection_deferred:" + control_it->source;
        } else if (control_it->decision == "expired") {
            record.trigger_source = "input_injection_expired:" + control_it->source;
        } else {
            record.trigger_source = "input_injection:" + control_it->source;
        }
        record.clock_merge_policy =
            control_it->clock_merge_policy.empty() ? "nested_slot" : control_it->clock_merge_policy;
        const RuntimeWindowActionRequest *primary_request =
            runtime_window_pick_primary_trigger_request(context);
        if (primary_request != nullptr) {
            record.source_snapshot_version =
                runtime_window_input_source_snapshot_version(*primary_request);
            record.source_time_s =
                runtime_window_input_source_time_s(*primary_request, context.source_time_s);
            record.target_window_id =
                runtime_window_input_target_window_id(*primary_request, context);
            record.barrier_order = runtime_window_input_barrier_order(
                *primary_request, {kRuntimeWindowBarrierInputInjection});
        } else {
            record.source_time_s = context.source_time_s;
        }
        return record;
    }

    if (!context.accepted_inputs.empty()) {
        const auto &trigger = context.accepted_inputs.front().request;
        record.execution_state = "executed";
        record.decision_reason =
            "maintained fire-control cadence triggered by accepted window input";
        record.trigger_source = "input_injection:" + trigger.action_intent.source_id;
        record.clock_merge_policy = runtime_window_input_clock_merge_policy(trigger, "nested_slot");
        record.source_snapshot_version = runtime_window_input_source_snapshot_version(trigger);
        record.source_time_s = runtime_window_input_source_time_s(trigger, context.source_time_s);
        record.target_window_id = runtime_window_input_target_window_id(trigger, context);
        record.barrier_order =
            runtime_window_input_barrier_order(trigger, {kRuntimeWindowBarrierInputInjection});
        return record;
    }

    if (!context.rejected_inputs.empty()) {
        const auto &rejected = context.rejected_inputs.front().request;
        record.execution_state = "rejected";
        record.decision_reason = "maintained fire-control cadence rejected candidate trigger input";
        record.trigger_source = "input_injection_rejected:" + rejected.action_intent.source_id;
        record.clock_merge_policy =
            runtime_window_input_clock_merge_policy(rejected, "reject_on_ambiguous_order");
        record.source_snapshot_version = runtime_window_input_source_snapshot_version(rejected);
        record.source_time_s = runtime_window_input_source_time_s(rejected, context.source_time_s);
        record.target_window_id = runtime_window_input_target_window_id(rejected, context);
        record.barrier_order =
            runtime_window_input_barrier_order(rejected, {kRuntimeWindowBarrierInputInjection});
        return record;
    }

    if (!context.deferred_inputs.empty() || !context.expired_inputs.empty()) {
        const bool expired = context.deferred_inputs.empty() && !context.expired_inputs.empty();
        const auto &deferred = !context.deferred_inputs.empty()
                                   ? context.deferred_inputs.front().request
                                   : context.expired_inputs.front().request;
        record.execution_state = expired ? "expired" : "deferred";
        record.decision_reason =
            expired ? "maintained fire-control cadence expired before the current window"
                    : "maintained fire-control cadence did not fire in the current window";
        record.trigger_source =
            std::string(expired ? "input_injection_expired:" : "input_injection_deferred:") +
            deferred.action_intent.source_id;
        record.clock_merge_policy = runtime_window_input_clock_merge_policy(
            deferred, expired ? "drop" : "defer_to_next_window");
        record.source_snapshot_version = runtime_window_input_source_snapshot_version(deferred);
        record.source_time_s = runtime_window_input_source_time_s(deferred, context.source_time_s);
        record.target_window_id = runtime_window_input_target_window_id(deferred, context);
        record.barrier_order =
            runtime_window_input_barrier_order(deferred, {kRuntimeWindowBarrierInputInjection});
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
    const runtime::scheduler::StageNodeManifest &manifest,
    const RuntimeWindowSchedulingContext &context,
    const RuntimeWindowNodeExecutionRecord &fire_control_record,
    const std::vector<RuntimeWindowCadenceTraceRecord> &cadence_trace) {
    RuntimeWindowNodeExecutionRecord record =
        runtime_window_base_node_execution_record(manifest, 0U);
    record.decision_barrier_id = std::string(kRuntimeWindowBarrierWindowCommit);
    record.target_window_id = context.window_id;
    record.barrier_order = runtime_window_partial_barrier_order({
        kRuntimeWindowBarrierInputInjection,
        kRuntimeWindowBarrierWindowCommit,
    });
    record.source_time_s = context.source_time_s;

    const RuntimeWindowCadenceTraceRecord *physics_it =
        runtime_window_preferred_cadence_trace_record(
            cadence_trace, kRuntimeWindowCadenceDomainPhysics, "effects_damage.v1");
    if (physics_it != nullptr) {
        record.execution_state =
            physics_it->decision == "triggered" ? "executed" : physics_it->decision;
        record.decision_reason = physics_it->decision_reason;
        if (physics_it->source == "none") {
            record.trigger_source = "window_commit:none";
        } else if (physics_it->decision == "rejected") {
            record.trigger_source = physics_it->source + ":rejected_upstream_trigger";
        } else if (physics_it->decision == "deferred") {
            record.trigger_source = physics_it->source + ":deferred_upstream_trigger";
        } else if (physics_it->decision == "expired") {
            record.trigger_source = physics_it->source + ":expired_upstream_trigger";
        } else {
            record.trigger_source = physics_it->source + ":fire_control_and_launch";
        }
        record.clock_merge_policy = physics_it->clock_merge_policy.empty()
                                        ? "enqueue_event"
                                        : physics_it->clock_merge_policy;
        record.source_snapshot_version = fire_control_record.source_snapshot_version;
        record.source_time_s = fire_control_record.source_time_s;
        return record;
    }

    if (fire_control_record.execution_state == "executed") {
        record.execution_state = "executed";
        record.decision_reason =
            "maintained effects/damage cadence triggered by the fire-control launch chain";
        record.trigger_source = "fire_control_launch.v1:fire_control_and_launch";
        record.clock_merge_policy = "enqueue_event";
        record.source_snapshot_version = fire_control_record.source_snapshot_version;
        record.source_time_s = fire_control_record.source_time_s;
        return record;
    }

    if (fire_control_record.execution_state == "rejected") {
        record.execution_state = "rejected";
        record.decision_reason = "maintained effects/damage cadence rejected because upstream "
                                 "fire-control trigger failed closed";
        record.trigger_source = "fire_control_launch.v1:rejected_upstream_trigger";
        record.clock_merge_policy = "reject_on_ambiguous_order";
        record.source_snapshot_version = fire_control_record.source_snapshot_version;
        record.source_time_s = fire_control_record.source_time_s;
        return record;
    }

    if (fire_control_record.execution_state == "deferred") {
        record.execution_state = "deferred";
        record.decision_reason =
            "maintained effects/damage cadence deferred with the upstream fire-control trigger";
        record.trigger_source = "fire_control_launch.v1:deferred_upstream_trigger";
        record.clock_merge_policy = "defer_to_next_window";
        record.source_snapshot_version = fire_control_record.source_snapshot_version;
        record.source_time_s = fire_control_record.source_time_s;
        return record;
    }

    if (fire_control_record.execution_state == "expired") {
        record.execution_state = "expired";
        record.decision_reason =
            "maintained effects/damage cadence expired with the upstream fire-control trigger";
        record.trigger_source = "fire_control_launch.v1:expired_upstream_trigger";
        record.clock_merge_policy = "drop";
        record.source_snapshot_version = fire_control_record.source_snapshot_version;
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
    const runtime::scheduler::StageNodeManifest &manifest, const RuntimeWindowRequest &request,
    const RuntimeWindowSchedulingContext &context,
    const RuntimeWindowCoordinatorCallbacks &callbacks,
    const std::vector<RuntimeWindowCadenceTraceRecord> &cadence_trace) {
    RuntimeWindowNodeExecutionRecord record =
        runtime_window_base_node_execution_record(manifest, 0U);
    record.decision_barrier_id = std::string(kRuntimeWindowBarrierExport);
    record.target_window_id = context.window_id;
    record.barrier_order = runtime_window_partial_barrier_order(
        {kRuntimeWindowBarrierWindowCommit, kRuntimeWindowBarrierExport});
    record.clock_merge_policy = "nested_slot";
    record.source_time_s = context.source_time_s;

    const RuntimeWindowCadenceTraceRecord *export_it =
        runtime_window_preferred_cadence_trace_record(
            cadence_trace, kRuntimeWindowCadenceDomainExport, "observation_export.v1");
    if (export_it != nullptr) {
        record.execution_state =
            export_it->decision == "triggered" ? "executed" : export_it->decision;
        record.decision_reason = export_it->decision_reason;
        record.trigger_source =
            export_it->source == "export" ? "export:maintained_facade_export" : "export:none";
        record.clock_merge_policy =
            export_it->clock_merge_policy.empty() ? "nested_slot" : export_it->clock_merge_policy;
    }

    if (!runtime_window_has_requested_export(request)) {
        record.decision_reason =
            "maintained observation/export cadence skipped because no facade export was requested";
        record.trigger_source = "export:none";
        return record;
    }

    if (!runtime_window_collect_missing_export_callbacks(request, callbacks).empty()) {
        record.execution_state = "rejected";
        record.decision_reason = "maintained observation/export cadence rejected because one or "
                                 "more requested export callbacks are missing";
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
