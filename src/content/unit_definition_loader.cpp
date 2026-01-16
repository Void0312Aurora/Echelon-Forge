#include "content/unit_definition_loader.h"

#include <fstream>
#include <nlohmann/json.hpp>

namespace {

bool parse_unit_type(const std::string& value, UnitType* out_type) {
    if (!out_type) return false;
    if (value == "Aircraft") { *out_type = UnitType::Aircraft; return true; }
    if (value == "Ship") { *out_type = UnitType::Ship; return true; }
    if (value == "Missile") { *out_type = UnitType::Missile; return true; }
    if (value == "Facility") { *out_type = UnitType::Facility; return true; }
    *out_type = UnitType::Unknown;
    return false;
}

} // namespace

bool load_unit_definitions_json(const std::string& path,
                                std::unordered_map<UnitType, UnitDefinition, UnitTypeHash>& out_definitions,
                                std::string* error) {
    std::ifstream file(path);
    if (!file.is_open()) {
        if (error) *error = "Failed to open unit definition file: " + path;
        return false;
    }

    nlohmann::json root;
    try {
        file >> root;
    } catch (const std::exception& ex) {
        if (error) *error = std::string("Failed to parse JSON: ") + ex.what();
        return false;
    }

    if (!root.contains("units") || !root["units"].is_array()) {
        if (error) *error = "Invalid unit definition JSON: missing 'units' array.";
        return false;
    }

    for (const auto& entry : root["units"]) {
        if (!entry.contains("type") || !entry["type"].is_string()) {
            if (error) *error = "Unit entry missing string 'type'.";
            return false;
        }

        UnitDefinition def{};
        std::string type_str = entry["type"].get<std::string>();
        if (!parse_unit_type(type_str, &def.type) || def.type == UnitType::Unknown) {
            if (error) *error = "Unknown unit type: " + type_str;
            return false;
        }

        def.name = entry.value("name", type_str);

        def.health = {100.0, 100.0};
        if (entry.contains("health")) {
            const auto& h = entry["health"];
            def.health.current_hp = h.value("current_hp", def.health.current_hp);
            def.health.max_hp = h.value("max_hp", def.health.max_hp);
        }

        def.has_sensor = true;
        def.sensor = {30000.0, 120.0, 1.0, -1.0, 1.0, 2.0, 0.0, 0.0, 0.0, 0.0};
        if (entry.contains("sensor")) {
            const auto& s = entry["sensor"];
            def.sensor.max_range = s.value("max_range", def.sensor.max_range);
            def.sensor.fov_deg = s.value("fov_deg", def.sensor.fov_deg);
            def.sensor.scan_period = s.value("scan_period", def.sensor.scan_period);
            def.sensor.last_scan_time = s.value("last_scan_time", def.sensor.last_scan_time);
            def.sensor.detection_prob = s.value("detection_prob", def.sensor.detection_prob);
            def.sensor.range_power = s.value("range_power", def.sensor.range_power);
            def.sensor.bearing_noise_std = s.value("bearing_noise_std", def.sensor.bearing_noise_std);
            def.sensor.range_noise_std = s.value("range_noise_std", def.sensor.range_noise_std);
            def.sensor.track_memory_s = s.value("track_memory_s", def.sensor.track_memory_s);
            def.sensor.aspect_influence = s.value("aspect_influence", def.sensor.aspect_influence);
        } else if (entry.contains("has_sensor")) {
            def.has_sensor = entry.value("has_sensor", def.has_sensor);
        }

        def.has_flight_model = entry.value("has_flight_model", false);
        def.flight_model = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
        if (entry.contains("flight_model")) {
            def.has_flight_model = true;
            const auto& fm = entry["flight_model"];
            def.flight_model.max_speed = fm.value("max_speed", def.flight_model.max_speed);
            def.flight_model.min_speed = fm.value("min_speed", def.flight_model.min_speed);
            def.flight_model.max_turn_rate = fm.value("max_turn_rate", def.flight_model.max_turn_rate);
            def.flight_model.max_accel = fm.value("max_accel", def.flight_model.max_accel);
            def.flight_model.max_climb_rate = fm.value("max_climb_rate", def.flight_model.max_climb_rate);
            def.flight_model.max_g = fm.value("max_g", def.flight_model.max_g);
        }

        def.has_score = entry.value("has_score", true);
        def.score = {0.0, 0, 0, 0};
        if (entry.contains("score")) {
            const auto& sc = entry["score"];
            def.score.total_reward = sc.value("total_reward", def.score.total_reward);
            def.score.missiles_fired = sc.value("missiles_fired", def.score.missiles_fired);
            def.score.hits_landed = sc.value("hits_landed", def.score.hits_landed);
            def.score.kills_confirmed = sc.value("kills_confirmed", def.score.kills_confirmed);
        }

        def.has_ammo = entry.value("has_ammo", false);
        def.ammo = {0, 0};
        if (entry.contains("ammo")) {
            def.has_ammo = true;
            const auto& ammo = entry["ammo"];
            def.ammo.missiles_remaining = ammo.value("missiles_remaining", def.ammo.missiles_remaining);
            def.ammo.max_missiles = ammo.value("max_missiles", def.ammo.max_missiles);
        }

        out_definitions[def.type] = def;
    }

    return true;
}
