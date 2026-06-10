#pragma once

#include <flecs.h>

#include "components/domains/ground/combat/damage_ground.h"

// DS-S1-A only establishes a Ground-owned system include/register surface.
// It intentionally does not claim maintained ground damage runtime behavior.
inline void register_ground_damage_system(flecs::world& ecs) {
    (void)ecs;
}
