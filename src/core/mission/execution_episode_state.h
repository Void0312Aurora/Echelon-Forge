#pragma once

#include <cstdint>
#include <string>
#include <vector>

#include "components/command/mission_command.h"
#include "core/geometry/spatial_query_runtime.h"

struct ExecutionEpisodeState {
    std::uint64_t agent_id = 0;
    int step_count = 0;

    bool has_mission_command = false;
    MissionCommand mission_command{};
    bool has_mission_command_json = false;
    std::string mission_command_json;

    std::vector<SpatialRouteWaypoint> route_waypoints;
    int waypoint_index = 0;
    bool has_waypoint_prev_dist_m = false;
    double waypoint_prev_dist_m = 0.0;
    double waypoint_total_route_length_m = 0.0;
    double waypoint_leg_origin_x_m = 0.0;
    double waypoint_leg_origin_y_m = 0.0;

    double prev_altitude_m = 0.0;
    double prev_ias_mps = 0.0;
    bool liftoff_awarded = false;
    bool gear_bonus_awarded = false;
    int off_runway_steps = 0;

    bool has_approach_prev_dme_m = false;
    double approach_prev_dme_m = 0.0;
    bool has_approach_prev_loc_abs = false;
    double approach_prev_loc_abs = 0.0;
    bool has_approach_prev_gs_abs = false;
    double approach_prev_gs_abs = 0.0;

    bool has_post_waypoint_transition_json = false;
    std::string post_waypoint_transition_json;
    std::string mission_phase_name = "idle";

    bool has_cached_route_ref_id = false;
    std::uint64_t cached_route_ref_id = 0;

    std::string last_termination_reason = "idle";
    double last_reward_total = 0.0;
    std::string last_reward_breakdown_json = "{}";
};

bool execution_episode_states_equivalent(
    const ExecutionEpisodeState& lhs,
    const ExecutionEpisodeState& rhs
);
