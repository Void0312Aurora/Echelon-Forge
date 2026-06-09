#pragma once

#include "systems/combat/damage_system_common.h"
#include "systems/combat/damage_system_air.h"
#include "systems/combat/damage_system_naval.h"
#include "systems/combat/damage_system_ground.h"

// Compatibility umbrella retained for existing public include users of
// systems/combat/damage_system.h. Maintained system ownership now lives under
// systems/combat/damage_system_{common,air,naval,ground}.h.
inline void register_damage_system(flecs::world& ecs) {
    register_damage_system_common(ecs);
    register_aircraft_damage_system(ecs);
    register_naval_damage_system(ecs);
    register_ground_damage_system(ecs);
}
