#pragma once

#include <flecs.h>

#include <algorithm>

#include "systems/combat/damage_system_common.h"

#include "components/combat/health.h"
#include "components/domains/ground/combat/damage_ground.h"

// Ground-domain per-tick damage response (DM-G1).
//
// This registers a real ECS system for ground platforms: it advances the
// ground-owned `GroundPlatformDamageState` and projects it into the shared
// `PlatformDamageState` capability fields through the same
// `sync_platform_damage_loss_state` helper that the common and naval paths use.
// There is deliberately no forked loss semantics: kill thresholds, loss-state
// ordering, and HP zeroing all come from that shared helper rather than from
// local constants.
//
// Progressive effect is expressed the same way the naval system expresses it:
// ground-owned severities decay per tick, and those severities keep subtracting
// capability until the element is a mission kill, a mobility kill, or lost.
//
// Explicit non-claims: this system is a damage-consequence owner only. It does
// not drive ground translation, route following, terrain interaction, sensing,
// or weapon release.
inline void register_ground_damage_system(flecs::world &ecs) {
    ecs.system<Health, PlatformDamageState, GroundPlatformDamageState>("GroundDamageStateUpdate")
        .kind(flecs::OnUpdate)
        .each([](flecs::entity e, Health &health, PlatformDamageState &damage,
                 GroundPlatformDamageState &ground) {
            constexpr double kFireDecayPerTick = 0.0008;
            constexpr double kIgnitionDecayPerTick = 0.0005;
            constexpr double kStructuralDecayPerTick = 0.0001;

            // Ground elements do not pump or flood, so there is no flooding
            // equivalent of the naval block. Fire and uncontained structural
            // loss are the two progressive ground casualties.
            const double fire_progress = ground.fire_severity;
            const double structural_progress = ground.ongoing_structural_damage;
            const double mobility_availability = ground_mobility_availability(ground);

            // Damage-control progression.
            ground.fire_severity = std::clamp(ground.fire_severity - kFireDecayPerTick, 0.0, 1.0);
            ground.ignition_source_severity =
                std::clamp(ground.ignition_source_severity - kIgnitionDecayPerTick, 0.0, 1.0);
            ground.ongoing_structural_damage =
                std::clamp(ground.ongoing_structural_damage - kStructuralDecayPerTick, 0.0, 1.0);
            ground.structural_integrity =
                std::clamp(ground.structural_integrity - 0.0004 * structural_progress, 0.0, 1.0);
            ground.casualty_fraction =
                std::clamp(ground.casualty_fraction + 0.0015 * fire_progress, 0.0, 1.0);

            // Capability projection into the shared state.
            const double containment = std::clamp(ground.fire_suppression_integrity, 0.0, 1.0);
            damage.mission_capability -= 0.0015 * fire_progress + 0.0010 * structural_progress +
                                         0.0008 * (1.0 - containment) * fire_progress;
            damage.mobility_capability -=
                0.0020 * (1.0 - mobility_availability) + 0.0006 * structural_progress;
            damage.survivability_margin -= 0.0022 * fire_progress + 0.0018 * structural_progress;

            // Fire projection. The ground system owns the fire load for ground
            // elements, so this is an assignment, not an accumulation: it keeps
            // repeated ticks idempotent instead of compounding the same load.
            damage.fire_severity = std::clamp(fire_progress, 0.0, 1.0);
            damage.ongoing_hull_breach = std::clamp(structural_progress, 0.0, 1.0);

            clamp_ground_platform_damage_state(ground);
            sync_platform_damage_loss_state(health, damage);

            ground.mobility_kill = damage.mobility_kill;
            ground.mission_kill = damage.mission_kill;
            ground.element_destroyed =
                damage.loss_state == PlatformLossState::Lost || health.current_hp <= 0.0;

            if (ground.element_destroyed) {
                health.current_hp = 0.0;
                e.destruct();
            }
        });
}
