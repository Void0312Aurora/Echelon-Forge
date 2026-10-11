#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include "models/weapons/world_cv_alpha_beta_tracker.h"

#include <array>
#include <cmath>
#include <fstream>
#include <iostream>
#include <numbers>
#include <stdexcept>

namespace {

using missile_guidance::Vec3;
using missile_guidance::WorldCvAlphaBetaTrackerOutput;
using missile_guidance::WorldCvAlphaBetaTrackerParams;
using missile_guidance::WorldCvAlphaBetaTrackerState;

// This is a test adapter, not a new runtime dispatcher. The inverse geometry
// supplies synthetic belief measurements with an independent analytic oracle.
Vec3 reconstruct_measurement(const Vec3 &target, double time_s) {
    Transform observer{};
    observer.x = -200.0 + 35.0 * time_s;
    observer.y = 400.0 - 10.0 * time_s;
    observer.z = 1000.0;
    observer.heading = 27.0 + 3.0 * time_s;
    const Vec3 relative{target.x - observer.x, target.y - observer.y, target.z - observer.z};
    const double rad_to_deg = 180.0 / std::numbers::pi_v<double>;
    const double bearing = std::atan2(relative.x, relative.y) * rad_to_deg - observer.heading;
    const double elevation =
        std::atan2(relative.z, std::hypot(relative.x, relative.y)) * rad_to_deg;
    const auto direction =
        missile_guidance::world_los_from_relative_angles(bearing, elevation, observer);
    return missile_guidance::world_position_from_los_range(
        direction, std::hypot(relative.x, relative.y, relative.z), observer);
}

Vec3 target_at(double time_s) {
    return {5000.0 + 120.0 * time_s, 7000.0 - 80.0 * time_s, 3000.0 + 5.0 * time_s};
}

double vector_error(const Vec3 &actual, const Vec3 &expected) {
    return std::hypot(actual.x - expected.x, actual.y - expected.y, actual.z - expected.z);
}

WorldCvAlphaBetaTrackerOutput qualify_elapsed_time(const WorldCvAlphaBetaTrackerParams &params,
                                                   int ticks_per_second) {
    WorldCvAlphaBetaTrackerState state{};
    WorldCvAlphaBetaTrackerOutput output{};
    // The physical measurement schedule is identical for every timestep:
    // epochs 0, .5, 1, 1.5, 2; then a two-second coast to the same horizon.
    for (int tick = 0; tick <= 4 * ticks_per_second; ++tick) {
        const double time_s = static_cast<double>(tick) / ticks_per_second;
        const bool measurement = tick <= 2 * ticks_per_second && tick % (ticks_per_second / 2) == 0;
        if (measurement) {
            const Vec3 position = reconstruct_measurement(target_at(time_s), time_s);
            CHECK(vector_error(position, target_at(time_s)) < 1.0e-8);
            output = missile_guidance::update_world_cv_alpha_beta_tracker(
                state, params, {time_s, true, position, time_s});
            REQUIRE(output.measurement_accepted);
        } else {
            output = missile_guidance::propagate_world_cv_alpha_beta_tracker(state, time_s);
        }
    }
    CHECK(output.position_valid);
    CHECK(output.velocity_valid);
    CHECK(output.coasted);
    CHECK(output.accepted_measurement_count == 5);
    CHECK(output.state_time_s == 4.0);
    CHECK(vector_error(output.position_world_m, target_at(4.0)) < 1.0e-8);
    CHECK(vector_error(output.velocity_world_mps, {120.0, -80.0, 5.0}) < 1.0e-9);
    return output;
}

} // namespace

TEST_SUITE("air_perception_qualification") {
    TEST_CASE("native adapters qualify equivalent elapsed time and child publication failure") {
        std::ifstream input("tests/fixtures/mechanisms/air_perception_qualification.json");
        REQUIRE(input.good());
        const auto config = nlohmann::json::parse(input);
        REQUIRE(config.at("schema_version") == "echelon_forge.air_perception_qualification.v1");
        REQUIRE(config.at("backend_ref") == "cpu_exact.reference");
        REQUIRE(config.at("clock_policy").at("lane") == "qualification_only");
        REQUIRE(config.at("clock_policy").at("numerical_rate") == "per_second");
        REQUIRE(config.at("clock_policy").at("publication_clock") == "window");
        const auto &parameters = config.at("tracker_parameters");
        const WorldCvAlphaBetaTrackerParams params{
            parameters.at("alpha").get<double>(), parameters.at("beta").get<double>(),
            parameters.at("minimum_velocity_baseline_s").get<double>(),
            parameters.at("maximum_speed_mps").get<double>()};

        nlohmann::json samples = nlohmann::json::array();
        for (const int frequency : {4, 10, 30, 60}) {
            const auto output = qualify_elapsed_time(params, frequency);
            samples.push_back(
                {{"dt_s", 1.0 / frequency},
                 {"horizon_s", output.state_time_s},
                 {"accepted_measurements", output.accepted_measurement_count},
                 {"position_error_m", vector_error(output.position_world_m, target_at(4.0))},
                 {"velocity_error_mps",
                  vector_error(output.velocity_world_mps, {120.0, -80.0, 5.0})}});
        }

        Transform observer{};
        observer.x = 19.0;
        const auto zero_range =
            missile_guidance::world_position_from_los_range({1, 0, 0}, -1, observer);
        CHECK(zero_range.x == observer.x);

        // Throw after the real child updated its native state, before the outer
        // track packet is published. This intentionally makes no rollback claim.
        WorldCvAlphaBetaTrackerState state{};
        missile_guidance::update_world_cv_alpha_beta_tracker(
            state, params, {0.0, true, reconstruct_measurement(target_at(0.0), 0.0), 0.0});
        REQUIRE(state.accepted_measurement_count == 1);
        bool output_published = false;
        auto child_then_publish = [&] {
            const auto output = missile_guidance::update_world_cv_alpha_beta_tracker(
                state, params, {0.5, true, reconstruct_measurement(target_at(0.5), 0.5), 0.5});
            if (output.measurement_accepted) {
                throw std::runtime_error("qualification.child.after_state_before_output");
            }
            output_published = true;
        };
        CHECK_THROWS_WITH_AS(child_then_publish(), "qualification.child.after_state_before_output",
                             std::runtime_error);
        CHECK(state.accepted_measurement_count == 2);
        CHECK(state.last_measurement_time_s == 0.5);
        CHECK_FALSE(output_published);

        const nlohmann::json evidence{
            {"schema_version", "echelon_forge.air_perception_native_evidence.v1"},
            {"config", config},
            {"implementations",
             {"missile_guidance::world_los_from_relative_angles",
              "missile_guidance::world_position_from_los_range",
              "missile_guidance::update_world_cv_alpha_beta_tracker"}},
            {"samples", samples},
            {"child_fault",
             {{"state_changed", true},
              {"output_published", output_published},
              {"rollback_proven", false},
              {"error_code", "qualification.child.after_state_before_output"}}}};
        std::cout << "RFC229_NATIVE_EVIDENCE=" << evidence.dump() << '\n';
    }
}
