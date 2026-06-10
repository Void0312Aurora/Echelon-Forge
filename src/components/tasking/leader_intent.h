#pragma once

#include "components/domains/air/tasking/leader_intent_air.h"
#include "components/tasking/common/leader_intent_core.h"
#include "components/domains/ground/tasking/leader_intent_ground.h"
#include "components/domains/naval/tasking/leader_intent_naval.h"

/**
 * LeaderIntent
 * Internal Leader-layer output before mapping into MissionCommand.
 */
struct LeaderIntent : LeaderIntentCore, LeaderIntentAir, LeaderIntentNaval, LeaderIntentGround {};

// Flat umbrella retained only as a compatibility/transport shell.
// Shared-core and domain slices remain the maintained owner surfaces.
using LeaderIntentCompatibilityTransportShell = LeaderIntent;
inline constexpr bool kLeaderIntentCompatibilityTransportShell = true;

static_assert(kLeaderIntentAirOwnedDomainSlice && kLeaderIntentNavalOwnedDomainSlice &&
                  kLeaderIntentGroundOwnedDomainSlice,
              "LeaderIntent compatibility shells must project to explicit owner slices.");

[[nodiscard]] inline const LeaderIntentCore &
leader_intent_shared_core(const LeaderIntentCompatibilityTransportShell &intent) noexcept {
    return intent;
}

[[nodiscard]] inline LeaderIntentCore &
leader_intent_shared_core(LeaderIntentCompatibilityTransportShell &intent) noexcept {
    return intent;
}

[[nodiscard]] inline const LeaderIntentAir &
leader_intent_air_owner_slice(const LeaderIntentCompatibilityTransportShell &intent) noexcept {
    return intent;
}

[[nodiscard]] inline LeaderIntentAir &
leader_intent_air_owner_slice(LeaderIntentCompatibilityTransportShell &intent) noexcept {
    return intent;
}

[[nodiscard]] inline const LeaderIntentNaval &
leader_intent_naval_owner_slice(const LeaderIntentCompatibilityTransportShell &intent) noexcept {
    return intent;
}

[[nodiscard]] inline LeaderIntentNaval &
leader_intent_naval_owner_slice(LeaderIntentCompatibilityTransportShell &intent) noexcept {
    return intent;
}

[[nodiscard]] inline const LeaderIntentGround &
leader_intent_ground_owner_slice(const LeaderIntentCompatibilityTransportShell &intent) noexcept {
    return intent;
}

[[nodiscard]] inline LeaderIntentGround &
leader_intent_ground_owner_slice(LeaderIntentCompatibilityTransportShell &intent) noexcept {
    return intent;
}

[[nodiscard]] inline LeaderIntentAir::RecoveryDirective leader_intent_air_recovery_directive(
    const LeaderIntentCompatibilityTransportShell &intent) noexcept {
    return leader_intent_air_recovery_directive(leader_intent_air_owner_slice(intent));
}

[[nodiscard]] inline LeaderIntentAir::TakeoffDirective leader_intent_air_takeoff_directive(
    const LeaderIntentCompatibilityTransportShell &intent) noexcept {
    return leader_intent_air_takeoff_directive(leader_intent_air_owner_slice(intent));
}

[[nodiscard]] inline LeaderIntentAir::FormationDirective leader_intent_air_formation_directive(
    const LeaderIntentCompatibilityTransportShell &intent) noexcept {
    return leader_intent_air_formation_directive(leader_intent_air_owner_slice(intent));
}

[[nodiscard]] inline LeaderIntentNaval::CommandAuthorityDirective
leader_intent_naval_command_authority(
    const LeaderIntentCompatibilityTransportShell &intent) noexcept {
    return leader_intent_naval_command_authority(leader_intent_naval_owner_slice(intent));
}

[[nodiscard]] inline LeaderIntentGround::StaticStatusDirective
leader_intent_ground_static_status_directive(
    const LeaderIntentCompatibilityTransportShell &intent) noexcept {
    return leader_intent_ground_static_status_directive(leader_intent_ground_owner_slice(intent));
}
