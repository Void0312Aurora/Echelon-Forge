#pragma once

#include "components/domains/air/command/mission_command_air.h"
#include "components/command/common/mission_command_core.h"
#include "components/domains/ground/command/mission_command_ground.h"
#include "components/domains/naval/command/mission_command_naval.h"

/**
 * MissionCommand
 * Implements [aim.md]: The high-level intent from Commander.
 */
struct MissionCommand : MissionCommandCore,
                        MissionCommandAir,
                        MissionCommandNaval,
                        MissionCommandGround {};

bool operator==(const MissionCommand &, const MissionCommand &) = delete;
bool operator==(const MissionCommand &, const MissionCommandCore &) = delete;
bool operator==(const MissionCommandCore &, const MissionCommand &) = delete;

// Flat umbrella retained only as a compatibility/transport shell.
// Shared-core and domain slices remain the maintained owner surfaces.
using MissionCommandCompatibilityTransportShell = MissionCommand;
using MissionCommandSharedCoreOwnerSlice = MissionCommandCore;
inline constexpr bool kMissionCommandCompatibilityTransportShell = true;
inline constexpr bool kMissionCommandSharedCoreOwnedSurface = true;

static_assert(kMissionCommandAirOwnedDomainSlice && kMissionCommandNavalOwnedDomainSlice &&
                  kMissionCommandGroundOwnedDomainSlice,
              "MissionCommand compatibility shells must project to explicit owner slices.");
static_assert(kMissionCommandSharedCoreOwnedSurface,
              "MissionCommand shared core must stay an explicit maintained owner surface.");

using MissionCommandSharedCoreDirective = MissionCommandCore;

[[nodiscard]] inline const MissionCommandSharedCoreOwnerSlice &
mission_command_shared_core(const MissionCommandCompatibilityTransportShell &command) noexcept {
    return command;
}

[[nodiscard]] inline MissionCommandSharedCoreOwnerSlice &
mission_command_shared_core(MissionCommandCompatibilityTransportShell &command) noexcept {
    return command;
}

[[nodiscard]] inline MissionCommandSharedCoreDirective
mission_command_shared_core_directive(const MissionCommandSharedCoreOwnerSlice &core) noexcept {
    return core;
}

[[nodiscard]] inline MissionCommandSharedCoreDirective mission_command_shared_core_directive(
    const MissionCommandCompatibilityTransportShell &command) noexcept {
    return mission_command_shared_core_directive(mission_command_shared_core(command));
}

[[nodiscard]] inline const MissionCommandAir &
mission_command_air_owner_slice(const MissionCommandCompatibilityTransportShell &command) noexcept {
    return command;
}

[[nodiscard]] inline MissionCommandAir &
mission_command_air_owner_slice(MissionCommandCompatibilityTransportShell &command) noexcept {
    return command;
}

[[nodiscard]] inline const MissionCommandNaval &mission_command_naval_owner_slice(
    const MissionCommandCompatibilityTransportShell &command) noexcept {
    return command;
}

[[nodiscard]] inline MissionCommandNaval &
mission_command_naval_owner_slice(MissionCommandCompatibilityTransportShell &command) noexcept {
    return command;
}

[[nodiscard]] inline const MissionCommandGround &mission_command_ground_owner_slice(
    const MissionCommandCompatibilityTransportShell &command) noexcept {
    return command;
}

[[nodiscard]] inline MissionCommandGround &
mission_command_ground_owner_slice(MissionCommandCompatibilityTransportShell &command) noexcept {
    return command;
}

[[nodiscard]] inline MissionCommandAir::RecoveryDirective mission_command_air_recovery_directive(
    const MissionCommandCompatibilityTransportShell &command) noexcept {
    return mission_command_air_recovery_directive(mission_command_air_owner_slice(command));
}

[[nodiscard]] inline MissionCommandAir::TakeoffDirective mission_command_air_takeoff_directive(
    const MissionCommandCompatibilityTransportShell &command) noexcept {
    return mission_command_air_takeoff_directive(mission_command_air_owner_slice(command));
}

[[nodiscard]] inline MissionCommandAir::FormationDirective mission_command_air_formation_directive(
    const MissionCommandCompatibilityTransportShell &command) noexcept {
    return mission_command_air_formation_directive(mission_command_air_owner_slice(command));
}

[[nodiscard]] inline MissionCommandNaval::StationingDirective
mission_command_naval_stationing_directive(
    const MissionCommandCompatibilityTransportShell &command) noexcept {
    return mission_command_naval_stationing_directive(mission_command_naval_owner_slice(command));
}

[[nodiscard]] inline MissionCommandNaval::EmbarkedHeloDirective
mission_command_naval_embarked_helo_directive(
    const MissionCommandCompatibilityTransportShell &command) noexcept {
    return mission_command_naval_embarked_helo_directive(
        mission_command_naval_owner_slice(command));
}

[[nodiscard]] inline MissionCommandGround::StaticTaskDirective
mission_command_ground_static_task_directive(
    const MissionCommandCompatibilityTransportShell &command) noexcept {
    return mission_command_ground_static_task_directive(
        mission_command_ground_owner_slice(command));
}
