#include "components/health.h"
#include "components/scoring.h" // Added score
#include <spdlog/spdlog.h>

inline void register_damage_system(flecs::world& ecs) {
    ecs.system<const Transform, Missile>("ProximityFuze")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto p = it.field<const Transform>(0);
                auto m = it.field<Missile>(1);
                
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
                    double dist_sq = dx*dx + dy*dy + dz*dz;
                    
                    double fuse_sq = m[i].fuse_distance * m[i].fuse_distance;
                    
                    if (dist_sq < fuse_sq) {
                        // HIT Logic
                        Health* hp = target_entity.get_mut<Health>();
                        bool destroyed = false;
                        
                        // Scoring Logic: Find Attacker
                        Score* score = nullptr;
                        auto attacker = it.world().entity(m[i].attacker_id);
                        if (attacker.is_valid()) {
                            score = attacker.get_mut<Score>();
                        }

                        if (hp) {
                            hp->current_hp -= m[i].damage;
                            
                            if (score) {
                                score->total_reward += m[i].damage; // Data Damage = Score
                                score->hits_landed++;
                            }

                            spdlog::info("HIT! Missile {} hit Target {} for {:.1f} dmg. Rem HP: {:.1f}", 
                                it.entity(i).id(), m[i].target_id, m[i].damage, hp->current_hp);
                            
                            if (hp->current_hp <= 0) {
                                target_entity.destruct();
                                destroyed = true;
                                spdlog::info("SPLASH! Target {} Destroyed.", m[i].target_id);
                            }
                        } else {
                            target_entity.destruct();
                            destroyed = true;
                            spdlog::info("SPLASH! Target {} Destroyed (No HP).", m[i].target_id);
                        }
                        
                        if (destroyed && score) {
                            score->total_reward += 1000.0; // Kill Bonus
                            score->kills_confirmed++;
                        }

                        it.entity(i).destruct();
                    }
                }
            }
        });
}
