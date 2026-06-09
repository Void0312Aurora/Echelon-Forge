#pragma once

// Compatibility umbrella for the legacy public combat weapon include.
// Canonical ownership now lives in the common, air, naval, and ground headers.

#include <flecs.h>

#include "components/combat/common/weapon_common.h"
#include "components/combat/air/weapon_air.h"
#include "components/combat/naval/weapon_naval.h"
#include "components/combat/ground/weapon_ground.h"
