#pragma once

#include <flecs.h>
#include <random>
#include "components/basic/common.h"
#include "components/physics/dynamics.h"
#include "components/systems/navigation.h"

// Simple Geo-Reference (Nellis AFB approx)
constexpr double kRefLat = 36.24;
constexpr double kRefLon = -115.05;
constexpr double kMetersPerDegLat = 111132.954;
constexpr double kMetersPerDegLon = 90000.0; // Approx at 36N

inline void register_navigation_system(flecs::world& ecs) {
    ecs.system<EGI, const Transform, const Velocity>("NavigationSystem")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            auto egi = it.field<EGI>(0);
            auto trans = it.field<const Transform>(1);
            auto vel = it.field<const Velocity>(2);
            
            const ecs_world_info_t* info = ecs_get_world_info(it.world().c_ptr());
            double dt = info->delta_time;
            double time = info->world_time_total;

            // Random Generator for Noise
            // Note: In a real system, we'd use a per-entity PRNG state to be deterministic
            // For MVP, we'll keep it simple or use a static one? 
            // Better: use Hash of entity ID + time for pseudo-noise
            
            for (auto i : it) {
                // 1. Truth Propagation
                double true_vn = vel[i].vy;
                double true_ve = vel[i].vx;
                double true_alt = trans[i].z;
                
                // 2. INS Drift Simulation
                // Drift grows with time since last fix
                egi[i].time_since_last_gps_fix += dt;
                
                // Simulate Drift Random Walk (simplified)
                // d(Drift)/dt = Noise
                // For MVP: Linear growth based on time
                // Error = Rate * Time
                double drift_scaler = egi[i].time_since_last_gps_fix;
                
                // If GPS is available, we "fix" periodically (e.g. 1Hz)
                if (egi[i].gps_available && egi[i].time_since_last_gps_fix > 1.0) {
                    egi[i].drift_lat_m *= 0.1; // Filter update (Kalman-ish)
                    egi[i].drift_lon_m *= 0.1;
                    egi[i].drift_alt_m *= 0.1;
                    egi[i].time_since_last_gps_fix = 0.0; // Reset
                    egi[i].position_uncertainty_m = 5.0; // GPS Accuracy
                } else {
                    // Drift accumulation (INS free inertial)
                    double noise_x = std::sin(time * 0.1 + i) * egi[i].ins_drift_rate_mps * dt;
                    double noise_y = std::cos(time * 0.1 + i) * egi[i].ins_drift_rate_mps * dt;
                    
                    egi[i].drift_lat_m += noise_y;
                    egi[i].drift_lon_m += noise_x;
                    egi[i].position_uncertainty_m += egi[i].ins_drift_rate_mps * dt;
                }
                
                // 3. Output State Calculation
                double nav_x = trans[i].x + egi[i].drift_lon_m;
                double nav_y = trans[i].y + egi[i].drift_lat_m;
                double nav_z = trans[i].z + egi[i].drift_alt_m;
                
                // Geo Projection
                egi[i].lat_deg = kRefLat + (nav_y / kMetersPerDegLat);
                egi[i].lon_deg = kRefLon + (nav_x / kMetersPerDegLon);
                
                // Velocities (Body to NED or just World NED?)
                // Velocity component is already World Frame (vx, vy, vz)
                egi[i].vn_mps = vel[i].vy; // Y is North
                egi[i].ve_mps = vel[i].vx; // X is East
                egi[i].vd_mps = -vel[i].vz; // Z Up -> D Down
                
                egi[i].alt_baro_m = nav_z; // Standard Day
                egi[i].alt_radar_m = std::max(0.0, nav_z); // Assuming flat ground at Z=0
                
                // Attitude (Truth for now, INS alignment is complex)
                // Transform uses DEGREES (NAV: 0=North, CW) according to common.h
                // "double heading, pitch, roll; // degrees"
                
                egi[i].heading_deg = trans[i].heading;
                egi[i].pitch_deg = trans[i].pitch;
                egi[i].roll_deg = trans[i].roll;
                
                // Wrap Heading [0, 360) just in case
                while (egi[i].heading_deg < 0.0) egi[i].heading_deg += 360.0;
                while (egi[i].heading_deg >= 360.0) egi[i].heading_deg -= 360.0;
            }
        });
}
