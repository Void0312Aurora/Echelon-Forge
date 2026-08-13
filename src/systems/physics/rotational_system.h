#pragma once

#include <flecs.h>
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <numbers>
#include "components/basic/common.h"
#include "components/physics/forces.h"
#include "components/physics/dynamics.h"

namespace {
    inline double deg_to_rad(double deg) { return deg * std::numbers::pi_v<double> / 180.0; }
    inline double rad_to_deg(double rad) { return rad * 180.0 / std::numbers::pi_v<double>; }

    inline double clamp_finite(double v, double lo, double hi) {
        if (!std::isfinite(v)) return 0.0;
        return std::clamp(v, lo, hi);
    }
	    
    inline double wrap_360(double deg) {
        deg = std::fmod(deg, 360.0);
        if (deg < 0) deg += 360.0;
        return deg;
    }

    inline double env_double(const char* key, double fallback) {
        const char* v = std::getenv(key);
        if (!v || !*v) return fallback;
        char* end = nullptr;
        const double out = std::strtod(v, &end);
        if (end == v || !std::isfinite(out)) return fallback;
        return out;
    }

    struct RotationalParams {
        double max_rate_cross_rad_s;
        double max_torque_nm;
        double max_ang_accel_rad_s2;
        double max_rate_rad_s;
        double min_abs_cos_theta;
        double pitch_limit_deg;
    };

    inline const RotationalParams& rotational_params() {
        static RotationalParams p = []() {
            RotationalParams v{};
            v.max_rate_cross_rad_s = std::max(1.0, env_double("CMO_ROT_MAX_RATE_CROSS_RAD_S", 50.0));
            v.max_torque_nm = std::max(1.0e4, env_double("CMO_ROT_MAX_TORQUE_NM", 5.0e6));
            v.max_ang_accel_rad_s2 = std::max(10.0, env_double("CMO_ROT_MAX_ANG_ACCEL_RAD_S2", 1.0e4));
            v.max_rate_rad_s = std::max(0.1, env_double("CMO_ROT_MAX_RATE_RAD_S", 6.0));

            const double min_pitch_deg = std::clamp(env_double("CMO_ROT_SINGULARITY_MIN_PITCH_DEG", 85.0), 70.0, 89.9);
            v.min_abs_cos_theta = std::cos(deg_to_rad(min_pitch_deg));

            v.pitch_limit_deg = std::clamp(env_double("CMO_ROT_PITCH_LIMIT_DEG", 89.0), 70.0, 89.9);
            return v;
        }();
        return p;
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

                const RotationalParams& prm = rotational_params();
                
                for (auto i : it) {
                    // 1. Update Angular Velocity (Euler's Equations of Motion)
                    // Assumes principal axes alignment (diagonal inertia tensor)
                    double Ixx = inertia[i].ixx;
                    double Iyy = inertia[i].iyy;
                    double Izz = inertia[i].izz;
                    
                    // Numeric stability guard: cap rates used in cross-coupling terms to
                    // prevent floating overflow when the sim enters an unrecoverable tumble.
                    // This is a proxy for real-world structural/aero limits and keeps RL
                    // observations finite.
                    double p = clamp_finite(ang_vel[i].p, -prm.max_rate_cross_rad_s, prm.max_rate_cross_rad_s);
                    double q = clamp_finite(ang_vel[i].q, -prm.max_rate_cross_rad_s, prm.max_rate_cross_rad_s);
                    double r = clamp_finite(ang_vel[i].r, -prm.max_rate_cross_rad_s, prm.max_rate_cross_rad_s);

                    // Also cap applied moments; control laws can generate stiff dynamics at high qbar.
                    double L = clamp_finite(forces[i].torque_roll, -prm.max_torque_nm, prm.max_torque_nm);
                    double M_moment = clamp_finite(forces[i].torque_pitch, -prm.max_torque_nm, prm.max_torque_nm);
                    double N = clamp_finite(forces[i].torque_yaw, -prm.max_torque_nm, prm.max_torque_nm);
                    
                    // dp/dt = (L - (Izz - Iyy)*q*r) / Ixx
                    double p_dot = (L - (Izz - Iyy) * q * r) / Ixx;
                    
                    // dq/dt = (M - (Ixx - Izz)*p*r) / Iyy
                    double q_dot = (M_moment - (Ixx - Izz) * p * r) / Iyy;
                    
                    // dr/dt = (N - (Iyy - Ixx)*p*q) / Izz
                    double r_dot = (N - (Iyy - Ixx) * p * q) / Izz;
                    
                    // Integrate Rates
                    p += clamp_finite(p_dot, -prm.max_ang_accel_rad_s2, prm.max_ang_accel_rad_s2) * dt;
                    q += clamp_finite(q_dot, -prm.max_ang_accel_rad_s2, prm.max_ang_accel_rad_s2) * dt;
                    r += clamp_finite(r_dot, -prm.max_ang_accel_rad_s2, prm.max_ang_accel_rad_s2) * dt;

                    // Physical-ish envelope: keep angular rates bounded.
                    // Fighters rarely exceed a few hundred deg/s in sustained motion.
                    ang_vel[i].p = clamp_finite(p, -prm.max_rate_rad_s, prm.max_rate_rad_s);
                    ang_vel[i].q = clamp_finite(q, -prm.max_rate_rad_s, prm.max_rate_rad_s);
                    ang_vel[i].r = clamp_finite(r, -prm.max_rate_rad_s, prm.max_rate_rad_s);
                    
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
                    
                    // Avoid gimbal-lock amplification near +/- 90 deg pitch.
                    // Clamp the effective cos(theta) to +/-cos(85deg).
                    if (std::abs(c_theta) < prm.min_abs_cos_theta) c_theta = std::copysign(prm.min_abs_cos_theta, c_theta);
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
                    
                    transform[i].pitch = std::max(-prm.pitch_limit_deg, std::min(prm.pitch_limit_deg, transform[i].pitch));
                    
                    transform[i].heading = wrap_360(transform[i].heading);
                }
            }
        });
}
