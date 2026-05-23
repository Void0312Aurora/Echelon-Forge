#pragma once

#include <cstdint>

#include <flecs.h>

#include "components/command/pilot_action.h"
#include "core/engine/simulation_kernel.h"

inline void register_pilot_weapon_release_system(
    flecs::world& ecs,
    SimulationKernel& kernel
) {
    ecs.system<const PilotAction>("PilotWeaponRelease")
        .kind(flecs::OnUpdate)
        .each([&kernel](flecs::entity e, const PilotAction& pilot) {
            if (!pilot.active || !pilot.master_arm || !pilot.fire_weapon) {
                return;
            }
            kernel.fire_weapon_from_pilot_action(static_cast<std::uint64_t>(e.id()));
        });
}
