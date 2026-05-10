#pragma once

#include "core/mission/execution_episode_batch_prepare.h"

namespace episode_controller_detail {

struct PostWaypointTransitionResolution {
    bool activated = false;
    bool pending = false;
    bool structural_state_changed = false;
    double transition_reward_bonus = 0.0;
};

void apply_pre_step_behavior_updates(
    StepEvaluationBatchEnvState* env_state,
    ExecutionEpisodeState* state
);

PostWaypointTransitionResolution maybe_apply_post_waypoint_transition(
    const StepEvaluationBatchEnvState& env_state,
    const ExecutionEpisodeRuntimeInputs& runtime_inputs,
    ExecutionEpisodeState* state
);

}  // namespace episode_controller_detail
