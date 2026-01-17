#include "content/unit_definition_loader.h"

#include <fstream>
#include <nlohmann/json.hpp>
#include <spdlog/spdlog.h>

namespace {

bool parse_unit_type(const std::string& value, UnitType* out_type) {
    if (!out_type) return false;
    // spdlog::info("Parsing unit type: '{}'", value);
    if (value == "Aircraft") { *out_type = UnitType::Aircraft; return true; }
    if (value == "Ship") { *out_type = UnitType::Ship; return true; }
    if (value == "Missile") { *out_type = UnitType::Missile; return true; }
    if (value == "Facility") { *out_type = UnitType::Facility; return true; }
    if (value == "C2Node") { *out_type = UnitType::C2Node; return true; }
    if (value == "Sensor") { *out_type = UnitType::Sensor; return true; }
    if (value == "Engine") { *out_type = UnitType::Engine; return true; }
    *out_type = UnitType::Unknown;
    return false;
}

} // namespace

namespace fs = std::filesystem;

// Helper to parse a single JSON object (unit definition)
bool parse_unit_json(const nlohmann::json& entry, UnitDefinition& def, std::string* error) {
    if (!entry.contains("type") || !entry["type"].is_string()) {
        if (error) *error = "Unit entry missing string 'type'.";
        return false;
    }

    std::string type_str = entry["type"].get<std::string>();
    if (!parse_unit_type(type_str, &def.type) || def.type == UnitType::Unknown) {
        if (error) *error = "Unknown unit type: " + type_str;
        return false;
    }

    def.name = entry.value("name", type_str);
    def.mass_kg = entry.value("mass_kg", 0.0);


    if (entry.contains("engine_ref")) {
        def.engine_ref = entry["engine_ref"].get<std::string>();
    }

    if (entry.contains("engine")) {
        const auto& e = entry["engine"];
        def.engine_data.mil_thrust_n = e.value("mil_thrust_n", 0.0);
        def.engine_data.ab_thrust_n = e.value("ab_thrust_n", 0.0);
        def.engine_data.sfc_mil = e.value("sfc_mil", 0.0);
        def.engine_data.sfc_ab = e.value("sfc_ab", 0.0);
        def.engine_data.bypass_ratio = e.value("bypass_ratio", 0.0);
    }

    if (entry.contains("hardpoints") && entry["hardpoints"].is_array()) {
        for (const auto& hp_json : entry["hardpoints"]) {
            Hardpoint hp;
            hp.station_id = hp_json.value("station_id", 0);
            hp.capacity_kg = hp_json.value("capacity_kg", 0.0);
            if (hp_json.contains("type") && hp_json["type"].is_array()) {
                for (const auto& t : hp_json["type"]) {
                    hp.supported_types.push_back(t.get<std::string>());
                }
            }
            def.hardpoints.push_back(hp);
        }
    }

    if (entry.contains("default_loadout") && entry["default_loadout"].is_object()) {
        for (auto& [key, val] : entry["default_loadout"].items()) {
            def.default_loadout[std::stoi(key)] = val.get<std::string>();
        }
    }

    def.health = {100.0, 100.0};
    if (entry.contains("health")) {
        const auto& h = entry["health"];
        def.health.current_hp = h.value("current_hp", def.health.current_hp);
        def.health.max_hp = h.value("max_hp", def.health.max_hp);
    }

    def.has_sensor = false;
    def.sensor = {30000.0, 120.0, 1.0, -1.0, 1.0, 2.0, 0.0, 0.0, 0.0, 0.0};
    
    if (entry.contains("sensor_ref")) {
        def.sensor_ref = entry["sensor_ref"].get<std::string>();
        // Note: We don't set has_sensor=true here yet, because the sensor isn't inline.
        // The factory will handle the assembly.
    } else if (entry.contains("sensor")) {
        def.has_sensor = true;
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
        
        // Backwards compatibility for dopper_notch_width if missing in struct default
        if (s.contains("doppler_notch_width")) {
             // If we add this field to Sensor struct, parse it here
        }
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

    if (entry.contains("airframe")) {
        const auto& af = entry["airframe"];
        def.airframe.empty_mass_kg = af.value("empty_mass_kg", 0.0);
        def.airframe.max_fuel_kg = af.value("max_fuel_kg", 0.0);
        def.airframe.drag_coefficient = af.value("drag_coefficient", 0.02);
        def.airframe.reference_area = af.value("reference_area", 27.0);
        
        def.airframe.length_m = af.value("length_m", 15.0);
        def.airframe.wingspan_m = af.value("wingspan_m", 10.0);
        def.airframe.height_m = af.value("height_m", 5.0);
        def.airframe.configuration = af.value("configuration", "Conventional");
    }

    if (entry.contains("damage_model") && entry["damage_model"].is_object()) {
        const auto& dm = entry["damage_model"];
        if (dm.contains("hitboxes") && dm["hitboxes"].is_array()) {
            int hb_idx = 0;
            for (const auto& hb_json : dm["hitboxes"]) {
                Hitbox hb;
                hb.id = hb_idx++;
                
                if (hb_json.contains("offset") && hb_json["offset"].is_array() && hb_json["offset"].size() >= 3) {
                     hb.offset_x = hb_json["offset"][0];
                     hb.offset_y = hb_json["offset"][1];
                     hb.offset_z = hb_json["offset"][2];
                }
                
                if (hb_json.contains("size") && hb_json["size"].is_array() && hb_json["size"].size() >= 3) {
                     hb.dim_l = hb_json["size"][0];
                     hb.dim_w = hb_json["size"][1];
                     hb.dim_h = hb_json["size"][2];
                }
                
                hb.armor_mm = hb_json.value("armor", 0.0);
                
                if (hb_json.contains("systems") && hb_json["systems"].is_array()) {
                    for (const auto& sys : hb_json["systems"]) {
                        hb.protected_systems.push_back(sys.get<std::string>());
                    }
                }
                def.damage_model.hitboxes.push_back(hb);
            }
        }
    }

    def.has_ammo = entry.value("has_ammo", false);
    def.ammo = {0, 0};
    if (entry.contains("ammo")) {
        def.has_ammo = true;
        const auto& ammo = entry["ammo"];
        def.ammo.missiles_remaining = ammo.value("missiles_remaining", def.ammo.missiles_remaining);
        def.ammo.max_missiles = ammo.value("max_missiles", def.ammo.max_missiles);
    }

    def.has_command_link = entry.value("has_command_link", false);
    def.command_link = {0.0, 0.0};
    if (entry.contains("command_link")) {
        def.has_command_link = true;
        const auto& link = entry["command_link"];
        def.command_link.latency_s = link.value("latency_s", def.command_link.latency_s);
        def.command_link.drop_prob = link.value("drop_prob", def.command_link.drop_prob);
    }

    def.has_data_link = entry.value("has_data_link", false);
    def.data_link_network_id = entry.value("data_link_network_id", 0);

    return true;
}

bool load_file(const std::string& path, std::vector<UnitDefinition>& out_definitions, std::string* error) {
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

    // Support both single object and array "units"
    // Case 1: Root is array (legacy units_demo.json structure inside "units" key)
    if (root.contains("units") && root["units"].is_array()) {
        for (const auto& entry : root["units"]) {
            UnitDefinition def;
            if (parse_unit_json(entry, def, error)) {
                out_definitions.push_back(def);
            } else {
                return false;
            }
        }
    } 
    // Case 2: Root IS the unit object (single file per unit)
    else if (root.contains("name") && root.contains("type")) {
        UnitDefinition def;
        if (parse_unit_json(root, def, error)) {
            out_definitions.push_back(def);
        } else {
            return false;
        }
    } else {
        if (error) *error = "Invalid unit definition JSON: expected 'units' array or a single unit object.";
        return false;
    }
    
    return true;
}

bool load_unit_definitions_json(const std::string& path,
                                std::vector<UnitDefinition>& out_definitions,
                                std::string* error) {
    if (fs::is_directory(path)) {
        // Recursive scan
        for (const auto& entry : fs::recursive_directory_iterator(path)) {
            if (entry.is_regular_file() && entry.path().extension() == ".json") {
                if (!load_file(entry.path().string(), out_definitions, error)) {
                    spdlog::warn("Failed to load file {}: {}", entry.path().string(), (error ? *error : "unknown"));
                    // Continue loading others? For now, yes, just warn.
                }
            }
        }
        return true;
    } else {
        return load_file(path, out_definitions, error);
    }
}
