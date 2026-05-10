#pragma once

#include <flecs.h>
#include <spdlog/spdlog.h>
#include "components/basic/common.h"
#include "components/basic/tags.h"
#include "components/command/legacy_command.h"
#include "components/systems/ew.h"

inline void register_ew_system(flecs::world& ecs) {
    // 1. Chaff Release System
    ecs.system<const ActionCommand, Countermeasures, const Transform, const Velocity>("EW_Release_Chaff")
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto cmd = it.field<const ActionCommand>(0);
                auto cm = it.field<Countermeasures>(1);
                auto p = it.field<const Transform>(2);
                auto v = it.field<const Velocity>(3);

                const ecs_world_info_t* info = ecs_get_world_info(it.world().c_ptr());
                double current_time = info ? (double)info->world_time_total : 0.0;

                for (auto i : it) {
                    if (cmd[i].release_chaff) {
                        if (cm[i].chaff_count > 0 && (current_time - cm[i].last_release_time >= cm[i].release_interval)) {
                            cm[i].chaff_count--;
                            cm[i].last_release_time = current_time;

                            // Spawn Chaff Entity
                            it.world().entity()
                                .set<Transform>({p[i].x, p[i].y, p[i].z, 0.0, 0.0, 0.0})
                                .set<Velocity>({v[i].vx * 0.1, v[i].vy * 0.1, v[i].vz * 0.1})
                                .set<RCSProfile>({50.0, 50.0, 50.0}) 
                                .set<Lifetime>({20.0, 0.0}) 
                                .set<KeyEntity>({UnitType::Unknown}) 
                                .add<SimObject>();
                            
                            spdlog::debug("Unit {} released Chaff. Remaining: {}", it.entity(i).id(), cm[i].chaff_count);
                        }
                    }
                }
            }
        });

    // 2. Flare Release System
    ecs.system<const ActionCommand, Countermeasures, const Transform, const Velocity>("EW_Release_Flare")
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto cmd = it.field<const ActionCommand>(0);
                auto cm = it.field<Countermeasures>(1);
                auto p = it.field<const Transform>(2);
                auto v = it.field<const Velocity>(3);

                const ecs_world_info_t* info = ecs_get_world_info(it.world().c_ptr());
                double current_time = info ? (double)info->world_time_total : 0.0;

                for (auto i : it) {
                    if (cmd[i].release_flare) {
                        if (cm[i].flare_count > 0 && (current_time - cm[i].last_release_time >= cm[i].release_interval)) {
                            cm[i].flare_count--;
                            cm[i].last_release_time = current_time;

                            it.world().entity()
                                .set<Transform>({p[i].x, p[i].y, p[i].z, 0.0, 0.0, 0.0})
                                .set<Velocity>({v[i].vx, v[i].vy, v[i].vz}) 
                                .set<Lifetime>({10.0, 0.0}) 
                                .set<KeyEntity>({UnitType::Unknown}) 
                                .add<SimObject>();
                                
                            spdlog::debug("Unit {} released Flare. Remaining: {}", it.entity(i).id(), cm[i].flare_count);
                        }
                    }
                }
            }
        });

    // 3. Lifetime Management System
    ecs.system<Lifetime>("EW_Lifetime_Manager")
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto l = it.field<Lifetime>(0);
                double dt = it.delta_time();
                
                for (auto i : it) {
                    l[i].current_age += dt;
                    if (l[i].current_age > l[i].max_age) {
                        it.entity(i).destruct();
                    }
                }
            }
        });
}
