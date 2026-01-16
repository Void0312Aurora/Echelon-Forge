#pragma once

#include <flecs.h>
#include <cmath>
#include <algorithm>
#include <spdlog/spdlog.h>
#include "components/common.h"
#include "components/action.h"
#include "components/performance.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

inline double normalize_angle(double angle) {
    while (angle > 180.0) angle -= 360.0;
    while (angle < -180.0) angle += 360.0;
    return angle;
}

inline double to_degrees(double rad) { return rad * 180.0 / M_PI; }
inline double to_radians(double deg) { return deg * M_PI / 180.0; }

inline void register_control_system(flecs::world& ecs) {
    ecs.system<Velocity, Transform, const MovementCommand, const FlightModel>("FlightControl")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto v = it.field<Velocity>(0);
                auto p = it.field<Transform>(1);
                auto cmd = it.field<const MovementCommand>(2);
                auto fm = it.field<const FlightModel>(3);
                double dt = it.delta_time();
                
                for (auto i : it) {
                    if (!cmd[i].active) continue;

                    // 1. Current State
                    double current_speed = std::sqrt(v[i].vx*v[i].vx + v[i].vy*v[i].vy + v[i].vz*v[i].vz);
                    
                    // Heading (2D plane)
                    double current_heading_math = std::atan2(v[i].vy, v[i].vx); 
                    double current_heading_nav = 90.0 - to_degrees(current_heading_math);
                    current_heading_nav = normalize_angle(current_heading_nav);

                    // 2. Heading Control (Turn)
                    double heading_error = normalize_angle(cmd[i].target_heading - current_heading_nav);
                    double max_turn = fm[i].max_turn_rate * dt;
                    double turn = std::clamp(heading_error, -max_turn, max_turn);
                    double new_heading_nav = current_heading_nav + turn;
                    
                    // 3. Speed Control
                    double safe_target_speed = std::clamp(cmd[i].target_speed, fm[i].min_speed, fm[i].max_speed);
                    double speed_error = safe_target_speed - current_speed;
                    double max_accel_step = fm[i].max_accel * dt;
                    double accel = std::clamp(speed_error, -max_accel_step, max_accel_step);
                    double new_speed = std::max(0.0, current_speed + accel); 

                    // 4. Altitude Control (Climb/Dive)
                    double alt_error = cmd[i].target_altitude - p[i].z;
                    double desired_climb_rate = alt_error; 
                    double max_climb = fm[i].max_climb_rate;
                    double climb_rate = std::clamp(desired_climb_rate, -max_climb, max_climb);
                    
                    // 5. Update Velocity Vector (3D)
                    double pitch_rad = 0.0;
                    if (new_speed > 1.0) {
                        pitch_rad = std::asin(std::clamp(climb_rate / new_speed, -1.0, 1.0));
                    }
                    
                    double h_speed = new_speed * std::cos(pitch_rad);
                    double new_heading_math_rad = to_radians(90.0 - new_heading_nav);
                    
                    v[i].vx = h_speed * std::cos(new_heading_math_rad);
                    v[i].vy = h_speed * std::sin(new_heading_math_rad);
                    v[i].vz = new_speed * std::sin(pitch_rad);
                    
                    p[i].heading = new_heading_nav;
                    p[i].pitch = to_degrees(pitch_rad); 
                    p[i].roll = turn * 2.0; 

                    // DEBUG LOG (Only for first entity to avoid spam)
                    if (i == 0) {
                          // spdlog::info("Control: ID {}, Speed {:.1f}->{:.1f}, AltErr {:.1f}, VX {:.1f}", 
                          //    it.entity(i).id(), current_speed, new_speed, alt_error, v[i].vx);
                    }
                }
            }
        });
}
