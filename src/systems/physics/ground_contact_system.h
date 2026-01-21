#pragma once

#include <flecs.h>
#include <cmath>
#include <iostream>
#include "components/basic/common.h"
#include "components/physics/forces.h"
#include "components/physics/dynamics.h"
#include "components/systems/logistics.h" // For GroundState
#include "components/physics/performance.h" // For LandingGear

namespace {
    // Penalty Method Constants
    // Spring K ~ Vehicle Mass * Gravity / Desired Compression (0.1m)
    // 15000 * 10 / 0.1 = 1,500,000
    constexpr double kGroundSpring = 2000000.0;
    
    // Damping C ~ 2 * sqrt(m * k) 
    // sqrt(15000 * 2000000) = sqrt(3e10) ~ 170000. 
    // 2 * 170000 = 340000.
    constexpr double kGroundDamper = 350000.0; 
    
    // Friction
    constexpr double kMuRolling = 0.02;
    constexpr double kMuBraking = 0.8;
}

/**
 * GroundContactSystem
 * 
 * Implements a Penalty Method for ground interaction.
 * Instead of hard position clamping, it applies:
 * 1. Normal Force (Spring-Damper) when penetration occurs.
 * 2. Friction Force (Coulomb) opposite to velocity.
 */
inline void register_ground_contact_system(flecs::world& ecs) {
    ecs.system<ForceAccumulator, const Transform, const Velocity, const Mass, GroundState>("GroundContact")
        .kind(flecs::OnUpdate)
        // Must run BEFORE Integration but AFTER Aerodynamics
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto forces = it.field<ForceAccumulator>(0);
                auto transform = it.field<const Transform>(1);
                auto velocity = it.field<const Velocity>(2);
                auto mass = it.field<const Mass>(3);
                auto ground = it.field<GroundState>(4);
                
                for (auto i : it) {
                    double m = mass[i].get_total_kg();
                    if (m < 1.0) m = 15000.0;

                    // 1. Detection
                    double terrain_z = ground[i].terrain_elevation; // Usually 0.0 for now
                    double z = transform[i].z;
                    
                    // Simple logic: Assume pivot is at CG. Gear extends downwards by l_gear.
                    // For now, let's treat 'z' as altitude AGL for simplicity, or assume CG height.
                    // Let's assume z is CG altitude. When z < 2.0 (gear height), we touch.
                    double gear_height = 2.0; 
                    
                    double penetration = gear_height - (z - terrain_z);
                    
                    bool is_touching = (penetration > 0.0);
                    ground[i].on_ground = is_touching;
                    
                    if (!is_touching) continue;
                    
                    // 2. Normal Force (Spring-Damper)
                    // F_spring = k * x
                    double f_spring = kGroundSpring * penetration;
                    
                    // F_damper = -c * v_z (only if moving down?)
                    // Daming should resist compression and expansion
                    double vz = velocity[i].vz;
                    double f_damper = -kGroundDamper * vz;
                    
                    // Total Normal Force (Unilateral constraint: Ground pushes up, never pulls down)
                    double Fn = f_spring + f_damper;
                    if (Fn < 0.0) Fn = 0.0;
                    
                    forces[i].add_force(0.0, 0.0, Fn);
                    
                    // 3. Friction
                    // F_f = -mu * Fn * v_tangent_normalized
                    double vx = velocity[i].vx;
                    double vy = velocity[i].vy;
                    double v_h_sq = vx*vx + vy*vy;
                    
                    if (v_h_sq > 0.001) {
                         double v_h = std::sqrt(v_h_sq);
                         double mu = kMuRolling;
                         
                         // Check friction brakes (from PilotAction or Command)
                         const PilotAction* pilot = it.entity(i).get<PilotAction>();
                         // Or Legacy
                         const MovementCommand* cmd = it.entity(i).get<MovementCommand>();
                         
                         bool braking = false;
                         if (pilot && pilot->active) {
                             // Assuming some brake flag or low throttle implies braking on ground?
                             // For now, let's say throttle < 0.1 on ground = brakes? 
                             // Or add specific brake input.
                             // Let's use: if throttle == 0, brakes applied lightly.
                             if (pilot->throttle < 0.05) braking = true;
                         } else if (cmd && cmd->active) {
                             if (cmd->throttle_cmd < 0.05) braking = true;
                         }
                         
                         if (braking) mu = kMuBraking;
                         
                         // Friction vector
                         double fx = -mu * Fn * (vx / v_h);
                         double fy = -mu * Fn * (vy / v_h);
                         
                         forces[i].add_force(fx, fy, 0.0);
                    } else {
                         // Static kill (prevent creeping)
                         if (std::abs(vx) < 0.1 && std::abs(vy) < 0.1) {
                             // Zero out velocity directly? 
                             // Physics engine purity says NO, apply opposing force.
                             // But for stability, a small velocity kill near zero is acceptable in games.
                             // Let's apply a "stiction" force equal and opposite to other horizontal forces
                             // Up to max static friction.
                             // (Skipping complex stiction for now)
                         }
                    }
                }
            }
        });
}
