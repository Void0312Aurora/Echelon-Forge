#pragma once

#include <flecs.h>
#include <cmath>
#include "components/common.h"
#include "components/weapon.h"
#include <spdlog/spdlog.h>

inline void register_damage_system(flecs::world& ecs) {
    ecs.system<const Transform, Missile>("ProximityFuze")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto p = it.field<const Transform>(0);
                auto m = it.field<Missile>(1);
                
                for (auto i : it) {
                    if (!m[i].active) continue;
                    
                    auto target_entity = it.world().entity(m[i].target_id);
                    if (!target_entity.is_valid()) {
                        // Target already dead, kill missile
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
                        // HEAT! Destroy Target
                        spdlog::info("SPLASH! Missile {} destroyed Target {}", 
                            it.entity(i).id(), m[i].target_id);
                            
                        target_entity.destruct();
                        it.entity(i).destruct();
                    }
                }
            }
        });
}
