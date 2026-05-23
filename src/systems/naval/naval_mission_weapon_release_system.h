#pragma once

#include <cstdint>

#include <flecs.h>

#include "components/combat/weapon.h"
#include "components/command/mission_command.h"
#include "core/engine/simulation_kernel.h"

inline void register_naval_mission_weapon_release_system(
    flecs::world& ecs,
    SimulationKernel& kernel
) {
    ecs.system<const MissionCommand, const NavalWeaponSystem>("NavalMissionWeaponRelease")
        .kind(flecs::OnUpdate)
        .each([&kernel](flecs::entity e, const MissionCommand& mission, const NavalWeaponSystem&) {
            if (!mission.active) {
                return;
            }
            (void)kernel.fire_naval_weapon_from_mission_command(static_cast<std::uint64_t>(e.id()));
        });
}
