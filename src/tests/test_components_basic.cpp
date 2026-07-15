// Basic component-structure tests.
//
// These tests verify that key ECS component types are instantiable
// and that their default values and helper functions behave correctly.
// They are intentionally lightweight — they test data integrity rather
// than system behaviour.

#include "components/basic/common.h"
#include "components/basic/tags.h"
#include "components/combat/common/damage_common.h"
#include "components/combat/health.h"
#include "components/combat/common/weapon_common.h"
#include "components/physics/instruments.h"
#include "components/physics/dynamics.h"
#include "components/command/pilot_action.h"
#include "components/command/mission_command.h"
#include "content/unit_definition_loader.h"
#include "components/tasking/task_order.h"
#include "components/tasking/leader_intent.h"
#include "models/weapons/missile_guidance_types.h"

#include <doctest/doctest.h>

#include <cmath>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

// ---------------------------------------------------------------------------
// TEST_SUITE: components_basic
// ---------------------------------------------------------------------------

TEST_SUITE("components_basic") {

    // --- Math utilities --------------------------------------------------------

    TEST_CASE("math_to_radians") {
        CHECK(Math::to_radians(0.0) == doctest::Approx(0.0));
        CHECK(Math::to_radians(180.0) == doctest::Approx(M_PI));
        CHECK(Math::to_radians(360.0) == doctest::Approx(2.0 * M_PI));
    }

    TEST_CASE("math_to_degrees") {
        CHECK(Math::to_degrees(0.0) == doctest::Approx(0.0));
        CHECK(Math::to_degrees(M_PI) == doctest::Approx(180.0));
        CHECK(Math::to_degrees(2.0 * M_PI) == doctest::Approx(360.0));
    }

    TEST_CASE("math_normalize_heading_deg") {
        CHECK(Math::normalize_heading_deg(0.0) == doctest::Approx(0.0));
        CHECK(Math::normalize_heading_deg(360.0) == doctest::Approx(0.0));
        CHECK(Math::normalize_heading_deg(-90.0) == doctest::Approx(270.0));
        CHECK(Math::normalize_heading_deg(450.0) == doctest::Approx(90.0));
        CHECK(Math::normalize_heading_deg(NAN) == doctest::Approx(0.0));
        CHECK(Math::normalize_heading_deg(INFINITY) == doctest::Approx(0.0));
    }

    TEST_CASE("math_ground_track_from_velocity") {
        // Eastward velocity => ground track ~90 deg.
        double track = Math::ground_track_deg_from_velocity(100.0, 0.0, 0.0);
        CHECK(track == doctest::Approx(90.0).epsilon(0.01));

        // Northward velocity => ground track ~0 deg.
        track = Math::ground_track_deg_from_velocity(0.0, 100.0, 0.0);
        CHECK(track == doctest::Approx(0.0).epsilon(0.01));

        // Nearly zero horizontal speed => fallback used.
        track = Math::ground_track_deg_from_velocity(0.0, 0.0, 45.0);
        CHECK(track == doctest::Approx(45.0));
    }

    // --- Damage component helpers ----------------------------------------------

    TEST_CASE("damage_component_key_uses_name") {
        DamageComponent c;
        c.name = "left_wing";
        c.system = "flight_control";
        CHECK(damage_component_key(c) == "left_wing");
    }

    TEST_CASE("damage_component_key_falls_back_to_system") {
        DamageComponent c;
        c.system = "hydraulic";
        CHECK(damage_component_key(c) == "hydraulic");
    }

    TEST_CASE("damage_component_key_falls_back_to_unnamed") {
        DamageComponent c;
        CHECK(damage_component_key(c) == "unnamed_component");
    }

    TEST_CASE("damage_component_redundancy_group_key_uses_id") {
        DamageComponent c;
        c.redundancy_group_id = "hyd_group_1";
        c.system = "hydraulic";
        CHECK(damage_component_redundancy_group_key(c) == "hyd_group_1");
    }

    TEST_CASE("damage_component_redundancy_group_key_falls_back_to_numeric") {
        DamageComponent c;
        c.redundancy_group = 3.0;
        c.system = "hydraulic";
        CHECK(damage_component_redundancy_group_key(c) == "hydraulic:rg:3.000000");
    }

    TEST_CASE("damage_component_geometry_defaults_to_axis_aligned_box") {
        DamageComponent c;
        CHECK(c.geometry_primitive == "aabb");
        CHECK(c.geometry_axes[0][0] == doctest::Approx(1.0));
        CHECK(c.geometry_axes[1][1] == doctest::Approx(1.0));
        CHECK(c.geometry_axes[2][2] == doctest::Approx(1.0));
        CHECK(c.geometry_half_extents_m[0] == doctest::Approx(0.0));
        CHECK(c.geometry_vertices_m.empty());
    }

    TEST_CASE("unit_definition_loader_parses_tg_p7_split_receiver_geometry") {
        const std::filesystem::path path =
            std::filesystem::temp_directory_path() / "ef_tg_p7_split_receiver_geometry_test.json";
        {
            std::ofstream file(path);
            file << R"json({
  "name": "F-16C_Block50_TG_P7_Parse_Test",
  "type": "Aircraft",
  "damage_model": {
    "hitboxes": [
      {
        "offset": [0.0, 0.0, 0.0],
        "size": [1.0, 1.0, 1.0],
        "components": [
          {
            "name": "engine_core_afterburner_segment",
            "system": "propulsion",
            "offset": [-5.2, 0.0, -0.2],
            "size": [1.2, 0.5, 0.4],
            "geometry_primitive": "aabb",
            "geometry": {
              "primitive": "aabb",
              "source": "a2_cross_region_ownership_split_candidate",
              "source_parent_component_name": "engine_core",
              "source_segment_id": "engine_core_afterburner_segment",
              "runtime_projection_status": "parse_ready_candidate_not_runtime_active"
            },
            "critical": true
          }
        ]
      }
    ]
  }
})json";
        }

        std::vector<UnitDefinition> definitions;
        std::string error;
        REQUIRE(load_unit_definitions_json(path.string(), definitions, &error));
        REQUIRE(definitions.size() == 1);
        REQUIRE(definitions[0].damage_model.hitboxes.size() == 1);
        REQUIRE(definitions[0].damage_model.hitboxes[0].components.size() == 1);

        const DamageComponent &component = definitions[0].damage_model.hitboxes[0].components[0];
        CHECK(component.name == "engine_core_afterburner_segment");
        CHECK(component.system == "propulsion");
        CHECK(component.critical);
        CHECK(component.offset_x == doctest::Approx(-5.2));
        CHECK(component.dim_l == doctest::Approx(1.2));
        CHECK(component.geometry_primitive == "aabb");
        CHECK(component.geometry_source_ref == "a2_cross_region_ownership_split_candidate");
        CHECK(component.geometry_half_extents_m[0] == doctest::Approx(0.6));
        CHECK(component.geometry_half_extents_m[1] == doctest::Approx(0.25));
        CHECK(component.geometry_half_extents_m[2] == doctest::Approx(0.2));

        std::filesystem::remove(path);
    }

    TEST_CASE("unit_definition_loader_parses_control_surface_aero_tuning_fields") {
        const std::filesystem::path path =
            std::filesystem::temp_directory_path() / "ef_control_surface_aero_tuning_test.json";
        {
            std::ofstream file(path);
            file << R"json({
  "name": "Control_Surface_Aero_Tuning_Parse_Test",
  "type": "Aircraft",
  "aero_tuning": {
    "enabled": true,
    "elevator_max_deflection_deg": 24.0,
    "aileron_max_deflection_deg": 18.0,
    "rudder_max_deflection_deg": 27.0,
    "cm_delta_e_per_rad": 1.1,
    "cl_delta_a_per_rad": 0.08,
    "cn_delta_r_per_rad": 0.12,
    "fbw_elevator_cmd_per_rate_err": 0.7,
    "fbw_aileron_cmd_per_rate_err": 1.1,
    "fbw_rudder_cmd_per_rate_err": 1.3,
    "ari_rudder_cmd_per_aileron_cmd": 0.2,
    "fbw_g_command_enabled": false,
    "fbw_g_command_neutral": 1.05,
    "fbw_g_command_max": 7.5,
    "fbw_g_command_min": -1.5,
    "fbw_pitch_rate_per_g_err": 0.25,
    "control_effectiveness_scale_vs_mach": [1.0, 0.85, 0.6],
    "actuator_tau_elevator_s": 0.11,
    "actuator_tau_aileron_s": 0.09,
    "actuator_tau_rudder_s": 0.13
  }
})json";
        }

        std::vector<UnitDefinition> definitions;
        std::string error;
        REQUIRE(load_unit_definitions_json(path.string(), definitions, &error));
        REQUIRE(definitions.size() == 1);
        REQUIRE(definitions[0].airframe.has_tuning);

        const AeroTuning &tuning = definitions[0].airframe.tuning;
        CHECK(tuning.elevator_max_deflection_deg == doctest::Approx(24.0));
        CHECK(tuning.aileron_max_deflection_deg == doctest::Approx(18.0));
        CHECK(tuning.rudder_max_deflection_deg == doctest::Approx(27.0));
        CHECK(tuning.cm_delta_e_per_rad == doctest::Approx(1.1));
        CHECK(tuning.cl_delta_a_per_rad == doctest::Approx(0.08));
        CHECK(tuning.cn_delta_r_per_rad == doctest::Approx(0.12));
        CHECK(tuning.fbw_elevator_cmd_per_rate_err == doctest::Approx(0.7));
        CHECK(tuning.fbw_aileron_cmd_per_rate_err == doctest::Approx(1.1));
        CHECK(tuning.fbw_rudder_cmd_per_rate_err == doctest::Approx(1.3));
        CHECK(tuning.ari_rudder_cmd_per_aileron_cmd == doctest::Approx(0.2));
        CHECK_FALSE(tuning.fbw_g_command_enabled);
        CHECK(tuning.fbw_g_command_neutral == doctest::Approx(1.05));
        CHECK(tuning.fbw_g_command_max == doctest::Approx(7.5));
        CHECK(tuning.fbw_g_command_min == doctest::Approx(-1.5));
        CHECK(tuning.fbw_pitch_rate_per_g_err == doctest::Approx(0.25));
        REQUIRE(tuning.control_effectiveness_scale_vs_mach.size() == 3);
        CHECK(tuning.control_effectiveness_scale_vs_mach[1] == doctest::Approx(0.85));
        CHECK(tuning.actuator_tau_elevator_s == doctest::Approx(0.11));
        CHECK(tuning.actuator_tau_aileron_s == doctest::Approx(0.09));
        CHECK(tuning.actuator_tau_rudder_s == doctest::Approx(0.13));

        std::filesystem::remove(path);
    }

    // --- Side enum -------------------------------------------------------------

    TEST_CASE("side_enum_values_are_distinct") {
        CHECK(static_cast<uint8_t>(Side::Blue) != static_cast<uint8_t>(Side::Red));
        CHECK(static_cast<uint8_t>(Side::Blue) != static_cast<uint8_t>(Side::Neutral));
        CHECK(static_cast<uint8_t>(Side::Red) != static_cast<uint8_t>(Side::Neutral));
    }

    // --- InstrumentState defaults ----------------------------------------------

    TEST_CASE("instrument_state_default_altitude_is_zero") {
        InstrumentState inst{};
        CHECK(inst.alt_baro_m == doctest::Approx(0.0));
    }

    // --- Transform coordinate helpers ------------------------------------------

    TEST_CASE("transform_body_to_world_identity") {
        Transform t{};
        t.x = 100.0;
        t.y = 200.0;
        t.z = 300.0;
        t.heading = 0.0;
        t.pitch = 0.0;
        t.roll = 0.0;

        // Body-frame offset at origin → world = body + transform position.
        auto w = Math::body_to_world(Math::Vector3{10.0, 5.0, -2.0}, t.heading, t.pitch, t.roll);
        // ENU: heading=0°=north → body-x (forward) → world +y.
        // With body {10,5,-2}: forward=10→y=10, right=5→x=-5 (west).
        CHECK(w.x == doctest::Approx(-5.0));
        CHECK(w.y == doctest::Approx(10.0));
        CHECK(w.z == doctest::Approx(-2.0));
    }

    TEST_CASE("transform_body_to_world_heading_90") {
        // Heading 90° (east) — body-forward maps to world +x.
        auto w = Math::body_to_world(Math::Vector3{10.0, 0.0, 0.0}, 90.0, 0.0, 0.0);
        CHECK(w.x == doctest::Approx(10.0).epsilon(0.001));
        CHECK(w.y == doctest::Approx(0.0).epsilon(0.001));
        CHECK(w.z == doctest::Approx(0.0).epsilon(0.001));
    }

    // --- PilotAction defaults --------------------------------------------------

    TEST_CASE("pilot_action_defaults") {
        PilotAction pa{};
        // Default-constructed PilotAction should have safe sentinel values.
        CHECK(std::isfinite(pa.stick_roll));
        CHECK(std::isfinite(pa.stick_pitch));
        CHECK(std::isfinite(pa.throttle));
    }

    // --- MissionCommand defaults -----------------------------------------------

    TEST_CASE("mission_command_default_phase_is_zero") {
        MissionCommand mc{};
        CHECK(mc.cmd_heading_deg == doctest::Approx(0.0));
    }

    // --- TaskOrder / LeaderIntent smoke ----------------------------------------

    TEST_CASE("task_order_default_construction") {
        TaskOrder to{};
        // Just verify default construction does not crash and produces
        // a value that survives copy.
        TaskOrder copy = to;
        (void)copy;
    }

    TEST_CASE("leader_intent_default_construction") {
        LeaderIntent li{};
        LeaderIntent copy = li;
        (void)copy;
    }

    // --- Weapon / Warhead structures -------------------------------------------

    TEST_CASE("warhead_profile_default_is_benign") {
        WarheadProfile wp{};
        // Default WarheadProfile uses NaN sentinels; verify they are
        // present (not zeroed, which would silently mask missing data).
        CHECK(std::isnan(wp.mass_kg));
        CHECK(std::isnan(wp.lethal_radius_m));
    }

    TEST_CASE("fuze_profile_default_is_benign") {
        FuzeProfile fp{};
        CHECK(fp.reliability == doctest::Approx(1.0));
    }

    // --- Health defaults -------------------------------------------------------

    TEST_CASE("health_component_defaults") {
        Health h{};
        // Default Health starts at zero — unit definitions set real values.
        CHECK(h.current_hp == doctest::Approx(0.0));
        CHECK(h.max_hp == doctest::Approx(0.0));
    }

    // --- Dynamics / Transform --------------------------------------------------

    TEST_CASE("transform_default_is_origin") {
        Transform t{};
        CHECK(t.x == doctest::Approx(0.0));
        CHECK(t.y == doctest::Approx(0.0));
        CHECK(t.z == doctest::Approx(0.0));
        CHECK(t.heading == doctest::Approx(0.0));
        CHECK(t.pitch == doctest::Approx(0.0));
        CHECK(t.roll == doctest::Approx(0.0));
    }

    // --- SimObject tag ---------------------------------------------------------

    TEST_CASE("sim_object_tag_exists") {
        // SimObject is a tag component — its existence is the only contract.
        SimObject so{};
        (void)so;
    }

    TEST_CASE("missile PN LOS-rate source parses strictly and preserves the unset default") {
        const std::filesystem::path valid_path =
            std::filesystem::temp_directory_path() / "ef_missile_pn_source_valid.json";
        {
            std::ofstream file(valid_path);
            file << R"json({
  "name": "PN_Source_Parse_Test",
  "type": "Missile",
  "flight_model": {"max_speed": 1000.0, "max_g": 30.0, "max_turn_rate": 25.0},
  "guidance": {"pn_los_rate_source": "world_los_history"}
})json";
        }

        std::vector<UnitDefinition> definitions;
        std::string error;
        REQUIRE(load_unit_definitions_json(valid_path.string(), definitions, &error));
        REQUIRE(definitions.size() == 1);
        CHECK(definitions[0].missile_tuning.pn_los_rate_source ==
              static_cast<int>(MissilePnLosRateSource::WorldLosHistory));
        std::filesystem::remove(valid_path);

        const std::filesystem::path default_path =
            std::filesystem::temp_directory_path() / "ef_missile_pn_source_default.json";
        {
            std::ofstream file(default_path);
            file << R"json({
  "name": "PN_Source_Default_Test",
  "type": "Missile",
  "flight_model": {"max_speed": 1000.0, "max_g": 30.0, "max_turn_rate": 25.0}
})json";
        }
        definitions.clear();
        error.clear();
        REQUIRE(load_unit_definitions_json(default_path.string(), definitions, &error));
        REQUIRE(definitions.size() == 1);
        CHECK(definitions[0].missile_tuning.pn_los_rate_source == -1);
        std::filesystem::remove(default_path);

        const std::filesystem::path invalid_path =
            std::filesystem::temp_directory_path() / "ef_missile_pn_source_invalid.json";
        {
            std::ofstream file(invalid_path);
            file << R"json({
  "name": "PN_Source_Invalid_Test",
  "type": "Missile",
  "flight_model": {"max_speed": 1000.0, "max_g": 30.0, "max_turn_rate": 25.0},
  "guidance": {"pn_los_rate_source": "truth_oracle"}
})json";
        }
        definitions.clear();
        error.clear();
        CHECK_FALSE(load_unit_definitions_json(invalid_path.string(), definitions, &error));
        CHECK(error.find("Unknown pn_los_rate_source") != std::string::npos);
        std::filesystem::remove(invalid_path);
    }

} // TEST_SUITE components_basic
