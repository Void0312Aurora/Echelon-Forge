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

struct PendingActionCommand {
    ActionCommand command;
    double deliver_time;
    bool active;
};

struct PendingMissionCommand {
    MissionCommand command;
    double deliver_time;
    bool active;
};
