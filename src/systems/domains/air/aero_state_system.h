#pragma once

#include <flecs.h>
#include <cmath>
#include <algorithm>
#include <iostream>
#include "components/basic/common.h"
#include "components/physics/forces.h"
#include "components/physics/dynamics.h"
#include "core/interfaces/environment_model.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace {
constexpr double kAeroScalarCanonicalQuantum = 1.0e-10;
constexpr double kAeroAngleCanonicalQuantumDeg = 0x1p-40;

inline double canonicalize_aero_scalar(double value, double quantum) {
    if (!std::isfinite(value) || quantum <= 0.0) {
        return value;
    }
    if (std::abs(value) <= (quantum * 0.5)) {
        return 0.0;
    }
    const double rounded = std::nearbyint(value / quantum) * quantum;
    return std::abs(rounded) <= (quantum * 0.5) ? 0.0 : rounded;
}

inline double canonicalize_aero_angle_deg(double value) {
    return canonicalize_aero_scalar(value, kAeroAngleCanonicalQuantumDeg);
}
} // namespace

/**
 * AeroStateSystem
 *
 * Computes aerodynamic state variables:
 * - Angle of Attack (alpha)
 * - Sideslip Angle (beta)
 * - Dynamic Pressure (q)
 * - Mach Number
 */
inline void register_aero_state_system(flecs::world &ecs) {
    ecs.system<AeroState, const Transform, const Velocity>("ComputeAeroState")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter &it) {
            const EnvironmentModelRef *env_ref = it.world().get<EnvironmentModelRef>();
            double dt = it.delta_time();
            if (dt <= 0.0) {
                dt = 0.05;
            }

            while (it.next()) {
                auto aero = it.field<AeroState>(0);
                auto transform = it.field<const Transform>(1);
                auto velocity = it.field<const Velocity>(2);

                for (auto i : it) {
                    // Ground-relative velocity (world frame)
                    double vx_gnd = velocity[i].vx;
                    double vy_gnd = velocity[i].vy;
                    double vz_gnd = velocity[i].vz;

                    // Atmosphere (includes wind). Treat aerodynamic state as air-relative.
                    double rho = 1.225;
                    double speed_of_sound = 340.29;
                    Vec3 wind = {0.0, 0.0, 0.0};

                    if (env_ref && env_ref->model) {
                        auto atmo = env_ref->model->get_atmosphere_at(
                            transform[i].x, transform[i].y, transform[i].z);
                        rho = atmo.air_density;
                        speed_of_sound = atmo.speed_of_sound;
                        wind = atmo.wind_velocity;
                    } else {
                        // US Standard Atmosphere 1976 first two layers.
                        constexpr double kG = 9.80665;
                        constexpr double kR = 287.0;
                        constexpr double kL = 0.0065;
                        constexpr double kT0 = 288.15;
                        constexpr double kP0 = 101325.0;
                        constexpr double kGamma = 1.4;
                        constexpr double kT11 = 216.65;
                        constexpr double kP11 = 22632.1;

                        const double h = std::max(0.0, transform[i].z);
                        double temperature = kT0;
                        double pressure = kP0;
                        if (h < 11000.0) {
                            temperature = kT0 - kL * h;
                            pressure = kP0 * std::pow(1.0 - (kL * h / kT0), kG / (kR * kL));
                        } else {
                            temperature = kT11;
                            pressure = kP11 * std::exp(-kG * (h - 11000.0) / (kR * kT11));
                        }
                        rho = pressure / (kR * temperature);
                        speed_of_sound = std::sqrt(kGamma * kR * temperature);
                    }

                    double vx = vx_gnd - wind.x;
                    double vy = vy_gnd - wind.y;
                    double vz = vz_gnd - wind.z;

                    double v_sq = vx * vx + vy * vy + vz * vz;

                    double v_total = std::sqrt(v_sq);

                    // 2. Dynamic Pressure & Mach
                    aero[i].dynamic_pressure = 0.5 * rho * v_sq;
                    aero[i].mach_number = (speed_of_sound > 1.0) ? (v_total / speed_of_sound) : 0.0;
                    aero[i].dynamic_pressure = canonicalize_aero_scalar(
                        aero[i].dynamic_pressure, kAeroScalarCanonicalQuantum);
                    aero[i].mach_number = canonicalize_aero_angle_deg(aero[i].mach_number);

                    // 3. Body Frame Velocity for Alpha/Beta
                    Math::Vector3 v_body = Math::world_to_body({vx, vy, vz}, transform[i]);

                    // u = Forward (X), v = Side (Y), w = Down (Z-down? No, Z-up system: w is Up)
                    // ...

                    // In this body frame, +Z points up relative to the airframe, so
                    // positive AoA corresponds to airflow coming from below the nose
                    // (negative body-Z component).
                    const double alpha_raw = Math::to_degrees(std::atan2(-v_body.z, v_body.x));

                    // Beta = asin(v_body.y / v_total)
                    double beta_arg = v_body.y / std::max(v_total, 1.0e-6);
                    beta_arg = std::clamp(beta_arg, -1.0, 1.0);
                    const double beta_raw = Math::to_degrees(std::asin(beta_arg));

                    // Smooth low-speed transition to avoid abrupt angle jumps during taxi/takeoff
                    // roll. Keep previous angles at very low speed and blend toward measured values
                    // as speed rises.
                    constexpr double kBlendStartMps = 2.0;
                    constexpr double kBlendEndMps = 8.0;
                    double w = 1.0;
                    if (v_total <= kBlendStartMps) {
                        w = 0.0;
                    } else if (v_total < kBlendEndMps) {
                        w = (v_total - kBlendStartMps) / (kBlendEndMps - kBlendStartMps);
                    }
                    w = std::clamp(w, 0.0, 1.0);

                    const double previous_alpha = aero[i].angle_of_attack;
                    aero[i].angle_of_attack = (1.0 - w) * aero[i].angle_of_attack + w * alpha_raw;
                    aero[i].sideslip_angle = (1.0 - w) * aero[i].sideslip_angle + w * beta_raw;

                    // Clamp for safety
                    aero[i].angle_of_attack =
                        std::max(-90.0, std::min(90.0, aero[i].angle_of_attack));
                    aero[i].sideslip_angle =
                        std::max(-90.0, std::min(90.0, aero[i].sideslip_angle));
                    aero[i].angle_of_attack = canonicalize_aero_angle_deg(aero[i].angle_of_attack);
                    aero[i].sideslip_angle = canonicalize_aero_angle_deg(aero[i].sideslip_angle);

                    aero[i].previous_angle_of_attack = previous_alpha;
                    if (w > 0.0 && dt > 1.0e-6) {
                        aero[i].angle_of_attack_rate_dps = canonicalize_aero_scalar(
                            (aero[i].angle_of_attack - previous_alpha) / dt,
                            kAeroAngleCanonicalQuantumDeg);
                    } else {
                        aero[i].angle_of_attack_rate_dps = 0.0;
                    }
                }
            }
        });
}
