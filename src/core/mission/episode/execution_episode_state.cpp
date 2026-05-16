#include "core/mission/episode/execution_episode_state.h"

namespace {

bool mission_commands_equal(const MissionCommand& lhs, const MissionCommand& rhs) {
    return lhs.cmd_heading_deg == rhs.cmd_heading_deg &&
        lhs.cmd_altitude_m == rhs.cmd_altitude_m &&
        lhs.cmd_speed_mps == rhs.cmd_speed_mps &&
        lhs.command_code == rhs.command_code &&
        lhs.route_ref_id == rhs.route_ref_id &&
        lhs.reference_entity_id == rhs.reference_entity_id &&
        lhs.station_radius_m == rhs.station_radius_m &&
        lhs.station_bearing_deg == rhs.station_bearing_deg &&
        lhs.embarked_helo_entity_id == rhs.embarked_helo_entity_id &&
        lhs.launch_helo == rhs.launch_helo &&
        lhs.recover_helo == rhs.recover_helo &&
        lhs.relay_oth_targeting == rhs.relay_oth_targeting &&
        lhs.recovery_base_id == rhs.recovery_base_id &&
        lhs.recovery_runway_id == rhs.recovery_runway_id &&
        lhs.recovery_approach_type == rhs.recovery_approach_type &&
        lhs.takeoff_procedure_id == rhs.takeoff_procedure_id &&
        lhs.takeoff_clearance_id == rhs.takeoff_clearance_id &&
        lhs.takeoff_interval_s == rhs.takeoff_interval_s &&
        lhs.runway_slot_id == rhs.runway_slot_id &&
        lhs.formation_id == rhs.formation_id &&
        lhs.form_offset_x == rhs.form_offset_x &&
        lhs.form_offset_y == rhs.form_offset_y &&
        lhs.form_offset_z == rhs.form_offset_z &&
        lhs.roe_state == rhs.roe_state &&
        lhs.engagement_authority_holder_id == rhs.engagement_authority_holder_id &&
        lhs.engagement_authority_grantor_id == rhs.engagement_authority_grantor_id &&
        lhs.assigned_target_id == rhs.assigned_target_id &&
        lhs.authorization_to_fire == rhs.authorization_to_fire &&
        lhs.active == rhs.active;
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
