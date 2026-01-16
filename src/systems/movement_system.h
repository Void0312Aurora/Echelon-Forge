#pragma once

#include <flecs.h>
#include <cmath>
#include "components/common.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

inline double movement_wrap_angle_360(double angle) {
    while (angle < 0.0) angle += 360.0;
    while (angle >= 360.0) angle -= 360.0;
    return angle;
}

inline double movement_math_deg_to_nav_deg(double math_deg) {
    return movement_wrap_angle_360(90.0 - math_deg);
}

// System implementation
// In Flecs C++, systems can be just a lambda or a function, 
// ensuring we keep it header-only or well-structured is good.

inline void register_movement_system(flecs::world& ecs) {
    ecs.system<Transform, const Velocity>("UpdatePosition")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto p = it.field<Transform>(0);
                auto v = it.field<const Velocity>(1);
                double dt = it.delta_time();
                
                for (auto i : it) {
                    p[i].x += v[i].vx * dt;
                    p[i].y += v[i].vy * dt;
                    p[i].z += v[i].vz * dt;

                    double h_speed_sq = v[i].vx * v[i].vx + v[i].vy * v[i].vy;
                    if (h_speed_sq > 1e-12) {
                        double math_deg = std::atan2(v[i].vy, v[i].vx) * 180.0 / M_PI;
                        p[i].heading = movement_math_deg_to_nav_deg(math_deg);
                    }
                }
            }
        });
}
