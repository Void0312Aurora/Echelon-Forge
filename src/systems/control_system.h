#pragma once

#include <flecs.h>
#include <cmath>
#include "components/common.h"
#include "components/action.h"
#include <algorithm>

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
    ecs.system<Velocity, const MovementCommand>("KinematicControl")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            // Constants for MVP (Could be components later)
            const double MAX_TURN_RATE = 15.0; // deg/s
            const double MAX_ACCEL = 50.0;     // m/s^2

            while (it.next()) {
                auto v = it.field<Velocity>(0);
                auto cmd = it.field<const MovementCommand>(1);
                double dt = it.delta_time();
                
                for (auto i : it) {
                    if (!cmd[i].active) continue;

                    // 1. Current State
                    double current_speed = std::sqrt(v[i].vx*v[i].vx + v[i].vy*v[i].vy);
                    
                    // Avoid atan2(0,0) by assuming heading 0 if stopped
                    double current_heading_math = std::atan2(v[i].vy, v[i].vx); // radians, 0=East, CCW
                    double current_heading_nav = 90.0 - to_degrees(current_heading_math);
                    current_heading_nav = normalize_angle(current_heading_nav);

                    // 2. Heading Control
                    double heading_error = normalize_angle(cmd[i].target_heading - current_heading_nav);
                    double max_turn = MAX_TURN_RATE * dt;
                    
                    // Clamp turn
                    double turn = std::clamp(heading_error, -max_turn, max_turn);
                    double new_heading_nav = current_heading_nav + turn;
                    
                    // 3. Speed Control
                    double speed_error = cmd[i].target_speed - current_speed;
                    double max_accel = MAX_ACCEL * dt;
                    double accel = std::clamp(speed_error, -max_accel, max_accel);
                    double new_speed = std::max(0.0, current_speed + accel);

                    // 4. Update Velocity
                    double new_heading_math = to_radians(90.0 - new_heading_nav);
                    
                    v[i].vx = new_speed * std::cos(new_heading_math);
                    v[i].vy = new_speed * std::sin(new_heading_math);
                    // Ignore Z for now (2D control)
                }
            }
        });
}
