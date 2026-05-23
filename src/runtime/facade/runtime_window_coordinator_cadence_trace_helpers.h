#pragma once

#include <cstdint>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

// Internal helper split for runtime_window_coordinator.h.
// Include this companion after selection and callback companions.

inline void runtime_window_append_cadence_trace(
    std::vector<RuntimeWindowCadenceTraceRecord>* cadence_trace,
    RuntimeWindowCadenceTraceRecord record
) {
    if (cadence_trace == nullptr) {
        return;
    }
    cadence_trace->push_back(std::move(record));
}

inline int runtime_window_cadence_decision_priority(std::string_view decision) {
    if (decision == "triggered") {
        return 6;
    }
    if (decision == "held") {
        return 5;
    }
    if (decision == "interpolated") {
        return 4;
    }
    if (decision == "rejected") {
        return 3;
    }
    if (decision == "expired") {
        return 2;
    }
    if (decision == "deferred") {
        return 1;
    }
    return 0;
}

inline const RuntimeWindowCadenceTraceRecord* runtime_window_preferred_cadence_trace_record(
    const std::vector<RuntimeWindowCadenceTraceRecord>& cadence_trace,
    std::string_view domain,
    std::string_view node_id
) {
    const RuntimeWindowCadenceTraceRecord* selected = nullptr;
    int selected_priority = -1;
    for (const auto& trace : cadence_trace) {
        if (trace.domain != domain || trace.node_id != node_id) {
            continue;
        }
        const int priority =
            runtime_window_cadence_decision_priority(trace.decision);
        if (selected == nullptr || priority > selected_priority ||
            (priority == selected_priority && trace.tick >= selected->tick)) {
            selected = &trace;
            selected_priority = priority;
        }
    }
    return selected;
}

inline void runtime_window_append_policy_cadence_trace(
    const RuntimeWindowSchedulingContext& context,
    const RuntimeWindowCadenceConfig& cadence_config,
    std::vector<RuntimeWindowCadenceTraceRecord>* cadence_trace
) {
    const RuntimeWindowCadence* policy =
        runtime_window_find_cadence_domain(
            cadence_config,
            kRuntimeWindowCadenceDomainPolicy
        );
    if (policy == nullptr) {
        return;
    }

    RuntimeWindowCadenceTraceRecord record{};
    record.domain = policy->domain;
    record.tick = 0U;
    record.node_id = "policy.selected_slice";
    record.barrier_id = policy->barrier_id;
    record.cadence_merge_policy = policy->merge_policy;
    record.clock_domain = "outer_window";
    record.clock_merge_policy = "nested_slot";
    record.relation = "selected_slice_strict";

    if (!context.accepted_inputs.empty()) {
        const auto& request = context.accepted_inputs.front().request;
        record.decision = "triggered";
        record.decision_reason = "policy boundary accepted the selected-slice trigger";
        record.source = request.action_intent.source_id;
        record.clock_domain = request.clock_domain_metadata.source_clock_domain;
        record.clock_merge_policy =
            runtime_window_input_clock_merge_policy(request, "nested_slot");
        record.relation = request.clock_domain_metadata.relation;
    } else if (!context.rejected_inputs.empty()) {
        const auto& request = context.rejected_inputs.front().request;
        record.decision = "rejected";
        record.decision_reason =
            "policy boundary rejected the selected-slice trigger";
        record.source = request.action_intent.source_id;
        record.clock_domain = request.clock_domain_metadata.source_clock_domain;
        record.clock_merge_policy =
            runtime_window_input_clock_merge_policy(
                request,
                "reject_on_ambiguous_order"
            );
        record.relation = request.clock_domain_metadata.relation;
    } else if (!context.deferred_inputs.empty()) {
        const auto& request = context.deferred_inputs.front().request;
        record.decision = "deferred";
        record.decision_reason =
            "policy boundary deferred the selected-slice trigger into another window";
        record.source = request.action_intent.source_id;
        record.clock_domain = request.clock_domain_metadata.source_clock_domain;
        record.clock_merge_policy =
            runtime_window_input_clock_merge_policy(request, "defer_to_next_window");
        record.relation = request.clock_domain_metadata.relation;
        record.deferred = true;
    } else if (!context.expired_inputs.empty()) {
        const auto& request = context.expired_inputs.front().request;
        record.decision = "expired";
        record.decision_reason =
            "policy boundary expired the selected-slice trigger before the current window";
        record.source = request.action_intent.source_id;
        record.clock_domain = request.clock_domain_metadata.source_clock_domain;
        record.clock_merge_policy =
            runtime_window_input_clock_merge_policy(request, "drop");
        record.relation = request.clock_domain_metadata.relation;
        record.expired = true;
    } else {
        record.decision = "skipped";
        record.decision_reason =
            "policy boundary had no visible trigger in the current selected slice";
        record.source = "none";
    }

    runtime_window_append_cadence_trace(cadence_trace, std::move(record));
}

inline void runtime_window_append_control_cadence_trace(
    const RuntimeWindowSchedulingContext& context,
    const RuntimeWindowCadenceConfig& cadence_config,
    std::vector<RuntimeWindowCadenceTraceRecord>* cadence_trace
) {
    const RuntimeWindowCadence* control =
        runtime_window_find_cadence_domain(
            cadence_config,
            kRuntimeWindowCadenceDomainControl
        );
    if (control == nullptr) {
        return;
    }

    const RuntimeWindowActionRequest* primary_request =
        runtime_window_pick_primary_trigger_request(context);
    ActionHoldPolicy hold_policy{};
    if (primary_request != nullptr && primary_request->cadence_control.enabled) {
        hold_policy = runtime_window_normalized_hold_policy(*primary_request);
    }

    for (std::uint32_t tick = 0; tick < control->tick_count; ++tick) {
        RuntimeWindowCadenceTraceRecord record{};
        record.domain = control->domain;
        record.tick = tick;
        record.node_id = "p7.fire_control_launch.v1";
        record.barrier_id = control->barrier_id;
        record.cadence_merge_policy = control->merge_policy;
        record.clock_domain = "event_driven_or_fire_control_cadence";
        record.clock_merge_policy = "nested_slot";
        record.relation = "selected_slice_strict";

        const double tick_time_s =
            context.source_time_s +
            static_cast<double>(tick) * control->interval_s;

        if (primary_request == nullptr) {
            record.decision = "skipped";
            record.decision_reason =
                "control cadence had no trigger or hold candidate";
            record.source = "none";
            runtime_window_append_cadence_trace(cadence_trace, std::move(record));
            continue;
        }

        record.source = primary_request->action_intent.source_id;
        if (!runtime_window_is_blank(
                primary_request->clock_domain_metadata.source_clock_domain)) {
            record.clock_domain =
                primary_request->clock_domain_metadata.source_clock_domain;
        }
        record.relation = primary_request->clock_domain_metadata.relation;

        if (!context.accepted_inputs.empty()) {
            record.clock_merge_policy =
                runtime_window_input_clock_merge_policy(
                    *primary_request,
                    control->merge_policy
                );
            if (tick == 0U) {
                record.decision = "triggered";
                record.decision_reason =
                    "control cadence consumed the accepted policy trigger";
            } else if (hold_policy.hold_mode == kActionHoldModeHoldLast) {
                if (runtime_window_hold_candidate_expired_at_tick(
                        *primary_request,
                        context.source_time_s,
                        tick_time_s)) {
                    record.decision = "expired";
                    record.decision_reason =
                        "control cadence hold_last evidence expired before this tick";
                    record.expired = true;
                } else {
                    record.decision = "held";
                    record.decision_reason =
                        "control cadence reused hold_last evidence between policy ticks";
                    record.held = true;
                }
            } else if (hold_policy.hold_mode == kActionHoldModeInterpolate) {
                if (runtime_window_hold_candidate_expired_at_tick(
                        *primary_request,
                        context.source_time_s,
                        tick_time_s)) {
                    record.decision = "expired";
                    record.decision_reason =
                        "control cadence interpolation evidence expired before this tick";
                    record.expired = true;
                } else {
                    record.decision = "interpolated";
                    record.decision_reason =
                        "control cadence produced diagnostics-only interpolation evidence";
                    record.diagnostics_only = true;
                }
            } else {
                record.clock_merge_policy = "nested_slot";
                record.decision = "skipped";
                record.decision_reason =
                    "control cadence had no maintained hold policy for the second tick";
            }
        } else if (!context.rejected_inputs.empty()) {
            record.clock_merge_policy = "reject_on_ambiguous_order";
            record.decision = "rejected";
            record.decision_reason =
                "control cadence failed closed because the policy trigger was rejected";
        } else if (!context.deferred_inputs.empty()) {
            record.clock_merge_policy = "defer_to_next_window";
            record.decision = "deferred";
            record.decision_reason =
                "control cadence deferred because the policy trigger belongs to another window";
            record.deferred = true;
        } else if (!context.expired_inputs.empty()) {
            record.clock_merge_policy = "drop";
            record.decision = "expired";
            record.decision_reason =
                "control cadence could not consume the trigger because it had expired";
            record.expired = true;
        } else {
            record.clock_merge_policy = "nested_slot";
            record.decision = "skipped";
            record.decision_reason =
                "control cadence had no visible trigger";
        }

        runtime_window_append_cadence_trace(cadence_trace, std::move(record));
    }
}

inline void runtime_window_append_physics_cadence_trace(
    const RuntimeWindowSchedulingContext& context,
    const RuntimeWindowCadenceConfig& cadence_config,
    std::vector<RuntimeWindowCadenceTraceRecord>* cadence_trace
) {
    const RuntimeWindowCadence* physics =
        runtime_window_find_cadence_domain(
            cadence_config,
            kRuntimeWindowCadenceDomainPhysics
        );
    if (physics == nullptr) {
        return;
    }

    const bool upstream_ready = !context.accepted_inputs.empty();
    const bool upstream_rejected = !context.rejected_inputs.empty();
    const bool upstream_deferred = !context.deferred_inputs.empty();
    const bool upstream_expired = !context.expired_inputs.empty();

    for (std::uint32_t tick = 0; tick < physics->tick_count; ++tick) {
        RuntimeWindowCadenceTraceRecord record{};
        record.domain = physics->domain;
        record.tick = tick;
        record.node_id = "p9.effects_damage.v1";
        record.barrier_id = physics->barrier_id;
        record.clock_domain = "event_driven_effects_resolution";
        record.clock_merge_policy = "enqueue_event";
        record.cadence_merge_policy = physics->merge_policy;
        record.relation = "selected_slice_strict";

        if (upstream_ready) {
            record.decision = "triggered";
            record.decision_reason =
                "physics cadence advanced inside the selected 100ms window";
            record.source = "p7.fire_control_launch.v1";
        } else if (upstream_rejected) {
            record.decision = "rejected";
            record.decision_reason =
                "physics cadence failed closed with the rejected upstream trigger";
            record.source = "p7.fire_control_launch.v1";
        } else if (upstream_deferred) {
            record.decision = "deferred";
            record.decision_reason =
                "physics cadence deferred because the upstream trigger is in another window";
            record.source = "p7.fire_control_launch.v1";
            record.deferred = true;
        } else if (upstream_expired) {
            record.decision = "expired";
            record.decision_reason =
                "physics cadence dropped because the upstream trigger had already expired";
            record.source = "p7.fire_control_launch.v1";
            record.expired = true;
        } else {
            record.decision = "skipped";
            record.decision_reason =
                "physics cadence had no upstream launch/effects trigger";
            record.source = "none";
        }

        runtime_window_append_cadence_trace(cadence_trace, std::move(record));
    }
}

inline void runtime_window_append_export_cadence_trace(
    const RuntimeWindowRequest& request,
    const RuntimeWindowCadenceConfig& cadence_config,
    const RuntimeWindowCoordinatorCallbacks& callbacks,
    std::vector<RuntimeWindowCadenceTraceRecord>* cadence_trace
) {
    const RuntimeWindowCadence* export_cadence =
        runtime_window_find_cadence_domain(
            cadence_config,
            kRuntimeWindowCadenceDomainExport
        );
    if (export_cadence == nullptr) {
        return;
    }

    RuntimeWindowCadenceTraceRecord record{};
    record.domain = export_cadence->domain;
    record.tick = 0U;
    record.node_id = "p10.observation_export.v1";
    record.barrier_id = export_cadence->barrier_id;
    record.clock_domain = "window_export";
    record.clock_merge_policy = "nested_slot";
    record.cadence_merge_policy = export_cadence->merge_policy;
    record.relation = "selected_slice_strict";
    record.source = "export";

    if (!runtime_window_has_requested_export(request)) {
        record.decision = "skipped";
        record.decision_reason =
            "export cadence skipped because no facade export was requested";
        runtime_window_append_cadence_trace(cadence_trace, std::move(record));
        return;
    }

    if (!runtime_window_collect_missing_export_callbacks(request, callbacks).empty()) {
        record.decision = "rejected";
        record.decision_reason =
            "export cadence rejected because one or more export callbacks are missing";
        runtime_window_append_cadence_trace(cadence_trace, std::move(record));
        return;
    }

    record.decision = "triggered";
    record.decision_reason =
        "export cadence emitted the selected-slice facade packets";
    runtime_window_append_cadence_trace(cadence_trace, std::move(record));
}

inline std::vector<RuntimeWindowCadenceTraceRecord>
build_runtime_window_cadence_trace(
    const RuntimeWindowRequest& request,
    const RuntimeWindowSchedulingContext& context,
    const RuntimeWindowCadenceConfig& cadence_config,
    const RuntimeWindowCoordinatorCallbacks& callbacks
) {
    std::vector<RuntimeWindowCadenceTraceRecord> cadence_trace;
    cadence_trace.reserve(16U);
    runtime_window_append_policy_cadence_trace(
        context,
        cadence_config,
        &cadence_trace
    );
    runtime_window_append_control_cadence_trace(
        context,
        cadence_config,
        &cadence_trace
    );
    runtime_window_append_physics_cadence_trace(
        context,
        cadence_config,
        &cadence_trace
    );
    runtime_window_append_export_cadence_trace(
        request,
        cadence_config,
        callbacks,
        &cadence_trace
    );
    return cadence_trace;
}
