#include "core/interfaces/effects_model.h"

#include <algorithm>
#include <cstdint>
#include <cmath>
#include <spdlog/spdlog.h>

#include "components/physics/action.h"
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

class DefaultEffectsModel : public IEffectsModel {
public:
    EffectsResult on_proximity_hit(flecs::world world,
                                   flecs::entity missile_entity,
                                   const Missile& missile,
                                   flecs::entity target_entity) override {
        EffectsResult result;

        bool destroyed = false;
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
                destroyed = true;
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
                    
                    // Simple damage Model: Impact destroys systems in the box
                    // Ideally we subtract HP based on Armor penetration
                     // Simple damage Model: Impact destroys systems in the box
                    // Ideally we subtract HP based on Armor penetration
                    for (const auto& system : box.protected_systems) {
                        sys_health->systems[system] -= 1.0; // Instant kill for now
                        if (sys_health->systems[system] < 0) sys_health->systems[system] = 0;
                        spdlog::info("   - {} Status: {:.2f}", system, sys_health->systems[system]);
                        
                        // Apply Functional Consequences
                        if (sys_health->systems[system] <= 0.0) {
                            if (system == "radar") {
                                if (Sensor* s = target_entity.get_mut<Sensor>()) {
                                    s->max_range = 0.0; // Blind
                                    spdlog::warn("   -> RADAR DESTROYED!");
                                }
                            }
                            else if (system == "engine" || system == "engine_left" || system == "engine_right") {
                                if (Propulsion* p = target_entity.get_mut<Propulsion>()) {
                                    p->mil_thrust_n *= 0.5; // Lose half thrust?
                                    p->ab_thrust_n *= 0.5;
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
