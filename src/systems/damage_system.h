#pragma once

#include <flecs.h>
#include <spdlog/spdlog.h>

#include "components/common.h"
#include "components/weapon.h"
#include "core/effects_model.h"
#include <spdlog/spdlog.h>

inline void register_damage_system(flecs::world& ecs) {
    ecs.system<const Transform, Missile>("ProximityFuze")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto p = it.field<const Transform>(0);
                auto m = it.field<Missile>(1);
                const EffectsModelRef* effects_ref = it.world().get<EffectsModelRef>();
                
                for (auto i : it) {
                    if (!m[i].active) continue;
                    
                    auto target_entity = it.world().entity(m[i].target_id);
                    if (!target_entity.is_valid()) {
                        it.entity(i).destruct();
                        continue;
                    }
                    
                    const Transform* t_pos = target_entity.get<Transform>();
                    if(!t_pos) continue;
                    
                    double dx = p[i].x - t_pos->x;
                    double dy = p[i].y - t_pos->y;
                    double dz = p[i].z - t_pos->z;
                    double dist_sq = dx*dx + dy*dy + dz*dz;
                    
                    double fuse_sq = m[i].fuse_distance * m[i].fuse_distance;
                    
                    if (dist_sq < fuse_sq) {
                        if (!effects_ref || !effects_ref->model) {
                            spdlog::warn("Effects model not configured; skipping hit resolution.");
                            it.entity(i).destruct();
                            continue;
                        }

                        EffectsResult result = effects_ref->model->on_proximity_hit(
                            it.world(), it.entity(i), m[i], target_entity);
                        if (result.destroy_missile) {
                            it.entity(i).destruct();
                        }
                    }
                }
            }
        });
}
