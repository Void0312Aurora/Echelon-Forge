#pragma once

#include <flecs.h>
#include <cmath>
#include <algorithm>
#include <iostream>
#include "components/basic/common.h"
#include "components/physics/forces.h"
#include "components/physics/dynamics.h"
#include "components/physics/performance.h"
#include "components/command/legacy_command.h"
#include "components/command/pilot_action.h"
#include "core/interfaces/environment_model.h"

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
                    const PilotAction* pilot = it.entity(i).get<PilotAction>();
                    bool has_pilot = (pilot && pilot->active);
                    bool has_legacy = command[i].active;
                    
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
                    
                    double throttle_input = 0.0;
                    
                    // Priority 1: Pilot Action (reuse pilot from above)
                    if (has_pilot) {
                        throttle_input = pilot->throttle;
                    } 
                    // Priority 2: Legacy MovementCommand (Backwards Compatibility)
                    else if (command[i].active) {
                        throttle_input = command[i].throttle_cmd;
                    }

                    throttle_input = std::clamp(throttle_input, 0.0, 1.0);
                    
                    double thrust_magnitude = 0.0;
                    bool afterburner_active = false;
                    if (throttle_input > 0.9) {
                        thrust_magnitude = propulsion[i].ab_thrust_n;
                        afterburner_active = true;
                    } else {
                        thrust_magnitude = propulsion[i].mil_thrust_n * throttle_input;
                    }

                    // [REALISM UPGRADE] Atmosphere & Mach scaling
                    // Derived from War Thunder & Standard Propulsion Theory
                    // 1. Density Effect: Jet thrust drops with air density (sigma)
                    // 2. Ram Effect: Ram air pressure increases mass flow (thrust) with speed
                    
                    if (env_ref && env_ref->model) {
                         AtmosphericData atm = env_ref->model->get_atmosphere_at(transform[i].x, transform[i].y, transform[i].z);
                         
                         double sigma = atm.air_density / kSeaLevelDensity; // Density Ratio
                         if (sigma < 0.01) sigma = 0.01; // Space edge case
                         
                         double mach = 0.0;
                         if (atm.speed_of_sound > 1.0) {
                             mach = speed / atm.speed_of_sound;
                         }
                         
                         // Simple Jet Model: T ~ sigma * (1 + 0.3 * M)
                         // (Based on general performance curves of 4th gen fighters)
                         double ram_factor = 1.0 + 0.3 * mach;  
                         
                         thrust_magnitude *= sigma * ram_factor;
                    }
                    thrust_magnitude = canonicalize_force_scalar(thrust_magnitude);

                    // Cache propulsion state for instruments/observation.
                    propulsion[i].current_thrust_n = thrust_magnitude;
                    propulsion[i].afterburner_active = afterburner_active;

                    const double thrust_fx = canonicalize_projected_force_scalar(thrust_magnitude * nose_x);
                    const double thrust_fy = canonicalize_projected_force_scalar(thrust_magnitude * nose_y);
                    const double thrust_fz = canonicalize_projected_force_scalar(thrust_magnitude * nose_z);

                    forces[i].add_force(
                        thrust_fx,
                        thrust_fy,
                        thrust_fz
                    );
                    

                    
                    // === 4. LIFT (Simplified) ===
                    // For now, we model lift implicitly through the control model
                    // A proper lift model will be added in Phase 2
                    
                    // Ground contact / friction is handled by GroundContactSystem.
                }
            }
        });
}
