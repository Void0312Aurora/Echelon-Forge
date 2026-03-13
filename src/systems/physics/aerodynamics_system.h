#pragma once

#include <flecs.h>
#include <cmath>
#include <iostream>
#include "components/basic/common.h"
#include "components/physics/forces.h"
#include "components/physics/dynamics.h" // For MassProperties (RefArea)
#include "components/physics/performance.h" // For LandingGear
#include "components/physics/action.h"       // For PilotAction (flaps/speedbrake)
#include "components/systems/logistics.h" // For MassProperties definition
#include "core/interfaces/environment_model.h"

namespace {
    inline Math::Vector3 vec_cross(const Math::Vector3& a, const Math::Vector3& b) {
        return {
            a.y*b.z - a.z*b.y,
            a.z*b.x - a.x*b.z,
            a.x*b.y - a.y*b.x
        };
    }
    
    inline Math::Vector3 get_body_right(double heading, double pitch, double roll) {
        // Yaw = 90 - Heading
        double psi = Math::to_radians(90.0 - heading);
        double theta = Math::to_radians(pitch);
        double phi = Math::to_radians(roll);
        
        double c_psi = std::cos(psi);
        double s_psi = std::sin(psi);
        double c_theta = std::cos(theta);
        double s_theta = std::sin(theta);
        double c_phi = std::cos(phi);
        double s_phi = std::sin(phi);
        
        // Body Y vector (0, 1, 0) transformed to World
        // R * [0;1;0] = 2nd column of R
        
        // Z-up convention
        return {
            -s_psi * c_phi + c_psi * s_theta * s_phi,
             c_psi * c_phi + s_psi * s_theta * s_phi,
             c_theta * s_phi
        };
    }

    inline double smoothstep01(double x) {
        x = std::clamp(x, 0.0, 1.0);
        return x * x * (3.0 - 2.0 * x);
    }
}

/**
 * AerodynamicsSystem
 * 
 * Computes Lift and Drag based on AeroState and MassProperties.
 */
inline void register_aerodynamics_system(flecs::world& ecs) {
    ecs.system<ForceAccumulator, AeroState, const MassProperties, const Velocity, const Transform>("ComputeAerodynamics")
        .kind(flecs::OnUpdate) // Run after AeroState and attitude updates
        // Forces are cleared once per frame by ForceClearSystem.
        // This system only adds lift/drag; ordering within OnUpdate is controlled
        // by registration order in SimulationKernel.
        .run([](flecs::iter& it) {
            const EnvironmentModelRef* env_ref = it.world().get<EnvironmentModelRef>();
            while (it.next()) {
                auto forces = it.field<ForceAccumulator>(0);
                auto aero = it.field<AeroState>(1);
                auto props = it.field<const MassProperties>(2);
                auto velocity = it.field<const Velocity>(3);
                auto transform = it.field<const Transform>(4);
                
                for (auto i : it) {
                    double q = aero[i].dynamic_pressure;
                    if (q < 0.1) continue;
                    
                    double alpha = aero[i].angle_of_attack;
                    double S = props[i].reference_area_m2;
                    if (S < 1.0) S = 30.0; // Fallback
                    
                    // --- Coefficient Models ---
                    // Lift model: linear regime + flap-aware post-stall blend + deep-stall plateau.
                    // This avoids abrupt clipping and better reflects loss of lift at very high AoA.
                    constexpr double kClAlphaPerDeg = 0.1;
                    constexpr double kCl0 = 0.0;
                    double Cl = kCl0 + kClAlphaPerDeg * alpha;
                    
                    // [F1 FIX] Flaps Lift Augmentation
                    // Flaps increase camber, boosting Cl by ~0.3-0.5 at full deflection
                    const PilotAction* pilot = it.entity(i).get<PilotAction>();
                    double flaps_deflection = 0.0;
                    double speedbrake_pos = 0.0;
                    if (pilot && pilot->active) {
                        flaps_deflection = std::clamp(static_cast<double>(pilot->flaps), 0.0, 1.0);
                        speedbrake_pos = std::clamp(static_cast<double>(pilot->speedbrake), 0.0, 1.0);
                    }
                    Cl += flaps_deflection * 0.35; // dCl_flaps ~ 0.35 at full deflection

                    const double alpha_abs = std::abs(alpha);
                    const double alpha_sign = (alpha >= 0.0) ? 1.0 : -1.0;

                    // Flaps increase max-lift and delay stall onset modestly.
                    const double alpha_stall_deg = 15.0 + 6.0 * flaps_deflection;
                    const double alpha_peak_deg = alpha_stall_deg + 8.0;
                    const double alpha_deep_deg = alpha_peak_deg + 18.0;

                    const double cl_peak_mag = 1.25 + 0.45 * flaps_deflection;
                    const double cl_deep_mag = 0.22 + 0.10 * flaps_deflection;

                    if (alpha_abs > alpha_stall_deg) {
                        if (alpha_abs <= alpha_peak_deg) {
                            const double t = smoothstep01((alpha_abs - alpha_stall_deg) / std::max(1e-6, (alpha_peak_deg - alpha_stall_deg)));
                            const double cl_target = alpha_sign * cl_peak_mag;
                            Cl = (1.0 - t) * Cl + t * cl_target;
                        } else if (alpha_abs <= alpha_deep_deg) {
                            const double t = smoothstep01((alpha_abs - alpha_peak_deg) / std::max(1e-6, (alpha_deep_deg - alpha_peak_deg)));
                            const double cl_target = alpha_sign * cl_deep_mag;
                            const double cl_peak = alpha_sign * cl_peak_mag;
                            Cl = (1.0 - t) * cl_peak + t * cl_target;
                        } else {
                            Cl = alpha_sign * cl_deep_mag;
                        }
                    }
                    
                    // Drag Polar
                    // Cd0 = 0.02 + gear? (gear handled in drag previously)
                    // k = 0.1
                    double Cd0 = 0.02; 
                    // Add Stores Drag index?
                    Cd0 += props[i].current_drag_index * 0.001; // Scale factor?

                    // Gear drag penalty
                    const LandingGear* gear = it.entity(i).get<LandingGear>();
                    if (gear) {
                         Cd0 += gear->extension_state * 0.04;
                    }
                    
                    // [F2 FIX] Speedbrake Drag Penalty
                    Cd0 += speedbrake_pos * 0.08; // dCd_speedbrake ~ 0.08 at full extension
                    
                    // Flaps also add some drag (induced + profile)
                    Cd0 += flaps_deflection * 0.02;
                    
                    double k = 0.1;

                    // Ground effect (real physics):
                    // - increases effective lift slightly
                    // - reduces induced drag near the ground
                    double ge = 0.0;
                    if (env_ref && env_ref->model) {
                        const double terrain_z = env_ref->model->get_terrain_elevation(transform[i].x, transform[i].y);
                        const double alt_agl = std::max(0.0, transform[i].z - terrain_z);
                        const double b_ref = std::max(1.0, props[i].wing_span_m);
                        const double ge_fade_h = 0.5 * b_ref; // fade out by ~0.5 span
                        if (ge_fade_h > 1.0e-6 && alt_agl < ge_fade_h) {
                            ge = 1.0 - (alt_agl / ge_fade_h);
                            ge = std::clamp(ge, 0.0, 1.0);
                        }
                    }
                    // Conservative scaling (keeps training stable while improving takeoff realism).
                    Cl *= (1.0 + 0.08 * ge);
                    const double k_eff = k * (1.0 - 0.70 * ge);

                    // Post-stall drag rise: strong drag increase after stall and into deep stall.
                    double stall_drag = 0.0;
                    if (alpha_abs > alpha_stall_deg) {
                        const double s1 = smoothstep01((alpha_abs - alpha_stall_deg) / std::max(1e-6, (alpha_peak_deg - alpha_stall_deg)));
                        const double s2 = smoothstep01((alpha_abs - alpha_peak_deg) / std::max(1e-6, (alpha_deep_deg - alpha_peak_deg)));
                        stall_drag = 0.25 * s1 + 0.55 * s2;
                    }

                    double Cd = Cd0 + k_eff * Cl * Cl + stall_drag;
                    
                    // Cache coefficients for readout
                    aero[i].lift_coefficient = Cl;
                    aero[i].drag_coefficient = Cd;
                    
                    // --- Force Calculation ---
                    double lift_mag = q * S * Cl;
                    double drag_mag = q * S * Cd;
                    
                    // --- Directions ---
                    // Use air-relative velocity for drag/lift direction (wind realism).
                    Math::Vector3 v_vec = {velocity[i].vx, velocity[i].vy, velocity[i].vz};
                    if (env_ref && env_ref->model) {
                        AtmosphericData atm = env_ref->model->get_atmosphere_at(transform[i].x, transform[i].y, transform[i].z);
                        v_vec.x -= atm.wind_velocity.x;
                        v_vec.y -= atm.wind_velocity.y;
                        v_vec.z -= atm.wind_velocity.z;
                    }
                    Math::Vector3 v_hat = Math::vec_norm(v_vec);
                    
                    // Drag Direction: -Velocity
                    Math::Vector3 drag_dir = {-v_hat.x, -v_hat.y, -v_hat.z};
                    
                    // Lift Direction: V x BodyRight (Projected Up)
                    Math::Vector3 body_right = get_body_right(transform[i].heading, transform[i].pitch, transform[i].roll);
                    Math::Vector3 lift_cross = vec_cross(v_vec, body_right); // V x Right = Up-ish
                    Math::Vector3 lift_dir = Math::vec_norm(lift_cross);
                    
                    // Apply Forces
                    double fz_lift = lift_mag * lift_dir.z;
                    double fz_drag = drag_mag * drag_dir.z;
                    
                    forces[i].add_force(
                        drag_mag * drag_dir.x + lift_mag * lift_dir.x,
                        drag_mag * drag_dir.y + lift_mag * lift_dir.y,
                        drag_mag * drag_dir.z + lift_mag * lift_dir.z
                    );

                    // --- MOMENTS (Torque) Calculation ---
                    // Implements simplistic linearized stability derivatives:
                    // M = qSc * Cm
                    // L = qSb * Cl
                    // N = qSb * Cn
                    
                    double b = props[i].wing_span_m;
                    if (b < 1.0) b = 10.0;
                    double c_bar = props[i].chord_m;
                    if (c_bar < 0.1) c_bar = 3.0;
                    
                    double V = std::max(10.0, std::sqrt(velocity[i].vx*velocity[i].vx + velocity[i].vy*velocity[i].vy + velocity[i].vz*velocity[i].vz));
                    
                    // Rates in body frame (rad/s) needed.
                    // We only have world ang_vel? No, AngularVelocity component is usually Body Frame (p,q,r).
                    // Let's assume it is.
                     const AngularVelocity* av = it.entity(i).get<AngularVelocity>();
                     double p=0, q_rate=0, r=0;
                     if (av) { p = av->p; q_rate = av->q; r = av->r; }
                     
                    // Normalized Rates
                    double p_hat = p * b / (2 * V);
                    double q_hat = q_rate * c_bar / (2 * V);
                    double r_hat = r * b / (2 * V);
                    
                    // --- 1. Pitching Moment (Cm) ---
                    // Cm = Cm0 + Cm_alpha * alpha + Cm_q * q_hat
                    // Cm0 is usually trim. Assume 0 for symmetric airfoil.
                    // Cm_alpha < 0 for stability (Stable: -0.5 to -1.5)
                    // Cm_q < 0 for damping (Damping: -10 to -20)
                    // Damping fades in deep stall where attached-flow derivatives lose authority.
                    const double stall_rel = smoothstep01((alpha_abs - alpha_stall_deg) / std::max(1e-6, (alpha_deep_deg - alpha_stall_deg)));
                    const double damp_scale = std::clamp(1.0 - 0.7 * stall_rel, 0.25, 1.0);

                    double Cm_alpha = -0.8;
                    double Cm_q = -12.0 * damp_scale;
                    double Cm = Cm_alpha * Math::to_radians(alpha) + Cm_q * q_hat;
                    
                    // --- 2. Rolling Moment (Cl) ---
                    // Cl = Cl_beta * beta + Cl_p * p_hat + Cl_r * r_hat
                    // Cl_beta < 0 for dihedral stability ("Roll away from sideslip"). (-0.1)
                    // Cl_p < 0 for roll damping. (-0.4)
                    double beta = aero[i].sideslip_angle; // Degrees
                    double Cl_beta = -0.1;
                    double Cl_p = -0.45 * damp_scale;
                    double Cl_r = 0.1; // Yaw-induced roll
                    double Cl_mom = Cl_beta * Math::to_radians(beta) + Cl_p * p_hat + Cl_r * r_hat;
                    
                    // --- 3. Yawing Moment (Cn) ---
                    // Cn = Cn_beta * beta + Cn_r * r_hat + Cn_p * p_hat
                    // Cn_beta > 0 for directional stability ("Weathercock"). (+0.15)
                    // Cn_r < 0 for yaw damping. (-0.2)
                    double Cn_beta = 0.15;
                    double Cn_r = -0.25 * damp_scale;
                    double Cn_mom = Cn_beta * Math::to_radians(beta) + Cn_r * r_hat; // Neglect Cn_p for now
                    
                    // Convert Coefficients to Torque
                    // M = q * S * c * Cm
                    // L = q * S * b * Cl
                    // N = q * S * b * Cn
                    double pitch_torque = q * S * c_bar * Cm;
                    double roll_torque  = q * S * b * Cl_mom;
                    double yaw_torque   = q * S * b * Cn_mom;
                    
                    forces[i].add_torque(roll_torque, pitch_torque, yaw_torque);
                    

                    
                    // Debug print for takeoff (check if lift > weight)
                    // Weight ~ 10000kg * 9.8 ~ 98000N
                    // Lift = q * 30 * Cl
                    // At 100 m/s (q=6125), Cl=0.5 (alpha=5) -> L = 6125*30*0.5 = 91875 N (Close)
                    // static int ctr = 0;
                    // if (ctr++ % 100 == 0 && lift_mag > 1000.0) {
                    //    std::cout << "Entity " << it.entity(i).id() << " L=" << lift_mag << " D=" << drag_mag << " Alpha=" << alpha << std::endl;
                    // }
                }
            }
        });
}
