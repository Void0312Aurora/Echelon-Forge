#pragma once

#include <flecs.h>
#include <cmath>
#include <algorithm>
#include <iostream>
#include "components/basic/common.h"
#include "components/command/air/control_input_resolution.h"
#include "components/physics/forces.h"
#include "components/physics/dynamics.h"
#include "components/physics/performance.h"
#include "systems/physics/propulsion_system.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace {
    constexpr double kGravity = 9.80665;
    constexpr double kDirectionScalarCanonicalQuantum = 1.0e-14;
    constexpr double kProjectedForceScalarCanonicalQuantum = 0x1p-32;

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
               const Mass, const Propulsion, const FlightModel>("ComputeForces")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto forces = it.field<ForceAccumulator>(0);
                auto transform = it.field<const Transform>(1);
                auto velocity = it.field<const Velocity>(2);
                auto mass = it.field<const Mass>(3);
                auto propulsion = it.field<const Propulsion>(4);
                auto flight_model = it.field<const FlightModel>(5);
                
                for (auto i : it) {
                    // Maintain a single bridge-owned compatibility seam for flight input presence.
                    const ResolvedAirControlInput control_input = resolve_air_control_input(
                        it.entity(i).get<PilotAction>(),
                        it.entity(i).get<MissionCommandControlState>(),
                        nullptr
                    );
                    if (!control_input.has_primary_flight_control_input) continue;
                    
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
                    double thrust_magnitude = propulsion[i].current_thrust_n;

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
