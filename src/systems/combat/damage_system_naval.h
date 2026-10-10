#pragma once

#include <cstddef>

#include <flecs.h>
#include <algorithm>

#include "systems/combat/damage_system_common.h"

#include "components/combat/health.h"
#include "components/domains/naval/combat/damage_naval.h"
#include "components/domains/naval/combat/weapon_naval.h"
#include "components/domains/naval/platform/ship_platform.h"
#include "components/physics/physics_input_policy.h"

// Naval damage-response tick (DM-N1).
//
// This system owns *no* coefficients. It resolves one declared
// NavalDamageResponseProfile per platform and drives fire / flooding / hull
// breach evolution plus the capability projection from that profile. All
// numerical response values live in
// `components/domains/naval/combat/damage_naval.h` with documented units and a
// provenance note.
//
// Maturity: mechanism only. Consumes the naval platform state it is given and
// produces no launch authority (N5) and no kill authority (N6).

namespace naval_damage_detail {

struct NavalDamageResponseSelection {
    const NavalDamageResponseProfile *profile = nullptr;
    const ShipPlatform *ship_platform = nullptr;
    bool structured_platform = false;
};

// Resolve the declared profile plus the platform attributes used by derived
// state. This branch admits ship platforms only; submarine damage response is
// not selected until it has a compatible speed/propulsion projection and an
// executable acceptance test.
inline NavalDamageResponseSelection select_naval_damage_response(flecs::entity e) {
    NavalDamageResponseSelection selection{};
    selection.ship_platform = e.get<ShipPlatform>();
    selection.structured_platform = selection.ship_platform != nullptr;
    if (!selection.structured_platform) {
        return selection;
    }

    // Profiles are address-stable for the process lifetime because the registry
    // is a function-local static.
    selection.profile =
        resolve_naval_damage_response_profile(kNavalDamageResponseProfileDefaultIndex);
    return selection;
}

// Mean ready/max mount fraction, the mount-state input to the response. A
// platform with no mount record is neutral (1.0), not degraded.
inline double resolve_naval_mount_ready_fraction(flecs::entity e) {
    const NavalWeaponSystem *weapon_system = e.get<NavalWeaponSystem>();
    if (weapon_system == nullptr) {
        return 1.0;
    }
    return naval_damage_mount_ready_fraction(weapon_system->mounts);
}

} // namespace naval_damage_detail

inline void register_naval_damage_system(flecs::world &ecs) {
    ecs.system<Health, PlatformDamageState, const ShipPlatform>("NavalDamageStateUpdate")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter &it) {
            // DM-N1 is currently a ship-only response surface. Resolving once
            // per iteration keeps the response independent of stage ordering
            // against the motion systems.
            const double dt_s = physics_runtime::resolve_entity_dt(it.delta_time());
            while (it.next()) {
                auto health = it.field<Health>(0);
                auto damage_field = it.field<PlatformDamageState>(1);
                for (auto i : it) {
                    flecs::entity e = it.entity(i);
                    Health &health_state = health[i];
                    PlatformDamageState &damage = damage_field[i];

                    const naval_damage_detail::NavalDamageResponseSelection selection =
                        naval_damage_detail::select_naval_damage_response(e);
                    if (!selection.structured_platform || selection.profile == nullptr) {
                        continue;
                    }
                    const NavalDamageResponseProfile &profile = *selection.profile;

                    const double mount_ready_fraction =
                        naval_damage_detail::resolve_naval_mount_ready_fraction(e);
                    const double mount_response_scale =
                        naval_damage_mount_response_scale(profile, mount_ready_fraction);
                    const double loss_response_scale =
                        naval_damage_mount_response_scale(profile, mount_ready_fraction);

                    const double fire_progress = damage.fire_severity;
                    const double flooding_progress = damage.flooding_severity;
                    const double breach_progress = damage.ongoing_hull_breach;

                    damage.fire_severity = std::clamp(
                        damage.fire_severity -
                            naval_damage_fire_decay_per_s(profile, mount_response_scale) * dt_s,
                        0.0, 1.0);
                    damage.flooding_severity = std::clamp(
                        damage.flooding_severity +
                            (naval_damage_breach_flooding_gain_per_s(profile, breach_progress) -
                             naval_damage_flooding_decay_per_s(profile, mount_response_scale)) *
                                dt_s,
                        0.0, 1.0);
                    damage.ongoing_hull_breach = std::clamp(
                        damage.ongoing_hull_breach -
                            naval_damage_breach_decay_per_s(profile, mount_response_scale) * dt_s,
                        0.0, 1.0);

                    damage.mission_capability -=
                        naval_damage_capability_loss_per_s(profile.mission_loss_per_s_at_fire,
                                                           fire_progress, loss_response_scale) *
                        dt_s;
                    damage.sensor_capability -=
                        naval_damage_capability_loss_per_s(profile.sensor_loss_per_s_at_fire,
                                                           fire_progress, loss_response_scale) *
                        dt_s;
                    damage.mobility_capability -=
                        naval_damage_capability_loss_per_s(profile.mobility_loss_per_s_at_flooding,
                                                           flooding_progress, loss_response_scale) *
                        dt_s;
                    damage.survivability_margin -= naval_damage_capability_loss_per_s(
                                                       profile.survivability_loss_per_s_at_flooding,
                                                       flooding_progress, loss_response_scale) *
                                                   dt_s;
                    damage.survivability_margin -=
                        naval_damage_capability_loss_per_s(profile.survivability_loss_per_s_at_fire,
                                                           fire_progress, loss_response_scale) *
                        dt_s;

                    // Loss semantics stay owned by the shared helper.
                    sync_platform_damage_loss_state(health_state, damage);

                    // Mobility reaches motion through mobility_capability, read by
                    // ShipMotion (systems/domains/naval/ship_motion_system.h).

                    if (damage.loss_state == PlatformLossState::Lost) {
                        health_state.current_hp = 0.0;
                        e.destruct();
                    }
                }
            }
        });
}
