#include "models/weapons/kalman_seeker.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <cmath>
#include <limits>
#include <string_view>

namespace {

constexpr double kPi = 3.14159265358979323846;

struct Vec3 {
    double x;
    double y;
    double z;
};

double distance(Vec3 a, Vec3 b) {
    const double dx = a.x - b.x;
    const double dy = a.y - b.y;
    const double dz = a.z - b.z;
    return std::sqrt(dx * dx + dy * dy + dz * dz);
}

Vec3 truth_state(std::string_view scenario, double t) {
    if (scenario == "weaving_target") {
        const double amp_m = 450.0;
        const double freq_hz = 0.22;
        return {8500.0 - 210.0 * t, 700.0 + amp_m * std::sin(2.0 * kPi * freq_hz * t), 120.0};
    }
    return {8000.0 - 220.0 * t, 900.0 + 18.0 * t, 120.0};
}

bool has_observation(std::string_view scenario, double t) {
    return scenario != "dropout_reacquire" || !(t >= 4.0 && t < 6.0);
}

void truth_to_measurement(Vec3 truth, double &bearing_rad, double &elevation_rad, double &range_m) {
    const double world[3] = {truth.x, truth.y, truth.z};
    const double missile_world[3] = {0.0, 0.0, 0.0};
    missile_seeker::world_to_body_rel(world, missile_world, 0.0, bearing_rad, elevation_rad,
                                      range_m);
}

Vec3 ekf_position(const missile_seeker::SeekerEkfState &ekf) {
    return {ekf.x[0], ekf.x[1], ekf.x[2]};
}

double covariance_block_trace(const missile_seeker::SeekerEkfState &ekf, int start_index) {
    return ekf.P[(start_index + 0) * 9 + start_index + 0] +
           ekf.P[(start_index + 1) * 9 + start_index + 1] +
           ekf.P[(start_index + 2) * 9 + start_index + 2];
}

struct ScenarioResult {
    double final_error_m = 0.0;
    double max_error_m = 0.0;
    double rmse_m = 0.0;
    double min_cov_trace = 0.0;
    double initial_position_cov_trace = 0.0;
    double final_position_cov_trace = 0.0;
    double max_position_cov_trace = 0.0;
    double final_velocity_cov_trace = 0.0;
    double final_accel_cov_trace = 0.0;
    double max_estimate_step_m = 0.0;
    double max_error_step_m = 0.0;
};

ScenarioResult run_observation_scenario(std::string_view scenario) {
    constexpr double dt = 1.0 / 60.0;
    constexpr double duration_s = 12.0;
    constexpr int steps = static_cast<int>(duration_s / dt);

    const double missile_world[3] = {0.0, 0.0, 0.0};
    missile_seeker::SeekerEkfState ekf;
    missile_seeker::SeekerEkfParams params;

    ScenarioResult result;
    result.min_cov_trace = std::numeric_limits<double>::infinity();
    double sum_sq_error_m2 = 0.0;
    int sample_count = 0;
    Vec3 previous_estimate{};
    double previous_error_m = 0.0;
    bool has_previous_estimate = false;

    for (int i = 0; i <= steps; ++i) {
        const double t = i * dt;
        const Vec3 truth = truth_state(scenario, t);

        if (has_observation(scenario, t)) {
            double bearing_rad = 0.0;
            double elevation_rad = 0.0;
            double range_m = 0.0;
            truth_to_measurement(truth, bearing_rad, elevation_rad, range_m);

            if (!ekf.initialized) {
                missile_seeker::ekf_init(ekf, params, bearing_rad, elevation_rad, range_m,
                                         missile_world, 0.0, t);
            } else {
                missile_seeker::ekf_predict(ekf, params, t - ekf.last_predict_time_s);
                missile_seeker::ekf_update(ekf, params, bearing_rad, elevation_rad, range_m,
                                           missile_world, 0.0);
            }
        } else if (ekf.initialized) {
            missile_seeker::ekf_predict(ekf, params, dt);
        }

        REQUIRE(ekf.initialized);
        const double cov_trace = missile_seeker::ekf_covariance_trace(ekf);
        REQUIRE(std::isfinite(cov_trace));
        CHECK(cov_trace >= -1.0e-6);
        result.min_cov_trace = std::min(result.min_cov_trace, cov_trace);

        const double position_cov_trace = covariance_block_trace(ekf, 0);
        const double velocity_cov_trace = covariance_block_trace(ekf, 3);
        const double accel_cov_trace = covariance_block_trace(ekf, 6);
        if (sample_count == 0) {
            result.initial_position_cov_trace = position_cov_trace;
        }
        result.final_position_cov_trace = position_cov_trace;
        result.max_position_cov_trace = std::max(result.max_position_cov_trace, position_cov_trace);
        result.final_velocity_cov_trace = velocity_cov_trace;
        result.final_accel_cov_trace = accel_cov_trace;

        const double err_m = distance(ekf_position(ekf), truth);
        REQUIRE(std::isfinite(err_m));
        result.max_error_m = std::max(result.max_error_m, err_m);
        result.final_error_m = err_m;
        sum_sq_error_m2 += err_m * err_m;

        const Vec3 estimate = ekf_position(ekf);
        if (has_previous_estimate) {
            result.max_estimate_step_m =
                std::max(result.max_estimate_step_m, distance(estimate, previous_estimate));
            result.max_error_step_m =
                std::max(result.max_error_step_m, std::abs(err_m - previous_error_m));
        }
        previous_estimate = estimate;
        previous_error_m = err_m;
        has_previous_estimate = true;
        ++sample_count;
    }

    result.rmse_m = std::sqrt(sum_sq_error_m2 / std::max(1, sample_count));
    return result;
}

} // namespace

TEST_SUITE("kalman_seeker") {

    TEST_CASE("process_noise_covariance_is_consistent") {
        double Q[81] = {};
        missile_seeker::SeekerEkfParams params;
        missile_seeker::singer_Q(1.0 / 60.0, params.maneuver_tau_s, params.process_noise_sigma_a,
                                 Q);

        for (int r = 0; r < 9; ++r) {
            for (int c = 0; c < 9; ++c) {
                CHECK(Q[r * 9 + c] == doctest::Approx(Q[c * 9 + r]));
            }
        }

        for (int axis = 0; axis < 3; ++axis) {
            const int p = axis;
            const int v = 3 + axis;
            const int a = 6 + axis;

            CHECK(Q[p * 9 + p] >= 0.0);
            CHECK(Q[v * 9 + v] >= 0.0);
            CHECK(Q[a * 9 + a] >= 0.0);
            CHECK(Q[p * 9 + v] * Q[p * 9 + v] <= Q[p * 9 + p] * Q[v * 9 + v] + 1.0e-12);
            CHECK(Q[p * 9 + a] * Q[p * 9 + a] <= Q[p * 9 + p] * Q[a * 9 + a] + 1.0e-12);
            CHECK(Q[v * 9 + a] * Q[v * 9 + a] <= Q[v * 9 + v] * Q[a * 9 + a] + 1.0e-12);
        }
    }

    TEST_CASE("observation_update_remains_stable_for_guidance_scenarios") {
        const ScenarioResult constant = run_observation_scenario("constant_velocity");
        CHECK(constant.rmse_m < 15.0);
        CHECK(constant.max_error_m < 60.0);
        CHECK(constant.final_error_m < 20.0);

        const ScenarioResult reacquire = run_observation_scenario("dropout_reacquire");
        CHECK(reacquire.rmse_m < 35.0);
        CHECK(reacquire.max_error_m < 130.0);
        CHECK(reacquire.final_error_m < 25.0);

        const ScenarioResult weaving = run_observation_scenario("weaving_target");
        CHECK(weaving.rmse_m < 40.0);
        CHECK(weaving.max_error_m < 120.0);
        CHECK(weaving.final_error_m < 60.0);
    }

    TEST_CASE("tracking_covariance_converges_and_weaving_track_is_continuous") {
        const ScenarioResult constant = run_observation_scenario("constant_velocity");
        CHECK(constant.initial_position_cov_trace == doctest::Approx(300.0));
        CHECK(constant.final_position_cov_trace < constant.initial_position_cov_trace * 0.30);
        CHECK(constant.final_velocity_cov_trace < 2000.0);
        CHECK(constant.final_accel_cov_trace < 20000.0);

        const ScenarioResult reacquire = run_observation_scenario("dropout_reacquire");
        CHECK(reacquire.max_position_cov_trace > reacquire.initial_position_cov_trace * 100.0);
        CHECK(reacquire.final_position_cov_trace < reacquire.initial_position_cov_trace * 0.30);
        CHECK(reacquire.final_error_m < 25.0);

        const ScenarioResult weaving = run_observation_scenario("weaving_target");
        CHECK(weaving.final_position_cov_trace < weaving.initial_position_cov_trace * 0.35);
        CHECK(weaving.max_estimate_step_m < 20.0);
        CHECK(weaving.max_error_step_m < 15.0);
        CHECK(weaving.rmse_m < 40.0);
    }

} // TEST_SUITE("kalman_seeker")
