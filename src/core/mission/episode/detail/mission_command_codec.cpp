#include "core/mission/episode/detail/mission_command_codec.h"

#include <cmath>
#include <utility>

namespace episode_controller_detail {

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

double normalize_heading_deg(double heading_deg) {
    double wrapped = std::fmod(heading_deg, 360.0);
    if (wrapped < 0.0) {
        wrapped += 360.0;
    }
    return wrapped;
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
        mission_json["takeoff_procedure_code"] = static_cast<int>(state.mission_command.takeoff_procedure_id);
        mission_json["takeoff_clearance_code"] = static_cast<int>(state.mission_command.takeoff_clearance_id);
        mission_json["takeoff_interval_s"] = state.mission_command.takeoff_interval_s;
        mission_json["runway_slot_code"] = static_cast<int>(state.mission_command.runway_slot_id);
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

}  // namespace episode_controller_detail
