#pragma once

#include <flecs.h>
#include <cmath>
#include "components/basic/common.h"
#include "components/physics/forces.h"
#include "components/physics/dynamics.h"

namespace {
    inline double deg_to_rad(double deg) { return deg * M_PI / 180.0; }
    inline double rad_to_deg(double rad) { return rad * 180.0 / M_PI; }
    
    inline double wrap_360(double deg) {
        deg = std::fmod(deg, 360.0);
        if (deg < 0) deg += 360.0;
        return deg;
    }
}

/**
 * RotationalIntegrationSystem
 * 
 * Updates Angular Velocity based on Torques (Euler's Equations).
 * Updates Orientation (Euler Angles) based on Angular Velocity (Kinematic Equations).
 */
inline void register_rotational_integration_system(flecs::world& ecs) {
    ecs.system<Transform, AngularVelocity, const Inertia, const ForceAccumulator>("RotationalIntegrate")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto transform = it.field<Transform>(0);
                auto ang_vel = it.field<AngularVelocity>(1);
                auto inertia = it.field<const Inertia>(2);
                auto forces = it.field<const ForceAccumulator>(3);
                
                double dt = it.delta_time();
                if (dt <= 0.0) dt = 0.05;
                
                for (auto i : it) {
                    // 1. Update Angular Velocity (Euler's Equations of Motion)
                    // Assumes principal axes alignment (diagonal inertia tensor)
                    double Ixx = inertia[i].ixx;
                    double Iyy = inertia[i].iyy;
                    double Izz = inertia[i].izz;
                    
                    double p = ang_vel[i].p;
                    double q = ang_vel[i].q;
                    double r = ang_vel[i].r;
                    
                    double L = forces[i].torque_roll;
                    double M_moment = forces[i].torque_pitch;
                    double N = forces[i].torque_yaw;
                    
                    // dp/dt = (L - (Izz - Iyy)*q*r) / Ixx
                    double p_dot = (L - (Izz - Iyy) * q * r) / Ixx;
                    
                    // dq/dt = (M - (Ixx - Izz)*p*r) / Iyy
                    double q_dot = (M_moment - (Ixx - Izz) * p * r) / Iyy;
                    
                    // dr/dt = (N - (Iyy - Ixx)*p*q) / Izz
                    double r_dot = (N - (Iyy - Ixx) * p * q) / Izz;
                    
                    // Integrate Rates
                    ang_vel[i].p += p_dot * dt;
                    ang_vel[i].q += q_dot * dt;
                    ang_vel[i].r += r_dot * dt;
                    
                    // Damping (temporary stability hack until Aerodynamics provides damping)
                    // In real life, aero damping (C_lp, C_mq, C_nr) would be in the "Forces" (Torques).
                    // If forces don't have damping, this spins forever.
                    // For now, let's assume "Forces" will eventually contain damping.
                    // But to start, apply a small decay if no torque?
                    // No, let's trust the physics. If it spins, it spins.
                    
                    // 2. Update Orientation (Kinematics: Body Rates -> Euler Rates)
                    // Uses local variables for current rates
                    p = ang_vel[i].p;
                    q = ang_vel[i].q;
                    r = ang_vel[i].r;
                    
                    double phi = deg_to_rad(transform[i].roll);
                    double theta = deg_to_rad(transform[i].pitch);
                    
                    // Singularity protection (Gimbal lock at +/- 90 pitch)
                    double c_phi = std::cos(phi);
                    double s_phi = std::sin(phi);
                    double c_theta = std::cos(theta);
                    double s_theta = std::sin(theta);
                    
                    if (std::abs(c_theta) < 1e-4) c_theta = 1e-4; // Avoid div by zero
                    double t_theta = s_theta / c_theta; // tan(theta)
                    double sec_theta = 1.0 / c_theta;   // sec(theta)
                    
                    // Euler Rate Equations (Standard Aerospace Z-Down Convention?)
                    // Rate of Roll (dPhi/dt)
                    double d_phi = p + (q * s_phi + r * c_phi) * t_theta;
                    
                    // Rate of Pitch (dTheta/dt)
                    double d_theta = q * c_phi - r * s_phi;
                    
                    // Rate of Heading/Yaw (dPsi/dt)
                    // Note: CMO uses "Heading" which is typically 0-360 CW (Navigation).
                    // Standard Body Yaw (Psi) is CCW from North or East.
                    // dPsi/dt = (q * s_phi + r * c_phi) * sec_theta
                    double d_psi = (q * s_phi + r * c_phi) * sec_theta;
                    
                    // Integrate Euler Angles
                    transform[i].roll  += rad_to_deg(d_phi) * dt;
                    transform[i].pitch += rad_to_deg(d_theta) * dt;
                    
                    // Heading Update
                    // dPsi is "Math" yaw rate (CCW). Heading is (90 - Psi) or similar.
                    // dHdg = -dPsi if standard nav.
                    // Let's stick to standard aerospace for now: Psi increases CCW.
                    // Heading usually decreases as Psi increases.
                    // transform[i].heading -= rad_to_deg(d_psi) * dt;
                    // BUT, let's check legacy math.
                    // Common::world_to_body uses `psi = 90 - heading`.
                    // d(psi) = -d(heading). -> d(heading) = -d(psi).
                    transform[i].heading -= rad_to_deg(d_psi) * dt;
                    
                    // Normalize
                    transform[i].roll = std::fmod(transform[i].roll + 180.0, 360.0);
                    if (transform[i].roll < 0) transform[i].roll += 360.0; 
                    transform[i].roll -= 180.0; // -180 to 180
                    
                    transform[i].pitch = std::max(-89.0, std::min(89.0, transform[i].pitch)); // Clamp pitch
                    
                    transform[i].heading = wrap_360(transform[i].heading);
                }
            }
        });
}
