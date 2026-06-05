#pragma once

#include "components/tasking/air/task_order_air.h"
#include "components/tasking/common/task_order_core.h"
#include "components/tasking/ground/task_order_ground.h"
#include "components/tasking/naval/task_order_naval.h"

/**
 * TaskOrder
 * Implements task_order_leader_standard.md: the C2 -> Leader task object.
 */
struct TaskOrder : TaskOrderCore, TaskOrderAir, TaskOrderNaval, TaskOrderGround {};

// Flat umbrella retained only as a compatibility/transport shell.
// Shared-core and domain slices remain the maintained owner surfaces.
using TaskOrderCompatibilityTransportShell = TaskOrder;
using TaskOrderSharedCoreOwnerSlice = TaskOrderCore;
using TaskOrderSharedCoreDirective = TaskOrderCore;
inline constexpr bool kTaskOrderCompatibilityTransportShell = true;
inline constexpr bool kTaskOrderSharedCoreOwnedSurface = true;

static_assert(
    kTaskOrderAirOwnedDomainSlice && kTaskOrderNavalOwnedDomainSlice &&
        kTaskOrderGroundOwnedDomainSlice,
    "TaskOrder compatibility shells must project to explicit owner slices."
);
static_assert(
    kTaskOrderSharedCoreOwnedSurface,
    "TaskOrder shared core must stay an explicit maintained owner surface."
);

[[nodiscard]] inline const TaskOrderSharedCoreOwnerSlice&
task_order_shared_core(const TaskOrderCompatibilityTransportShell& order) noexcept {
    return order;
}

[[nodiscard]] inline TaskOrderSharedCoreOwnerSlice&
task_order_shared_core(TaskOrderCompatibilityTransportShell& order) noexcept {
    return order;
}

[[nodiscard]] inline TaskOrderSharedCoreDirective
task_order_shared_core_directive(const TaskOrderSharedCoreOwnerSlice& core) noexcept {
    return core;
}

[[nodiscard]] inline TaskOrderSharedCoreDirective
task_order_shared_core_directive(const TaskOrderCompatibilityTransportShell& order) noexcept {
    return task_order_shared_core_directive(task_order_shared_core(order));
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

[[nodiscard]] inline const TaskOrderGround&
task_order_ground_owner_slice(const TaskOrderCompatibilityTransportShell& order) noexcept {
    return order;
}

[[nodiscard]] inline TaskOrderGround&
task_order_ground_owner_slice(TaskOrderCompatibilityTransportShell& order) noexcept {
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

[[nodiscard]] inline TaskOrderGround::StaticTaskDirective
task_order_ground_static_task_directive(
    const TaskOrderCompatibilityTransportShell& order
) noexcept {
    return task_order_ground_static_task_directive(task_order_ground_owner_slice(order));
}
