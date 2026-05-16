#pragma once

#include <cstdint>
#include <string>
#include <vector>

#include <nlohmann/json.hpp>

#include "core/geometry/spatial_query_runtime.h"
#include "core/mission/episode/execution_episode_state.h"

namespace episode_controller_detail {

std::string stable_json_dump(const nlohmann::json& value);

double json_double_or(const nlohmann::json& value, const char* key, double fallback);
int json_int_or(const nlohmann::json& value, const char* key, int fallback);
std::uint64_t json_uint64_or(const nlohmann::json& value, const char* key, std::uint64_t fallback);
bool json_bool_or(const nlohmann::json& value, const char* key, bool fallback);
std::string json_string_or(const nlohmann::json& value, const char* key, std::string fallback);
std::string trim_copy(std::string value);

bool parse_json_object(const std::string& raw, nlohmann::json* out);
double normalize_heading_deg(double heading_deg);

RecoveryApproachType parse_recovery_approach_type(const nlohmann::json& mission_json);
std::vector<SpatialRouteWaypoint> build_route_waypoints_from_json(const nlohmann::json& mission_json);
void write_mission_command_fields_to_json(const MissionCommand& command, nlohmann::json* mission_json);
MissionCommand build_mission_command_from_json(const nlohmann::json& mission_json);

nlohmann::json build_state_mission_command_json(const ExecutionEpisodeState& state);
void update_state_mission_command_heading(ExecutionEpisodeState* state, double target_heading_deg);
bool update_state_mission_command_targets(
    ExecutionEpisodeState* state,
    double target_heading_deg,
    double target_altitude_m,
    double target_speed_mps
);

}  // namespace episode_controller_detail
