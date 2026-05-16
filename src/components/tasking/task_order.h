#pragma once

#include "components/tasking/air/task_order_air.h"
#include "components/tasking/common/task_order_core.h"
#include "components/tasking/naval/task_order_naval.h"

/**
 * TaskOrder
 * Implements task_order_leader_standard.md: the C2 -> Leader task object.
 */
struct TaskOrder : TaskOrderCore, TaskOrderAir, TaskOrderNaval {};
