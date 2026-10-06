// Explicit RF content and state-transfer contracts use synthetic inputs.
#include "core/engine/state_transfer_component_reflection.h"
#include "components/systems/ew.h"
#include "components/systems/rf_signal.h"
#include "components/systems/sensor.h"
#include "content/unit_definition_loader.h"
#include <flecs.h>
#include <doctest/doctest.h>
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <limits>

namespace {
Sensor rf_radar() {
    Sensor s = make_unit_definition_default_sensor();
    s.type = static_cast<int>(SensorType::Radar);
    s.rf_eirp_watts = 100.0;
    s.rf_frequency_mhz = 1000.0;
    s.rf_bandwidth_mhz = 20.0;
    return s;
}
ESMReceiver strict_receiver() {
    ESMReceiver r;
    r.require_rf_contract = true;
    r.frequency_min_mhz = 900.0;
    r.frequency_max_mhz = 1100.0;
    r.sensitivity_dbm = -85.0;
    return r;
}
}

TEST_SUITE("air_ew_rf_contract") {
    TEST_CASE("free space receive power has correct units and distance/frequency scaling") {
        // 100 W EIRP at 1 GHz, 10 km: 112.4478 dB free-space loss, 50 dBm transmit.
        CHECK(rf_received_power_dbm(100.0, 1000.0, 10000.0) ==
              doctest::Approx(-62.4477832219));
        const double base = rf_received_power_dbm(100.0, 1000.0, 10000.0);
        CHECK(rf_received_power_dbm(100.0, 1000.0, 20000.0) - base ==
              doctest::Approx(-6.0205999133));
        CHECK(rf_received_power_dbm(100.0, 2000.0, 10000.0) - base ==
              doctest::Approx(-6.0205999133));
        CHECK(rf_received_power_dbm(1000.0, 1000.0, 10000.0) - base == doctest::Approx(10.0));
        CHECK_FALSE(std::isfinite(rf_received_power_dbm(0.0, 1000.0, 10.0)));
        CHECK_FALSE(rf_emission_valid(1.0, std::numeric_limits<double>::infinity(), 1.0));
    }

    TEST_CASE("RF and ESM state survive reflection roundtrip with correct sensor booleans") {
        flecs::world world;
        register_state_transfer_component_reflection(world);
        Sensor sensor = rf_radar();
        sensor.enable_ducting = true;
        sensor.sea_clutter_enabled = false;
        sensor.bearing_only = true;
        const auto sensor_json = world.to_json(&sensor);
        Sensor restored{};
        REQUIRE(world.from_json(&restored, sensor_json.c_str()) != nullptr);
        CHECK(restored.enable_ducting);
        CHECK_FALSE(restored.sea_clutter_enabled);
        CHECK(restored.bearing_only);
        CHECK(restored.type == sensor.type);
        CHECK(restored.rf_eirp_watts == sensor.rf_eirp_watts);
        CHECK(restored.rf_frequency_mhz == sensor.rf_frequency_mhz);
        CHECK(restored.rf_bandwidth_mhz == sensor.rf_bandwidth_mhz);
        ESMReceiver esm = strict_receiver();
        esm.memory_s = 2.0;
        esm.confirmation_scans = 3;
        EmitterDetection d{};
        d.source_id = 51;
        d.has_rf_power = true;
        d.received_power_dbm = -70.0;
        d.sensitivity_margin_db = 15.0;
        d.observed_time_s = 1.25;
        d.confidence = 2.0 / 3.0;
        d.confirmation_count = 2;
        esm.detections.push_back(d);
        const auto esm_json = world.to_json(&esm);
        ESMReceiver restored_esm;
        REQUIRE(world.from_json(&restored_esm, esm_json.c_str()) != nullptr);
        CHECK(restored_esm.require_rf_contract);
        CHECK(restored_esm.frequency_min_mhz == 900.0);
        CHECK(restored_esm.memory_s == 2.0);
        CHECK(restored_esm.confirmation_scans == 3);
        REQUIRE(restored_esm.detections.size() == 1);
        CHECK(restored_esm.detections.front().has_rf_power);
        CHECK(restored_esm.detections.front().received_power_dbm == -70.0);
        CHECK(restored_esm.detections.front().observed_time_s == 1.25);
        CHECK(restored_esm.detections.front().confidence == doctest::Approx(2.0 / 3.0));
        CHECK(restored_esm.detections.front().confirmation_count == 2);
    }

    TEST_CASE("RF content loads inline mounted and jammer fields and rejects malformed groups atomically") {
        using json = nlohmann::json;
        const auto path = std::filesystem::temp_directory_path() / "ef_air_ew_rf_content_test.json";
        const json emission = {{"type", "Radar"}, {"rf_eirp_watts", 100.0},
                               {"rf_frequency_mhz", 1000.0}, {"rf_bandwidth_mhz", 20.0}};
        const json good = {{"type", "Aircraft"}, {"name", "RF_Test"}, {"sensor", emission},
            {"mounted_sensors", json::array({{{"label", "RF"}, {"sensor", emission}}})},
            {"jammer", {{"power_watts", 1000.0}, {"rf_eirp_watts", 100.0},
                         {"rf_frequency_mhz", 1000.0}, {"bandwidth_mhz", 20.0}}},
            {"esm", {{"require_rf_contract", true}, {"frequency_min_mhz", 900.0},
                     {"frequency_max_mhz", 1100.0}, {"memory_s", 2.0}, {"confirmation_scans", 2}}}};
        { std::ofstream(path) << good; }
        std::string error;
        std::vector<UnitDefinition> definitions;
        REQUIRE(load_unit_definitions_json(path.string(), definitions, &error));
        REQUIRE(definitions.size() == 1);
        CHECK(definitions[0].sensor.rf_eirp_watts == 100.0);
        REQUIRE(definitions[0].mounted_sensors.mounts.size() == 1);
        CHECK(definitions[0].mounted_sensors.mounts[0].sensor.rf_frequency_mhz == 1000.0);
        CHECK(definitions[0].jammer_data.rf_eirp_watts == 100.0);
        CHECK(definitions[0].esm_data.require_rf_contract);
        CHECK(definitions[0].esm_data.confirmation_scans == 2);
        for (int defect = 0; defect < 9; ++defect) {
            CAPTURE(defect);
            auto bad = good;
            if (defect == 0) bad["sensor"].erase("rf_frequency_mhz");
            if (defect == 1) bad["sensor"]["rf_eirp_watts"] = 0.0;
            if (defect == 2) bad["mounted_sensors"][0]["sensor"]["rf_bandwidth_mhz"] = "20";
            if (defect == 3) bad["jammer"].erase("bandwidth_mhz");
            if (defect == 4) bad["esm"]["confirmation_scans"] = 1.5;
            if (defect == 5) bad["esm"]["frequency_max_mhz"] = 800.0;
            if (defect == 6) bad["esm"]["memory_s"] = 0.0;
            if (defect == 7) bad["esm"]["sensitivity_dbm"] = nullptr;
            if (defect == 8) bad["esm"]["require_rf_contract"] = "true";
            { std::ofstream(path) << json{{"units", json::array({good, bad})}}; }
            std::vector<UnitDefinition> sentinel(1);
            sentinel[0].name = "Retain";
            error.clear();
            CHECK_FALSE(load_unit_definitions_json(path.string(), sentinel, &error));
            const char *expected[] = {"rf_frequency_mhz", "rf_eirp_watts", "rf_bandwidth_mhz",
                "bandwidth_mhz", "confirmation_scans", "frequency bounds", "memory_s",
                "sensitivity_dbm", "require_rf_contract"};
            CHECK(error.find(expected[defect]) != std::string::npos);
            REQUIRE(sentinel.size() == 1);
            CHECK(sentinel.front().name == "Retain");
        }
        std::filesystem::remove(path);
    }
}
