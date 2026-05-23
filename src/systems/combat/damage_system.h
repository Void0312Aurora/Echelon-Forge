#pragma once

#include <flecs.h>
#include <cmath>
#include <limits>
#include <spdlog/spdlog.h>

#include "components/basic/common.h"
#include "components/command/legacy_command_bridge.h"
#include "components/combat/damage.h"
#include "components/combat/health.h"
#include "components/combat/weapon.h"
#include "components/naval/ship_platform.h"
#include "components/physics/performance.h"
#include "core/interfaces/effects_model.h"
#include <spdlog/spdlog.h>

namespace {
inline uint64_t damage_splitmix64(uint64_t seed) {
    uint64_t z = seed + 0x9e3779b97f4a7c15ULL;
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

inline double damage_rand_uniform01(uint64_t& state) {
    state = damage_splitmix64(state);
    return (state >> 11) * (1.0 / 9007199254740992.0);
}

inline bool proximity_fuze_has_terminal_guidance_support(const Missile& missile) {
    if (missile.seeker_has_valid_track) {
        return true;
    }
    if (!missile.terminal_seeker_active) {
        return false;
    }
    return missile.seeker_mode == 1;
}
} // namespace

inline void register_damage_system(flecs::world& ecs) {
    ecs.system<const Transform, Missile>("ProximityFuze")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto p = it.field<const Transform>(0);
                auto m = it.field<Missile>(1);
                const EffectsModelRef* effects_ref = it.world().get<EffectsModelRef>();
                
                for (auto i : it) {
                    if (!m[i].active) continue;
                    
                    auto target_entity = it.world().entity(m[i].target_id);
                    if (!target_entity.is_valid()) {
                        it.entity(i).destruct();
                        continue;
                    }
                    
                    const Transform* t_pos = target_entity.get<Transform>();
                    if(!t_pos) continue;
                    
                    double dx = p[i].x - t_pos->x;
                    double dy = p[i].y - t_pos->y;
                    double dz = p[i].z - t_pos->z;
                    double dist_sq = dx * dx + dy * dy + dz * dz;
                    double dist = std::sqrt(std::max(0.0, dist_sq));

                    if (!std::isfinite(m[i].proximity_last_dist_m)) {
                        m[i].proximity_last_dist_m = dist;
                        m[i].proximity_min_dist_m = dist;
                        continue;
                    }

                    if (dist < m[i].proximity_min_dist_m) {
                        m[i].proximity_min_dist_m = dist;
                    }

                    const double epsilon = 1e-3;
                    if (dist < m[i].proximity_last_dist_m - epsilon) {
                        m[i].proximity_engaged = true;
                        m[i].proximity_last_dist_m = dist;
                        continue;
                    }

                    if (!m[i].proximity_engaged) {
                        m[i].proximity_last_dist_m = dist;
                        continue;
                    }

                    if (!proximity_fuze_has_terminal_guidance_support(m[i])) {
                        it.entity(i).destruct();
                        continue;
                    }

                    double min_dist = m[i].proximity_min_dist_m;
                    if (min_dist > m[i].fuse_distance) {
                        it.entity(i).destruct();
                        continue;
                    }

                    double fuse = std::max(1e-6, m[i].fuse_distance);
                    double quality = std::clamp(1.0 - min_dist / fuse, 0.0, 1.0);

                    const double evasion = resolved_compatibility_damage_evasion(target_entity);

                    double base_hit = 0.35 + 0.65 * quality;
                    double hit_prob = std::clamp(base_hit * (1.0 - 0.3 * evasion), 0.05, 0.98);
                    if (damage_rand_uniform01(m[i].rng_state) > hit_prob) {
                        it.entity(i).destruct();
                        continue;
                    }

                    if (!effects_ref || !effects_ref->model) {
                        spdlog::warn("Effects model not configured; skipping hit resolution.");
                        it.entity(i).destruct();
                        continue;
                    }

                    Missile effective = m[i];
                    // Scale damage by proximity quality to allow partial hits.
                    effective.damage = effective.damage * (0.6 + 0.4 * quality);
                    effects_ref->model->on_proximity_hit(
                        it.world(), it.entity(i), effective, target_entity);
                    it.entity(i).destruct();
                }
            }
        });

    ecs.system<Health, PlatformDamageState, const ShipPlatform>("NavalDamageStateUpdate")
        .kind(flecs::OnUpdate)
        .each([](flecs::entity e, Health& health, PlatformDamageState& damage, const ShipPlatform& ship) {
            const double fire_decay = 0.0008;
            const double flooding_decay = 0.0002;
            const double breach_decay = 0.0001;

            const double fire_progress = damage.fire_severity;
            const double flooding_progress = damage.flooding_severity;
            const double breach_progress = damage.ongoing_hull_breach;

            damage.fire_severity = std::clamp(damage.fire_severity - fire_decay, 0.0, 1.0);
            damage.flooding_severity = std::clamp(
                damage.flooding_severity + 0.003 * breach_progress - flooding_decay,
                0.0,
                1.0
            );
            damage.ongoing_hull_breach = std::clamp(damage.ongoing_hull_breach - breach_decay, 0.0, 1.0);

            damage.mission_capability -= 0.0015 * fire_progress;
            damage.sensor_capability -= 0.0012 * fire_progress;
            damage.mobility_capability -= 0.0018 * flooding_progress;
            damage.survivability_margin -= 0.0022 * flooding_progress + 0.0010 * fire_progress;

            damage.mission_capability = std::clamp(damage.mission_capability, 0.0, 1.0);
            damage.mobility_capability = std::clamp(damage.mobility_capability, 0.0, 1.0);
            damage.sensor_capability = std::clamp(damage.sensor_capability, 0.0, 1.0);
            damage.survivability_margin = std::clamp(damage.survivability_margin, 0.0, 1.0);

            damage.mission_kill = damage.mission_capability <= 0.25;
            damage.mobility_kill = damage.mobility_capability <= 0.25;
            damage.sensor_kill = damage.sensor_capability <= 0.25;

            if (damage.survivability_margin <= 0.0 || health.current_hp <= 0.0) {
                damage.loss_state = PlatformLossState::Lost;
            } else if (damage.mobility_kill) {
                damage.loss_state = PlatformLossState::MobilityKill;
            } else if (damage.sensor_kill) {
                damage.loss_state = PlatformLossState::SensorKill;
            } else if (damage.mission_kill) {
                damage.loss_state = PlatformLossState::MissionKill;
            } else {
                damage.loss_state = PlatformLossState::CombatCapable;
            }

            health.mission_kill = damage.mission_kill;
            health.mobility_kill = damage.mobility_kill;
            health.sensor_kill = damage.sensor_kill;

            if (Propulsion* propulsion = e.get_mut<Propulsion>()) {
                const double mobility_scale = std::clamp(damage.mobility_capability, 0.2, 1.0);
                propulsion->mil_thrust_n = std::min(propulsion->mil_thrust_n, ship.max_speed_mps * 100000.0 * mobility_scale);
                propulsion->ab_thrust_n = std::min(propulsion->ab_thrust_n, ship.max_speed_mps * 120000.0 * mobility_scale);
            }

            if (damage.loss_state == PlatformLossState::Lost) {
                health.current_hp = 0.0;
                e.destruct();
            }
        });
}
