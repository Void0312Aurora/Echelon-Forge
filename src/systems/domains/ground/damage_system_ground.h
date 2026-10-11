#pragma once

#include <flecs.h>

#include <algorithm>
#include <cmath>

#include "systems/combat/damage_system_common.h"

#include "components/combat/health.h"
#include "components/domains/ground/combat/damage_ground.h"

// Ground-domain progressive damage response (DM-G1).
//
// Rates are expressed per simulated second. The prior values were per tick
// constants, which made equal elapsed-time scenarios diverge when their valid
// positive timestep changed. The fixed-step baseline remains 1/60 s: each
// per-second rate below is the former per-tick value multiplied by 60.
namespace ground_damage_detail {

inline constexpr double kFireDecayPerS = 0.048;
inline constexpr double kIgnitionDecayPerS = 0.030;
inline constexpr double kStructuralDecayPerS = 0.006;
inline constexpr double kStructuralIntegrityLossPerS = 0.024;
inline constexpr double kCasualtyGrowthPerS = 0.090;
inline constexpr double kMissionLossPerSAtFire = 0.090;
inline constexpr double kMissionLossPerSAtStructure = 0.060;
inline constexpr double kMissionLossPerSAtUncontainedFire = 0.048;
inline constexpr double kMobilityLossPerSAtUnavailable = 0.120;
inline constexpr double kMobilityLossPerSAtStructure = 0.036;
inline constexpr double kSurvivabilityLossPerSAtFire = 0.132;
inline constexpr double kSurvivabilityLossPerSAtStructure = 0.108;

// A paused or invalid stage must not invent damage progression. This is
// deliberately different from the compatibility fallbacks used by integrator
// and motion systems.
[[nodiscard]] inline double resolve_damage_dt(double value) noexcept {
    return std::isfinite(value) && value > 0.0 ? value : 0.0;
}

} // namespace ground_damage_detail

// Ground-domain damage response (DM-G1).
//
// This registers a real ECS system for ground platforms: it advances the
// ground-owned `GroundPlatformDamageState` and projects it into the shared
// `PlatformDamageState` capability fields through the same
// `sync_platform_damage_loss_state` helper that the common and naval paths use.
// There is deliberately no forked loss semantics: kill thresholds, loss-state
// ordering, and HP zeroing all come from that shared helper rather than from
// local constants.
//
// Explicit non-claims: this system is a damage-consequence owner only. It does
// not drive ground translation, route following, terrain interaction, sensing,
// or weapon release.
inline void register_ground_damage_system(flecs::world &ecs) {
    ecs.system<Health, PlatformDamageState, GroundPlatformDamageState>("GroundDamageStateUpdate")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter &it) {
            const double dt_s = ground_damage_detail::resolve_damage_dt(it.delta_time());
            while (it.next()) {
                auto health = it.field<Health>(0);
                auto damage = it.field<PlatformDamageState>(1);
                auto ground = it.field<GroundPlatformDamageState>(2);
                for (auto i : it) {
                    flecs::entity e = it.entity(i);
                    Health &health_state = health[i];
                    PlatformDamageState &damage_state = damage[i];
                    GroundPlatformDamageState &ground_state = ground[i];

                    // Ground elements do not pump or flood, so there is no
                    // flooding equivalent of the naval block. Fire and
                    // uncontained structural loss are the two progressive
                    // ground casualties.
                    const double fire_progress = ground_state.fire_severity;
                    const double structural_progress = ground_state.ongoing_structural_damage;
                    const double mobility_availability = ground_mobility_availability(ground_state);

                    // Damage-control progression, in units per simulated second.
                    ground_state.fire_severity = std::clamp(
                        ground_state.fire_severity - ground_damage_detail::kFireDecayPerS * dt_s,
                        0.0, 1.0);
                    ground_state.ignition_source_severity =
                        std::clamp(ground_state.ignition_source_severity -
                                       ground_damage_detail::kIgnitionDecayPerS * dt_s,
                                   0.0, 1.0);
                    ground_state.ongoing_structural_damage =
                        std::clamp(ground_state.ongoing_structural_damage -
                                       ground_damage_detail::kStructuralDecayPerS * dt_s,
                                   0.0, 1.0);
                    ground_state.structural_integrity =
                        std::clamp(ground_state.structural_integrity -
                                       ground_damage_detail::kStructuralIntegrityLossPerS *
                                           structural_progress * dt_s,
                                   0.0, 1.0);
                    ground_state.casualty_fraction = std::clamp(
                        ground_state.casualty_fraction +
                            ground_damage_detail::kCasualtyGrowthPerS * fire_progress * dt_s,
                        0.0, 1.0);

                    // Capability projection into the shared state.
                    const double containment =
                        std::clamp(ground_state.fire_suppression_integrity, 0.0, 1.0);
                    damage_state.mission_capability -=
                        (ground_damage_detail::kMissionLossPerSAtFire * fire_progress +
                         ground_damage_detail::kMissionLossPerSAtStructure * structural_progress +
                         ground_damage_detail::kMissionLossPerSAtUncontainedFire *
                             (1.0 - containment) * fire_progress) *
                        dt_s;
                    damage_state.mobility_capability -=
                        (ground_damage_detail::kMobilityLossPerSAtUnavailable *
                             (1.0 - mobility_availability) +
                         ground_damage_detail::kMobilityLossPerSAtStructure * structural_progress) *
                        dt_s;
                    damage_state.survivability_margin -=
                        (ground_damage_detail::kSurvivabilityLossPerSAtFire * fire_progress +
                         ground_damage_detail::kSurvivabilityLossPerSAtStructure *
                             structural_progress) *
                        dt_s;

                    // The ground system owns the fire load for ground elements,
                    // so this is an assignment rather than an accumulation.
                    damage_state.fire_severity = std::clamp(fire_progress, 0.0, 1.0);
                    damage_state.ongoing_hull_breach = std::clamp(structural_progress, 0.0, 1.0);

                    clamp_ground_platform_damage_state(ground_state);
                    sync_platform_damage_loss_state(health_state, damage_state);

                    ground_state.mobility_kill = damage_state.mobility_kill;
                    ground_state.mission_kill = damage_state.mission_kill;
                    ground_state.element_destroyed =
                        damage_state.loss_state == PlatformLossState::Lost ||
                        health_state.current_hp <= 0.0;

                    if (ground_state.element_destroyed) {
                        health_state.current_hp = 0.0;
                        e.destruct();
                    }
                }
            }
        });
}
