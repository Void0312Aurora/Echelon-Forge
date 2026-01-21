#pragma once

#include <flecs.h>
#include <cmath>
#include <iostream>
#include "components/basic/common.h"
#include "components/physics/forces.h"
#include "components/physics/dynamics.h" // For MassProperties (RefArea)
#include "components/physics/performance.h" // For LandingGear
#include "components/systems/logistics.h" // For MassProperties definition

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
                    // Simple Linear Lift
                    // Cl0 = 0.1 (symm airfoil has 0, but usually some incidence)
                    // Cla = 0.1 per deg
                    // THEORY: Thin Airfoil Theory gives dCl/dAlpha = 2*PI per radian.
                    // 2*PI rad^-1 = 6.28 / 57.3 deg^-1 approx 0.11 deg^-1.
                    // So 0.1 is a valid physical approximation for subsonic flight.
                    double Cl = 0.0 + 0.1 * alpha;
                    
                    // Stall Logic (Simple)
                    if (std::abs(alpha) > 15.0) {
                        // Post-stall drop
                        double stall_factor = std::max(0.0, 1.0 - (std::abs(alpha) - 15.0) * 0.1);
                        Cl *= stall_factor;
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
                    
                    double k = 0.1;
                    double Cd = Cd0 + k * Cl * Cl;
                    
                    // Cache coefficients for readout
                    aero[i].lift_coefficient = Cl;
                    aero[i].drag_coefficient = Cd;
                    
                    // --- Force Calculation ---
                    double lift_mag = q * S * Cl;
                    double drag_mag = q * S * Cd;
                    
                    // --- Directions ---
                    Math::Vector3 v_vec = {velocity[i].vx, velocity[i].vy, velocity[i].vz};
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
                    double Cm_alpha = -0.8; 
                    double Cm_q = -12.0;
                    double Cm = Cm_alpha * Math::to_radians(alpha) + Cm_q * q_hat;
                    
                    // --- 2. Rolling Moment (Cl) ---
                    // Cl = Cl_beta * beta + Cl_p * p_hat + Cl_r * r_hat
                    // Cl_beta < 0 for dihedral stability ("Roll away from sideslip"). (-0.1)
                    // Cl_p < 0 for roll damping. (-0.4)
                    double beta = aero[i].sideslip_angle; // Degrees
                    double Cl_beta = -0.1;
                    double Cl_p = -0.45;
                    double Cl_r = 0.1; // Yaw-induced roll
                    double Cl_mom = Cl_beta * Math::to_radians(beta) + Cl_p * p_hat + Cl_r * r_hat;
                    
                    // --- 3. Yawing Moment (Cn) ---
                    // Cn = Cn_beta * beta + Cn_r * r_hat + Cn_p * p_hat
                    // Cn_beta > 0 for directional stability ("Weathercock"). (+0.15)
                    // Cn_r < 0 for yaw damping. (-0.2)
                    double Cn_beta = 0.15;
                    double Cn_r = -0.25;
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
