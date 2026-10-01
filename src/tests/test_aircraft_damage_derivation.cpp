// Differential regression for the memoized aircraft damage derivation.
//
// derive_aircraft_damage_from_component_state() classifies each component by
// substring tokens in its system name and component key. The classification is
// memoized per thread; this test keeps a verbatim copy of the pre-memoization
// derivation and requires bit-identical AircraftDamageState output for every
// component the shipped unit database defines plus synthetic keys that hit each
// axis-weight branch, at several integrity levels and on repeated calls.

#include "components/domains/air/combat/damage_air.h"
#include "content/unit_definition.h"
#include "content/unit_definition_loader.h"

#include <doctest/doctest.h>

#include <cstring>
#include <filesystem>
#include <string>
#include <utility>
#include <vector>

namespace {

void reference_derive_aircraft_damage(const ComponentDamageState &component_damage,
                                      AircraftDamageState &aircraft_damage) {
    for (const auto &[component_key, integrity] : component_damage.component_integrity) {
        const auto system_it = component_damage.component_system.find(component_key);
        if (system_it == component_damage.component_system.end() || system_it->second.empty()) {
            continue;
        }
        double availability = std::clamp(integrity, 0.0, 1.0);
        const auto group_it = component_damage.component_redundancy_group.find(component_key);
        if (group_it != component_damage.component_redundancy_group.end()) {
            const auto availability_it =
                component_damage.redundancy_group_availability.find(group_it->second);
            if (availability_it != component_damage.redundancy_group_availability.end()) {
                availability = std::clamp(availability_it->second, 0.0, 1.0);
            }
        }

        const std::string &system = system_it->second;
        if (damage_dependency_system_is_air_control_surface(system)) {
            aircraft_damage.flight_control_integrity =
                std::min(aircraft_damage.flight_control_integrity, availability);
            const bool side_specific =
                damage_dependency_system_name_matches(component_key, "left") ||
                damage_dependency_system_name_matches(component_key, "right");
            const bool aileron_like =
                damage_dependency_system_name_matches(component_key, "aileron") ||
                damage_dependency_system_name_matches(component_key, "elevon") ||
                damage_dependency_system_name_matches(component_key, "flaperon");
            const bool elevator_like =
                damage_dependency_system_name_matches(component_key, "elevator") ||
                damage_dependency_system_name_matches(component_key, "horizontal_tail") ||
                damage_dependency_system_name_matches(component_key, "stabilator") ||
                damage_dependency_system_name_matches(component_key, "elevon");
            const bool flap_like = damage_dependency_system_name_matches(component_key, "flap");
            const bool spoiler_like =
                damage_dependency_system_name_matches(component_key, "spoiler");
            const bool thrust_vector_like =
                damage_dependency_system_name_matches(component_key, "thrust_vector") ||
                damage_dependency_system_name_matches(component_key, "vector_actuator");
            const bool cyclic_like = damage_dependency_system_name_matches(component_key, "cyclic");
            const bool collective_like =
                damage_dependency_system_name_matches(component_key, "collective");
            const bool rudder_like = damage_dependency_system_name_matches(component_key, "rudder");

            double roll_weight = 0.0;
            double pitch_weight = 0.0;
            double yaw_weight = 0.0;
            if (aileron_like) {
                roll_weight = std::max(roll_weight, 1.0);
            }
            if (spoiler_like) {
                roll_weight = std::max(roll_weight, 0.85);
            }
            if (flap_like && side_specific) {
                roll_weight = std::max(roll_weight, 0.55);
            }
            if (cyclic_like) {
                roll_weight = std::max(roll_weight, 0.80);
            }
            if (elevator_like) {
                pitch_weight = std::max(pitch_weight, 0.70);
            }
            if (flap_like) {
                pitch_weight = std::max(pitch_weight, 0.55);
            }
            if (thrust_vector_like) {
                pitch_weight = std::max(pitch_weight, 0.75);
                yaw_weight = std::max(yaw_weight, 0.75);
            }
            if (cyclic_like) {
                pitch_weight = std::max(pitch_weight, 0.65);
            }
            if (collective_like) {
                pitch_weight = std::max(pitch_weight, 0.80);
            }
            if (rudder_like) {
                yaw_weight = std::max(yaw_weight, 1.0);
            }
            if (roll_weight > 0.0) {
                aircraft_damage.roll_control_integrity =
                    std::min(aircraft_damage.roll_control_integrity,
                             damage_component_axis_availability(availability, roll_weight));
            }
            if (pitch_weight > 0.0) {
                aircraft_damage.pitch_control_integrity =
                    std::min(aircraft_damage.pitch_control_integrity,
                             damage_component_axis_availability(availability, pitch_weight));
            }
            if (yaw_weight > 0.0) {
                aircraft_damage.yaw_control_integrity =
                    std::min(aircraft_damage.yaw_control_integrity,
                             damage_component_axis_availability(availability, yaw_weight));
            }
            if (damage_dependency_system_name_matches(system, "hydraulic")) {
                aircraft_damage.hydraulic_integrity =
                    std::min(aircraft_damage.hydraulic_integrity, availability);
                aircraft_damage.hydraulic_pressure_availability =
                    std::min(aircraft_damage.hydraulic_pressure_availability, availability);
            }
        }
        if (damage_dependency_system_is_air_sensor(system) ||
            damage_dependency_system_name_matches(system, "avionics") ||
            damage_dependency_system_name_matches(system, "data_link")) {
            aircraft_damage.avionics_integrity =
                std::min(aircraft_damage.avionics_integrity, availability);
        }
        if (damage_dependency_system_name_matches(system, "command") ||
            damage_dependency_system_name_matches(system, "navigation")) {
            aircraft_damage.command_navigation_integrity =
                std::min(aircraft_damage.command_navigation_integrity, availability);
            aircraft_damage.avionics_integrity =
                std::min(aircraft_damage.avionics_integrity, availability);
        }
        if (damage_dependency_system_is_air_propulsion(system)) {
            aircraft_damage.propulsion_integrity =
                std::min(aircraft_damage.propulsion_integrity, availability);
        }
        if (damage_dependency_system_is_air_fuel(system)) {
            aircraft_damage.fuel_system_integrity =
                std::min(aircraft_damage.fuel_system_integrity, availability);
        }
        if (damage_dependency_system_is_air_structure(system)) {
            aircraft_damage.structural_integrity =
                std::min(aircraft_damage.structural_integrity, availability);
        }
        if (damage_dependency_system_is_fire_suppression(system)) {
            aircraft_damage.fire_suppression_integrity =
                std::min(aircraft_damage.fire_suppression_integrity, availability);
        }
        if (damage_dependency_system_name_matches(system, "cockpit") ||
            damage_dependency_system_name_matches(system, "pilot") ||
            damage_dependency_system_name_matches(system, "crew")) {
            aircraft_damage.crew_effectiveness =
                std::min(aircraft_damage.crew_effectiveness, availability);
            aircraft_damage.pilot_effectiveness =
                std::min(aircraft_damage.pilot_effectiveness, availability);
        }
    }
}

std::string resolve_unit_database_path() {
    const std::filesystem::path source_relative{"examples/config/database"};
    if (std::filesystem::exists(source_relative)) {
        return source_relative.string();
    }
    const std::filesystem::path build_relative = std::filesystem::path{".."} / source_relative;
    if (std::filesystem::exists(build_relative)) {
        return build_relative.string();
    }
    return source_relative.string();
}

// (component_key, system) pairs from every damage-model component in the
// shipped database, plus synthetic keys covering each axis-weight token.
std::vector<std::pair<std::string, std::string>> component_corpus() {
    std::vector<std::pair<std::string, std::string>> corpus;
    std::vector<UnitDefinition> definitions;
    std::string error;
    REQUIRE(load_unit_definitions_json(resolve_unit_database_path(), definitions, &error));
    for (const auto &definition : definitions) {
        for (const auto &hitbox : definition.damage_model.hitboxes) {
            for (const auto &component : hitbox.components) {
                corpus.emplace_back(damage_component_key(component), component.system);
            }
        }
    }
    REQUIRE(corpus.size() > 50);
    for (const char *key :
         {"left_aileron", "right_flaperon", "elevon_actuator", "horizontal_tail_actuator",
          "stabilator", "left_flap", "inboard_flap", "spoiler_panel", "thrust_vector_nozzle",
          "vector_actuator", "cyclic_servo", "collective_servo", "rudder_actuator",
          "right_elevator_left_rudder", "plain_surface"}) {
        corpus.emplace_back(key, "flight_control");
        corpus.emplace_back(key, "hydraulic");
    }
    for (const char *system :
         {"radar", "rwr", "esm", "sensor_payload", "engineering", "propeller", "transmission",
          "fuel", "airframe", "fuselage", "structure", "rotor", "tail_rotor", "fire_bottle",
          "extinguisher", "pilot_seat", "crew_station", "mission_systems", ""}) {
        corpus.emplace_back(std::string("synthetic_") + system, system);
    }
    return corpus;
}

bool same_bits(double a, double b) {
    return std::memcmp(&a, &b, sizeof(double)) == 0;
}

void require_identical(const AircraftDamageState &a, const AircraftDamageState &b) {
    CHECK(same_bits(a.structural_integrity, b.structural_integrity));
    CHECK(same_bits(a.flight_control_integrity, b.flight_control_integrity));
    CHECK(same_bits(a.hydraulic_integrity, b.hydraulic_integrity));
    CHECK(same_bits(a.hydraulic_pressure_availability, b.hydraulic_pressure_availability));
    CHECK(same_bits(a.roll_control_integrity, b.roll_control_integrity));
    CHECK(same_bits(a.pitch_control_integrity, b.pitch_control_integrity));
    CHECK(same_bits(a.yaw_control_integrity, b.yaw_control_integrity));
    CHECK(same_bits(a.propulsion_integrity, b.propulsion_integrity));
    CHECK(same_bits(a.fuel_system_integrity, b.fuel_system_integrity));
    CHECK(same_bits(a.avionics_integrity, b.avionics_integrity));
    CHECK(same_bits(a.crew_effectiveness, b.crew_effectiveness));
    CHECK(same_bits(a.pilot_effectiveness, b.pilot_effectiveness));
    CHECK(same_bits(a.command_navigation_integrity, b.command_navigation_integrity));
    CHECK(same_bits(a.fire_suppression_integrity, b.fire_suppression_integrity));
}

} // namespace

TEST_SUITE("aircraft_damage_derivation") {

    TEST_CASE("memoized derivation matches the string-scanning reference per component") {
        const auto corpus = component_corpus();
        for (const double integrity : {1.0, 0.73, 0.31, 0.0, -0.2, 1.4}) {
            for (const auto &[key, system] : corpus) {
                ComponentDamageState state;
                state.component_integrity[key] = integrity;
                state.component_system[key] = system;
                AircraftDamageState expected{};
                AircraftDamageState actual{};
                reference_derive_aircraft_damage(state, expected);
                derive_aircraft_damage_from_component_state(state, actual);
                INFO("component_key=" << key << " system=" << system << " integrity=" << integrity);
                require_identical(expected, actual);
            }
        }
    }

    TEST_CASE("memoized derivation matches the reference on whole damaged airframes") {
        const auto corpus = component_corpus();
        ComponentDamageState state;
        for (size_t i = 0; i < corpus.size(); ++i) {
            const auto &[key, system] = corpus[i];
            state.component_integrity[key] = 1.0 - 0.013 * static_cast<double>(i % 70);
            state.component_system[key] = system;
            if (i % 3 == 0) {
                const std::string group = "group_" + std::to_string(i % 11);
                state.component_redundancy_group[key] = group;
                state.redundancy_group_availability[group] = 0.4 + 0.05 * (i % 11);
            }
        }
        // Repeated calls exercise the warm-cache path against the same input.
        for (int pass = 0; pass < 3; ++pass) {
            AircraftDamageState expected{};
            AircraftDamageState actual{};
            reference_derive_aircraft_damage(state, expected);
            derive_aircraft_damage_from_component_state(state, actual);
            require_identical(expected, actual);
        }
    }

} // TEST_SUITE("aircraft_damage_derivation")
