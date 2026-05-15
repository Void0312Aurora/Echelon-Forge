#include "core/mission/episode/detail/episode_transition_runtime.h"

#include <algorithm>
#include <cmath>
#include <limits>

#include "core/mission/episode/detail/mission_command_codec.h"
#include "core/mission/runtime/mission_runtime.h"

namespace episode_controller_detail {

namespace {

double safe_get(const std::vector<double>& values, std::size_t index, double fallback = 0.0) {
    return index < values.size() ? values[index] : fallback;
}

bool is_landing_command_code(int command_code) {
    return command_code == 4;
}

double pending_post_waypoint_transition_double(
    const ExecutionEpisodeState& state,
    const char* key,
    double fallback
) {
    if (!state.has_post_waypoint_transition_json || state.post_waypoint_transition_json.empty()) {
        return fallback;
    }
    nlohmann::json next_cmd_json;
    if (!parse_json_object(state.post_waypoint_transition_json, &next_cmd_json)) {
        return fallback;
    }
    return json_double_or(next_cmd_json, key, fallback);
}

bool state_route_complete(const ExecutionEpisodeState& state) {
    return !state.route_waypoints.empty() &&
        state.waypoint_index >= static_cast<int>(state.route_waypoints.size());
}

int pending_post_waypoint_transition_command_code(const ExecutionEpisodeState& state) {
    if (!state.has_post_waypoint_transition_json || state.post_waypoint_transition_json.empty()) {
        return 0;
    }
    nlohmann::json next_cmd_json;
    if (!parse_json_object(state.post_waypoint_transition_json, &next_cmd_json)) {
        return 0;
    }
    return json_int_or(next_cmd_json, "command_code", 4);
}

double resolve_inst_heading_deg(const StepEvaluationBatchEnvState& env_state) {
    return safe_get(env_state.inst_vec, 9, env_state.truth_heading);
}

double resolve_inst_ground_track_deg(const StepEvaluationBatchEnvState& env_state) {
    return safe_get(env_state.inst_vec, 30, std::numeric_limits<double>::quiet_NaN());
}

bool apply_route_guidance_targets(
    StepEvaluationBatchEnvState* env_state,
    ExecutionEpisodeState* state
) {
    if (env_state == nullptr || state == nullptr) {
        return false;
    }
    if (!state->has_mission_command || state->mission_command.command_code != 3) {
        return false;
    }
    if (!env_state->has_mission_observation) {
        return false;
    }
    const auto& mission_inputs = env_state->mission_observation;
    if (!mission_inputs.has_route_guidance || !mission_inputs.route_guidance.valid) {
        return false;
    }
    if (state->route_waypoints.empty()) {
        return false;
    }

    const int route_idx = std::clamp(
        int(mission_inputs.route_guidance.idx),
        0,
        static_cast<int>(state->route_waypoints.size()) - 1
    );
    const auto& waypoint = state->route_waypoints[static_cast<std::size_t>(route_idx)];
    const double target_heading_deg = normalize_heading_deg(double(mission_inputs.route_guidance.cmd_track_deg));
    const double target_altitude_m = double(mission_inputs.nav_inputs.waypoint_altitude_m);
    const double target_speed_mps = waypoint.speed_mps;

    const double ground_track_deg = resolve_inst_ground_track_deg(*env_state);
    const double heading_error_deg = compute_command_tracking_error_deg(
        target_heading_deg,
        env_state->truth_heading,
        state->mission_command.command_code,
        ground_track_deg
    );
    const double ground_track_error_deg = compute_ground_track_error_deg(
        target_heading_deg,
        env_state->truth_heading,
        ground_track_deg
    );

    env_state->mission_observation.target_heading_deg = target_heading_deg;
    env_state->mission_observation.target_altitude_m = target_altitude_m;
    env_state->mission_observation.target_speed_mps = target_speed_mps;

    if (env_state->has_flight_shaping) {
        env_state->flight_shaping.target_altitude_m = target_altitude_m;
        env_state->flight_shaping.target_speed_mps = target_speed_mps;
        env_state->flight_shaping.heading_error_deg = heading_error_deg;
        env_state->flight_shaping.ground_track_error_deg = ground_track_error_deg;
    }

    if (env_state->has_objectives) {
        env_state->objective_inputs.target_heading_deg = target_heading_deg;
        env_state->objective_inputs.target_altitude_m = target_altitude_m;
        env_state->objective_inputs.target_speed_mps = target_speed_mps;
        env_state->objective_inputs.heading_error_deg = heading_error_deg;
        env_state->objective_inputs.ground_track_error_deg = ground_track_error_deg;
    }

    return update_state_mission_command_targets(
        state,
        target_heading_deg,
        target_altitude_m,
        target_speed_mps
    );
}

bool landing_post_transition_terminal_ready(
    const StepEvaluationBatchEnvState& env_state,
    const ExecutionEpisodeRuntimeInputs& runtime_inputs,
    const ExecutionEpisodeState& state
) {
    if (!runtime_inputs.has_step_info) {
        return false;
    }
    const auto& step_info = runtime_inputs.step_info;
    if (!step_info.has_runway_frame || !step_info.runway_frame.valid) {
        return false;
    }

    const double along_m = double(step_info.runway_frame.along_m);
    const double cross_m = double(step_info.runway_frame.cross_m);
    const double runway_len_m = double(step_info.runway_frame.length_m);
    double threshold_arming_window_m = pending_post_waypoint_transition_double(
        state,
        "terminal_ready_threshold_window_m",
        1000.0
    );
    threshold_arming_window_m = std::clamp(threshold_arming_window_m, 500.0, 6000.0);
    const double min_along_m = -0.5 * std::max(runway_len_m, 0.0) - threshold_arming_window_m;
    if (along_m < min_along_m) {
        return false;
    }
    double max_cross_m = pending_post_waypoint_transition_double(
        state,
        "terminal_ready_cross_m_max",
        3500.0
    );
    max_cross_m = std::clamp(max_cross_m, 1000.0, 8000.0);
    if (std::abs(cross_m) > max_cross_m) {
        return false;
    }

    const double runway_heading_deg = double(step_info.runway_frame.heading_deg);
    const double own_heading_deg = resolve_inst_heading_deg(env_state);
    const double runway_heading_err_deg = std::abs(
        std::remainder(own_heading_deg - runway_heading_deg, 360.0)
    );
    if (runway_heading_err_deg > 85.0) {
        return false;
    }

    const double ils_dme_m = safe_get(env_state.ils_vec, 3, std::numeric_limits<double>::infinity());
    double max_dme_m = pending_post_waypoint_transition_double(
        state,
        "terminal_ready_dme_m_max",
        18000.0
    );
    max_dme_m = std::clamp(max_dme_m, 6000.0, 40000.0);
    return ils_dme_m <= max_dme_m;
}

bool apply_pending_landing_vector(
    const StepEvaluationBatchEnvState& env_state,
    const ExecutionEpisodeRuntimeInputs& runtime_inputs,
    ExecutionEpisodeState* state
) {
    if (state == nullptr || !runtime_inputs.has_step_info) {
        return false;
    }
    const auto& step_info = runtime_inputs.step_info;
    if (!step_info.has_runway_frame || !step_info.runway_frame.valid) {
        return false;
    }

    nlohmann::json post_transition_json;
    if (!parse_json_object(state->post_waypoint_transition_json, &post_transition_json)) {
        return false;
    }

    const double runway_heading_deg = double(step_info.runway_frame.heading_deg);
    const double runway_heading_rad = runway_heading_deg * M_PI / 180.0;
    const double fwd_x = std::sin(runway_heading_rad);
    const double fwd_y = std::cos(runway_heading_rad);
    const double right_x = std::cos(runway_heading_rad);
    const double right_y = -std::sin(runway_heading_rad);

    const double center_x = env_state.truth_x
        - double(step_info.runway_frame.along_m) * fwd_x
        - double(step_info.runway_frame.cross_m) * right_x;
    const double center_y = env_state.truth_y
        - double(step_info.runway_frame.along_m) * fwd_y
        - double(step_info.runway_frame.cross_m) * right_y;
    const double threshold_x = center_x - 0.5 * double(step_info.runway_frame.length_m) * fwd_x;
    const double threshold_y = center_y - 0.5 * double(step_info.runway_frame.length_m) * fwd_y;

    double intercept_before_threshold_m = json_double_or(
        post_transition_json,
        "approach_arm_before_threshold_m",
        1600.0
    );
    intercept_before_threshold_m = std::clamp(intercept_before_threshold_m, 1000.0, 5000.0);
    const double intercept_x = threshold_x - fwd_x * intercept_before_threshold_m;
    const double intercept_y = threshold_y - fwd_y * intercept_before_threshold_m;

    const double dx = intercept_x - env_state.truth_x;
    const double dy = intercept_y - env_state.truth_y;
    double desired_heading_deg = runway_heading_deg;
    if (dx * dx + dy * dy > 1.0) {
        desired_heading_deg = std::atan2(dx, dy) * 180.0 / M_PI;
        desired_heading_deg = std::fmod(desired_heading_deg, 360.0);
        if (desired_heading_deg < 0.0) {
            desired_heading_deg += 360.0;
        }
    }

    const double current_heading_deg = state->has_mission_command
        ? state->mission_command.cmd_heading_deg
        : json_double_or(build_state_mission_command_json(*state), "target_heading", 0.0);
    if (std::abs(std::remainder(current_heading_deg - desired_heading_deg, 360.0)) <= 1.0e-9) {
        return false;
    }
    update_state_mission_command_heading(state, desired_heading_deg);
    return true;
}

bool activate_post_waypoint_transition(
    ExecutionEpisodeState* state,
    double* transition_reward_out
) {
    if (state == nullptr || !state->has_post_waypoint_transition_json || state->post_waypoint_transition_json.empty()) {
        return false;
    }

    nlohmann::json next_cmd_json;
    try {
        next_cmd_json = nlohmann::json::parse(state->post_waypoint_transition_json);
    } catch (...) {
        return false;
    }
    if (!next_cmd_json.is_object()) {
        return false;
    }

    const int command_code = json_int_or(next_cmd_json, "command_code", 4);

    nlohmann::json mission_json = nlohmann::json::object();
    mission_json["command_code"] = command_code;
    mission_json["target_heading"] = json_double_or(
        next_cmd_json,
        "target_heading",
        state->has_mission_command ? state->mission_command.cmd_heading_deg : 0.0
    );
    mission_json["target_altitude"] = json_double_or(
        next_cmd_json,
        "target_altitude",
        state->has_mission_command ? state->mission_command.cmd_altitude_m : 0.0
    );
    mission_json["target_speed"] = json_double_or(
        next_cmd_json,
        "target_speed",
        state->has_mission_command ? state->mission_command.cmd_speed_mps : 0.0
    );
    mission_json["route_ref_id"] = json_uint64_or(next_cmd_json, "route_ref_id", 0);
    mission_json["recovery_base_id"] = json_uint64_or(next_cmd_json, "recovery_base_id", 0);
    mission_json["recovery_runway_id"] = json_uint64_or(next_cmd_json, "recovery_runway_id", 0);
    mission_json["recovery_approach_type"] = json_string_or(next_cmd_json, "recovery_approach_type", "None");
    mission_json["takeoff_procedure_code"] = json_int_or(next_cmd_json, "takeoff_procedure_code", 0);
    mission_json["takeoff_clearance_code"] = json_int_or(next_cmd_json, "takeoff_clearance_code", 0);
    mission_json["takeoff_interval_s"] = json_double_or(next_cmd_json, "takeoff_interval_s", 0.0);
    mission_json["runway_slot_code"] = json_int_or(next_cmd_json, "runway_slot_code", 0);
    for (auto it = next_cmd_json.begin(); it != next_cmd_json.end(); ++it) {
        if (
            it.key() == "command_code" ||
            it.key() == "target_heading" ||
            it.key() == "target_altitude" ||
            it.key() == "target_speed" ||
            it.key() == "transition_reward"
        ) {
            continue;
        }
        mission_json[it.key()] = it.value();
    }

    MissionCommand next_command{};
    next_command.cmd_heading_deg = mission_json["target_heading"].get<double>();
    next_command.cmd_altitude_m = mission_json["target_altitude"].get<double>();
    next_command.cmd_speed_mps = mission_json["target_speed"].get<double>();
    next_command.command_code = command_code;
    next_command.route_ref_id = command_code == 3 ? mission_json["route_ref_id"].get<std::uint64_t>() : 0;
    next_command.recovery_base_id = mission_json["recovery_base_id"].get<std::uint64_t>();
    next_command.recovery_runway_id = mission_json["recovery_runway_id"].get<std::uint64_t>();
    next_command.recovery_approach_type = parse_recovery_approach_type(mission_json);
    next_command.takeoff_procedure_id = static_cast<TakeoffProcedureType>(mission_json["takeoff_procedure_code"].get<int>());
    next_command.takeoff_clearance_id = static_cast<TakeoffClearanceState>(mission_json["takeoff_clearance_code"].get<int>());
    next_command.takeoff_interval_s = mission_json["takeoff_interval_s"].get<double>();
    next_command.runway_slot_id = static_cast<RunwaySlotPosition>(mission_json["runway_slot_code"].get<int>());
    next_command.active = true;

    state->has_mission_command = true;
    state->mission_command = next_command;
    state->has_mission_command_json = true;
    state->mission_command_json = stable_json_dump(mission_json);
    state->has_post_waypoint_transition_json = false;
    state->post_waypoint_transition_json.clear();

    std::string phase_name = trim_copy(
        json_string_or(next_cmd_json, "phase_name", json_string_or(next_cmd_json, "landing_mode", "post_waypoint"))
    );
    state->mission_phase_name = phase_name.empty() ? "post_waypoint" : phase_name;

    state->route_waypoints = build_route_waypoints_from_json(mission_json);
    state->waypoint_index = 0;
    state->has_waypoint_prev_dist_m = false;
    state->waypoint_prev_dist_m = 0.0;
    state->waypoint_total_route_length_m = 0.0;
    state->waypoint_leg_origin_x_m = 0.0;
    state->waypoint_leg_origin_y_m = 0.0;
    state->has_cached_route_ref_id = next_command.route_ref_id > 0;
    state->cached_route_ref_id = state->has_cached_route_ref_id ? next_command.route_ref_id : 0;
    state->has_approach_prev_dme_m = false;
    state->approach_prev_dme_m = 0.0;
    state->has_approach_prev_loc_abs = false;
    state->approach_prev_loc_abs = 0.0;
    state->has_approach_prev_gs_abs = false;
    state->approach_prev_gs_abs = 0.0;

    if (transition_reward_out != nullptr) {
        *transition_reward_out = json_double_or(next_cmd_json, "transition_reward", 600.0);
    }
    return true;
}

}  // namespace

void apply_pre_step_behavior_updates(
    StepEvaluationBatchEnvState* env_state,
    ExecutionEpisodeState* state
) {
    if (env_state == nullptr || state == nullptr) {
        return;
    }
    apply_route_guidance_targets(env_state, state);
}

PostWaypointTransitionResolution maybe_apply_post_waypoint_transition(
    const StepEvaluationBatchEnvState& env_state,
    const ExecutionEpisodeRuntimeInputs& runtime_inputs,
    ExecutionEpisodeState* state
) {
    PostWaypointTransitionResolution out{};
    if (state == nullptr || !state->has_post_waypoint_transition_json || !state_route_complete(*state)) {
        return out;
    }

    const int command_code = pending_post_waypoint_transition_command_code(*state);
    if (!is_landing_command_code(command_code)) {
        double transition_reward = 0.0;
        if (activate_post_waypoint_transition(state, &transition_reward)) {
            out.activated = true;
            out.structural_state_changed = true;
            out.transition_reward_bonus = transition_reward;
        }
        return out;
    }

    out.pending = true;
    if (env_state.defer_landing_post_transition) {
        return out;
    }

    if (landing_post_transition_terminal_ready(env_state, runtime_inputs, *state)) {
        double transition_reward = 0.0;
        if (activate_post_waypoint_transition(state, &transition_reward)) {
            out.activated = true;
            out.structural_state_changed = true;
            out.transition_reward_bonus = transition_reward;
            out.pending = false;
        }
        return out;
    }

    if (apply_pending_landing_vector(env_state, runtime_inputs, state)) {
        out.structural_state_changed = true;
    }
    return out;
}

}  // namespace episode_controller_detail
