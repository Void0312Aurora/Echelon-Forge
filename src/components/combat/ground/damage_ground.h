#pragma once

#include "components/combat/common/damage_common.h"

// DS-C1-A establishes a Ground-owned include surface only. It intentionally
// does not declare a Ground runtime damage component or claim ground damage
// behavior maturity.
inline constexpr bool kGroundDomainDamageOwnerShell = true;
