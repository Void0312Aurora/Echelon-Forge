#pragma once

#include <cstdint>

#include <flecs.h>

#include "components/command/pilot_action.h"
#include "core/interfaces/weapon_release_service.h"

inline void register_pilot_weapon_release_system(
    flecs::world& ecs,
    IWeaponReleaseService& weapon_release_service
) {
    ecs.system<const PilotAction>("PilotWeaponRelease")
        .kind(flecs::OnUpdate)
        .each([&weapon_release_service](flecs::entity e, const PilotAction& pilot) {
            if (!pilot.active || !pilot.master_arm || !pilot.fire_weapon) {
                return;
            }
            weapon_release_service.fire_weapon_from_pilot_action(static_cast<std::uint64_t>(e.id()));
        });
}
