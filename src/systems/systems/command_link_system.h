#pragma once

#include <flecs.h>
#include "components/command/command_link.h"

namespace {
template <typename CommandT, typename PendingT>
inline void deliver_pending_command(
    CommandT& cmd,
    PendingT& pending,
    double current_time
) {
    if (!pending.active) return;
    if (current_time < pending.deliver_time) return;
    cmd = pending.command;
    cmd.active = true;
    pending.active = false;
}
}  // namespace

inline void register_command_link_system(flecs::world& ecs) {
    ecs.system<MovementCommand, PendingMovementCommand, const CommandLink>("CommandLinkMovement")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto cmd = it.field<MovementCommand>(0);
                auto pending = it.field<PendingMovementCommand>(1);
                (void)it.field<const CommandLink>(2);
                const ecs_world_info_t* info = ecs_get_world_info(it.world().c_ptr());
                double current_time = info ? (double)info->world_time_total : 0.0;

                for (auto i : it) {
                    deliver_pending_command(cmd[i], pending[i], current_time);
                }
            }
        });

    ecs.system<ActionCommand, PendingActionCommand, const CommandLink>("CommandLinkAction")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto cmd = it.field<ActionCommand>(0);
                auto pending = it.field<PendingActionCommand>(1);
                (void)it.field<const CommandLink>(2);
                const ecs_world_info_t* info = ecs_get_world_info(it.world().c_ptr());
                double current_time = info ? (double)info->world_time_total : 0.0;

                for (auto i : it) {
                    deliver_pending_command(cmd[i], pending[i], current_time);
                }
            }
        });

    ecs.system<MissionCommand, PendingMissionCommand, const CommandLink>("CommandLinkMission")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto cmd = it.field<MissionCommand>(0);
                auto pending = it.field<PendingMissionCommand>(1);
                (void)it.field<const CommandLink>(2);
                const ecs_world_info_t* info = ecs_get_world_info(it.world().c_ptr());
                double current_time = info ? (double)info->world_time_total : 0.0;

                for (auto i : it) {
                    deliver_pending_command(cmd[i], pending[i], current_time);
                }
            }
        });
}
