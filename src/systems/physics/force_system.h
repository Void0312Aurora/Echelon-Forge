#pragma once

#include <flecs.h>
#include <cmath>
#include <algorithm>
#include <iostream>
#include "components/basic/common.h"
#include "components/command/air/control_input_resolution.h"
#include "components/physics/forces.h"
#include "components/physics/dynamics.h"
#include "components/physics/flight_dynamics_tuning.h"
#include "components/physics/performance.h"
#include "components/command/legacy_command.h"
#include "components/command/pilot_action.h"
#include "core/interfaces/environment_model.h"
#include "systems/physics/propulsion_system.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace {
    constexpr double kGravity = 9.80665;
    constexpr double kSeaLevelDensity = 1.225;  // kg/m³
    constexpr double kForceScalarCanonicalQuantum = 0x1p-32;
    constexpr double kDirectionScalarCanonicalQuantum = 1.0e-14;
    constexpr double kProjectedForceScalarCanonicalQuantum = 0x1p-32;

    inline double canonicalize_force_scalar(double value) {
        if (!std::isfinite(value) || kForceScalarCanonicalQuantum <= 0.0) {
            return value;
        }
        if (std::abs(value) <= (kForceScalarCanonicalQuantum * 0.5)) {
            return 0.0;
        }
        const double rounded = std::nearbyint(value / kForceScalarCanonicalQuantum) *
            kForceScalarCanonicalQuantum;
        return std::abs(rounded) <= (kForceScalarCanonicalQuantum * 0.5) ? 0.0 : rounded;
    }

    inline double canonicalize_direction_scalar(double value) {
        if (!std::isfinite(value) || kDirectionScalarCanonicalQuantum <= 0.0) {
            return value;
        }
        if (std::abs(value) <= (kDirectionScalarCanonicalQuantum * 0.5)) {
            return 0.0;
        }
        const double rounded = std::nearbyint(value / kDirectionScalarCanonicalQuantum) *
            kDirectionScalarCanonicalQuantum;
        return std::abs(rounded) <= (kDirectionScalarCanonicalQuantum * 0.5) ? 0.0 : rounded;
    }

    inline double canonicalize_projected_force_scalar(double value) {
        if (!std::isfinite(value) || kProjectedForceScalarCanonicalQuantum <= 0.0) {
            return value;
        }
        if (std::abs(value) <= (kProjectedForceScalarCanonicalQuantum * 0.5)) {
            return 0.0;
        }
        const double rounded = std::nearbyint(value / kProjectedForceScalarCanonicalQuantum) *
            kProjectedForceScalarCanonicalQuantum;
        return std::abs(rounded) <= (kProjectedForceScalarCanonicalQuantum * 0.5) ? 0.0 : rounded;
    }
}

/**
 * ForceSystem
 * 
 * Computes all forces acting on aircraft entities and accumulates them
 * into the ForceAccumulator component. Forces include:
 * - Gravity (always downward)
 * - Thrust (along nose direction, controlled by throttle)
 * - Drag (opposite to velocity direction)
 * - Lift (perpendicular to velocity, future enhancement)
 */
inline void register_force_system(flecs::world& ecs) {
    ecs.system<ForceAccumulator, const Transform, const Velocity, 
               const Mass, Propulsion, const FlightModel, const MovementCommand>("ComputeForces")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            const EnvironmentModelRef* env_ref = it.world().get<EnvironmentModelRef>();
            
            while (it.next()) {
                auto forces = it.field<ForceAccumulator>(0);
                auto transform = it.field<const Transform>(1);
                auto velocity = it.field<const Velocity>(2);
                auto mass = it.field<const Mass>(3);
                auto propulsion = it.field<Propulsion>(4);
                auto flight_model = it.field<const FlightModel>(5);
                auto command = it.field<const MovementCommand>(6);
                
                for (auto i : it) {
                    // Check if entity has an active control source
                    // Skip only if BOTH PilotAction and MovementCommand are inactive
                    const PilotAction* pilot = active_pilot_action(it.entity(i).get<PilotAction>());
                    const MovementCommand* legacy = active_legacy_movement_command(&command[i]);
                    bool has_pilot = (pilot != nullptr);
                    bool has_legacy = (legacy != nullptr);
                    
                    if (!has_pilot && !has_legacy) continue;
                    
                    double m = mass[i].get_total_kg();
                    if (m < 1.0) m = 15000.0;  // Fallback
                    
                    // Current speed
                    double vx = velocity[i].vx;
                    double vy = velocity[i].vy;
                    double vz = velocity[i].vz;
                    double speed_sq = vx*vx + vy*vy + vz*vz;
                    double speed = std::sqrt(speed_sq);
                    
                    // === 1. GRAVITY ===
                    // Always acts downward in world frame
                    forces[i].add_force(0.0, 0.0, -m * kGravity);
                    
                    // === 2. THRUST ===
                    // Acts along nose direction
                    double yaw_rad = Math::to_radians(90.0 - transform[i].heading);
                    double pitch_rad = Math::to_radians(transform[i].pitch);
                    
                    double nose_x = canonicalize_direction_scalar(std::cos(yaw_rad) * std::cos(pitch_rad));
                    double nose_y = canonicalize_direction_scalar(std::sin(yaw_rad) * std::cos(pitch_rad));
                    double nose_z = canonicalize_direction_scalar(std::sin(pitch_rad));
                    
                    double throttle_input = resolved_pilot_or_legacy_throttle(pilot, legacy);

                    // [REALISM UPGRADE] Atmosphere & Mach scaling
                    // Derived from War Thunder & Standard Propulsion Theory
                    // 1. Density Effect: Jet thrust drops with air density (sigma)
                    // 2. Ram Effect: Ram air pressure increases mass flow (thrust) with speed
                    flight_dynamics::PropulsionAtmosphereInputs propulsion_inputs{};
                    double oat_temperature_k = 288.15;
                    if (env_ref && env_ref->model) {
                         AtmosphericData atm = env_ref->model->get_atmosphere_at(transform[i].x, transform[i].y, transform[i].z);
                         propulsion_inputs.sigma = atm.air_density / kSeaLevelDensity;
                         if (atm.speed_of_sound > 1.0) {
                             propulsion_inputs.mach = speed / atm.speed_of_sound;
                         }
                         oat_temperature_k = atm.temperature;
                    } else {
                         constexpr double kG = 9.80665;
                         constexpr double kR = 287.0;
                         constexpr double kL = 0.0065;
                         constexpr double kT0 = 288.15;
                         constexpr double kP0 = 101325.0;
                         constexpr double kGamma = 1.4;
                         constexpr double kT11 = 216.65;
                         constexpr double kP11 = 22632.1;

                         const double h = std::max(0.0, transform[i].z);
                         double pressure = kP0;
                         if (h < 11000.0) {
                             oat_temperature_k = kT0 - (kL * h);
                             pressure = kP0 * std::pow(1.0 - (kL * h / kT0), kG / (kR * kL));
                         } else {
                             oat_temperature_k = kT11;
                             pressure = kP11 * std::exp(-kG * (h - 11000.0) / (kR * kT11));
                         }
                         const double rho = pressure / (kR * oat_temperature_k);
                         propulsion_inputs.sigma = rho / kSeaLevelDensity;
                         const double speed_of_sound = std::sqrt(kGamma * kR * oat_temperature_k);
                         if (speed_of_sound > 1.0) {
                             propulsion_inputs.mach = speed / speed_of_sound;
                         }
                    }
                    propulsion_inputs.theta = oat_temperature_k / 288.15;

                    const EngineTuning* attached_tuning = it.entity(i).get<EngineTuning>();
                    EngineTuning runtime_tuning = attached_tuning ? *attached_tuning : flight_dynamics::default_engine_tuning();
                    runtime_tuning.enabled = true;
                    if (runtime_tuning.mil_thrust_n <= 1.0) {
                        runtime_tuning.mil_thrust_n = propulsion[i].mil_thrust_n;
                    }
                    if (runtime_tuning.ab_thrust_n <= runtime_tuning.mil_thrust_n) {
                        runtime_tuning.ab_thrust_n = std::max(propulsion[i].ab_thrust_n, runtime_tuning.mil_thrust_n);
                    }

                    flight_dynamics::advance_propulsion_state(
                        propulsion[i],
                        runtime_tuning,
                        throttle_input,
                        it.delta_time() > 0.0 ? it.delta_time() : 0.05,
                        propulsion_inputs
                    );

                    double thrust_magnitude = propulsion[i].current_thrust_n;
                    thrust_magnitude = canonicalize_force_scalar(thrust_magnitude);

                    // Cache propulsion state for instruments/observation.
                    propulsion[i].current_thrust_n = thrust_magnitude;

                    const double thrust_fx = canonicalize_projected_force_scalar(thrust_magnitude * nose_x);
                    const double thrust_fy = canonicalize_projected_force_scalar(thrust_magnitude * nose_y);
                    const double thrust_fz = canonicalize_projected_force_scalar(thrust_magnitude * nose_z);

                    forces[i].add_force(
                        thrust_fx,
                        thrust_fy,
                        thrust_fz
                    );
                    

                    
                    // Ground contact / friction is handled by GroundContactSystem.
                }
            }
        });
}
