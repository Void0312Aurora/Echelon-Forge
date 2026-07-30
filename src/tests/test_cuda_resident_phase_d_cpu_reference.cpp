#include <doctest/doctest.h>

#include <cmath>

#include "runtime/contracts/cuda_resident_phase_d_fixture_contract.h"

namespace {

struct PhaseDReference {
    double speed = 0.0;
    double total_reward = 0.0;
    bool terminated = false;
};

PhaseDReference reference(double vx, double vy, double vz, double altitude_m, double pitch_deg,
                          double roll_deg, double alpha_deg) {
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
        .total_reward = runtime::cuda_resident::kPhaseDSurvivalReward +
                        runtime::cuda_resident::phase_d_speed_reward(speed),
        .terminated = !finite || envelope,
    };
}

} // namespace

TEST_CASE("RB7 CPU reference freezes Phase-D projection semantics independently") {
    using namespace runtime::cuda_resident;
    const PhaseDReference nominal = reference(200.0, 0.0, -0.49, 1499.9, 0.1, -0.02, 0.0);
    CHECK(nominal.speed > 50.0);
    CHECK(nominal.total_reward == doctest::Approx(kPhaseDSurvivalReward));
    CHECK_FALSE(nominal.terminated);

    const PhaseDReference nonfinite = reference(NAN, 0.0, 0.0, 1500.0, 0.0, 0.0, 0.0);
    CHECK(nonfinite.terminated);
    const PhaseDReference outside = reference(200.0, 0.0, 0.0, 50.0, 0.0, 0.0, 0.0);
    CHECK(outside.terminated);
}
