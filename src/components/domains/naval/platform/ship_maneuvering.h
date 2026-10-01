#pragma once

// Surface-ship maneuvering law (CSG-S1-B).
//
// Pure functions over `ShipPlatform` fields; the per-tick loop lives in
// `systems/domains/naval/ship_motion_system.h`. The law couples surge, yaw,
// and their interaction:
//
// * Surge. Propulsive acceleration A against quadratic resistance,
//       dU/dt = A - c M(r) U |U|.
//   `max_accel_mps2` is the full-ahead acceleration from rest, a0, and the
//   resistance coefficient follows from full ahead balancing resistance at the
//   maximum speed, c = a0 / U_max^2. `max_decel_mps2` is the full-astern
//   (backing) authority. The step is semi-implicit in the resistance, so it is
//   monotone and stays non-negative for any step size.
// * Damage. `mobility_capability` is read as the surviving fraction of
//   propulsive power. Power at speed scales as U^3 (resistance ~ U^2), so the
//   attainable speed is U_max cap^(1/3), reached with the thrust scaled by
//   cap^(2/3). A mobility kill leaves no propulsion: the ship coasts down
//   under resistance alone, still steering while above steerageway.
// * Yaw. First-order Nomoto response r' = (r_c - r) / T with T = T' L / U and
//   an exact exponential step. The commanded rate is bounded by the steady
//   turning circle, |r_c| <= U / R with R = steady_turning_diameter_m / 2, so a
//   full-rudder turn traces a speed-independent circle.
// * Speed loss in a turn. Drift and rudder drag scale the resistance by
//       M(r) = 1 + (1/sigma^2 - 1) (|r| R / U)^2,
//   so that a steady full-rudder turn at an unchanged engine order settles at
//   sigma = `steady_turn_speed_ratio` times the straight-line speed.
//
// Engine orders follow the "make turns for N knots" convention: the order sets
// the straight-line thrust for the ordered speed, so a turn loses speed exactly
// as on trials. A speed regulator only shortens the transient toward the speed
// the current order and turn imply (U_o / sqrt(M)); it never cancels the turn
// loss.
//
// The heading autopilot is a PD law on the heading error e,
//     r_c = T w^2 e - (2 T w - 1) r,
// which with the Nomoto law gives the closed loop T psi'' + psi' = r_c with a
// double pole at -w: a critically damped course change that never overshoots,
// running at the full-rudder rate while the error is large.

#include <algorithm>
#include <cmath>

#include "components/domains/naval/platform/ship_platform.h"

namespace ship_maneuvering {

// Heading-loop natural frequency in units of 1/T (control setting, not a hull
// property). Two keeps the loop well inside the rudder-saturated response while
// staying below wave-frequency yaw.
inline constexpr double kHeadingLoopBandwidthPerYawTime = 2.0;

// Time constant of the machinery speed regulator. It is a control setting,
// not a hull property: it decides when a full-power transient hands over to
// the steady order (within a0 * tau of the target), and it does not change any
// steady state.
inline constexpr double kSpeedRegulatorTimeConstantS = 20.0;

struct Envelope {
    double max_speed_mps = 0.0;
    double resistance_per_m = 0.0;     // c [1/m]
    double ahead_accel_mps2 = 0.0;     // a0
    double astern_accel_mps2 = 0.0;    // backing authority
    double steady_turn_radius_m = 0.0; // R
    double nomoto_time_constant = 0.0; // T' (non-dimensional)
    double length_m = 0.0;
    double steerageway_mps = 0.0;
    double turn_speed_ratio = 1.0; // sigma
};

[[nodiscard]] inline Envelope make_envelope(const ShipPlatform &ship) noexcept {
    Envelope env{};
    env.max_speed_mps = std::max(0.0, ship.max_speed_mps);
    env.ahead_accel_mps2 = std::max(0.0, ship.max_accel_mps2);
    env.astern_accel_mps2 = std::max(0.0, ship.max_decel_mps2);
    env.resistance_per_m = env.max_speed_mps > 0.0
                               ? env.ahead_accel_mps2 / (env.max_speed_mps * env.max_speed_mps)
                               : 0.0;
    env.steady_turn_radius_m = 0.5 * std::max(0.0, ship.steady_turning_diameter_m);
    env.nomoto_time_constant = std::max(1.0e-3, ship.nomoto_time_constant);
    env.length_m = std::max(1.0, ship.length_m);
    env.steerageway_mps = std::max(0.0, ship.steerageway_speed_mps);
    env.turn_speed_ratio = std::clamp(ship.steady_turn_speed_ratio, 0.1, 1.0);
    return env;
}

// Yaw time constant T = T' L / U, evaluated no lower than steerageway.
[[nodiscard]] inline double yaw_time_constant_s(const Envelope &env, double speed_mps) noexcept {
    const double u = std::max({std::abs(speed_mps), env.steerageway_mps, 0.5});
    return env.nomoto_time_constant * env.length_m / u;
}

// Full-rudder yaw-rate bound U / R [rad/s]; zero below steerageway or without a
// declared turning circle (the rudder then has no authority).
[[nodiscard]] inline double max_yaw_rate_rad_s(const Envelope &env, double speed_mps) noexcept {
    const double u = std::abs(speed_mps);
    if (u <= env.steerageway_mps || !(env.steady_turn_radius_m > 0.0)) {
        return 0.0;
    }
    return u / env.steady_turn_radius_m;
}

// Critically damped heading autopilot, saturated at the full-rudder rate.
[[nodiscard]] inline double commanded_yaw_rate_rad_s(const Envelope &env, double speed_mps,
                                                     double heading_error_rad,
                                                     double yaw_rate_rad_s) noexcept {
    const double r_max = max_yaw_rate_rad_s(env, speed_mps);
    if (r_max <= 0.0) {
        return 0.0;
    }
    const double t = yaw_time_constant_s(env, speed_mps);
    const double w = kHeadingLoopBandwidthPerYawTime / t;
    const double command = t * w * w * heading_error_rad - (2.0 * t * w - 1.0) * yaw_rate_rad_s;
    return std::clamp(command, -r_max, r_max);
}

// Exact first-order Nomoto step toward the commanded rate over h.
[[nodiscard]] inline double step_yaw_rate_rad_s(const Envelope &env, double speed_mps,
                                                double yaw_rate_rad_s, double commanded_rad_s,
                                                double h) noexcept {
    const double decay = std::exp(-h / yaw_time_constant_s(env, speed_mps));
    return commanded_rad_s + (yaw_rate_rad_s - commanded_rad_s) * decay;
}

// Resistance multiplier from turning, M(r) >= 1.
[[nodiscard]] inline double turn_resistance_multiplier(const Envelope &env, double speed_mps,
                                                       double yaw_rate_rad_s) noexcept {
    const double r_max = max_yaw_rate_rad_s(env, speed_mps);
    if (r_max <= 0.0) {
        return 1.0;
    }
    const double sigma = env.turn_speed_ratio;
    const double turn_fraction = std::min(1.0, std::abs(yaw_rate_rad_s) / r_max);
    return 1.0 + (1.0 / (sigma * sigma) - 1.0) * turn_fraction * turn_fraction;
}

// Fraction of full thrust available at a surviving power fraction (cap^(2/3)),
// zero at a mobility kill.
[[nodiscard]] inline double propulsive_thrust_fraction(double mobility_capability,
                                                       bool mobility_kill) noexcept {
    if (mobility_kill) {
        return 0.0;
    }
    return std::cbrt(std::pow(std::clamp(mobility_capability, 0.0, 1.0), 2.0));
}

// Highest straight-line speed the surviving power can hold (cap^(1/3) U_max),
// further limited by the declared seaway speed fraction.
[[nodiscard]] inline double attainable_speed_mps(const Envelope &env, double mobility_capability,
                                                 bool mobility_kill,
                                                 double seaway_speed_fraction) noexcept {
    if (mobility_kill) {
        return 0.0;
    }
    return env.max_speed_mps * std::cbrt(std::clamp(mobility_capability, 0.0, 1.0)) *
           std::clamp(seaway_speed_fraction, 0.0, 1.0);
}

// Propulsive acceleration for an engine order: the straight-line thrust that
// holds the ordered speed plus the regulator transient toward the speed that
// order sustains in the current turn, bounded by the available ahead and
// astern authority.
[[nodiscard]] inline double propulsive_accel_mps2(const Envelope &env, double ordered_speed_mps,
                                                  double speed_mps, double turn_multiplier,
                                                  double thrust_fraction) noexcept {
    const double fraction = std::clamp(thrust_fraction, 0.0, 1.0);
    const double ahead = env.ahead_accel_mps2 * fraction;
    const double astern = env.astern_accel_mps2 * fraction;
    const double ordered = std::max(0.0, ordered_speed_mps);
    const double hold = env.resistance_per_m * ordered * ordered;
    const double sustained = ordered / std::sqrt(std::max(1.0, turn_multiplier));
    const double regulate = (sustained - speed_mps) / kSpeedRegulatorTimeConstantS;
    return std::clamp(hold + regulate, -astern, ahead);
}

// Semi-implicit surge step: resistance at the end-of-step speed, so a coasting
// ship decays monotonically toward rest and never reverses.
[[nodiscard]] inline double step_speed_mps(const Envelope &env, double speed_mps,
                                           double propulsive_accel_mps2, double turn_multiplier,
                                           double h) noexcept {
    const double damping = h * env.resistance_per_m * turn_multiplier * std::abs(speed_mps);
    return std::max(0.0, (speed_mps + h * propulsive_accel_mps2) / (1.0 + damping));
}

} // namespace ship_maneuvering
