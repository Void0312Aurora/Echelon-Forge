#pragma once

#include <algorithm>
#include <cmath>

#include "components/basic/common.h"
#include "components/physics/aero_tables.h"
#include "core/interfaces/environment_model.h"

namespace aero_physics {

constexpr double kSeaLevelDensityKgM3 = 1.225;
constexpr double kSeaLevelTemperatureK = 288.15;
constexpr double kSeaLevelPressurePa = 101325.0;
constexpr double kGasConstantDryAir = 287.0;
constexpr double kGravityMps2 = 9.80665;
constexpr double kTroposphereLapseRateKPerM = 0.0065;
constexpr double kSpecificHeatRatioAir = 1.4;
constexpr double kTropopauseAltitudeM = 11000.0;
constexpr double kTropopauseTemperatureK = 216.65;
constexpr double kTropopausePressurePa = 22632.1;
constexpr double kSeaLevelSpeedOfSoundMps = 340.29;

struct AirRelativeFlow {
    AtmosphericData atmosphere{};
    Math::Vector3 velocity_mps{0.0, 0.0, 0.0};
    double speed_sq_m2ps2 = 0.0;
    double speed_mps = 0.0;
    double dynamic_pressure_pa = 0.0;
    double mach = 0.0;
};

inline AtmosphericData standard_atmosphere_at_altitude(double altitude_m) {
    const double h = std::max(0.0, altitude_m);
    double temperature = kSeaLevelTemperatureK;
    double pressure = kSeaLevelPressurePa;
    if (h < kTropopauseAltitudeM) {
        temperature = kSeaLevelTemperatureK - (kTroposphereLapseRateKPerM * h);
        pressure = kSeaLevelPressurePa *
                   std::pow(1.0 - (kTroposphereLapseRateKPerM * h / kSeaLevelTemperatureK),
                            kGravityMps2 / (kGasConstantDryAir * kTroposphereLapseRateKPerM));
    } else {
        temperature = kTropopauseTemperatureK;
        pressure = kTropopausePressurePa *
                   std::exp(-kGravityMps2 * (h - kTropopauseAltitudeM) /
                            (kGasConstantDryAir * kTropopauseTemperatureK));
    }

    AtmosphericData data;
    data.air_density = pressure / (kGasConstantDryAir * temperature);
    data.speed_of_sound = std::sqrt(kSpecificHeatRatioAir * kGasConstantDryAir * temperature);
    data.pressure = pressure;
    data.temperature = temperature;
    data.wind_velocity = {0.0, 0.0, 0.0};
    return data;
}

inline AtmosphericData sample_atmosphere(const Transform &transform,
                                         const EnvironmentModelRef *env_ref) {
    if (env_ref && env_ref->model) {
        return env_ref->model->get_atmosphere_at(transform.x, transform.y, transform.z);
    }
    return standard_atmosphere_at_altitude(transform.z);
}

inline double mach_from_speed(double speed_mps, double speed_of_sound_mps) {
    return speed_of_sound_mps > 1.0 ? speed_mps / speed_of_sound_mps : 0.0;
}

inline double dynamic_pressure(double air_density_kg_m3, double speed_sq_m2ps2) {
    return 0.5 * air_density_kg_m3 * speed_sq_m2ps2;
}

inline AirRelativeFlow compute_air_relative_flow(const Transform &transform,
                                                 const Velocity &velocity,
                                                 const EnvironmentModelRef *env_ref) {
    AirRelativeFlow flow;
    flow.atmosphere = sample_atmosphere(transform, env_ref);
    flow.velocity_mps = {
        velocity.vx - flow.atmosphere.wind_velocity.x,
        velocity.vy - flow.atmosphere.wind_velocity.y,
        velocity.vz - flow.atmosphere.wind_velocity.z,
    };
    flow.speed_sq_m2ps2 = flow.velocity_mps.x * flow.velocity_mps.x +
                          flow.velocity_mps.y * flow.velocity_mps.y +
                          flow.velocity_mps.z * flow.velocity_mps.z;
    flow.speed_mps = std::sqrt(flow.speed_sq_m2ps2);
    flow.dynamic_pressure_pa =
        dynamic_pressure(flow.atmosphere.air_density, flow.speed_sq_m2ps2);
    flow.mach = mach_from_speed(flow.speed_mps, flow.atmosphere.speed_of_sound);
    return flow;
}

} // namespace aero_physics
