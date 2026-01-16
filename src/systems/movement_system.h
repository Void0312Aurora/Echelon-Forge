#pragma once

#include <flecs.h>
#include "components/common.h"

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
                }
            }
        });
}
