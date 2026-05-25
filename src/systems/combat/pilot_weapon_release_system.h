#pragma once

#include <cstdint>

#include <flecs.h>

#include "components/combat/weapon.h"
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
                if (PilotWeaponReleaseState* state = e.get_mut<PilotWeaponReleaseState>()) {
                    state->fire_weapon_was_down = bool(pilot.active && pilot.master_arm && pilot.fire_weapon);
                    state->release_consumed = false;
                }
                return;
            }
            PilotWeaponReleaseState* state = e.get_mut<PilotWeaponReleaseState>();
            if (state && state->release_consumed) {
                state->fire_weapon_was_down = true;
                return;
            }
            flecs::entity launched =
                weapon_release_service.fire_weapon_from_pilot_action(static_cast<std::uint64_t>(e.id()));
            PilotWeaponReleaseState next_state = state ? *state : PilotWeaponReleaseState{};
            next_state.fire_weapon_was_down = true;
            next_state.release_consumed = launched.id() != 0;
            e.set<PilotWeaponReleaseState>(next_state);
        });
}
