#include "core/mission/execution_episode_controller.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <string>
#include <utility>

#include <nlohmann/json.hpp>

#include "core/mission/mission_runtime.h"
#include "core/mission/termination_runtime.h"

namespace {

double safe_get(const std::vector<double>& values, std::size_t index, double fallback = 0.0) {
    return index < values.size() ? values[index] : fallback;
}

void add_breakdown_term(nlohmann::json* breakdown, const std::string& name, double value) {
    if (breakdown == nullptr) {
        return;
    }
    const double current = breakdown->contains(name) ? (*breakdown)[name].get<double>() : 0.0;
    (*breakdown)[name] = current + value;
}

std::string stable_json_dump(const nlohmann::json& value) {
    if (value.is_object()) {
        std::string out = "{";
        bool first = true;
        for (auto it = value.begin(); it != value.end(); ++it) {
            if (!first) {
                out += ", ";
            }
            first = false;
            out += nlohmann::json(it.key()).dump(-1, ' ', true);
            out += ": ";
            out += stable_json_dump(it.value());
        }
        out += "}";
        return out;
    }
    if (value.is_array()) {
        std::string out = "[";
        bool first = true;
        for (const auto& item : value) {
            if (!first) {
                out += ", ";
            }
            first = false;
            out += stable_json_dump(item);
        }
        out += "]";
        return out;
    }
    return value.dump(-1, ' ', true);
}

void apply_flight_shaping_breakdown_terms(
    const FlightShapingRuntimeProducts& products,
    bool include_roll_stability,
    nlohmann::json* breakdown
) {
    const std::pair<const char*, double> gated_terms[] = {
        {"altitude_progress", products.altitude_progress},
        {"low_alt_descent_penalty", products.low_alt_descent_penalty},
        {"speed_progress", products.speed_progress},
        {"speed_regress", products.speed_regress},
        {"stationary_penalty", products.stationary_penalty},
        {"liftoff_bonus", products.liftoff_bonus},
        {"rotation_reward", products.rotation_reward},
        {"rotation_overpitch_penalty", products.rotation_overpitch_penalty},
        {"gear_up_bonus", products.gear_up_bonus},
        {"heading_error_penalty", products.heading_error_penalty},
        {"heading_hold_bonus", products.heading_hold_bonus},
        {"altitude_error_penalty", products.altitude_error_penalty},
        {"altitude_hold_bonus", products.altitude_hold_bonus},
        {"speed_error_penalty", products.speed_error_penalty},
        {"speed_hold_bonus", products.speed_hold_bonus},
        {"roll_abs_penalty", products.roll_abs_penalty},
        {"pitch_abs_penalty", products.pitch_abs_penalty},
        {"yaw_rate_abs_penalty", products.yaw_rate_abs_penalty},
        {"beta_abs_penalty", products.beta_abs_penalty},
        {"g_deviation_penalty", products.g_deviation_penalty},
        {"runway_centerline_m_penalty", products.runway_centerline_m_penalty},
        {"runway_centerline_penalty", products.runway_centerline_penalty},
        {"runway_centerline_barrier", products.runway_centerline_barrier},
        {"departure_centerline_m_penalty", products.departure_centerline_m_penalty},
        {"departure_centerline_reward", products.departure_centerline_reward},
        {"departure_track_error_penalty", products.departure_track_error_penalty},
        {"departure_track_reward", products.departure_track_reward},
        {"alignment_reward", products.alignment_reward},
    };
    for (const auto& [name, value] : gated_terms) {
        if (value != 0.0) {
            add_breakdown_term(breakdown, name, value);
        }
    }
    add_breakdown_term(breakdown, "speed_reward", products.speed_reward);
    if (include_roll_stability) {
        add_breakdown_term(breakdown, "roll_stability", products.roll_stability);
    }
}

bool is_landing_command_code(int command_code) {
    return command_code == 4;
}

double json_double_or(const nlohmann::json& value, const char* key, double fallback) {
    if (!value.is_object()) {
        return fallback;
    }
    const auto it = value.find(key);
    if (it == value.end()) {
        return fallback;
    }
    try {
        return it->get<double>();
    } catch (...) {
        return fallback;
    }
}

int json_int_or(const nlohmann::json& value, const char* key, int fallback) {
    if (!value.is_object()) {
        return fallback;
    }
    const auto it = value.find(key);
    if (it == value.end()) {
        return fallback;
    }
    try {
        return it->get<int>();
    } catch (...) {
        return fallback;
    }
}

std::uint64_t json_uint64_or(const nlohmann::json& value, const char* key, std::uint64_t fallback) {
    if (!value.is_object()) {
        return fallback;
    }
    const auto it = value.find(key);
    if (it == value.end()) {
        return fallback;
    }
    try {
        return it->get<std::uint64_t>();
    } catch (...) {
        return fallback;
    }
}

std::string json_string_or(const nlohmann::json& value, const char* key, std::string fallback) {
    if (!value.is_object()) {
        return fallback;
    }
    const auto it = value.find(key);
    if (it == value.end()) {
        return fallback;
    }
    try {
        return it->get<std::string>();
    } catch (...) {
        return fallback;
    }
}

std::string trim_copy(std::string value) {
    const auto first = value.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) {
        return "";
    }
    const auto last = value.find_last_not_of(" \t\r\n");
    return value.substr(first, last - first + 1);
}

RecoveryApproachType parse_recovery_approach_type(const nlohmann::json& mission_json) {
    const auto it = mission_json.find("recovery_approach_type");
    if (it == mission_json.end()) {
        return RecoveryApproachType::None;
    }
    if (it->is_number_integer()) {
        const int raw = it->get<int>();
        switch (raw) {
        case 1:
            return RecoveryApproachType::StraightIn;
        case 2:
            return RecoveryApproachType::ILS;
        case 3:
            return RecoveryApproachType::Visual;
        case 4:
            return RecoveryApproachType::Overhead;
        case 5:
            return RecoveryApproachType::TACAN;
        default:
            return RecoveryApproachType::None;
        }
    }
    const std::string raw = trim_copy(it->is_string() ? it->get<std::string>() : std::string{});
    if (raw == "StraightIn") {
        return RecoveryApproachType::StraightIn;
    }
    if (raw == "ILS") {
        return RecoveryApproachType::ILS;
    }
    if (raw == "Visual") {
        return RecoveryApproachType::Visual;
    }
    if (raw == "Overhead") {
        return RecoveryApproachType::Overhead;
    }
    if (raw == "TACAN") {
        return RecoveryApproachType::TACAN;
    }
    return RecoveryApproachType::None;
}

std::vector<SpatialRouteWaypoint> build_route_waypoints_from_json(const nlohmann::json& mission_json) {
    std::vector<SpatialRouteWaypoint> route_waypoints;
    const auto it = mission_json.find("waypoints");
    if (it == mission_json.end() || !it->is_array()) {
        return route_waypoints;
    }
    const std::string default_mode = json_string_or(mission_json, "waypoint_mode", "flyby");
    const double default_altitude = json_double_or(mission_json, "target_altitude", 0.0);
    const double default_speed = json_double_or(mission_json, "target_speed", 0.0);
    const double default_radius = json_double_or(
        mission_json,
        "waypoint_radius_m",
        json_double_or(mission_json, "arrival_radius_m", 500.0)
    );
    route_waypoints.reserve(it->size());
    for (const auto& waypoint_json : *it) {
        if (!waypoint_json.is_object()) {
            continue;
        }
        SpatialRouteWaypoint waypoint{};
        waypoint.x_m = json_double_or(waypoint_json, "x", 0.0);
        waypoint.y_m = json_double_or(waypoint_json, "y", 0.0);
        waypoint.z_m = json_double_or(
            waypoint_json,
            "z",
            json_double_or(waypoint_json, "altitude_m", default_altitude)
        );
        waypoint.radius_m = json_double_or(waypoint_json, "radius_m", default_radius);
        waypoint.altitude_m = json_double_or(waypoint_json, "altitude_m", waypoint.z_m);
        waypoint.speed_mps = json_double_or(waypoint_json, "speed_mps", default_speed);
        waypoint.waypoint_mode = json_string_or(waypoint_json, "waypoint_mode", default_mode);
        route_waypoints.push_back(std::move(waypoint));
    }
    return route_waypoints;
}

bool parse_json_object(const std::string& raw, nlohmann::json* out) {
    if (out == nullptr || raw.empty()) {
        return false;
    }
    try {
        *out = nlohmann::json::parse(raw);
    } catch (...) {
        return false;
    }
    return out->is_object();
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

double normalize_heading_deg(double heading_deg) {
    double wrapped = std::fmod(heading_deg, 360.0);
    if (wrapped < 0.0) {
        wrapped += 360.0;
    }
    return wrapped;
}

nlohmann::json build_state_mission_command_json(const ExecutionEpisodeState& state) {
    nlohmann::json mission_json = nlohmann::json::object();
    if (state.has_mission_command_json && parse_json_object(state.mission_command_json, &mission_json)) {
        return mission_json;
    }

    if (state.has_mission_command) {
        mission_json["command_code"] = state.mission_command.command_code;
        mission_json["target_heading"] = state.mission_command.cmd_heading_deg;
        mission_json["target_altitude"] = state.mission_command.cmd_altitude_m;
        mission_json["target_speed"] = state.mission_command.cmd_speed_mps;
        mission_json["route_ref_id"] = state.mission_command.route_ref_id;
        mission_json["recovery_base_id"] = state.mission_command.recovery_base_id;
        mission_json["recovery_runway_id"] = state.mission_command.recovery_runway_id;
    }
    if (state.has_post_waypoint_transition_json) {
        nlohmann::json post_transition_json;
        if (parse_json_object(state.post_waypoint_transition_json, &post_transition_json)) {
            mission_json["post_waypoint_transition"] = post_transition_json;
        }
    }
    return mission_json;
}

void update_state_mission_command_heading(
    ExecutionEpisodeState* state,
    double target_heading_deg
) {
    if (state == nullptr) {
        return;
    }
    if (state->has_mission_command) {
        state->mission_command.cmd_heading_deg = target_heading_deg;
    }

    nlohmann::json mission_json = build_state_mission_command_json(*state);
    mission_json["target_heading"] = target_heading_deg;
    state->has_mission_command_json = true;
    state->mission_command_json = stable_json_dump(mission_json);
}

bool update_state_mission_command_targets(
    ExecutionEpisodeState* state,
    double target_heading_deg,
    double target_altitude_m,
    double target_speed_mps
) {
    if (state == nullptr) {
        return false;
    }

    const double normalized_heading_deg = normalize_heading_deg(target_heading_deg);
    bool changed = false;
    if (state->has_mission_command) {
        if (std::abs(std::remainder(state->mission_command.cmd_heading_deg - normalized_heading_deg, 360.0)) > 1.0e-9) {
            state->mission_command.cmd_heading_deg = normalized_heading_deg;
            changed = true;
        }
        if (std::abs(state->mission_command.cmd_altitude_m - target_altitude_m) > 1.0e-9) {
            state->mission_command.cmd_altitude_m = target_altitude_m;
            changed = true;
        }
        if (std::abs(state->mission_command.cmd_speed_mps - target_speed_mps) > 1.0e-9) {
            state->mission_command.cmd_speed_mps = target_speed_mps;
            changed = true;
        }
    } else {
        changed = true;
    }

    nlohmann::json mission_json = build_state_mission_command_json(*state);
    const double prior_heading_deg = json_double_or(mission_json, "target_heading", normalized_heading_deg);
    const double prior_altitude_m = json_double_or(mission_json, "target_altitude", target_altitude_m);
    const double prior_speed_mps = json_double_or(mission_json, "target_speed", target_speed_mps);
    if (std::abs(std::remainder(prior_heading_deg - normalized_heading_deg, 360.0)) > 1.0e-9) {
        changed = true;
    }
    if (std::abs(prior_altitude_m - target_altitude_m) > 1.0e-9) {
        changed = true;
    }
    if (std::abs(prior_speed_mps - target_speed_mps) > 1.0e-9) {
        changed = true;
    }

    mission_json["target_heading"] = normalized_heading_deg;
    mission_json["target_altitude"] = target_altitude_m;
    mission_json["target_speed"] = target_speed_mps;
    state->has_mission_command_json = true;
    state->mission_command_json = stable_json_dump(mission_json);
    return changed;
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
    const double target_altitude_m = waypoint.altitude_m;
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

void apply_pre_step_behavior_updates(
    StepEvaluationBatchEnvState* env_state,
    ExecutionEpisodeState* state
) {
    if (env_state == nullptr || state == nullptr) {
        return;
    }
    apply_route_guidance_targets(env_state, state);
}

bool landing_post_transition_terminal_ready(
    const StepEvaluationBatchEnvState& env_state,
    const ExecutionEpisodeRuntimeInputs& runtime_inputs
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
    const double threshold_arming_window_m = 1000.0;
    const double min_along_m = -0.5 * std::max(runway_len_m, 0.0) - threshold_arming_window_m;
    if (along_m < min_along_m) {
        return false;
    }
    if (std::abs(cross_m) > 3500.0) {
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
    return ils_dme_m <= 18000.0;
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
        1000.0
    );
    intercept_before_threshold_m = std::clamp(intercept_before_threshold_m, 600.0, 2500.0);
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

struct PostWaypointTransitionResolution {
    bool activated = false;
    bool pending = false;
    bool structural_state_changed = false;
    double transition_reward_bonus = 0.0;
};

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

    if (landing_post_transition_terminal_ready(env_state, runtime_inputs)) {
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

}  // namespace

void ExecutionEpisodeController::clear_state() noexcept {
    has_state_ = false;
    state_ = ExecutionEpisodeState{};
}

bool ExecutionEpisodeController::has_state() const noexcept {
    return has_state_;
}

void ExecutionEpisodeController::import_state(const ExecutionEpisodeState& state) {
    state_ = state;
    has_state_ = true;
}

ExecutionEpisodeState ExecutionEpisodeController::export_state() const {
    return state_;
}

void ExecutionEpisodeController::apply_episode_state_overrides(
    const ExecutionEpisodeState& episode_state,
    StepEvaluationBatchEnvState* env_state
) {
    if (env_state == nullptr) {
        return;
    }

    env_state->prev_altitude_m = episode_state.prev_altitude_m;
    env_state->prev_ias_mps = episode_state.prev_ias_mps;
    env_state->liftoff_awarded = episode_state.liftoff_awarded;
    env_state->gear_bonus_awarded = episode_state.gear_bonus_awarded;

    if (env_state->has_safety) {
        env_state->safety.off_runway_steps = (
            env_state->safety.runway_surface_phase && !env_state->safety.on_runway_task
        )
            ? std::max(0, episode_state.off_runway_steps + 1)
            : 0;
    }

    if (env_state->has_waypoint) {
        env_state->waypoint.waypoint_index = episode_state.waypoint_index;
        env_state->waypoint.has_prev_dist = episode_state.has_waypoint_prev_dist_m;
        env_state->waypoint.prev_dist_m = episode_state.has_waypoint_prev_dist_m
            ? episode_state.waypoint_prev_dist_m
            : 0.0;
    }

    if (env_state->has_approach) {
        env_state->approach.has_prev_dme = episode_state.has_approach_prev_dme_m;
        env_state->approach.prev_dme_m = episode_state.has_approach_prev_dme_m
            ? episode_state.approach_prev_dme_m
            : 0.0;
        env_state->approach.has_prev_loc = episode_state.has_approach_prev_loc_abs;
        env_state->approach.prev_loc_abs = episode_state.has_approach_prev_loc_abs
            ? episode_state.approach_prev_loc_abs
            : 0.0;
        env_state->approach.has_prev_gs = episode_state.has_approach_prev_gs_abs;
        env_state->approach.prev_gs_abs = episode_state.has_approach_prev_gs_abs
            ? episode_state.approach_prev_gs_abs
            : 0.0;
    }

    if (env_state->has_flight_shaping) {
        env_state->flight_shaping.prev_altitude_m = episode_state.prev_altitude_m;
        env_state->flight_shaping.prev_ias_mps = episode_state.prev_ias_mps;
        env_state->flight_shaping.liftoff_awarded = episode_state.liftoff_awarded;
        env_state->flight_shaping.gear_bonus_awarded = episode_state.gear_bonus_awarded;
    }
}

StepEvaluationBatchEnvState ExecutionEpisodeController::resolve_env_state(
    const StepEvaluationBatchEnvState& env_state
) const {
    StepEvaluationBatchEnvState resolved = env_state;
    if (!resolved.has_episode_state && has_state_) {
        resolved.has_episode_state = true;
        resolved.episode_state = state_;
    }
    if (resolved.has_episode_state) {
        apply_episode_state_overrides(resolved.episode_state, &resolved);
    }
    return resolved;
}

ExecutionEpisodeRuntimeInputs ExecutionEpisodeController::prepare_runtime_inputs(
    const StepEvaluationBatchConfig& config,
    const StepEvaluationBatchEnvState& env_state
) const {
    auto resolved = resolve_env_state(env_state);
    ExecutionEpisodeState working_state{};
    if (resolved.has_episode_state) {
        working_state = resolved.episode_state;
    } else if (has_state_) {
        working_state = state_;
    }
    apply_pre_step_behavior_updates(&resolved, &working_state);
    auto batch = prepare_step_evaluations_batch(config, {resolved});
    if (batch.empty()) {
        return ExecutionEpisodeRuntimeInputs{};
    }
    return batch.front();
}

ExecutionEpisodeRuntimeProducts ExecutionEpisodeController::evaluate(
    const StepEvaluationBatchConfig& config,
    const StepEvaluationBatchEnvState& env_state
) const {
    return compute_execution_episode_runtime(prepare_runtime_inputs(config, env_state));
}

ExecutionEpisodeRuntimeProducts ExecutionEpisodeController::step(
    const StepEvaluationBatchConfig& config,
    const StepEvaluationBatchEnvState& env_state
) {
    auto resolved = resolve_env_state(env_state);
    ExecutionEpisodeState next_state{};
    if (resolved.has_episode_state) {
        next_state = resolved.episode_state;
    } else if (has_state_) {
        next_state = state_;
    }
    apply_pre_step_behavior_updates(&resolved, &next_state);
    auto batch = prepare_step_evaluations_batch(config, {resolved});
    const auto runtime_inputs = batch.empty() ? ExecutionEpisodeRuntimeInputs{} : batch.front();
    const auto products = compute_execution_episode_runtime(runtime_inputs);
    apply_runtime_products_to_state(resolved, runtime_inputs, products, &next_state);
    state_ = std::move(next_state);
    has_state_ = true;
    return products;
}

ExecutionEpisodeControllerStepResult ExecutionEpisodeController::step_result(
    const StepEvaluationBatchConfig& config,
    const StepEvaluationBatchEnvState& env_state
) {
    auto resolved = resolve_env_state(env_state);
    ExecutionEpisodeState next_state{};
    if (resolved.has_episode_state) {
        next_state = resolved.episode_state;
    } else if (has_state_) {
        next_state = state_;
    }
    apply_pre_step_behavior_updates(&resolved, &next_state);
    auto batch = prepare_step_evaluations_batch(config, {resolved});
    const auto runtime_inputs = batch.empty() ? ExecutionEpisodeRuntimeInputs{} : batch.front();
    const auto products = compute_execution_episode_runtime(runtime_inputs);

    ExecutionEpisodeControllerStepResult result{};
    apply_runtime_products_to_state(resolved, runtime_inputs, products, &next_state, &result);
    state_ = next_state;
    has_state_ = true;
    result.valid = products.valid;
    result.controller_state = state_;
    return result;
}

void ExecutionEpisodeController::apply_runtime_products_to_state(
    const StepEvaluationBatchEnvState& env_state,
    const ExecutionEpisodeRuntimeInputs& runtime_inputs,
    const ExecutionEpisodeRuntimeProducts& products,
    ExecutionEpisodeState* state,
    ExecutionEpisodeControllerStepResult* result
) {
    if (state == nullptr) {
        return;
    }

    double reward_total = double(products.compiled_reward_total);
    const bool truncated = runtime_inputs.has_execution_step
        ? bool(runtime_inputs.execution_step.truncated)
        : bool(env_state.truncated);
    double status0 = double(products.status0);
    double status1 = double(products.status1);
    double status2 = double(products.status2);
    double status3 = double(products.status3);
    bool structural_state_changed = false;
    bool objective_has_status = false;
    const bool had_post_waypoint_transition_before = state->has_post_waypoint_transition_json;
    bool waypoint_arrived = false;
    double phase_transition_bonus = 0.0;
    bool landing_transition_pending = false;

    state->step_count = int(env_state.steps);
    state->prev_altitude_m = runtime_inputs.has_flight_shaping
        ? double(runtime_inputs.flight_shaping.truth_altitude_m)
        : env_state.truth_z;
    state->prev_ias_mps = runtime_inputs.has_flight_shaping
        ? double(runtime_inputs.flight_shaping.curr_ias_mps)
        : safe_get(env_state.inst_vec, 0, env_state.truth_speed);
    state->last_termination_reason = termination_reason_name(products.final_reason_code);

    if (runtime_inputs.has_execution_step) {
        state->off_runway_steps = int(runtime_inputs.execution_step.safety.off_runway_steps);
    }

    if (products.flight_shaping_evaluated) {
        state->liftoff_awarded = bool(products.flight_shaping.next_liftoff_awarded);
        state->gear_bonus_awarded = bool(products.flight_shaping.next_gear_bonus_awarded);
    }

    if (products.execution_step_evaluated) {
        const auto& step_products = products.execution_step;
        objective_has_status = step_products.objective_evaluated &&
            step_products.objective_status_count > 0;

        if (step_products.approach_evaluated) {
            if (bool(step_products.approach.clear_history)) {
                state->has_approach_prev_dme_m = false;
                state->approach_prev_dme_m = 0.0;
                state->has_approach_prev_loc_abs = false;
                state->approach_prev_loc_abs = 0.0;
                state->has_approach_prev_gs_abs = false;
                state->approach_prev_gs_abs = 0.0;
            } else if (bool(step_products.approach.next_prev_valid)) {
                state->has_approach_prev_dme_m = true;
                state->approach_prev_dme_m = double(step_products.approach.next_prev_dme_m);
                state->has_approach_prev_loc_abs = true;
                state->approach_prev_loc_abs = double(step_products.approach.next_prev_loc_abs);
                state->has_approach_prev_gs_abs = true;
                state->approach_prev_gs_abs = double(step_products.approach.next_prev_gs_abs);
            }
        }

        if (step_products.waypoint_evaluated) {
            const int prior_waypoint_index = state->waypoint_index;
            const int waypoint_count = runtime_inputs.execution_step.has_waypoint
                ? int(runtime_inputs.execution_step.waypoint.waypoint_count)
                : int(state->route_waypoints.size());
            if (!objective_has_status) {
                status0 = runtime_inputs.execution_step.has_waypoint
                    ? double(runtime_inputs.execution_step.waypoint.dist_m)
                    : status0;
                status1 = double(prior_waypoint_index);
                status2 = double(waypoint_count);
            }
            if (bool(step_products.waypoint.arrived)) {
                waypoint_arrived = true;
                state->waypoint_index = std::min(state->waypoint_index + 1, std::max(0, waypoint_count));
                state->has_waypoint_prev_dist_m = false;
                state->waypoint_prev_dist_m = 0.0;
                if (!objective_has_status) {
                    status1 = double(state->waypoint_index);
                    if (
                        state->waypoint_index >= 0 &&
                        state->waypoint_index < waypoint_count &&
                        static_cast<std::size_t>(state->waypoint_index) < state->route_waypoints.size()
                    ) {
                        const auto& next_waypoint = state->route_waypoints[static_cast<std::size_t>(state->waypoint_index)];
                        const double next_dx = next_waypoint.x_m - env_state.truth_x;
                        const double next_dy = next_waypoint.y_m - env_state.truth_y;
                        status0 = std::hypot(next_dx, next_dy);
                    } else {
                        status0 = 0.0;
                    }
                }
            } else if (bool(step_products.waypoint.next_prev_dist_valid)) {
                state->has_waypoint_prev_dist_m = true;
                state->waypoint_prev_dist_m = double(step_products.waypoint.next_prev_dist_m);
            }
        }
    }

    const auto post_transition = maybe_apply_post_waypoint_transition(env_state, runtime_inputs, state);
    if (post_transition.activated) {
        phase_transition_bonus = post_transition.transition_reward_bonus;
        reward_total += phase_transition_bonus;
    }
    if (post_transition.structural_state_changed) {
        structural_state_changed = true;
    }
    landing_transition_pending = post_transition.pending;
    if (!objective_has_status) {
        if (post_transition.activated) {
            status0 = 0.0;
            status1 = 0.0;
        } else if (landing_transition_pending) {
            status0 = 0.0;
            status1 = double(state->waypoint_index);
        }
    }

    nlohmann::json breakdown = nlohmann::json::object();
    if (!products.execution_step_evaluated) {
        breakdown["tracked_total"] = 0.0;
        breakdown["untracked"] = reward_total;
        breakdown["total"] = reward_total;
    } else {
        const auto& execution_step = products.execution_step;
        const auto& safety_terms = execution_step.safety;
        if (double(safety_terms.crash_penalty) != 0.0) {
            add_breakdown_term(&breakdown, "crash_penalty", double(safety_terms.crash_penalty));
            if (double(safety_terms.nan_guard_marker) != 0.0) {
                add_breakdown_term(&breakdown, "nan_guard", double(safety_terms.nan_guard_marker));
            }
        } else {
            add_breakdown_term(&breakdown, "survival", double(safety_terms.survival));
            if (products.flight_shaping_evaluated) {
                apply_flight_shaping_breakdown_terms(
                    products.flight_shaping,
                    runtime_inputs.include_roll_stability,
                    &breakdown
                );
            }
            if (double(safety_terms.stall_penalty) != 0.0) {
                add_breakdown_term(&breakdown, "stall_penalty", double(safety_terms.stall_penalty));
            }
            if (double(safety_terms.overload_penalty) != 0.0) {
                add_breakdown_term(&breakdown, "overload_penalty", double(safety_terms.overload_penalty));
            }
            if (double(safety_terms.failfast_penalty) != 0.0) {
                add_breakdown_term(&breakdown, "failfast_penalty", double(safety_terms.failfast_penalty));
            }
            if (double(safety_terms.gear_collapse_penalty) != 0.0) {
                add_breakdown_term(&breakdown, "gear_collapse_penalty", double(safety_terms.gear_collapse_penalty));
            }
            if (double(safety_terms.off_runway_penalty) != 0.0) {
                add_breakdown_term(&breakdown, "off_runway_penalty", double(safety_terms.off_runway_penalty));
            }
            if (double(safety_terms.gear_stress_penalty) != 0.0) {
                add_breakdown_term(&breakdown, "gear_stress_penalty", double(safety_terms.gear_stress_penalty));
            }
            if (double(safety_terms.off_runway_terminate_penalty) != 0.0) {
                add_breakdown_term(
                    &breakdown,
                    "off_runway_terminate_penalty",
                    double(safety_terms.off_runway_terminate_penalty)
                );
            }

            if (runtime_inputs.execution_step.has_approach && execution_step.approach_evaluated) {
                const auto& approach_inputs = runtime_inputs.execution_step.approach;
                const auto& approach_terms = execution_step.approach;
                if (double(approach_terms.approach_localizer) != 0.0) {
                    add_breakdown_term(&breakdown, "approach_localizer", double(approach_terms.approach_localizer));
                }
                if (double(approach_inputs.localizer_improve_weight) != 0.0 && bool(approach_inputs.has_prev_loc)) {
                    add_breakdown_term(
                        &breakdown,
                        "approach_localizer_improve",
                        double(approach_terms.approach_localizer_improve)
                    );
                }
                if (double(approach_terms.approach_glideslope) != 0.0) {
                    add_breakdown_term(&breakdown, "approach_glideslope", double(approach_terms.approach_glideslope));
                }
                if (double(approach_inputs.glideslope_improve_weight) != 0.0 && bool(approach_inputs.has_prev_gs)) {
                    add_breakdown_term(
                        &breakdown,
                        "approach_glideslope_improve",
                        double(approach_terms.approach_glideslope_improve)
                    );
                }
                if (
                    double(approach_inputs.dme_progress_weight) != 0.0 &&
                    bool(approach_inputs.has_prev_dme) &&
                    std::isfinite(double(approach_inputs.ils_dme_m))
                ) {
                    add_breakdown_term(
                        &breakdown,
                        "approach_dme_progress",
                        double(approach_terms.approach_dme_progress)
                    );
                }
                if (double(approach_terms.approach_capture_bonus) != 0.0) {
                    add_breakdown_term(
                        &breakdown,
                        "approach_capture_bonus",
                        double(approach_terms.approach_capture_bonus)
                    );
                }
                if (double(approach_terms.landing_sink_rate_penalty) != 0.0) {
                    add_breakdown_term(
                        &breakdown,
                        "landing_sink_rate_penalty",
                        double(approach_terms.landing_sink_rate_penalty)
                    );
                }
            }

            if (runtime_inputs.execution_step.has_waypoint && execution_step.waypoint_evaluated) {
                const auto& waypoint_inputs = runtime_inputs.execution_step.waypoint;
                const auto& waypoint_terms = execution_step.waypoint;
                if (double(waypoint_inputs.progress_weight) != 0.0 && bool(waypoint_inputs.has_prev_dist)) {
                    add_breakdown_term(
                        &breakdown,
                        "waypoint_progress",
                        double(waypoint_terms.waypoint_progress)
                    );
                }
                if (double(waypoint_inputs.distance_weight) != 0.0) {
                    add_breakdown_term(
                        &breakdown,
                        "waypoint_distance",
                        double(waypoint_terms.waypoint_distance)
                    );
                }
                if (double(waypoint_terms.waypoint_cross_track) != 0.0) {
                    add_breakdown_term(
                        &breakdown,
                        "waypoint_cross_track",
                        double(waypoint_terms.waypoint_cross_track)
                    );
                }
                if (double(waypoint_terms.waypoint_proximity) != 0.0) {
                    add_breakdown_term(
                        &breakdown,
                        "waypoint_proximity",
                        double(waypoint_terms.waypoint_proximity)
                    );
                }
                if (waypoint_arrived) {
                    add_breakdown_term(
                        &breakdown,
                        "waypoint_reached_bonus",
                        double(waypoint_terms.waypoint_reached_bonus)
                    );
                    if (
                        !had_post_waypoint_transition_before &&
                        execution_step.waypoint_episode_success
                    ) {
                        add_breakdown_term(
                            &breakdown,
                            "waypoint_success_bonus",
                            double(execution_step.waypoint_episode_success_bonus)
                        );
                    }
                }
            }

            if (phase_transition_bonus != 0.0) {
                add_breakdown_term(&breakdown, "phase_transition_bonus", phase_transition_bonus);
            }

            if (execution_step.objective_evaluated && execution_step.matched_objective_index >= 0) {
                if (double(execution_step.objective.success_runway_cross_penalty) != 0.0) {
                    add_breakdown_term(
                        &breakdown,
                        "success_runway_cross_penalty",
                        double(execution_step.objective.success_runway_cross_penalty)
                    );
                }
                if (double(execution_step.objective.success_ground_track_error_penalty) != 0.0) {
                    add_breakdown_term(
                        &breakdown,
                        "success_ground_track_error_penalty",
                        double(execution_step.objective.success_ground_track_error_penalty)
                    );
                }
                add_breakdown_term(
                    &breakdown,
                    "objective_bonus",
                    double(execution_step.objective.objective_bonus)
                );
            }
        }

        double tracked_total = 0.0;
        for (auto it = breakdown.begin(); it != breakdown.end(); ++it) {
            if (!it.value().is_number()) {
                continue;
            }
            tracked_total += it.value().get<double>();
        }
        breakdown["tracked_total"] = tracked_total;
        breakdown["untracked"] = reward_total - tracked_total;
        breakdown["total"] = reward_total;
    }

    state->last_reward_total = reward_total;
    state->last_reward_breakdown_json = stable_json_dump(breakdown);
    if (result != nullptr) {
        result->valid = products.valid;
        result->reward_total = reward_total;
        result->terminated = bool(products.terminated);
        result->truncated = truncated;
        result->status0 = status0;
        result->status1 = status1;
        result->status2 = status2;
        result->status3 = status3;
        result->step_info_valid = bool(products.step_info_evaluated);
        if (products.step_info_evaluated) {
            result->step_info = products.step_info;
        }
        result->structural_state_changed = structural_state_changed;
    }
}
