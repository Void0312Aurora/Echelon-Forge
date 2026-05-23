#pragma once

#include <algorithm>

#include "components/command/common/mission_command_control_state.h"
#include "components/command/legacy_command.h"
#include "components/command/mission_command.h"

struct CommandLink {
    double latency_s;   // One-way command latency
    double drop_prob;   // [0,1] command drop probability
};

struct PendingMissionControlCommand {
    MissionCommandControlState control_state;
};

inline PendingMissionControlCommand make_pending_mission_control_command(
    double heading_deg = 0.0,
    double speed_mps = 0.0,
    double altitude_m = 0.0,
    bool active = false
) {
    PendingMissionControlCommand pending{};
    set_mission_command_control_target(
        pending.control_state,
        heading_deg,
        speed_mps,
        altitude_m,
        active
    );
    pending.control_state.lagged_heading_deg = 0.0;
    pending.control_state.lagged_speed_mps = 0.0;
    pending.control_state.lagged_altitude_m = 0.0;
    pending.control_state.lagged_active = false;
    return pending;
}

inline PendingMissionControlCommand make_pending_mission_control_command(
    const MissionCommandControlState& control_state
) {
    PendingMissionControlCommand pending{};
    pending.control_state = control_state;
    pending.control_state.lagged_heading_deg = 0.0;
    pending.control_state.lagged_speed_mps = 0.0;
    pending.control_state.lagged_altitude_m = 0.0;
    pending.control_state.lagged_active = false;
    return pending;
}

inline PendingMissionControlCommand make_pending_mission_control_command(
    const MovementCommand& command
) {
    return make_pending_mission_control_command(
        command.target_heading,
        command.target_speed,
        command.target_altitude,
        command.active
    );
}

inline MovementCommand project_pending_movement_command_diagnostics_shell(
    const PendingMissionControlCommand& pending
) {
    return make_legacy_autopilot_movement_command(
        pending.control_state.target_heading_deg,
        pending.control_state.target_speed_mps,
        pending.control_state.target_altitude_m,
        pending.control_state.active
    );
}

inline MissionCommandTypedAirControlState project_pending_action_command_typed_air_control_bridge(
    const ActionCommand& command
) {
    MissionCommandTypedAirControlState typed_air_control{};
    typed_air_control.throttle_command =
        std::clamp((command.accel_cmd + 1.0) * 0.5, 0.0, 1.0);
    typed_air_control.throttle_active = command.active;
    typed_air_control.throttle_idle = typed_air_control.throttle_command < 0.01;
    typed_air_control.ground_active = command.active;
    typed_air_control.action_semantics_active = command.active;
    return typed_air_control;
}

struct PendingMovementCommand {
    PendingMissionControlCommand typed_command;
    // Diagnostics transport shell only; maintained delivery must consume typed_command.
    MovementCommand command;
    double deliver_time;
    bool active;
};

inline PendingMovementCommand make_pending_movement_command(
    const PendingMissionControlCommand& typed_command = make_pending_mission_control_command(),
    double deliver_time = 0.0,
    bool active = false
) {
    return {
        typed_command,
        project_pending_movement_command_diagnostics_shell(typed_command),
        deliver_time,
        active,
    };
}

inline PendingMovementCommand make_pending_movement_command(
    const MovementCommand& command,
    double deliver_time = 0.0,
    bool active = false
) {
    const PendingMissionControlCommand typed_command =
        make_pending_mission_control_command(command);
    // Compatibility diagnostics seed only: maintained delivery consumes the
    // typed MissionCommandControlState payload derived below, not this shell.
    return {
        typed_command,
        project_pending_movement_command_diagnostics_shell(typed_command),
        deliver_time,
        active,
    };
}

inline void refresh_pending_movement_command_diagnostics_shell(
    PendingMovementCommand& pending
) {
    pending.command = project_pending_movement_command_diagnostics_shell(
        pending.typed_command
    );
}

// Quarantined legacy action transport shell: no lossless typed replacement yet.
struct PendingActionCommand {
    // Bridge-owned typed overlay snapshot only. This is not a full typed
    // action replacement; it merely preserves the maintained air-control
    // overlay semantics that can be refreshed onto MissionCommandControlState.
    MissionCommandTypedAirControlState typed_air_control_bridge;
    ActionCommand command;
    double deliver_time;
    bool active;
};

inline PendingActionCommand make_pending_action_command(
    const ActionCommand& command = make_action_command(),
    double deliver_time = 0.0,
    bool active = false
) {
    return {
        project_pending_action_command_typed_air_control_bridge(command),
        command,
        deliver_time,
        active,
    };
}

inline void refresh_pending_action_command_typed_air_control_bridge(
    PendingActionCommand& pending
) {
    pending.typed_air_control_bridge =
        project_pending_action_command_typed_air_control_bridge(pending.command);
}

struct PendingMissionCommand {
    MissionCommand command;
    double deliver_time;
    bool active;
};

inline PendingMissionCommand make_pending_mission_command(
    const MissionCommand& command = MissionCommand{},
    double deliver_time = 0.0,
    bool active = false
) {
    return {command, deliver_time, active};
}
