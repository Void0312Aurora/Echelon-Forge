#pragma once

#include <flecs.h>
#include "components/physics/forces.h"

inline void register_force_clear_system(flecs::world& ecs) {
    ecs.system<ForceAccumulator>("ClearForces")
        .kind(flecs::OnLoad)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto forces = it.field<ForceAccumulator>(0);
                for (auto i : it) {
                    forces[i].clear();
                }
            }
        });
}
