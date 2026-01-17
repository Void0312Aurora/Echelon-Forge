#pragma once

#include <flecs.h>
#include <cmath>
#include <limits>
#include <spdlog/spdlog.h>

#include "components/basic/common.h"
#include "components/physics/action.h"
#include "components/combat/weapon.h"
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

                    double min_dist = m[i].proximity_min_dist_m;
                    if (min_dist > m[i].fuse_distance) {
                        it.entity(i).destruct();
                        continue;
                    }

                    double fuse = std::max(1e-6, m[i].fuse_distance);
                    double quality = std::clamp(1.0 - min_dist / fuse, 0.0, 1.0);

                    double evasion = 0.0;
                    if (const ActionCommand* ac = target_entity.get<ActionCommand>()) {
                        evasion = std::clamp(std::abs(ac->turn_rate_cmd), 0.0, 1.0);
                    }

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
}
