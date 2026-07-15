#include <doctest/doctest.h>

#include "models/weapons/world_cv_alpha_beta_tracker.h"

namespace {

using missile_guidance::Vec3;
using missile_guidance::WorldCvAlphaBetaTrackerInput;
using missile_guidance::WorldCvAlphaBetaTrackerOutput;
using missile_guidance::WorldCvAlphaBetaTrackerParams;
using missile_guidance::WorldCvAlphaBetaTrackerState;
using missile_guidance::operator+;
using missile_guidance::operator-;
using missile_guidance::operator*;

WorldCvAlphaBetaTrackerOutput observe(WorldCvAlphaBetaTrackerState &state,
                                      const WorldCvAlphaBetaTrackerParams &params, double time_s,
                                      const Vec3 &position_world_m) {
    return missile_guidance::update_world_cv_alpha_beta_tracker(
        state, params, WorldCvAlphaBetaTrackerInput{time_s, true, position_world_m, time_s});
}

Vec3 reconstruct_world_measurement(const Vec3 &observer_world_m,
                                   const Vec3 &target_relative_to_observer_m) {
    return observer_world_m + target_relative_to_observer_m;
}

void check_vector(const Vec3 &actual, const Vec3 &expected) {
    CHECK(actual.x == doctest::Approx(expected.x).epsilon(1.0e-12));
    CHECK(actual.y == doctest::Approx(expected.y).epsilon(1.0e-12));
    CHECK(actual.z == doctest::Approx(expected.z).epsilon(1.0e-12));
}

} // namespace

TEST_SUITE("world_cv_alpha_beta_tracker") {

    TEST_CASE("first position and second velocity bootstrap remain explicitly staged") {
        WorldCvAlphaBetaTrackerState state;
        const WorldCvAlphaBetaTrackerParams params{0.8, 0.2};

        const auto first = observe(state, params, 10.0, {100.0, -50.0, 20.0});
        CHECK(first.measurement_accepted);
        CHECK(first.position_valid);
        CHECK_FALSE(first.velocity_valid);
        CHECK(state.accepted_measurement_count == 1);
        check_vector(first.position_world_m, {100.0, -50.0, 20.0});
        check_vector(first.velocity_world_mps, {0.0, 0.0, 0.0});

        const auto second = observe(state, params, 12.0, {120.0, -40.0, 16.0});
        CHECK(second.measurement_accepted);
        CHECK(second.position_valid);
        CHECK_FALSE(second.velocity_valid);
        CHECK(state.accepted_measurement_count == 2);
        check_vector(second.position_world_m, {120.0, -40.0, 16.0});
        check_vector(second.velocity_world_mps, {10.0, 5.0, -2.0});

        const auto third = observe(state, params, 14.0, {140.0, -30.0, 12.0});
        CHECK(third.measurement_accepted);
        CHECK(third.velocity_valid);
        CHECK(state.accepted_measurement_count == 3);
        check_vector(third.position_world_m, {140.0, -30.0, 12.0});
        check_vector(third.velocity_world_mps, {10.0, 5.0, -2.0});
        check_vector(third.acceleration_world_mps2, {0.0, 0.0, 0.0});
    }

    TEST_CASE("repeated and out of order measurement timestamps never correct state") {
        WorldCvAlphaBetaTrackerState state;
        const WorldCvAlphaBetaTrackerParams params{0.8, 0.2};
        observe(state, params, 0.0, {0.0, 0.0, 0.0});
        observe(state, params, 1.0, {10.0, 0.0, 0.0});
        observe(state, params, 2.0, {20.0, 0.0, 0.0});

        const auto accepted_count = state.accepted_measurement_count;
        const Vec3 corrected_position = state.corrected_position_world_m;
        const Vec3 corrected_velocity = state.corrected_velocity_world_mps;
        const double correction_time_s = state.correction_time_s;

        const auto duplicate = missile_guidance::update_world_cv_alpha_beta_tracker(
            state, params, WorldCvAlphaBetaTrackerInput{3.0, true, {900.0, 800.0, 700.0}, 2.0});
        CHECK_FALSE(duplicate.measurement_accepted);
        CHECK(duplicate.measurement_rejected_nonmonotonic);
        CHECK(state.accepted_measurement_count == accepted_count);
        CHECK(state.correction_time_s == correction_time_s);
        check_vector(state.corrected_position_world_m, corrected_position);
        check_vector(state.corrected_velocity_world_mps, corrected_velocity);
        check_vector(duplicate.position_world_m, {30.0, 0.0, 0.0});

        const auto older = missile_guidance::update_world_cv_alpha_beta_tracker(
            state, params, WorldCvAlphaBetaTrackerInput{3.0, true, {-900.0, 0.0, 0.0}, 1.5});
        CHECK_FALSE(older.measurement_accepted);
        CHECK(older.measurement_rejected_nonmonotonic);
        CHECK(state.accepted_measurement_count == accepted_count);
        check_vector(older.position_world_m, {30.0, 0.0, 0.0});
    }

    TEST_CASE("constant velocity track is exact and coast acceleration stays zero") {
        WorldCvAlphaBetaTrackerState state;
        const WorldCvAlphaBetaTrackerParams params{0.65, 0.12};
        const Vec3 initial{500.0, -200.0, 1000.0};
        const Vec3 velocity{-80.0, 35.0, -4.0};

        for (int sample = 0; sample < 5; ++sample) {
            const double time_s = static_cast<double>(sample) * 0.5;
            const auto output = observe(state, params, time_s, initial + velocity * time_s);
            check_vector(output.position_world_m, initial + velocity * time_s);
        }
        REQUIRE(state.velocity_valid);
        check_vector(state.corrected_velocity_world_mps, velocity);

        const auto coast = missile_guidance::update_world_cv_alpha_beta_tracker(
            state, params, WorldCvAlphaBetaTrackerInput{6.0, false, {}, 0.0});
        CHECK(coast.coasted);
        CHECK(coast.velocity_valid);
        CHECK_FALSE(coast.measurement_accepted);
        check_vector(coast.position_world_m, initial + velocity * 6.0);
        check_vector(coast.velocity_world_mps, velocity);
        check_vector(coast.acceleration_world_mps2, {0.0, 0.0, 0.0});
    }

    TEST_CASE("world measurements produce observer independent tracking") {
        WorldCvAlphaBetaTrackerState tracker_a;
        WorldCvAlphaBetaTrackerState tracker_b;
        const WorldCvAlphaBetaTrackerParams params{0.75, 0.15};
        const Vec3 observer_a{0.0, 0.0, 0.0};
        const Vec3 observer_b{2000.0, -3000.0, 400.0};

        for (int sample = 0; sample < 4; ++sample) {
            const double time_s = static_cast<double>(sample);
            const Vec3 target_world{8000.0 - 250.0 * time_s, 900.0 + 40.0 * time_s, 1200.0};
            const Vec3 measurement_a =
                reconstruct_world_measurement(observer_a, target_world - observer_a);
            const Vec3 measurement_b =
                reconstruct_world_measurement(observer_b, target_world - observer_b);
            const auto output_a = observe(tracker_a, params, time_s, measurement_a);
            const auto output_b = observe(tracker_b, params, time_s, measurement_b);

            check_vector(output_a.position_world_m, output_b.position_world_m);
            check_vector(output_a.velocity_world_mps, output_b.velocity_world_mps);
            CHECK(output_a.velocity_valid == output_b.velocity_valid);
        }
    }

    TEST_CASE("alpha beta correction starts after the velocity baseline is admitted") {
        WorldCvAlphaBetaTrackerState state;
        const WorldCvAlphaBetaTrackerParams params{0.5, 0.25};
        observe(state, params, 0.0, {0.0, 0.0, 0.0});
        observe(state, params, 1.0, {10.0, 0.0, 0.0});

        const auto corrected = observe(state, params, 2.0, {24.0, -2.0, 1.0});
        CHECK(corrected.velocity_valid);
        check_vector(corrected.position_world_m, {24.0, -2.0, 1.0});
        check_vector(corrected.velocity_world_mps, {12.0, -1.0, 0.5});
        check_vector(corrected.acceleration_world_mps2, {0.0, 0.0, 0.0});

        const auto alpha_beta = observe(state, params, 3.0, {34.0, -2.0, 1.0});
        check_vector(alpha_beta.position_world_m, {35.0, -2.5, 1.25});
        check_vector(alpha_beta.velocity_world_mps, {11.5, -0.75, 0.375});
    }

} // TEST_SUITE("world_cv_alpha_beta_tracker")
