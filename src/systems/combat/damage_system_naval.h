#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>

#include <flecs.h>

#include "systems/combat/damage_system_common.h"

#include "components/combat/health.h"
#include "components/domains/naval/combat/damage_naval.h"
#include "components/domains/naval/combat/weapon_naval.h"
#include "components/domains/naval/platform/ship_platform.h"
#include "components/domains/naval/platform/submarine_platform.h"

// Naval damage-response tick (DM-N1).
//
// Ship and submarine response are separate ECS admission surfaces. The shared
// projection helper keeps Health/PlatformDamageState loss ownership identical,
// while the submarine profile is explicit and bounded rather than reusing a
// ShipPlatform query or silently copying a surface-ship class.
namespace naval_damage_detail {

struct NavalDamageResponseSelection {
    const NavalDamageResponseProfile *profile = nullptr;
    bool structured_platform = false;
};

inline NavalDamageResponseSelection select_ship_damage_response(flecs::entity e) {
    NavalDamageResponseSelection selection{};
    selection.structured_platform = e.get<ShipPlatform>() != nullptr;
    if (selection.structured_platform) {
        selection.profile =
            resolve_naval_damage_response_profile(kNavalDamageResponseProfileDefaultIndex);
    }
    return selection;
}

// This is a deliberately separate, synthetic engineering profile. It is
// bounded for runtime closure and is not calibrated evidence for any named
// submarine class.
inline const NavalDamageResponseProfile *submarine_damage_response_profile() noexcept {
    static const NavalDamageResponseProfile profile = [] {
        NavalDamageResponseProfile out{};
        out.ship_class_id = "naval_damage_response_submarine_v1";
        out.fire_decay_per_s = 0.0006;
        out.breach_decay_per_s = 0.00008;
        out.flooding_decay_per_s = 0.00015;
        out.breach_to_flooding_per_s = 0.004;
        out.mission_loss_per_s_at_fire = 0.0018;
        out.sensor_loss_per_s_at_fire = 0.0014;
        out.mobility_loss_per_s_at_flooding = 0.0030;
        out.survivability_loss_per_s_at_flooding = 0.0035;
        out.survivability_loss_per_s_at_fire = 0.0012;
        out.provenance =
            "synthetic_engineering: bounded_submarine_damage_response_v1; not_calibrated";
        out.synthetic = true;
        out.calibrated = false;
        out.evidence_backed = false;
        return out;
    }();
    return &profile;
}

inline NavalDamageResponseSelection select_submarine_damage_response(flecs::entity e) {
    NavalDamageResponseSelection selection{};
    // A dual-family entity is not admitted to two response owners in one tick.
    if (e.get<SubmarinePlatform>() != nullptr && e.get<ShipPlatform>() == nullptr) {
        selection.structured_platform = true;
        selection.profile = submarine_damage_response_profile();
    }
    return selection;
}

// Mean ready/max mount fraction, the mount-state input to the response. A
// platform with no mount record is neutral (1.0), including submarines whose
// functional torpedo/VLS mechanisms are not admitted here.
inline double resolve_naval_mount_ready_fraction(flecs::entity e) {
    const NavalWeaponSystem *weapon_system = e.get<NavalWeaponSystem>();
    if (weapon_system == nullptr) {
        return 1.0;
    }
    return naval_damage_mount_ready_fraction(weapon_system->mounts);
}

inline void apply_naval_damage_response(flecs::entity entity, Health &health,
                                        PlatformDamageState &damage,
                                        const NavalDamageResponseProfile &profile, double dt_s) {
    const double mount_ready_fraction = resolve_naval_mount_ready_fraction(entity);
    const double mount_response_scale =
        naval_damage_mount_response_scale(profile, mount_ready_fraction);
    const double loss_response_scale =
        naval_damage_mount_response_scale(profile, mount_ready_fraction);

    const double fire_progress = damage.fire_severity;
    const double flooding_progress = damage.flooding_severity;
    const double breach_progress = damage.ongoing_hull_breach;

    damage.fire_severity = std::clamp(
        damage.fire_severity - naval_damage_fire_decay_per_s(profile, mount_response_scale) * dt_s,
        0.0, 1.0);
    damage.flooding_severity =
        std::clamp(damage.flooding_severity +
                       (naval_damage_breach_flooding_gain_per_s(profile, breach_progress) -
                        naval_damage_flooding_decay_per_s(profile, mount_response_scale)) *
                           dt_s,
                   0.0, 1.0);
    damage.ongoing_hull_breach =
        std::clamp(damage.ongoing_hull_breach -
                       naval_damage_breach_decay_per_s(profile, mount_response_scale) * dt_s,
                   0.0, 1.0);

    damage.mission_capability -=
        naval_damage_capability_loss_per_s(profile.mission_loss_per_s_at_fire, fire_progress,
                                           loss_response_scale) *
        dt_s;
    damage.sensor_capability -=
        naval_damage_capability_loss_per_s(profile.sensor_loss_per_s_at_fire, fire_progress,
                                           loss_response_scale) *
        dt_s;
    damage.mobility_capability -=
        naval_damage_capability_loss_per_s(profile.mobility_loss_per_s_at_flooding,
                                           flooding_progress, loss_response_scale) *
        dt_s;
    damage.survivability_margin -=
        naval_damage_capability_loss_per_s(profile.survivability_loss_per_s_at_flooding,
                                           flooding_progress, loss_response_scale) *
        dt_s;
    damage.survivability_margin -=
        naval_damage_capability_loss_per_s(profile.survivability_loss_per_s_at_fire, fire_progress,
                                           loss_response_scale) *
        dt_s;

    sync_platform_damage_loss_state(health, damage);
    if (damage.loss_state == PlatformLossState::Lost) {
        health.current_hp = 0.0;
        entity.destruct();
    }
}

} // namespace naval_damage_detail

inline void register_naval_damage_system(flecs::world &ecs) {
    ecs.system<Health, PlatformDamageState, const ShipPlatform>("NavalDamageStateUpdate")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter &it) {
            const double raw_dt_s = it.delta_time();
            const double dt_s = std::isfinite(raw_dt_s) && raw_dt_s > 0.0 ? raw_dt_s : 1.0 / 60.0;
            while (it.next()) {
                auto health = it.field<Health>(0);
                auto damage = it.field<PlatformDamageState>(1);
                for (auto i : it) {
                    flecs::entity entity = it.entity(i);
                    const naval_damage_detail::NavalDamageResponseSelection selection =
                        naval_damage_detail::select_ship_damage_response(entity);
                    if (!selection.structured_platform || selection.profile == nullptr) {
                        continue;
                    }
                    naval_damage_detail::apply_naval_damage_response(entity, health[i], damage[i],
                                                                     *selection.profile, dt_s);
                }
            }
        });

    // Submarines are admitted through their own family query. This keeps the
    // surface-ship selector honest while installing the bounded response in
    // the same naval damage stage.
    ecs.system<Health, PlatformDamageState, const SubmarinePlatform>("SubmarineDamageStateUpdate")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter &it) {
            const double raw_dt_s = it.delta_time();
            const double dt_s = std::isfinite(raw_dt_s) && raw_dt_s > 0.0 ? raw_dt_s : 1.0 / 60.0;
            while (it.next()) {
                auto health = it.field<Health>(0);
                auto damage = it.field<PlatformDamageState>(1);
                for (auto i : it) {
                    flecs::entity entity = it.entity(i);
                    const naval_damage_detail::NavalDamageResponseSelection selection =
                        naval_damage_detail::select_submarine_damage_response(entity);
                    if (!selection.structured_platform || selection.profile == nullptr) {
                        continue;
                    }
                    naval_damage_detail::apply_naval_damage_response(entity, health[i], damage[i],
                                                                     *selection.profile, dt_s);
                }
            }
        });
}
