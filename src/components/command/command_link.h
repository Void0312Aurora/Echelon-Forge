#pragma once

#include "components/command/legacy_command.h"
#include "components/command/mission_command.h"

struct CommandLink {
    double latency_s;   // One-way command latency
    double drop_prob;   // [0,1] command drop probability
};

struct PendingMovementCommand {
    MovementCommand command;
    double deliver_time;
    bool active;
};

inline PendingMovementCommand make_pending_movement_command(
    const MovementCommand& command = make_legacy_autopilot_movement_command(0.0, 0.0, 0.0, false),
    double deliver_time = 0.0,
    bool active = false
) {
    return {command, deliver_time, active};
}

struct PendingActionCommand {
    ActionCommand command;
    double deliver_time;
    bool active;
};

inline PendingActionCommand make_pending_action_command(
    const ActionCommand& command = make_action_command(),
    double deliver_time = 0.0,
    bool active = false
) {
    return {command, deliver_time, active};
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
