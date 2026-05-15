#pragma once

#include <string>

#include "core/mission/runtime/execution_episode_runtime.h"

namespace episode_controller_detail {

std::string build_episode_reward_breakdown_json(
    const ExecutionEpisodeRuntimeInputs& runtime_inputs,
    const ExecutionEpisodeRuntimeProducts& products,
    double reward_total,
    bool waypoint_arrived,
    bool had_post_waypoint_transition_before,
    double phase_transition_bonus
);

}  // namespace episode_controller_detail
