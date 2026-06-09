#pragma once

#include "components/combat/common/damage_common.h"

// Naval flooding and hull-breach state are still physically stored on the
// DS-C1-A PlatformDamageState compatibility baseline. This owner header names
// the naval surface without changing runtime component identity.
using NavalDamageCompatibilityState = PlatformDamageState;
using NavalPlatformDamageState = PlatformDamageState;

inline constexpr bool kNavalDamageFloodingCompatibilityOwnedSurface = true;

[[nodiscard]] inline double naval_damage_flooding_severity(
    const NavalDamageCompatibilityState& state
) noexcept {
    return state.flooding_severity;
}

[[nodiscard]] inline double naval_damage_ongoing_hull_breach(
    const NavalDamageCompatibilityState& state
) noexcept {
    return state.ongoing_hull_breach;
}
