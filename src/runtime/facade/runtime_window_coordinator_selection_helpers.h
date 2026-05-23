#pragma once

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <vector>

// Internal helper split for runtime_window_coordinator.h.
// Include this companion after runtime_window_coordinator_helpers.h.

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

inline const RuntimeWindowActionRequest* runtime_window_pick_primary_trigger_request(
    const RuntimeWindowSchedulingContext& context
) {
    if (!context.accepted_inputs.empty()) {
        return &context.accepted_inputs.front().request;
    }
    if (!context.rejected_inputs.empty()) {
        return &context.rejected_inputs.front().request;
    }
    if (!context.deferred_inputs.empty()) {
        return &context.deferred_inputs.front().request;
    }
    if (!context.expired_inputs.empty()) {
        return &context.expired_inputs.front().request;
    }
    return nullptr;
}
