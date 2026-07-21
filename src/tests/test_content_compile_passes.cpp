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

} // TEST_SUITE content_compile_passes
