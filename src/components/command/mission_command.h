#pragma once

#include "components/command/air/mission_command_air.h"
#include "components/command/common/mission_command_core.h"
#include "components/command/ground/mission_command_ground.h"
#include "components/command/naval/mission_command_naval.h"

/**
 * MissionCommand
 * Implements [aim.md]: The high-level intent from Commander.
 */
struct MissionCommand : MissionCommandCore, MissionCommandAir, MissionCommandNaval, MissionCommandGround {};

// Flat umbrella retained only as a compatibility/transport shell.
// Shared-core and domain slices remain the maintained owner surfaces.
using MissionCommandCompatibilityTransportShell = MissionCommand;
using MissionCommandSharedCoreOwnerSlice = MissionCommandCore;
inline constexpr bool kMissionCommandCompatibilityTransportShell = true;
inline constexpr bool kMissionCommandSharedCoreOwnedSurface = true;

static_assert(
    kMissionCommandAirOwnedDomainSlice && kMissionCommandNavalOwnedDomainSlice &&
        kMissionCommandGroundOwnedDomainSlice,
    "MissionCommand compatibility shells must project to explicit owner slices."
);
static_assert(
    kMissionCommandSharedCoreOwnedSurface,
    "MissionCommand shared core must stay an explicit maintained owner surface."
);

struct MissionCommandSharedCoreDirective {
    double cmd_heading_deg = 0.0;
    double cmd_altitude_m = 0.0;
    double cmd_speed_mps = 0.0;
    int command_code = 0;
    std::uint64_t route_ref_id = 0;
    int roe_state = 0;
    std::uint64_t engagement_authority_holder_id = 0;
    std::uint64_t engagement_authority_grantor_id = 0;
    std::uint64_t assigned_target_id = 0;
    int threat_state = 0;
    std::uint64_t assigned_target_track_id = 0;
    std::uint64_t assigned_target_source_id = 0;
    double assigned_target_snapshot_time_s = 0.0;
    bool authorization_to_fire = false;
    bool active = false;

    bool operator==(const MissionCommandSharedCoreDirective&) const = default;
};

[[nodiscard]] inline const MissionCommandSharedCoreOwnerSlice&
mission_command_shared_core(
    const MissionCommandCompatibilityTransportShell& command
) noexcept {
    return command;
}

[[nodiscard]] inline MissionCommandSharedCoreOwnerSlice&
mission_command_shared_core(MissionCommandCompatibilityTransportShell& command) noexcept {
    return command;
}

[[nodiscard]] inline MissionCommandSharedCoreDirective
mission_command_shared_core_directive(
    const MissionCommandSharedCoreOwnerSlice& core
) noexcept {
    return {
        .cmd_heading_deg = core.cmd_heading_deg,
        .cmd_altitude_m = core.cmd_altitude_m,
        .cmd_speed_mps = core.cmd_speed_mps,
        .command_code = core.command_code,
        .route_ref_id = core.route_ref_id,
        .roe_state = core.roe_state,
        .engagement_authority_holder_id = core.engagement_authority_holder_id,
        .engagement_authority_grantor_id = core.engagement_authority_grantor_id,
        .assigned_target_id = core.assigned_target_id,
        .threat_state = core.threat_state,
        .assigned_target_track_id = core.assigned_target_track_id,
        .assigned_target_source_id = core.assigned_target_source_id,
        .assigned_target_snapshot_time_s = core.assigned_target_snapshot_time_s,
        .authorization_to_fire = core.authorization_to_fire,
        .active = core.active,
    };
}

[[nodiscard]] inline MissionCommandSharedCoreDirective
mission_command_shared_core_directive(
    const MissionCommandCompatibilityTransportShell& command
) noexcept {
    return mission_command_shared_core_directive(mission_command_shared_core(command));
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

[[nodiscard]] inline const MissionCommandGround&
mission_command_ground_owner_slice(
    const MissionCommandCompatibilityTransportShell& command
) noexcept {
    return command;
}

[[nodiscard]] inline MissionCommandGround&
mission_command_ground_owner_slice(
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

[[nodiscard]] inline MissionCommandGround::StaticTaskDirective
mission_command_ground_static_task_directive(
    const MissionCommandCompatibilityTransportShell& command
) noexcept {
    return mission_command_ground_static_task_directive(
        mission_command_ground_owner_slice(command)
    );
}
