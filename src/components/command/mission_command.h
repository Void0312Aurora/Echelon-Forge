#pragma once

#include "components/command/air/mission_command_air.h"
#include "components/command/common/mission_command_core.h"
#include "components/command/naval/mission_command_naval.h"

/**
 * MissionCommand
 * Implements [aim.md]: The high-level intent from Commander.
 */
struct MissionCommand : MissionCommandCore, MissionCommandAir, MissionCommandNaval {};

// Flat umbrella retained only as a compatibility/transport shell.
// Shared-core and domain slices remain the maintained owner surfaces.
using MissionCommandCompatibilityTransportShell = MissionCommand;
inline constexpr bool kMissionCommandCompatibilityTransportShell = true;

static_assert(
    kMissionCommandAirOwnedDomainSlice && kMissionCommandNavalOwnedDomainSlice,
    "MissionCommand compatibility shells must project to explicit owner slices."
);

[[nodiscard]] inline const MissionCommandCore&
mission_command_shared_core(
    const MissionCommandCompatibilityTransportShell& command
) noexcept {
    return command;
}

[[nodiscard]] inline MissionCommandCore&
mission_command_shared_core(MissionCommandCompatibilityTransportShell& command) noexcept {
    return command;
}

[[nodiscard]] inline const MissionCommandAir&
mission_command_air_owner_slice(
    const MissionCommandCompatibilityTransportShell& command
) noexcept {
    return command;
}

[[nodiscard]] inline MissionCommandAir&
mission_command_air_owner_slice(MissionCommandCompatibilityTransportShell& command) noexcept {
    return command;
}

[[nodiscard]] inline const MissionCommandNaval&
mission_command_naval_owner_slice(
    const MissionCommandCompatibilityTransportShell& command
) noexcept {
    return command;
}

[[nodiscard]] inline MissionCommandNaval&
mission_command_naval_owner_slice(
    MissionCommandCompatibilityTransportShell& command
) noexcept {
    return command;
}

[[nodiscard]] inline MissionCommandAir::RecoveryDirective
mission_command_air_recovery_directive(
    const MissionCommandCompatibilityTransportShell& command
) noexcept {
    return mission_command_air_recovery_directive(mission_command_air_owner_slice(command));
}

[[nodiscard]] inline MissionCommandAir::TakeoffDirective
mission_command_air_takeoff_directive(
    const MissionCommandCompatibilityTransportShell& command
) noexcept {
    return mission_command_air_takeoff_directive(mission_command_air_owner_slice(command));
}

[[nodiscard]] inline MissionCommandAir::FormationDirective
mission_command_air_formation_directive(
    const MissionCommandCompatibilityTransportShell& command
) noexcept {
    return mission_command_air_formation_directive(mission_command_air_owner_slice(command));
}

[[nodiscard]] inline MissionCommandNaval::StationingDirective
mission_command_naval_stationing_directive(
    const MissionCommandCompatibilityTransportShell& command
) noexcept {
    return mission_command_naval_stationing_directive(mission_command_naval_owner_slice(command));
}

[[nodiscard]] inline MissionCommandNaval::EmbarkedHeloDirective
mission_command_naval_embarked_helo_directive(
    const MissionCommandCompatibilityTransportShell& command
) noexcept {
    return mission_command_naval_embarked_helo_directive(
        mission_command_naval_owner_slice(command)
    );
}
