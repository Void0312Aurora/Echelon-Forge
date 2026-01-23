#pragma once

#include <flecs.h>
#include <cmath>
#include <iostream>
#include "components/basic/common.h"
#include "components/physics/forces.h"
#include "components/physics/dynamics.h"
#include "components/systems/logistics.h" // For GroundState
#include "components/physics/performance.h" // For LandingGear
#include "components/combat/health.h"        // For Health
#include "core/interfaces/environment_model.h"

namespace {
    // Penalty Method Constants
    constexpr double kGroundSpring = 2000000.0;
    constexpr double kGroundDamper = 350000.0; 
    
    // Default Friction (Fallback)
    constexpr double kMuBraking = 0.8;

    // Simple Nose Wheel Steering (NWS) approximation:
    // Map rudder pedal input to a ground yaw moment at low speeds when weight-on-wheels.
    // This provides realistic directional control during the takeoff roll (rudder surfaces have little authority
    // at low airspeed). The effect fades out at higher speeds to avoid unrealistic high-speed steering.
    constexpr double kNwsLeverArmM = 2.0;          // Effective wheelbase lever arm
    constexpr double kNwsLateralMu = 0.6;          // Tire lateral grip approximation
    constexpr double kNwsMinSpeedMps = 2.0;        // No steering at (near) standstill
    constexpr double kNwsFadeStartMps = 45.0;      // Begin fading out toward aero rudder
    constexpr double kNwsFadeEndMps = 80.0;        // Fully faded out by this speed
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
                    
                    // 2.5 Pitch Damping When On Ground
                    // Prevent uncontrolled pitch-up rotation on ground roll.
                    // The gear pivot creates a restoring moment that limits pitch.
                    // Acting like a torsional spring-damper on pitch.
                    const AngularVelocity* ang_vel = it.entity(i).get<AngularVelocity>();
                    if (ang_vel) {
                        double q_rate = ang_vel->q; // Pitch rate (rad/s)
                        double pitch_deg = transform[i].pitch;
                        
                        // Ground pitch limit: ~10 degrees (rotation attitude)
                        // Stiffness must exceed aerodynamic control moment.
                        // Control: ~60 * q * 0.8 @ q=3000 -> 144,000 Nm
                        // We need restoring > 144,000 at 10 deg -> Kp > 825,000/rad
                        double kp_pitch = 2000000.0;  // 2 MNm per radian
                        double kd_pitch = 200000.0;   // 200 kNm per rad/s
                        
                        // Always apply restoring if pitch > 2 degrees on ground
                        if (pitch_deg > 2.0) {
                            double restoring_torque = -kp_pitch * Math::to_radians(pitch_deg - 2.0);
                            double damping_torque = -kd_pitch * q_rate;
                            forces[i].add_torque(0.0, restoring_torque + damping_torque, 0.0);
                        } else if (std::abs(q_rate) > 0.01) {
                            // Just damping for small angles
                            forces[i].add_torque(0.0, -kd_pitch * q_rate, 0.0);
                        }
                    }
                    
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
                         
                         // --- Gear State Update ---
                         // Track whether on paved surface and accumulate stress if off-road at speed
                         GearState* gear = it.entity(i).get_mut<GearState>();
                         if (gear) {
                             gear->on_runway = !is_offroad;
                             gear->stress_rate = 0.0; // Reset each frame
                             
                             // Stress accumulation only when gear down, off-road, and moving fast
                             if (gear->gear_down && !gear->collapsed && is_offroad && v_h > 40.0) {
                                 // Severity based on surface type
                                 double severity = 1.0;
                                 if (terrain.type == Surface::SoftDirt) severity = 1.0;
                                 else if (terrain.type == Surface::HardPacked) severity = 0.3;
                                 else if (terrain.type == Surface::Water) severity = 2.0;
                                 else if (terrain.type == Surface::Obstacle) severity = 5.0;
                                 
                                 // Stress rate: (v - 40) / 60 * severity → ~1.0/s at 100 m/s on SoftDirt
                                 double dt = it.delta_time();
                                 gear->stress_rate = severity * (v_h - 40.0) / 60.0;
                                 gear->stress += gear->stress_rate * dt;
                                 
                                 // Increase friction to simulate digging in
                                 mu_rolling *= (1.0 + 4.0 * gear->stress); // Up to 5x at collapse
                                 
                                 // Check for collapse
                                 if (gear->stress >= 1.0) {
                                     gear->collapsed = true;
                                     // Gear collapse → aircraft crash
                                     Health* health = it.entity(i).get_mut<Health>();
                                     if (health) {
                                         health->current_hp = 0.0;
                                     }
                                 }
                             }
                         } else {
                             // Legacy behavior: just increase friction
                             if (is_offroad && v_h > 40.0) {
                                 mu_rolling *= 5.0;
                             }
                         }

                         double mu = mu_rolling;
                         
	                         // Check friction brakes
	                         const PilotAction* pilot = it.entity(i).get<PilotAction>();
	                         const MovementCommand* cmd = it.entity(i).get<MovementCommand>();

	                         // 3.5 Nose Wheel Steering (ground yaw control)
	                         // Use rudder pedal input as steering demand when on ground.
	                         if (pilot && pilot->active) {
                                 // [Modified] Reduce input sensitivity to prevent PIO/Rollover at high speed.
                                 // A raw steer of 1.0 (noise) at 30m/s was causing immediate rollover.
                                 // Scale input by 0.2 (divide by 5) to widen the stability margin.
                                 // Update: Bumped to 0.4 to tackle understeer in Phase 15.
                                 constexpr double kNwsInputScaler = 0.4; 
	                             double steer = std::clamp(pilot->rudder, -1.0, 1.0) * kNwsInputScaler;
	                             
	                             if (std::abs(steer) > 1e-6) {
	                                 // Require gear mostly extended (if present).
	                                 bool gear_extended = true;
	                                 if (const LandingGear* lg = it.entity(i).get<LandingGear>()) {
	                                     gear_extended = (lg->extension_state >= 0.5);
	                                 }

	                                 if (gear_extended) {
	                                     double speed_factor = std::clamp(v_h / kNwsMinSpeedMps, 0.0, 1.0);
	                                     double fade = 1.0;
	                                     if (v_h >= kNwsFadeStartMps) {
	                                         double t = (v_h - kNwsFadeStartMps) / (kNwsFadeEndMps - kNwsFadeStartMps);
	                                         fade = 1.0 - std::clamp(t, 0.0, 1.0);
	                                     }
	                                     double gain = speed_factor * fade;
	                                     if (gain > 0.0) {
	                                         double tau_nws = steer * (Fn * kNwsLateralMu) * kNwsLeverArmM * gain;
	                                         forces[i].add_torque(0.0, 0.0, tau_nws);
	                                     }
	                                 }
	                             }
	                         }
	                         
	                         double brake_amount = 0.0;
	                         if (pilot && pilot->active) {
	                             brake_amount = std::clamp(pilot->brake, 0.0, 1.0);
                             // Optional: if either wheel brake is explicitly asserted, treat as full braking.
                             if (pilot->brake_left || pilot->brake_right) {
                                 brake_amount = std::max(brake_amount, 1.0);
                             }
                             // Auto-stop / parking brake when throttle is idle at low speed.
                             if (pilot->throttle < 0.01 && v_h < 10.0) {
                                 brake_amount = std::max(brake_amount, 1.0);
                             }
                         } else if (cmd && cmd->active) {
                             // Legacy: treat throttle idle as braking when no PilotAction is present.
                             if (cmd->throttle_cmd < 0.01) brake_amount = 1.0;
                         }
                         
                         // Blend rolling friction to braking friction using brake amount.
                         // brake=0 -> rolling; brake=1 -> full braking.
                         if (brake_amount > 0.0) {
                             mu = mu_rolling + brake_amount * (kMuBraking - mu_rolling);
                         }
                         
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
