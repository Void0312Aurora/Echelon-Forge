#pragma once

#include <flecs.h>
#include "components/command/command_link.h"

inline void register_command_link_system(flecs::world& ecs) {
    ecs.system<MovementCommand, PendingMovementCommand, const CommandLink>("CommandLinkMovement")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto cmd = it.field<MovementCommand>(0);
                auto pending = it.field<PendingMovementCommand>(1);
                auto link = it.field<const CommandLink>(2);
                const ecs_world_info_t* info = ecs_get_world_info(it.world().c_ptr());
                double current_time = info ? (double)info->world_time_total : 0.0;

                for (auto i : it) {
                    if (!pending[i].active) continue;
                    if (current_time < pending[i].deliver_time) continue;
                    cmd[i] = pending[i].command;
                    cmd[i].active = true;
                    pending[i].active = false;
                    (void)link;
                }
            }
        });

    ecs.system<ActionCommand, PendingActionCommand, const CommandLink>("CommandLinkAction")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto cmd = it.field<ActionCommand>(0);
                auto pending = it.field<PendingActionCommand>(1);
                auto link = it.field<const CommandLink>(2);
                const ecs_world_info_t* info = ecs_get_world_info(it.world().c_ptr());
                double current_time = info ? (double)info->world_time_total : 0.0;

                for (auto i : it) {
                    if (!pending[i].active) continue;
                    if (current_time < pending[i].deliver_time) continue;
                    cmd[i] = pending[i].command;
                    cmd[i].active = true;
                    pending[i].active = false;
                    (void)link;
                }
            }
        });

    ecs.system<MissionCommand, PendingMissionCommand, const CommandLink>("CommandLinkMission")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto cmd = it.field<MissionCommand>(0);
                auto pending = it.field<PendingMissionCommand>(1);
                auto link = it.field<const CommandLink>(2);
                const ecs_world_info_t* info = ecs_get_world_info(it.world().c_ptr());
                double current_time = info ? (double)info->world_time_total : 0.0;

                for (auto i : it) {
                    if (!pending[i].active) continue;
                    if (current_time < pending[i].deliver_time) continue;
                    cmd[i] = pending[i].command;
                    cmd[i].active = true;
                    pending[i].active = false;
                    (void)link;
                }
            }
        });
}
