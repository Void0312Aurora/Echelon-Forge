#include <doctest/doctest.h>

#include <cmath>

#include "runtime/contracts/cuda_resident_observation_projection_fixture_contract.h"

namespace {

struct ObservationProjectionReference {
    double speed = 0.0;
    double total_reward = 0.0;
    bool terminated = false;
};

ObservationProjectionReference reference(double vx, double vy, double vz, double altitude_m,
                                         double pitch_deg, double roll_deg, double alpha_deg) {
    const double speed = std::sqrt(vx * vx + vy * vy + vz * vz);
    const bool finite = std::isfinite(speed) && std::isfinite(altitude_m) &&
                        std::isfinite(pitch_deg) && std::isfinite(roll_deg) &&
                        std::isfinite(alpha_deg);
    const bool envelope = altitude_m < 100.0 || altitude_m > 10000.0 || speed < 50.0 ||
                          speed > 350.0 || std::abs(vy) > 50.0 || std::abs(vz) > 50.0 ||
                          std::abs(pitch_deg) > 10.0 || std::abs(roll_deg) > 10.0 ||
                          std::abs(alpha_deg) > 14.0;
    return {
        .speed = speed,
        .total_reward = runtime::cuda_resident::kObservationProjectionSurvivalReward +
                        runtime::cuda_resident::observation_projection_speed_reward(speed),
        .terminated = !finite || envelope,
    };
}

} // namespace

TEST_CASE("CPU reference freezes observation-projection semantics independently") {
    using namespace runtime::cuda_resident;
    const ObservationProjectionReference nominal =
        reference(200.0, 0.0, -0.49, 1499.9, 0.1, -0.02, 0.0);
    CHECK(nominal.speed > 50.0);
    CHECK(nominal.total_reward == doctest::Approx(kObservationProjectionSurvivalReward));
    CHECK_FALSE(nominal.terminated);

    const ObservationProjectionReference nonfinite =
        reference(NAN, 0.0, 0.0, 1500.0, 0.0, 0.0, 0.0);
    CHECK(nonfinite.terminated);
    const ObservationProjectionReference outside = reference(200.0, 0.0, 0.0, 50.0, 0.0, 0.0, 0.0);
    CHECK(outside.terminated);
}
