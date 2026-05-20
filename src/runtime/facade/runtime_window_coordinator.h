#pragma once

#include <algorithm>
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
    for (const auto* manifest : manifests) {
        if (manifest == nullptr) {
            continue;
        }
        const bool reads_post_injection =
            manifest->read_snapshot_policy ==
            runtime::scheduler::kReadSnapshotPolicyPostInjection;
        result.executed_nodes.push_back(RuntimeWindowNodeExecutionRecord{
            .node_id = manifest->node_id,
            .read_snapshot_policy = manifest->read_snapshot_policy,
            .write_commit_policy = manifest->write_commit_policy,
            .visible_input_count = reads_post_injection ? result.injected_inputs.size() : 0U,
        });
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

    const ObservationBatchRequest observation_request =
        resolve_runtime_window_observation_request(request, result.injected_inputs);
    const EngagementBatchRequest engagement_request =
        resolve_runtime_window_engagement_request(request, result.injected_inputs);

    if (request.export_observation && callbacks.export_observation_packet) {
        result.observation_packet =
            callbacks.export_observation_packet(observation_request);
    }
    if (request.export_engagement && callbacks.export_engagement_event_packet) {
        result.engagement_packet =
            callbacks.export_engagement_event_packet(engagement_request);
    }
    if (request.export_diagnostics && callbacks.export_diagnostics_traces) {
        result.diagnostics_traces =
            callbacks.export_diagnostics_traces(engagement_request);
    }

    runtime_window_advance_barrier(
        &result.context,
        &result.barrier_trace,
        kRuntimeWindowBarrierExport
    );
    return result;
}
