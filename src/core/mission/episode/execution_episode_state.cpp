#include "core/mission/episode/execution_episode_state.h"

namespace {

bool mission_commands_equal(const MissionCommand& lhs, const MissionCommand& rhs) {
    const auto lhs_core = mission_command_shared_core_directive(lhs);
    const auto rhs_core = mission_command_shared_core_directive(rhs);
    const auto lhs_recovery = mission_command_air_recovery_directive(lhs);
    const auto rhs_recovery = mission_command_air_recovery_directive(rhs);
    const auto lhs_takeoff = mission_command_air_takeoff_directive(lhs);
    const auto rhs_takeoff = mission_command_air_takeoff_directive(rhs);
    const auto lhs_formation = mission_command_air_formation_directive(lhs);
    const auto rhs_formation = mission_command_air_formation_directive(rhs);
    const auto lhs_stationing = mission_command_naval_stationing_directive(lhs);
    const auto rhs_stationing = mission_command_naval_stationing_directive(rhs);
    const auto lhs_embarked_helo = mission_command_naval_embarked_helo_directive(lhs);
    const auto rhs_embarked_helo = mission_command_naval_embarked_helo_directive(rhs);
    const auto lhs_ground_static_task =
        mission_command_ground_static_task_directive(lhs);
    const auto rhs_ground_static_task =
        mission_command_ground_static_task_directive(rhs);

    return lhs_core == rhs_core &&
        lhs_stationing == rhs_stationing &&
        lhs_embarked_helo == rhs_embarked_helo &&
        lhs_ground_static_task == rhs_ground_static_task &&
        lhs_recovery == rhs_recovery &&
        lhs_takeoff == rhs_takeoff &&
        lhs_formation == rhs_formation;
}

bool spatial_route_waypoints_equal(const SpatialRouteWaypoint& lhs, const SpatialRouteWaypoint& rhs) {
    return lhs.x_m == rhs.x_m &&
        lhs.y_m == rhs.y_m &&
        lhs.z_m == rhs.z_m &&
        lhs.radius_m == rhs.radius_m &&
        lhs.altitude_m == rhs.altitude_m &&
        lhs.speed_mps == rhs.speed_mps &&
        lhs.waypoint_mode == rhs.waypoint_mode;
}

bool spatial_route_waypoint_vectors_equal(
    const std::vector<SpatialRouteWaypoint>& lhs,
    const std::vector<SpatialRouteWaypoint>& rhs
) {
    if (lhs.size() != rhs.size()) {
        return false;
    }
    for (std::size_t i = 0; i < lhs.size(); ++i) {
        if (!spatial_route_waypoints_equal(lhs[i], rhs[i])) {
            return false;
        }
    }
    return true;
}

}  // namespace

bool execution_episode_states_equivalent(
    const ExecutionEpisodeState& lhs,
    const ExecutionEpisodeState& rhs
) {
    return lhs.agent_id == rhs.agent_id &&
        lhs.step_count == rhs.step_count &&
        lhs.has_mission_command == rhs.has_mission_command &&
        mission_commands_equal(lhs.mission_command, rhs.mission_command) &&
        lhs.has_mission_command_json == rhs.has_mission_command_json &&
        lhs.mission_command_json == rhs.mission_command_json &&
        spatial_route_waypoint_vectors_equal(lhs.route_waypoints, rhs.route_waypoints) &&
        lhs.waypoint_index == rhs.waypoint_index &&
        lhs.has_waypoint_prev_dist_m == rhs.has_waypoint_prev_dist_m &&
        lhs.waypoint_prev_dist_m == rhs.waypoint_prev_dist_m &&
        lhs.waypoint_total_route_length_m == rhs.waypoint_total_route_length_m &&
        lhs.waypoint_leg_origin_x_m == rhs.waypoint_leg_origin_x_m &&
        lhs.waypoint_leg_origin_y_m == rhs.waypoint_leg_origin_y_m &&
        lhs.prev_altitude_m == rhs.prev_altitude_m &&
        lhs.prev_ias_mps == rhs.prev_ias_mps &&
        lhs.liftoff_awarded == rhs.liftoff_awarded &&
        lhs.gear_bonus_awarded == rhs.gear_bonus_awarded &&
        lhs.off_runway_steps == rhs.off_runway_steps &&
        lhs.has_approach_prev_dme_m == rhs.has_approach_prev_dme_m &&
        lhs.approach_prev_dme_m == rhs.approach_prev_dme_m &&
        lhs.has_approach_prev_loc_abs == rhs.has_approach_prev_loc_abs &&
        lhs.approach_prev_loc_abs == rhs.approach_prev_loc_abs &&
        lhs.has_approach_prev_gs_abs == rhs.has_approach_prev_gs_abs &&
        lhs.approach_prev_gs_abs == rhs.approach_prev_gs_abs &&
        lhs.has_post_waypoint_transition_json == rhs.has_post_waypoint_transition_json &&
        lhs.post_waypoint_transition_json == rhs.post_waypoint_transition_json &&
        lhs.mission_phase_name == rhs.mission_phase_name &&
        lhs.has_cached_route_ref_id == rhs.has_cached_route_ref_id &&
        lhs.cached_route_ref_id == rhs.cached_route_ref_id &&
        lhs.last_termination_reason == rhs.last_termination_reason &&
        lhs.last_reward_total == rhs.last_reward_total &&
        lhs.last_reward_breakdown_json == rhs.last_reward_breakdown_json;
}
