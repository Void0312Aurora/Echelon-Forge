#pragma once

#include "components/command/air/mission_command_air.h"
#include "components/command/common/mission_command_core.h"
#include "components/command/naval/mission_command_naval.h"

/**
 * MissionCommand
 * Implements [aim.md]: The high-level intent from Commander.
 */
struct MissionCommand : MissionCommandCore, MissionCommandAir, MissionCommandNaval {};
