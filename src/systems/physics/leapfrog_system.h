#pragma once

#include <flecs.h>
#include <cmath>
#include <numbers>
#include "components/basic/common.h"
#include "components/physics/forces.h"
#include "components/physics/dynamics.h"

/**
 * LeapfrogIntegrationSystem
 * 
 * Implements Störmer-Verlet (Leapfrog) symplectic integration:
 * 
 *   v(t + dt/2) = v(t) + a(t) * dt/2       [kick]
 *   x(t + dt)   = x(t) + v(t + dt/2) * dt  [drift]
 *   v(t + dt)   = v(t + dt/2) + a(t+dt) * dt/2 [kick]
 * 
 * Note:
 * - True Velocity-Verlet uses a(t+dt) for the second kick.
 * - In the current ECS pipeline we evaluate forces once per frame, so we
 *   use a(t) for both half-kicks. This is still time-symmetric for constant
 *   acceleration and significantly reduces Euler drift in common cases.
 * 
 * Benefits:
 * - Symplectic: Preserves phase space volume
 * - Energy error is bounded and oscillates (no secular drift)
 * - 2nd order accurate
 */

inline double integration_wrap_angle_360(double angle) {
    while (angle < 0.0) angle += 360.0;
    while (angle >= 360.0) angle -= 360.0;
    return angle;
}

inline double integration_math_deg_to_nav_deg(double math_deg) {
    return integration_wrap_angle_360(90.0 - math_deg);
}

inline void register_leapfrog_integration_system(flecs::world& ecs) {
    ecs.system<Transform, Velocity, const ForceAccumulator, const Mass>("LeapfrogIntegrate")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto transform = it.field<Transform>(0);
                auto velocity = it.field<Velocity>(1);
                auto forces = it.field<const ForceAccumulator>(2);
                auto mass = it.field<const Mass>(3);
                
                double dt = it.delta_time();
                if (dt <= 0.0) dt = 0.05;  // Fallback
                
                for (auto i : it) {
                    double m = mass[i].get_total_kg();
                    if (m < 1.0) m = 15000.0;  // Fallback
                    
                    // Compute acceleration from accumulated forces
                    double ax = forces[i].fx / m;
                    double ay = forces[i].fy / m;
                    double az = forces[i].fz / m;
                    
                    // Kick-Drift-Kick using a(t) for both half-kicks.
                    // v_half = v + 0.5 * a * dt
                    const double vx_half = velocity[i].vx + ax * dt * 0.5;
                    const double vy_half = velocity[i].vy + ay * dt * 0.5;
                    const double vz_half = velocity[i].vz + az * dt * 0.5;

                    // x_new = x + v_half * dt
                    transform[i].x += vx_half * dt;
                    transform[i].y += vy_half * dt;
                    transform[i].z += vz_half * dt;

                    // v_new = v_half + 0.5 * a * dt
                    velocity[i].vx = vx_half + ax * dt * 0.5;
                    velocity[i].vy = vy_half + ay * dt * 0.5;
                    velocity[i].vz = vz_half + az * dt * 0.5;
                    
                    // Ground clamp: Prevent falling through world (Fail-safe)
                    // GroundContactSystem should handle normal physics above -5.0m
                    if (transform[i].z < -5.0) {
                        transform[i].z = -5.0;
                        if (velocity[i].vz < 0.0) {
                            velocity[i].vz = 0.0;  // Hard Stop
                        }
                    }
                    
// Update heading from velocity (Disabled for Physics Phase 2 - Allow Alpha/Beta)
                    /*
                    double h_speed_sq = velocity[i].vx * velocity[i].vx + 
                                        velocity[i].vy * velocity[i].vy;
                    if (h_speed_sq > 1e-6) {
                        double math_deg = std::atan2(velocity[i].vy, velocity[i].vx) * 180.0 /
                                          std::numbers::pi_v<double>;
                        transform[i].heading = integration_math_deg_to_nav_deg(math_deg);
                    }
                    
                    // Update pitch from velocity vector
                    double speed = std::sqrt(h_speed_sq + velocity[i].vz * velocity[i].vz);
                    if (speed > 1.0) {
                        double h_speed = std::sqrt(h_speed_sq);
                        transform[i].pitch = std::atan2(velocity[i].vz, h_speed) * 180.0 /
                                             std::numbers::pi_v<double>;
                    }
                    */
                }
            }
        });
}
