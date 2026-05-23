#pragma once

#include "components/tasking/air/task_order_air.h"
#include "components/tasking/common/task_order_core.h"
#include "components/tasking/naval/task_order_naval.h"

/**
 * TaskOrder
 * Implements task_order_leader_standard.md: the C2 -> Leader task object.
 */
struct TaskOrder : TaskOrderCore, TaskOrderAir, TaskOrderNaval {};

// Flat umbrella retained only as a compatibility/transport shell.
// Shared-core and domain slices remain the maintained owner surfaces.
using TaskOrderCompatibilityTransportShell = TaskOrder;
inline constexpr bool kTaskOrderCompatibilityTransportShell = true;

static_assert(
    kTaskOrderAirOwnedDomainSlice && kTaskOrderNavalOwnedDomainSlice,
    "TaskOrder compatibility shells must project to explicit owner slices."
);

[[nodiscard]] inline const TaskOrderCore&
task_order_shared_core(const TaskOrderCompatibilityTransportShell& order) noexcept {
    return order;
}

[[nodiscard]] inline TaskOrderCore&
task_order_shared_core(TaskOrderCompatibilityTransportShell& order) noexcept {
    return order;
}

[[nodiscard]] inline const TaskOrderAir&
task_order_air_owner_slice(const TaskOrderCompatibilityTransportShell& order) noexcept {
    return order;
}

[[nodiscard]] inline TaskOrderAir&
task_order_air_owner_slice(TaskOrderCompatibilityTransportShell& order) noexcept {
    return order;
}

[[nodiscard]] inline const TaskOrderNaval&
task_order_naval_owner_slice(const TaskOrderCompatibilityTransportShell& order) noexcept {
    return order;
}

[[nodiscard]] inline TaskOrderNaval&
task_order_naval_owner_slice(TaskOrderCompatibilityTransportShell& order) noexcept {
    return order;
}

[[nodiscard]] inline TaskOrderAir::RecoveryDirective
task_order_air_recovery_directive(
    const TaskOrderCompatibilityTransportShell& order
) noexcept {
    return task_order_air_recovery_directive(task_order_air_owner_slice(order));
}

[[nodiscard]] inline TaskOrderAir::TakeoffDirective
task_order_air_takeoff_directive(
    const TaskOrderCompatibilityTransportShell& order
) noexcept {
    return task_order_air_takeoff_directive(task_order_air_owner_slice(order));
}

[[nodiscard]] inline TaskOrderNaval::CommandAuthorityDirective
task_order_naval_command_authority(
    const TaskOrderCompatibilityTransportShell& order
) noexcept {
    return task_order_naval_command_authority(task_order_naval_owner_slice(order));
}
