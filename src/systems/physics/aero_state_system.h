#pragma once

#include <flecs.h>
#include <cmath>
#include <algorithm>
#include <iostream>
#include "components/basic/common.h"
#include "components/physics/forces.h"
#include "components/physics/dynamics.h"
#include "core/interfaces/environment_model.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace {
    // World to Body transformation (Yaw -> Pitch -> Roll sequence)
    // Actually, usually we need World->Body, which is Inverse(Body->World).
    // Body->World (R_b2w) using Heading(Psi), Pitch(Theta), Roll(Phi).
    
    inline Math::Vector3 world_to_body(const Math::Vector3& v_world, double heading, double pitch, double roll) {
        // We need Rotation Matrix R_w2b = R_b2w^T
        // Psi (Yaw) = 90 - Heading
        double psi = Math::to_radians(90.0 - heading); // Math Yaw (Counter-Clockwise from X-East)
        double theta = Math::to_radians(pitch);
        double phi = Math::to_radians(roll);

        double c_psi = std::cos(psi);
        double s_psi = std::sin(psi);
        double c_theta = std::cos(theta);
        double s_theta = std::sin(theta);
        double c_phi = std::cos(phi);
        double s_phi = std::sin(phi);

        // Standard Euler Rotation Matrix R_z(psi) * R_y(theta) * R_x(phi) is Body->World
        // We want World->Body: R_x(-phi) * R_y(-theta) * R_z(-psi)
        
        // Intermediate: Rotate Z (Un-Yaw)
        // x1 =  x*c + y*s
        // y1 = -x*s + y*c
        double x1 =  v_world.x * c_psi + v_world.y * s_psi;
        double y1 = -v_world.x * s_psi + v_world.y * c_psi;
        double z1 =  v_world.z;

        // Rotate Y (Un-Pitch)
        // x2 = x1*c + z1*s
        // z2 = -x1*s + z1*c
        double x2 =  x1 * c_theta + z1 * s_theta;
        double y2 =  y1;
        double z2 = -x1 * s_theta + z1 * c_theta;

        // Rotate X (Un-Roll)
        // y3 = y2*c + z2*s
        // z3 = -y2*s + z2*c
        double x_body = x2;
        double y_body =  y2 * c_phi + z2 * s_phi;
        double z_body = -y2 * s_phi + z2 * c_phi;

        return {x_body, y_body, z_body};
    }
}

/**
 * AeroStateSystem
 * 
 * Computes aerodynamic state variables:
 * - Angle of Attack (alpha)
 * - Sideslip Angle (beta)
 * - Dynamic Pressure (q)
 * - Mach Number
 */
inline void register_aero_state_system(flecs::world& ecs) {
    ecs.system<AeroState, const Transform, const Velocity>("ComputeAeroState")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            const EnvironmentModelRef* env_ref = it.world().get<EnvironmentModelRef>();
            
            while (it.next()) {
                auto aero = it.field<AeroState>(0);
                auto transform = it.field<const Transform>(1);
                auto velocity = it.field<const Velocity>(2);
                
                for (auto i : it) {
                    // Ground-relative velocity (world frame)
                    double vx_gnd = velocity[i].vx;
                    double vy_gnd = velocity[i].vy;
                    double vz_gnd = velocity[i].vz;

                    // Atmosphere (includes wind). Treat aerodynamic state as air-relative.
                    double rho = 1.225;
                    double speed_of_sound = 340.29;
                    Vec3 wind = {0.0, 0.0, 0.0};

                    if (env_ref && env_ref->model) {
                        auto atmo = env_ref->model->get_atmosphere_at(
                            transform[i].x, transform[i].y, transform[i].z);
                        rho = atmo.air_density;
                        speed_of_sound = atmo.speed_of_sound;
                        wind = atmo.wind_velocity;
                    } else {
                        // Simple fallback atmosphere model
                        double alt_km = std::max(0.0, transform[i].z) / 1000.0;
                        rho = 1.225 * std::exp(-alt_km / 7.2);
                        speed_of_sound = 340.29 - (4.0 * alt_km); // Very rough linear approx
                        if (speed_of_sound < 295.0) speed_of_sound = 295.0;
                    }

                    double vx = vx_gnd - wind.x;
                    double vy = vy_gnd - wind.y;
                    double vz = vz_gnd - wind.z;

                    double v_sq = vx*vx + vy*vy + vz*vz;
                    
                    // Low-speed guard: AoA is meaningless at very low speeds
                    // Threshold: 5 m/s² means ~2.2 m/s.  Below this, aerodynamic
                    // angles are unstable due to small velocity components.
                    if (v_sq < 25.0) {  // 5 m/s threshold
                        aero[i].angle_of_attack = 0.0;
                        aero[i].sideslip_angle = 0.0;
                        aero[i].dynamic_pressure = 0.5 * 1.225 * v_sq; // Still compute q
                        aero[i].mach_number = 0.0;
                        continue;
                    }
                    
                    double v_total = std::sqrt(v_sq);
                    
                    // 2. Dynamic Pressure & Mach
                    aero[i].dynamic_pressure = 0.5 * rho * v_sq;
                    aero[i].mach_number = v_total / speed_of_sound;
                    
                    // 3. Body Frame Velocity for Alpha/Beta
                    Math::Vector3 v_body = world_to_body(
                        {vx, vy, vz}, 
                        transform[i].heading, 
                        transform[i].pitch, 
                        transform[i].roll
                    );
                    
                    // u = Forward (X), v = Side (Y), w = Down (Z-down? No, Z-up system: w is Up)
                    // ...
                    
                    aero[i].angle_of_attack = Math::to_degrees(std::atan2(-v_body.z, v_body.x));
                    
                    // Beta = asin(v_body.y / v_total)
                    double beta_arg = v_body.y / v_total;
                    beta_arg = std::clamp(beta_arg, -1.0, 1.0);
                    aero[i].sideslip_angle = Math::to_degrees(std::asin(beta_arg));
                    
                    // Clamp for safety
                    aero[i].angle_of_attack = std::max(-90.0, std::min(90.0, aero[i].angle_of_attack));
                    aero[i].sideslip_angle = std::max(-90.0, std::min(90.0, aero[i].sideslip_angle));
                }
            }
        });
}
