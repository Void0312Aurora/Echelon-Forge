#pragma once

#include <flecs.h>
#include <cmath>
#include <iostream>
#include "components/basic/common.h"
#include "components/physics/forces.h"
#include "components/physics/dynamics.h"
#include "components/systems/logistics.h" // For GroundState
#include "components/physics/performance.h" // For LandingGear
#include "core/interfaces/environment_model.h"

namespace {
    // Penalty Method Constants
    constexpr double kGroundSpring = 2000000.0;
    constexpr double kGroundDamper = 350000.0; 
    
    // Default Friction (Fallback)
    constexpr double kMuBraking = 0.8;
}

/**
 * GroundContactSystem
 * 
 * Implements a Penalty Method for ground interaction.
 * Integrates with EnvironmentModel for surface-dependent physics (Friction, Damage).
 */
inline void register_ground_contact_system(flecs::world& ecs, IEnvironmentModel* env) {
    ecs.system<ForceAccumulator, const Transform, const Velocity, const Mass, GroundState>("GroundContact")
        .kind(flecs::OnUpdate)
        // Must run BEFORE Integration but AFTER Aerodynamics
        .run([env](flecs::iter& it) {
            while (it.next()) {
                auto forces = it.field<ForceAccumulator>(0);
                auto transform = it.field<const Transform>(1);
                auto velocity = it.field<const Velocity>(2);
                auto mass = it.field<const Mass>(3);
                auto ground = it.field<GroundState>(4);
                
                for (auto i : it) {
                    double m = mass[i].get_total_kg();
                    if (m < 1.0) m = 15000.0;

                    // 1. Detection: Query Environment
                    // Use current position (x, y)
                    auto terrain = env->get_terrain_at(transform[i].x, transform[i].y);
                    
                    double terrain_z = terrain.elevation;
                    ground[i].terrain_elevation = terrain_z;
                    
                    double z = transform[i].z;
                    
                    // Simple logic: Assume pivot is at CG. Gear extends downwards by l_gear.
                    double gear_height = 2.0; 
                    
                    double penetration = gear_height - (z - terrain_z);
                    
                    bool is_touching = (penetration > 0.0);
                    ground[i].on_ground = is_touching;
                    
                    if (!is_touching) continue;
                    
                    // 2. Normal Force (Spring-Damper)
                    double f_spring = kGroundSpring * penetration;
                    
                    double vz = velocity[i].vz;
                    double f_damper = -kGroundDamper * vz;
                    
                    double Fn = std::max(0.0, f_spring + f_damper); // Unilateral
                    
                    forces[i].add_force(0.0, 0.0, Fn);
                    
                    // 3. Friction & Surface Interaction
                    double vx = velocity[i].vx;
                    double vy = velocity[i].vy;
                    double v_h_sq = vx*vx + vy*vy;
                    
                    if (v_h_sq > 0.001) {
                         double v_h = std::sqrt(v_h_sq);
                         
                         // --- Surface Logic ---
                         double mu_rolling = 0.02; // Default Concrete
                         
                         using Surface = IEnvironmentModel::SurfaceType;
                         bool is_offroad = false;

                         switch (terrain.type) {
                             case Surface::Concrete:   mu_rolling = 0.02; break;
                             case Surface::Asphalt:    mu_rolling = 0.025; break;
                             case Surface::HardPacked: mu_rolling = 0.05; is_offroad = true; break;
                             case Surface::SoftDirt:   mu_rolling = 0.15; is_offroad = true; break;
                             case Surface::Water:      mu_rolling = 0.80; is_offroad = true; break; // Sinking
                             case Surface::Obstacle:   mu_rolling = 1.0;  is_offroad = true; break; // Collision
                             default:                  mu_rolling = 0.10; is_offroad = true; break;
                         }
                         
                         // --- Damage Logic ---
                         // If fast off-road, risk damage or catastrophic drag
                         if (is_offroad && v_h > 40.0) { // > 80 kts
                             // Exponentially increase friction to represent digging in / gear stress
                             // This effectively stops the plane or prevents takeoff
                             mu_rolling *= 5.0; 
                             
                             // In a full ECS, we would emit a 'DamageEvent' or modify Health
                             // For now, the high friction acts as a soft "crash" (can't take off)
                         }

                         double mu = mu_rolling;
                         
                         // Check friction brakes
                         const PilotAction* pilot = it.entity(i).get<PilotAction>();
                         const MovementCommand* cmd = it.entity(i).get<MovementCommand>();
                         
                         bool braking = false;
                         if (pilot && pilot->active) {
                             if (pilot->brake > 0.1) braking = true;
                             if (pilot->throttle < 0.01 && v_h < 10.0) braking = true; // Auto-stop
                         } else if (cmd && cmd->active) {
                             if (cmd->throttle_cmd < 0.01) braking = true;
                         }
                         
                         if (braking) mu = kMuBraking;
                         
                         // Friction vector
                         double f_fric = mu * Fn;
                         double fx = -f_fric * (vx / v_h);
                         double fy = -f_fric * (vy / v_h);
                         
                         forces[i].add_force(fx, fy, 0.0);
                         
                         // 4. Rotational Friction (Yaw Damping)
                         const AngularVelocity* ang_vel = it.entity(i).get<AngularVelocity>();
                         if (ang_vel) {
                             double r = ang_vel->r;
                             if (std::abs(r) > 0.001) {
                                 double mu_rot = 2.0; 
                                 double tau_z = -mu_rot * Fn * r * 0.1;
                                 forces[i].add_torque(0.0, 0.0, tau_z);
                             }
                         }
                    } else {
                         // Static stiction (simplified)
                         if (std::abs(vx) < 0.1 && std::abs(vy) < 0.1) {
                             // Apply small opposing force to zero out creep?
                             // Needed for absolute stillness.
                         }
                    }
                }
            }
        });
}
