#pragma once

#include "components/command/air/mission_command_air.h"
#include "components/command/common/mission_command_core.h"

/**
 * MissionCommand
 * Implements [aim.md]: The high-level intent from Commander.
 */
struct MissionCommand : MissionCommandCore, MissionCommandAir {};
