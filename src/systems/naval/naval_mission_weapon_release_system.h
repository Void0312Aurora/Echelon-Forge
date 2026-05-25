#pragma once

#include <cstdint>

#include <flecs.h>

#include "components/combat/weapon.h"
#include "components/command/mission_command.h"
#include "core/interfaces/weapon_release_service.h"

inline void register_naval_mission_weapon_release_system(
    flecs::world& ecs,
    IWeaponReleaseService& weapon_release_service
) {
    ecs.system<const MissionCommand, const NavalWeaponSystem>("NavalMissionWeaponRelease")
        .kind(flecs::OnUpdate)
        .each([&weapon_release_service](flecs::entity e, const MissionCommand& mission, const NavalWeaponSystem&) {
            if (!mission.active) {
                return;
            }
            (void)weapon_release_service.fire_naval_weapon_from_mission_command(static_cast<std::uint64_t>(e.id()));
        });
}
