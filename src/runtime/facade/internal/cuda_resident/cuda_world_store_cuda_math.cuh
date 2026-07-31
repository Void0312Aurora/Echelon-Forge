#pragma once

#include "runtime/contracts/cuda_resident_phase_b_fixture_contract.h"

#include <cmath>

namespace runtime::cuda_resident::detail {

__device__ inline double phase_b_clamp(double value, double lo, double hi) {
    return fmin(fmax(value, lo), hi);
}

__device__ inline double phase_b_deg_to_rad(double value) {
    return value * 3.1415926535897932384626433832795 / 180.0;
}

__device__ inline double phase_b_rad_to_deg(double value) {
    return value * 180.0 / 3.1415926535897932384626433832795;
}

__device__ inline double phase_b_lerp(double a, double b, double t) {
    return a + (b - a) * phase_b_clamp(t, 0.0, 1.0);
}

__device__ inline double phase_b_lookup(double mach, int table) {
    constexpr double x[] = {0.0, 0.8, 0.95, 1.1, 1.6, 2.0};
    constexpr double cl_alpha[] = {1.00, 1.04, 1.10, 0.96, 0.82, 0.72};
    constexpr double cd0[] = {0.00, 0.005, 0.025, 0.040, 0.030, 0.025};
    constexpr double induced[] = {1.00, 1.00, 1.05, 1.12, 1.05, 1.00};
    constexpr double cm_alpha[] = {1.00, 1.00, 0.96, 0.92, 0.86, 0.82};
    constexpr double control[] = {1.00, 1.00, 0.92, 0.78, 0.68, 0.60};
    const double *values = cl_alpha;
    if (table == 1) values = cd0;
    if (table == 2) values = induced;
    if (table == 3) values = cm_alpha;
    if (table == 4) values = control;
    if (mach <= x[0]) return values[0];
    if (mach >= x[5]) return values[5];
    for (int i = 1; i < 6; ++i) {
        if (mach <= x[i]) {
            const double t = (mach - x[i - 1]) / fmax(1.0e-6, x[i] - x[i - 1]);
            return phase_b_lerp(values[i - 1], values[i], t);
        }
    }
    return values[5];
}

__device__ inline double phase_b_canonical(double value, double quantum) {
    if (!isfinite(value) || quantum <= 0.0) return value;
    if (fabs(value) <= quantum * 0.5) return 0.0;
    const double rounded = nearbyint(value / quantum) * quantum;
    return fabs(rounded) <= quantum * 0.5 ? 0.0 : rounded;
}

struct PhaseBAtmosphere {
    double density;
    double temperature;
    double speed_of_sound;
    double wind_x;
};

__device__ inline PhaseBAtmosphere phase_b_atmosphere(double altitude_m) {
    const double h = fmax(0.0, altitude_m);
    double temperature = kPhaseBSeaLevelTemperatureK;
    double pressure = kPhaseBSeaLevelPressurePa;
    if (h < kPhaseBTropopauseAltitudeM) {
        temperature = kPhaseBSeaLevelTemperatureK - kPhaseBLapseRateKPerM * h;
        pressure = kPhaseBSeaLevelPressurePa *
                   pow(1.0 - kPhaseBLapseRateKPerM * h / kPhaseBSeaLevelTemperatureK,
                       kPhaseBGravityMps2 / (kPhaseBGasConstantDryAir * kPhaseBLapseRateKPerM));
    } else {
        temperature = kPhaseBTropopauseTemperatureK;
        pressure = kPhaseBTropopausePressurePa *
                   exp(-kPhaseBGravityMps2 * (h - kPhaseBTropopauseAltitudeM) /
                       (kPhaseBGasConstantDryAir * kPhaseBTropopauseTemperatureK));
    }
    return {
        pressure / (kPhaseBGasConstantDryAir * temperature),
        temperature,
        sqrt(kPhaseBSpecificHeatRatioAir * kPhaseBGasConstantDryAir * temperature),
        kPhaseBWindBaseMps + kPhaseBWindShearMpsPerKm * h / 1000.0,
    };
}

struct PhaseBRotation {
    double cpsi;
    double spsi;
    double ctheta;
    double stheta;
    double cphi;
    double sphi;
};

__device__ inline PhaseBRotation phase_b_rotation(double heading, double pitch, double roll) {
    const double psi = phase_b_deg_to_rad(90.0 - heading);
    const double theta = phase_b_deg_to_rad(-pitch);
    const double phi = phase_b_deg_to_rad(roll);
    return {cos(psi), sin(psi), cos(theta), sin(theta), cos(phi), sin(phi)};
}

__device__ inline void phase_b_world_to_body(double vx, double vy, double vz,
                                             const PhaseBRotation &rot, double *bx, double *by,
                                             double *bz) {
    *bx = rot.cpsi * rot.ctheta * vx + rot.spsi * rot.ctheta * vy - rot.stheta * vz;
    *by = (rot.cpsi * rot.stheta * rot.sphi - rot.spsi * rot.cphi) * vx +
          (rot.spsi * rot.stheta * rot.sphi + rot.cpsi * rot.cphi) * vy +
          rot.ctheta * rot.sphi * vz;
    *bz = (rot.cpsi * rot.stheta * rot.cphi + rot.spsi * rot.sphi) * vx +
          (rot.spsi * rot.stheta * rot.cphi - rot.cpsi * rot.sphi) * vy +
          rot.ctheta * rot.cphi * vz;
}

__device__ inline void phase_b_body_to_world(double bx, double by, double bz,
                                             const PhaseBRotation &rot, double *vx, double *vy,
                                             double *vz) {
    *vx = rot.cpsi * rot.ctheta * bx +
          (rot.cpsi * rot.stheta * rot.sphi - rot.spsi * rot.cphi) * by +
          (rot.cpsi * rot.stheta * rot.cphi + rot.spsi * rot.sphi) * bz;
    *vy = rot.spsi * rot.ctheta * bx +
          (rot.spsi * rot.stheta * rot.sphi + rot.cpsi * rot.cphi) * by +
          (rot.spsi * rot.stheta * rot.cphi - rot.cpsi * rot.sphi) * bz;
    *vz = -rot.stheta * bx + rot.ctheta * rot.sphi * by + rot.ctheta * rot.cphi * bz;
}

__device__ inline double phase_b_first_order(double state, double command, double dt, double tau) {
    if (!isfinite(state)) state = 0.0;
    if (!isfinite(command)) return state;
    if (tau <= 1.0e-6 || dt <= 0.0) return command;
    const double gain = phase_b_clamp(dt / (tau + dt), 0.0, 1.0);
    return state + gain * (command - state);
}

__device__ inline double phase_b_wrap_360(double angle) {
    angle = fmod(angle, 360.0);
    if (angle < 0.0) angle += 360.0;
    return angle;
}

} // namespace runtime::cuda_resident::detail
