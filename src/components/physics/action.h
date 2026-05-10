#pragma once

// Compatibility umbrella for historical includes.
//
// New code should include the specific command/tasking header it needs:
// - components/command/pilot_action.h
// - components/command/mission_command.h
// - components/command/legacy_command.h
// - components/command/command_link.h
// - components/tasking/tasking_enums.h
// - components/tasking/task_order.h
// - components/tasking/leader_intent.h
// - components/tasking/pilot_report.h

#include "components/command/command_link.h"
#include "components/command/legacy_command.h"
#include "components/command/mission_command.h"
#include "components/command/pilot_action.h"
#include "components/tasking/leader_intent.h"
#include "components/tasking/pilot_report.h"
#include "components/tasking/task_order.h"
#include "components/tasking/tasking_enums.h"
