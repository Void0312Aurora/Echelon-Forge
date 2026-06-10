#pragma once

#include <flecs.h>
#include "components/basic/common.h"
#include "components/combat/common/weapon_common.h"
#include "core/interfaces/guidance_model.h"

inline void register_guidance_system(flecs::world& ecs) {
    ecs.system<Velocity, const Transform, Missile>("MissileGuidance")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto v = it.field<Velocity>(0);
                auto p = it.field<const Transform>(1);
                auto missile_comp = it.field<Missile>(2);
                const GuidanceModelRef* model_ref = it.world().get<GuidanceModelRef>();
                
                double dt = it.delta_time();

                for (auto i : it) {
                    if (!model_ref || !model_ref->model) {
                        continue;
                    }

                    model_ref->model->update(it.world(),
                                             it.entity(i),
                                             v[i],
                                             p[i],
                                             missile_comp[i],
                                             dt);
                }
            }
        });
}
