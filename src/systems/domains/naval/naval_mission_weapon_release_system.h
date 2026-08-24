#pragma once

#include <cstdint>

#include <flecs.h>

#include "components/domains/naval/combat/weapon_naval.h"
#include "components/command/mission_command.h"
#include "core/interfaces/weapon_release_service.h"

inline void register_naval_mission_weapon_release_system(flecs::world &ecs) {
    ecs.system<const MissionCommand, const NavalWeaponSystem>("NavalMissionWeaponRelease")
        .kind(flecs::OnUpdate)
        .each([](flecs::entity e, const MissionCommand &mission, const NavalWeaponSystem &) {
            if (!mission.active) {
                return;
            }
            const WeaponReleaseServiceRef *service_ref = e.world().get<WeaponReleaseServiceRef>();
            if (service_ref == nullptr || service_ref->service == nullptr) {
                return;
            }
            (void)service_ref->service->fire_naval_weapon_from_mission_command(
                static_cast<std::uint64_t>(e.id()));
        });
}
