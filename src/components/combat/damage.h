#pragma once

#include "components/combat/common/damage_common.h"
#include "components/combat/air/damage_air.h"
#include "components/combat/naval/damage_naval.h"
#include "components/combat/ground/damage_ground.h"

// Compatibility umbrella retained for existing public include users of
// components/combat/damage.h. Maintained owner surfaces now live under
// components/combat/{common,air,naval,ground}/.
inline constexpr bool kCombatDamageCompatibilityUmbrellaHeader = true;
