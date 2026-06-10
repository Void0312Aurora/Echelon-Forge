#pragma once

#include "components/combat/common/damage_common.h"

using NavalPlatformDamageState = PlatformDamageState;

[[nodiscard]] inline double naval_damage_flooding_severity(
    const NavalPlatformDamageState& state
) noexcept {
    return state.flooding_severity;
}

[[nodiscard]] inline double naval_damage_ongoing_hull_breach(
    const NavalPlatformDamageState& state
) noexcept {
    return state.ongoing_hull_breach;
}
