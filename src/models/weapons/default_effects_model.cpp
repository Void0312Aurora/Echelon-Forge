#include "core/interfaces/effects_model.h"

#include <algorithm>
#include <cstdint>
#include <cmath>
#include <spdlog/spdlog.h>

#include "components/combat/health.h"
#include "components/physics/performance.h"
#include "components/combat/scoring.h"
#include "components/systems/sensor.h"
#include "components/combat/weapon.h"
#include "components/combat/damage.h"
#include "components/combat/damage.h"
#include "components/physics/dynamics.h"
#include "components/basic/common.h"

namespace {

// Geometry Helpers
struct Vec3 { double x, y, z; };

// Rotate vector into Body Frame (inverse rotation)
// Simplified sequence: Undo Heading, then Pitch, then Roll
// Note: Coordinate system is ENU. Heading 0=North (Y). 
// This math can be tricky. For MVP reliability, let's treat Heading as rotation around Z.
// Pitch around X, Roll around Y?
// Actually, standard Euler inverse: R_total = R_z(heading) * R_x(pitch) * R_y(roll). Inverse is R_y(-r)*R_x(-p)*R_z(-h).
// But standard aerospace sequence is usually Yaw -> Pitch -> Roll.
// Let's implement a simplified 2D+Height transformation for stability first.
// The most important is Relative Bearing.
Vec3 world_to_body(const Transform& t, double wx, double wy, double wz) {
    // Relative position
    double dx = wx - t.x;
    double dy = wy - t.y;
    double dz = wz - t.z;
    
    // Rotate -Heading (around Z) to align X with North?
    // Wait, Heading definition: 0=North(Y+), 90=East(X+).
    // Math angle (from X+, CCW): math_deg = 90 - heading.
    double math_rad = (90.0 - t.heading) * M_PI / 180.0;
    
    // Rotate by -math_math effectively aligns body X with world X? 
    // No, we want to align World Vector into Body Axis.
    // If Body Heading is 45 (NE), and Point is at (1,1) (NE), Local X should be +dist, Y=0.
    
    // Projection to horizontal plane
    double dist_h = std::sqrt(dx*dx + dy*dy);
    double bearing_rad = std::atan2(dy, dx); // Math angle of vector
    double relative_angle = bearing_rad - math_rad;
    
    double lx = dist_h * std::cos(relative_angle); // Forward axis? No, in math X is East.
    // Let's stick to standard Body Axis: X=Forward, Y=Right, Z=Up.
    // Current Sim: Heading is Nav. 
    // Let's assum "Forward" is unit vector logic.
    
    // Re-verify coordinate system: ENU.
    // Body X (Forward) = (sin(h), cos(h), 0) roughly (ignoring pitch).
    // Body Y (Right) = (cos(h), -sin(h), 0).
    // Let's do a Dot Product projection.
    double head_rad = t.heading * M_PI / 180.0;
    double fwd_x = std::sin(head_rad);
    double fwd_y = std::cos(head_rad);
    double right_x = std::cos(head_rad);
    double right_y = -std::sin(head_rad);
    
    // Project delta vector onto axes
    double local_x = dx * fwd_x + dy * fwd_y; // Dot(delta, fwd)
    double local_y = dx * right_x + dy * right_y; // Dot(delta, right)
    double local_z = dz; // Assuming flat pitch/roll for MVP interception
    
    return {local_x, local_y, local_z};
}

uint64_t splitmix64(uint64_t& state) {
    uint64_t z = (state += 0x9e3779b97f4a7c15ULL);
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

double rand_uniform01(uint64_t& state) {
    // 53 random bits / 2^53
    return (splitmix64(state) >> 11) * (1.0 / 9007199254740992.0);
}

bool check_hitbox(const Vec3& local_p, const Hitbox& box) {
    // Check if point is inside box (centered at offset)
    double min_x = box.offset_x - box.dim_l * 0.5;
    double max_x = box.offset_x + box.dim_l * 0.5;
    double min_y = box.offset_y - box.dim_w * 0.5;
    double max_y = box.offset_y + box.dim_w * 0.5;
    double min_z = box.offset_z - box.dim_h * 0.5;
    double max_z = box.offset_z + box.dim_h * 0.5;
    
    return (local_p.x >= min_x && local_p.x <= max_x &&
            local_p.y >= min_y && local_p.y <= max_y &&
            local_p.z >= min_z && local_p.z <= max_z);
}

bool system_name_matches(const std::string& system, const char* token) {
    return system.find(token) != std::string::npos;
}

void clamp_platform_damage_state(PlatformDamageState* state) {
    if (!state) return;
    state->mission_capability = std::clamp(state->mission_capability, 0.0, 1.0);
    state->mobility_capability = std::clamp(state->mobility_capability, 0.0, 1.0);
    state->sensor_capability = std::clamp(state->sensor_capability, 0.0, 1.0);
    state->survivability_margin = std::clamp(state->survivability_margin, 0.0, 1.0);

    state->mission_kill = state->mission_capability <= 0.25;
    state->mobility_kill = state->mobility_capability <= 0.25;
    state->sensor_kill = state->sensor_capability <= 0.25;

    if (state->survivability_margin <= 0.0) {
        state->loss_state = PlatformLossState::Lost;
    } else if (state->mobility_kill) {
        state->loss_state = PlatformLossState::MobilityKill;
    } else if (state->sensor_kill) {
        state->loss_state = PlatformLossState::SensorKill;
    } else if (state->mission_kill) {
        state->loss_state = PlatformLossState::MissionKill;
    } else {
        state->loss_state = PlatformLossState::CombatCapable;
    }
}

class DefaultEffectsModel : public IEffectsModel {
public:
    EffectsResult on_proximity_hit(flecs::world world,
                                   flecs::entity missile_entity,
                                   const Missile& missile,
                                   flecs::entity target_entity) override {
        EffectsResult result;

        Score* score = nullptr;
        auto attacker = world.entity(missile.attacker_id);
        if (attacker.is_valid()) {
            score = attacker.get_mut<Score>();
        }
        
        // --- 1. Generic Health Handling (Legacy) ---
        Health* hp = target_entity.get_mut<Health>();
        if (hp) {
            hp->current_hp -= missile.damage;
            if (score) {
                score->total_reward += missile.damage;
                score->hits_landed++;
            }
            if (hp->current_hp <= 0) {
                target_entity.destruct();
                if (score) { 
                    score->total_reward += 1000.0; 
                    score->kills_confirmed++;
                }
                spdlog::info("SPLASH! Target {} Destroyed.", target_entity.id());
                return result; // Target dead, exit
            }
        }

        // --- 2. Geometric Damage Logic (New) ---
        const HitboxConfig* hitboxes = target_entity.get<HitboxConfig>();
        SystemHealth* sys_health = target_entity.get_mut<SystemHealth>();
        PlatformDamageState* platform_damage = target_entity.get_mut<PlatformDamageState>();
        const Transform* t_tgt = target_entity.get<Transform>();
        const Transform* t_msl = missile_entity.get<Transform>();

        if (hitboxes && sys_health && t_tgt && t_msl) {
            // Transform Missile Pos to Target Body Frame
            Vec3 local_imp = world_to_body(*t_tgt, t_msl->x, t_msl->y, t_msl->z);
            
            // Check Intersections
            bool structure_hit = false;
            for (const auto& box : hitboxes->hitboxes) {
                if (check_hitbox(local_imp, box)) {
                    structure_hit = true;
                    spdlog::info("HITBOX >>> Box {} HIT! Protected Systems:", box.id);
                    
                    for (const auto& system : box.protected_systems) {
                        const double severity = std::clamp(missile.damage / 180.0, 0.15, 0.65);
                        sys_health->systems[system] = std::max(0.0, sys_health->systems[system] - severity);
                        spdlog::info("   - {} Status: {:.2f}", system, sys_health->systems[system]);

                        if (platform_damage) {
                            platform_damage->survivability_margin -= 0.08 + 0.08 * severity;
                            if (system_name_matches(system, "radar")) {
                                platform_damage->sensor_capability -= 0.35 + 0.20 * severity;
                                platform_damage->fire_severity += 0.05 + 0.05 * severity;
                            }
                            if (system_name_matches(system, "engineering") ||
                                system_name_matches(system, "engine") ||
                                system_name_matches(system, "fuel")) {
                                platform_damage->mobility_capability -= 0.25 + 0.20 * severity;
                                platform_damage->fire_severity += 0.08 + 0.08 * severity;
                                platform_damage->flooding_severity += 0.04 + 0.05 * severity;
                                platform_damage->ongoing_hull_breach += 0.03 + 0.04 * severity;
                            }
                            if (system_name_matches(system, "combat") ||
                                system_name_matches(system, "command") ||
                                system_name_matches(system, "data_link") ||
                                system_name_matches(system, "vls") ||
                                system_name_matches(system, "gun") ||
                                system_name_matches(system, "radar")) {
                                platform_damage->mission_capability -= 0.20 + 0.20 * severity;
                                platform_damage->fire_severity += 0.04 + 0.04 * severity;
                            }
                            platform_damage->fire_severity = std::clamp(platform_damage->fire_severity, 0.0, 1.0);
                            platform_damage->flooding_severity = std::clamp(platform_damage->flooding_severity, 0.0, 1.0);
                            platform_damage->ongoing_hull_breach = std::clamp(platform_damage->ongoing_hull_breach, 0.0, 1.0);
                        }
                        
                        // Apply Functional Consequences
                        if (sys_health->systems[system] <= 0.5) {
                            if (system == "radar" || system_name_matches(system, "radar")) {
                                if (Sensor* s = target_entity.get_mut<Sensor>()) {
                                    s->max_range *= 0.4;
                                    spdlog::warn("   -> RADAR DEGRADED!");
                                }
                            }
                            else if (system == "engineering" || system == "engine" ||
                                     system == "engine_left" || system == "engine_right") {
                                if (Propulsion* p = target_entity.get_mut<Propulsion>()) {
                                    p->mil_thrust_n *= 0.75;
                                    p->ab_thrust_n *= 0.75;
                                    spdlog::warn("   -> ENGINE DAMAGE! Thrust reduced.");
                                }
                            }
                            else if (system == "fuel") {
                                if (Mass* m = target_entity.get_mut<Mass>()) {
                                    m->fuel_leak_rate_kg_s += 5.0; // 5kg/s massive heavy leak
                                    spdlog::warn("   -> FUEL TANK RUPTURED! Massive Leak Started.");
                                }
                            }
                        }
                    }
                }
            }

            if (platform_damage) {
                clamp_platform_damage_state(platform_damage);
                if (hp) {
                    hp->mission_kill = platform_damage->mission_kill;
                    hp->mobility_kill = platform_damage->mobility_kill;
                    hp->sensor_kill = platform_damage->sensor_kill;
                    if (platform_damage->loss_state == PlatformLossState::Lost) {
                        hp->current_hp = 0.0;
                    }
                }
                if (platform_damage->loss_state == PlatformLossState::Lost) {
                    target_entity.destruct();
                    return result;
                }
            }
            
            if (!structure_hit) {
                spdlog::info("PROXIMITY HIT BUT NO STRUCTURAL IMPACT (Near Miss or Gap)");
            }
        } 
        // --- 3. Fallback to Randomized Effects (Legacy) ---
        else {
             // ... preserve existing random code if no geometry ...
             // (Copying simplified random logic for fallback)
             double severity = 0.5;
             if (hp && hp->max_hp > 0) severity = missile.damage / hp->max_hp;
             
             // Randomly damage sensor
             double p = std::clamp(0.3 + 0.5 * severity, 0.0, 1.0);
             uint64_t rng_state = missile.rng_state;
             double u = rand_uniform01(rng_state);
             if (u < p) {
                 // if (Sensor* s = target_entity.get_mut<Sensor>()) apply_sensor_damage(*s, severity);
                 // Skip apply_sensor_damage for now as helpers are gone, simple blind
                 if (Sensor* s = target_entity.get_mut<Sensor>()) {
                    s->max_range *= 0.5;
                 }
             }
             if (Missile* m = missile_entity.get_mut<Missile>()) {
                 m->rng_state = rng_state;
             }
        }

        return result;
    }
};

} // namespace

std::unique_ptr<IEffectsModel> make_default_effects_model() {
    return std::make_unique<DefaultEffectsModel>();
}
