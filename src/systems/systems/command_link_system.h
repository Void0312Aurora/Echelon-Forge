#pragma once

#include <flecs.h>
#include "components/command/command_link.h"
#include "components/command/command_link_qos.h"
#include "components/command/common/mission_command_control_state.h"
#include "components/command/legacy_command_bridge.h"
#include "components/basic/common.h"

namespace {
// Compatibility bridge seam for deferred delivery of quarantined action DTOs.
inline void deliver_pending_action_command(
    flecs::entity entity,
    ActionCommand& cmd,
    PendingActionCommand& pending,
    double current_time
) {
    if (!pending.active) return;
    if (current_time < pending.deliver_time) return;
    cmd = pending.command;
    cmd.active = true;
    refresh_optional_compatibility_typed_air_control_from_action_command(
        entity,
        cmd
    );
    pending.active = false;
}

inline void deliver_pending_movement_command(
    MissionCommandControlState& state,
    MovementCommand* cmd,
    LaggedCommand* lagged,
    PendingMovementCommand& pending,
    double current_time
) {
    if (!pending.active) return;
    if (current_time < pending.deliver_time) return;

    const MissionCommandControlState& delivered = pending.typed_command.control_state;

    set_mission_command_control_target(
        state,
        delivered.target_heading_deg,
        delivered.target_speed_mps,
        delivered.target_altitude_m,
        delivered.active
    );

    if (!state.lagged_active) {
        set_mission_command_control_lagged(
            state,
            delivered.target_heading_deg,
            delivered.target_speed_mps,
            delivered.target_altitude_m,
            delivered.active
        );
    }

    refresh_optional_compatibility_autopilot_movement_command_from_control_state(
        cmd,
        state
    );
    refresh_optional_compatibility_lagged_command_mirror_from_control_state(
        lagged,
        state
    );
    pending.command = project_pending_movement_command_diagnostics_shell(
        pending.typed_command
    );
    pending.active = false;
}
}  // namespace

inline void register_command_link_system(flecs::world& ecs) {
    ecs.system<MissionCommandControlState, MovementCommand, LaggedCommand, PendingMovementCommand, const CommandLink>("CommandLinkMovement")
        .term_at(1).optional()
        .term_at(2).optional()
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto state = it.field<MissionCommandControlState>(0);
                auto pending = it.field<PendingMovementCommand>(3);
                (void)it.field<const CommandLink>(4);
                const ecs_world_info_t* info = ecs_get_world_info(it.world().c_ptr());
                double current_time = info ? (double)info->world_time_total : 0.0;
                MovementCommand* movement_mirror =
                    it.is_set(1) ? &it.field_at<MovementCommand>(1, 0) : nullptr;
                LaggedCommand* lagged_mirror =
                    it.is_set(2) ? &it.field_at<LaggedCommand>(2, 0) : nullptr;

                for (auto i : it) {
                    deliver_pending_movement_command(
                        state[i],
                        movement_mirror ? &movement_mirror[i] : nullptr,
                        lagged_mirror ? &lagged_mirror[i] : nullptr,
                        pending[i],
                        current_time
                    );
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
                    deliver_pending_action_command(
                        it.entity(i),
                        cmd[i],
                        pending[i],
                        current_time
                    );
                }
            }
        });

    ecs.system<MissionCommand, PendingMissionCommand, MissionCommandPendingQueue, const CommandLink>("CommandLinkMission")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto cmd = it.field<MissionCommand>(0);
                auto pending = it.field<PendingMissionCommand>(1);
                auto queue = it.field<MissionCommandPendingQueue>(2);
                (void)it.field<const CommandLink>(3);
                const ecs_world_info_t* info = ecs_get_world_info(it.world().c_ptr());
                double current_time = info ? (double)info->world_time_total : 0.0;

                for (auto i : it) {
                    if (!pending[i].active || current_time < pending[i].deliver_time) {
                        continue;
                    }

                    cmd[i] = pending[i].command;
                    cmd[i].active = true;

                    if (!promote_next_pending_mission_command(pending[i], queue[i])) {
                        pending[i].active = false;
                    }
                }
            }
        });
}
