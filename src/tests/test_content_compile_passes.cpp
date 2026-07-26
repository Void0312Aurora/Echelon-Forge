// Focused tests for the T11 slice-3 ContentCompile passes (I55).
//
// These pin the declared parse -> validate -> resolve pass boundaries added
// behind load_unit_definitions_json: the validate pass's unknown-top-level-key
// diagnostics, the resolve pass's non-mutating pass-through contract, and the
// orchestrator's byte/behaviour parity (a file with an unrecognized top-level
// key loads to the same UnitDefinition as one without it).

#include "content/content_compile_passes.h"
#include "content/unit_definition_loader.h"

#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include <cmath>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

using content_compile::ContentDiagnostic;

TEST_SUITE("content_compile_passes") {

    TEST_CASE("validate whitelist recognizes surveyed keys and rejects unknowns") {
        // Spot-checks across the 106 read keys, the present-but-unread keys, and
        // the underscore-annotation convention.
        CHECK(content_compile::is_recognized_top_level_key("type"));
        CHECK(content_compile::is_recognized_top_level_key("guidance"));
        CHECK(content_compile::is_recognized_top_level_key("max_flight_time_s"));
        CHECK(content_compile::is_recognized_top_level_key("fuse"));            // dual spelling
        CHECK(content_compile::is_recognized_top_level_key("countermeasures"));
        CHECK(content_compile::is_recognized_top_level_key("ew_suite_ref"));    // present-but-unread
        CHECK(content_compile::is_recognized_top_level_key("rcs_profile_ref")); // present-but-unread
        CHECK(content_compile::is_recognized_top_level_key("rcs"));             // present-but-unread
        CHECK(content_compile::is_recognized_top_level_key("_provenance"));     // underscore rule
        CHECK(content_compile::is_recognized_top_level_key("_real_world"));
        CHECK_FALSE(content_compile::is_recognized_top_level_key("totally_unknown_key"));
        CHECK_FALSE(content_compile::is_recognized_top_level_key("engine_reff"));
        CHECK_FALSE(content_compile::is_recognized_top_level_key(""));
    }

    TEST_CASE("validate pass flags exactly the unknown top-level key") {
        const nlohmann::json entry = {
            {"type", "Aircraft"},
            {"name", "Validate_Test_Jet"},
            {"mass_kg", 12000.0},
            {"_provenance", "annotation-should-not-warn"},
            {"ew_suite_ref", "present-but-unread-should-not-warn"},
            {"totally_unknown_key", 42},
        };
        const auto diagnostics = content_compile::validate_unit_json_entry(entry, "synthetic.json");
        REQUIRE(diagnostics.size() == 1);
        CHECK(diagnostics[0].code == "unknown_top_level_key");
        CHECK(diagnostics[0].key == "totally_unknown_key");
        CHECK(diagnostics[0].unit_name == "Validate_Test_Jet");
        CHECK(diagnostics[0].source == "synthetic.json");
        CHECK(static_cast<int>(diagnostics[0].severity) ==
              static_cast<int>(ContentDiagnostic::Severity::Warning));
    }

    TEST_CASE("validate pass is silent on a fully recognized entry") {
        const nlohmann::json entry = {
            {"type", "Aircraft"},
            {"name", "Clean_Jet"},
            {"flight_model", {{"max_speed", 600.0}}},
            {"has_command_link", true},
        };
        CHECK(content_compile::validate_unit_json_entry(entry).empty());
    }

    TEST_CASE("validate pass never throws or rejects on non-object input") {
        CHECK(content_compile::validate_unit_json_entry(nlohmann::json::array()).empty());
        CHECK(content_compile::validate_unit_json_entry(nlohmann::json(7)).empty());
        CHECK(content_compile::validate_unit_json_entry(nlohmann::json("scalar")).empty());
    }

    TEST_CASE("validate pass batches diagnostics across entries") {
        std::vector<nlohmann::json> entries = {
            {{"type", "Aircraft"}, {"name", "A"}, {"bogus_a", 1}},
            {{"type", "Ship"}, {"name", "B"}},
            {{"type", "Missile"}, {"name", "C"}, {"bogus_c1", 1}, {"bogus_c2", 2}},
        };
        const auto diagnostics = content_compile::validate_pass(entries, "batch");
        CHECK(diagnostics.size() == 3);
    }

    TEST_CASE("resolve pass is a non-mutating pass-through with a deferred tally") {
        std::vector<UnitDefinition> definitions(2);
        definitions[0].name = "Ship_A";
        definitions[0].sensor_ref = "AN/SPY-1D";
        definitions[0].default_loadout[1] = "SM-2";
        definitions[1].name = "Jet_B";
        definitions[1].engine_ref = "F110";
        definitions[1].sensor_refs = {"APG-68"};

        const std::vector<UnitDefinition> before = definitions;
        const auto report = content_compile::resolve_pass(definitions);

        // Pass-through: no mutation of the definitions.
        REQUIRE(definitions.size() == before.size());
        CHECK(definitions[0].name == before[0].name);
        CHECK(definitions[0].sensor_ref == before[0].sensor_ref);
        CHECK(definitions[0].default_loadout.size() == before[0].default_loadout.size());
        CHECK(definitions[1].engine_ref == before[1].engine_ref);
        CHECK(definitions[1].sensor_refs.size() == before[1].sensor_refs.size());

        // Deferred-edge tally reflects the inputs (resolution still happens later).
        CHECK(report.definitions == 2);
        CHECK(report.sensor_ref == 1);
        CHECK(report.sensor_refs == 1);
        CHECK(report.engine_ref == 1);
        CHECK(report.default_loadout == 1);
        CHECK(report.definitions_with_deferred_refs == 2);
    }

    TEST_CASE("orchestrator loads identically with an unknown top-level key") {
        // The validate pass must never change the load result: a file carrying an
        // unrecognized top-level key loads to the same UnitDefinition as one
        // without it (parse ignores unknown keys; validate only warns; the
        // warning is discarded by the loader).
        namespace fs = std::filesystem;
        const fs::path directory = fs::temp_directory_path() / "ef_content_compile_pass_test";
        fs::remove_all(directory);
        fs::create_directories(directory);

        const std::string clean = R"json({
  "name": "Orchestrator_Parity_Jet",
  "type": "Aircraft",
  "mass_kg": 9000.0,
  "flight_model": { "max_speed": 610.0, "max_g": 9.0 },
  "has_command_link": true
})json";
        const std::string with_unknown = R"json({
  "name": "Orchestrator_Parity_Jet",
  "type": "Aircraft",
  "mass_kg": 9000.0,
  "flight_model": { "max_speed": 610.0, "max_g": 9.0 },
  "has_command_link": true,
  "totally_unknown_key": {"nested": [1, 2, 3]}
})json";

        const fs::path clean_path = directory / "clean.json";
        const fs::path unknown_path = directory / "unknown.json";
        { std::ofstream(clean_path) << clean; }
        { std::ofstream(unknown_path) << with_unknown; }

        std::vector<UnitDefinition> clean_definitions;
        std::vector<UnitDefinition> unknown_definitions;
        std::string clean_error;
        std::string unknown_error;
        REQUIRE(load_unit_definitions_json(clean_path.string(), clean_definitions, &clean_error));
        REQUIRE(
            load_unit_definitions_json(unknown_path.string(), unknown_definitions, &unknown_error));
        REQUIRE(clean_definitions.size() == 1);
        REQUIRE(unknown_definitions.size() == 1);

        const UnitDefinition &a = clean_definitions[0];
        const UnitDefinition &b = unknown_definitions[0];
        CHECK(a.name == b.name);
        CHECK(static_cast<int>(a.type) == static_cast<int>(b.type));
        CHECK(a.mass_kg == doctest::Approx(b.mass_kg));
        CHECK(a.has_flight_model == b.has_flight_model);
        CHECK(a.flight_model.max_speed == doctest::Approx(b.flight_model.max_speed));
        CHECK(a.flight_model.max_g == doctest::Approx(b.flight_model.max_g));
        CHECK(a.has_command_link == b.has_command_link);

        // The validate pass sees the unknown key and would warn (result ignored
        // by the loader); the load still succeeds and matches the clean load.
        const nlohmann::json unknown_json = nlohmann::json::parse(with_unknown);
        const auto diagnostics =
            content_compile::validate_unit_json_entry(unknown_json, "unknown.json");
        REQUIRE(diagnostics.size() == 1);
        CHECK(diagnostics[0].key == "totally_unknown_key");

        fs::remove_all(directory);
    }

    TEST_CASE("missile tuning parse: all 52 helper keys map to their members (I58)") {
        // Synthetic-face parity for the I58 table-driven parse: a Missile entry
        // whose nested missile_tuning object carries every one of the 52 keys
        // with a distinct sentinel must land each value on the matching
        // MissileTuningDefinition member (a mis-wired key/member would collide
        // or miss). No warhead/fuze/fuse/guidance/sensor blocks are present, so
        // the 52 helper reads are the only writers.
        namespace fs = std::filesystem;
        const fs::path directory = fs::temp_directory_path() / "ef_missile_tuning_all_keys_test";
        fs::remove_all(directory);
        fs::create_directories(directory);

        const std::string all_keys = R"json({
  "type": "Missile",
  "name": "Synthetic_All_Keys_Missile",
  "missile_tuning": {
    "max_speed": 1.5,
    "turn_rate": 2.5,
    "fuse_distance": 3.5,
    "damage": 4.5,
    "seeker_fov_deg": 5.5,
    "seeker_lock_range": 6.5,
    "guidance_delay_s": 7.5,
    "guidance_update_period_s": 8.5,
    "max_flight_time_s": 9.5,
    "nav_gain": 10.5,
    "apn_target_accel_gain": 11.5,
    "sensor_max_range": 12.5,
    "sensor_fov_deg": 13.5,
    "sensor_scan_period": 14.5,
    "sensor_detection_prob": 15.5,
    "sensor_bearing_noise_std": 16.5,
    "sensor_range_noise_std": 17.5,
    "sensor_track_memory_s": 18.5,
    "seeker_type": 7,
    "seeker_activation_range_m": 20.5,
    "seeker_gimbal_limit_deg": 21.5,
    "seeker_ifov_deg": 22.5,
    "bearing_filter_tau_s": 23.5,
    "elevation_filter_tau_s": 24.5,
    "range_filter_tau_s": 25.5,
    "track_break_time_s": 26.5,
    "boost_time_s": 27.5,
    "sustain_time_s": 28.5,
    "boost_thrust_n": 29.5,
    "sustain_thrust_n": 30.5,
    "reference_area_m2": 31.5,
    "cd0_subsonic": 32.5,
    "cd0_supersonic": 33.5,
    "induced_drag_k": 34.5,
    "cd0_mach_breakpoints": [1.0, 2.0, 3.0],
    "cd0_mach_values": [4.0, 5.0],
    "induced_drag_k_mach_breakpoints": [6.0],
    "induced_drag_k_mach_values": [7.0, 8.0, 9.0, 10.0],
    "propellant_mass_kg": 39.5,
    "max_lateral_g": 40.5,
    "autopilot_tau_s": 41.5,
    "autopilot_damping": 42.5,
    "autopilot_order": 9,
    "max_accel_response_g_per_s": 44.5,
    "mach_transonic_start": 45.5,
    "mach_transonic_end": 46.5,
    "cd0_power_on_ratio": 47.5,
    "min_launch_range_m": 48.5,
    "max_launch_off_boresight_deg": 49.5,
    "lobl_required": true,
    "midcourse_datalink_supported": true,
    "use_kalman_seeker": true
  }
})json";

        const fs::path path = directory / "all_keys.json";
        { std::ofstream(path) << all_keys; }

        std::vector<UnitDefinition> defs;
        std::string error;
        REQUIRE(load_unit_definitions_json(path.string(), defs, &error));
        REQUIRE(defs.size() == 1);
        REQUIRE(defs[0].has_missile_tuning);
        const MissileTuningDefinition &mt = defs[0].missile_tuning;

        CHECK(mt.max_speed == doctest::Approx(1.5));
        CHECK(mt.turn_rate == doctest::Approx(2.5));
        CHECK(mt.fuse_distance == doctest::Approx(3.5));
        CHECK(mt.damage == doctest::Approx(4.5));
        CHECK(mt.seeker_fov_deg == doctest::Approx(5.5));
        CHECK(mt.seeker_lock_range == doctest::Approx(6.5));
        CHECK(mt.guidance_delay_s == doctest::Approx(7.5));
        CHECK(mt.guidance_update_period_s == doctest::Approx(8.5));
        CHECK(mt.max_flight_time_s == doctest::Approx(9.5));
        CHECK(mt.nav_gain == doctest::Approx(10.5));
        CHECK(mt.apn_target_accel_gain == doctest::Approx(11.5));
        CHECK(mt.sensor_max_range == doctest::Approx(12.5));
        CHECK(mt.sensor_fov_deg == doctest::Approx(13.5));
        CHECK(mt.sensor_scan_period == doctest::Approx(14.5));
        CHECK(mt.sensor_detection_prob == doctest::Approx(15.5));
        CHECK(mt.sensor_bearing_noise_std == doctest::Approx(16.5));
        CHECK(mt.sensor_range_noise_std == doctest::Approx(17.5));
        CHECK(mt.sensor_track_memory_s == doctest::Approx(18.5));
        CHECK(mt.seeker_type == 7);
        CHECK(mt.seeker_activation_range_m == doctest::Approx(20.5));
        CHECK(mt.seeker_gimbal_limit_deg == doctest::Approx(21.5));
        CHECK(mt.seeker_ifov_deg == doctest::Approx(22.5));
        CHECK(mt.bearing_filter_tau_s == doctest::Approx(23.5));
        CHECK(mt.elevation_filter_tau_s == doctest::Approx(24.5));
        CHECK(mt.range_filter_tau_s == doctest::Approx(25.5));
        CHECK(mt.track_break_time_s == doctest::Approx(26.5));
        CHECK(mt.boost_time_s == doctest::Approx(27.5));
        CHECK(mt.sustain_time_s == doctest::Approx(28.5));
        CHECK(mt.boost_thrust_n == doctest::Approx(29.5));
        CHECK(mt.sustain_thrust_n == doctest::Approx(30.5));
        CHECK(mt.reference_area_m2 == doctest::Approx(31.5));
        CHECK(mt.cd0_subsonic == doctest::Approx(32.5));
        CHECK(mt.cd0_supersonic == doctest::Approx(33.5));
        CHECK(mt.induced_drag_k == doctest::Approx(34.5));
        CHECK(mt.cd0_mach_breakpoints == std::vector<double>{1.0, 2.0, 3.0});
        CHECK(mt.cd0_mach_values == std::vector<double>{4.0, 5.0});
        CHECK(mt.induced_drag_k_mach_breakpoints == std::vector<double>{6.0});
        CHECK(mt.induced_drag_k_mach_values == std::vector<double>{7.0, 8.0, 9.0, 10.0});
        CHECK(mt.propellant_mass_kg == doctest::Approx(39.5));
        CHECK(mt.max_lateral_g == doctest::Approx(40.5));
        CHECK(mt.autopilot_tau_s == doctest::Approx(41.5));
        CHECK(mt.autopilot_damping == doctest::Approx(42.5));
        CHECK(mt.autopilot_order == 9);
        CHECK(mt.max_accel_response_g_per_s == doctest::Approx(44.5));
        CHECK(mt.mach_transonic_start == doctest::Approx(45.5));
        CHECK(mt.mach_transonic_end == doctest::Approx(46.5));
        CHECK(mt.cd0_power_on_ratio == doctest::Approx(47.5));
        CHECK(mt.min_launch_range_m == doctest::Approx(48.5));
        CHECK(mt.max_launch_off_boresight_deg == doctest::Approx(49.5));
        CHECK(mt.lobl_required);
        CHECK(mt.midcourse_datalink_supported);
        CHECK(mt.use_kalman_seeker);

        // The four members not read by the helper stay at their struct defaults.
        CHECK_FALSE(mt.has_warhead_profile);
        CHECK_FALSE(mt.has_fuze_profile);

        fs::remove_all(directory);
    }

    TEST_CASE("missile tuning parse: three-source override order, seed, and missing-key default (I58)") {
        // Parity for the call-side entry -> missile_tuning -> guidance merge: the
        // same helper runs on each source in order, so the last writer wins.
        // reference_area_m2 / boost_time_s are pure helper reads (not guidance
        // aliases), so guidance overrides the nested value; damage is set by
        // source 1 then source 2; max_speed is only seeded from flight_model;
        // sustain_time_s is unset everywhere and keeps its NaN default.
        namespace fs = std::filesystem;
        const fs::path directory = fs::temp_directory_path() / "ef_missile_tuning_merge_test";
        fs::remove_all(directory);
        fs::create_directories(directory);

        const std::string merged = R"json({
  "type": "Missile",
  "name": "Synthetic_Merge_Missile",
  "flight_model": { "max_speed": 900.0 },
  "damage": 1.0,
  "missile_tuning": { "damage": 2.0, "boost_time_s": 20.0 },
  "guidance": { "boost_time_s": 30.0, "reference_area_m2": 3.0 }
})json";

        const fs::path path = directory / "merged.json";
        { std::ofstream(path) << merged; }

        std::vector<UnitDefinition> defs;
        std::string error;
        REQUIRE(load_unit_definitions_json(path.string(), defs, &error));
        REQUIRE(defs.size() == 1);
        REQUIRE(defs[0].has_missile_tuning);
        const MissileTuningDefinition &mt = defs[0].missile_tuning;

        CHECK(mt.damage == doctest::Approx(2.0));            // source 2 over source 1
        CHECK(mt.boost_time_s == doctest::Approx(30.0));     // source 3 over source 2
        CHECK(mt.reference_area_m2 == doctest::Approx(3.0)); // source 3 only
        CHECK(mt.max_speed == doctest::Approx(900.0));       // flight_model seed, never overridden
        CHECK(std::isnan(mt.sustain_time_s));                // unset key keeps default

        fs::remove_all(directory);
    }

    TEST_CASE("direct fields parse: mechanical scalar subset maps to member and keeps default (I61)") {
        // Synthetic-face parity for the I61 table-driven direct-scalar migration
        // (content/detail/unit_definition_direct_fields.inc). The converged
        // purely-mechanical subset is {mass_kg, data_link_network_id}: present
        // keys must land on their matching UnitDefinition members, and omitted
        // keys must keep the exact literal defaults used by the pre-I61 reads.
        // A mis-wired phase macro (wrong member/default) fails these checks.
        namespace fs = std::filesystem;
        const fs::path directory = fs::temp_directory_path() / "ef_unit_direct_fields_test";
        fs::remove_all(directory);
        fs::create_directories(directory);

        const std::string present_json = R"json({
  "type": "Aircraft",
  "name": "Synthetic_Direct_Present",
  "mass_kg": 4242.5,
  "data_link_network_id": 37
})json";
        const std::string absent_json = R"json({
  "type": "Aircraft",
  "name": "Synthetic_Direct_Absent"
})json";

        const fs::path present = directory / "present.json";
        const fs::path absent = directory / "absent.json";
        { std::ofstream(present) << present_json; }
        { std::ofstream(absent) << absent_json; }

        std::vector<UnitDefinition> present_defs;
        std::vector<UnitDefinition> absent_defs;
        std::string error;
        REQUIRE(load_unit_definitions_json(present.string(), present_defs, &error));
        REQUIRE(load_unit_definitions_json(absent.string(), absent_defs, &error));
        REQUIRE(present_defs.size() == 1);
        REQUIRE(absent_defs.size() == 1);

        CHECK(present_defs[0].mass_kg == doctest::Approx(4242.5)); // table-driven read
        CHECK(absent_defs[0].mass_kg == doctest::Approx(0.0));     // literal default preserved
        CHECK(present_defs[0].data_link_network_id == 37);          // late-phase read
        CHECK(absent_defs[0].data_link_network_id == 0);            // literal default preserved

        fs::remove_all(directory);
    }

    TEST_CASE("direct fields parse: phase expansion preserves malformed-key fail-first order (I61)") {
        // Successful-input parity is insufficient: nlohmann conversions throw,
        // so moving a table-driven read across another read changes which bad
        // key fails first. These two probes pin mass_kg's early phase and the
        // data-link field's original position between has_data_link and the
        // clamped data_link_max_reports_per_update read.
        namespace fs = std::filesystem;
        const fs::path directory = fs::temp_directory_path() / "ef_unit_direct_fields_order_test";
        fs::remove_all(directory);
        fs::create_directories(directory);

        const std::string before_data_link_json = R"json({
  "type": "Aircraft",
  "name": "Synthetic_Direct_Order_Before",
  "engine_ref": 17,
  "data_link_network_id": "bad-network-id"
})json";
        const std::string within_data_link_json = R"json({
  "type": "Aircraft",
  "name": "Synthetic_Direct_Order_Within",
  "data_link_network_id": [],
  "data_link_max_reports_per_update": {}
})json";

        const fs::path before_data_link = directory / "before_data_link.json";
        const fs::path within_data_link = directory / "within_data_link.json";
        { std::ofstream(before_data_link) << before_data_link_json; }
        { std::ofstream(within_data_link) << within_data_link_json; }

        const auto thrown_message = [](const fs::path &path) {
            std::vector<UnitDefinition> defs;
            std::string error;
            try {
                (void)load_unit_definitions_json(path.string(), defs, &error);
            } catch (const std::exception &ex) {
                return std::string(ex.what());
            }
            return std::string{};
        };

        const std::string before_message = thrown_message(before_data_link);
        const std::string within_message = thrown_message(within_data_link);
        CHECK(before_message.find("type must be string, but is number") != std::string::npos);
        CHECK(within_message.find("type must be number, but is array") != std::string::npos);

        fs::remove_all(directory);
    }

} // TEST_SUITE content_compile_passes
