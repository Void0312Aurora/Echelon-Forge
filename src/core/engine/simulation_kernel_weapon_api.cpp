#include "simulation_kernel.h"

#include "components/combat/scoring.h"
#include "components/combat/weapon.h"
#include "components/systems/sensor.h"

#include <spdlog/spdlog.h>

#include <cmath>
#include <cstdint>
#include <limits>

namespace {
uint64_t splitmix64(uint64_t seed) {
    uint64_t z = seed + 0x9e3779b97f4a7c15ULL;
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}
} // namespace

flecs::entity SimulationKernel::fire_missile(uint64_t attacker_id, uint64_t target_id) {
    auto attacker = ecs.entity(attacker_id);
    if (!attacker.is_valid()) {
        spdlog::warn("Invalid attacker ID: {}", attacker_id);
        return flecs::entity::null();
    }
    
    const Transform* p = attacker.get<Transform>();
    const Velocity* v = attacker.get<Velocity>();
    const Alliance* side = attacker.get<Alliance>();
    Ammo* ammo = attacker.get_mut<Ammo>();
    WeaponCooldown* cooldown = attacker.get_mut<WeaponCooldown>();
    Score* score = attacker.get_mut<Score>();
    
    if (!p || !v || !side) return flecs::entity::null();

    const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
    double current_time = info ? (double)info->world_time_total : 0.0;

    if (cooldown && cooldown->cooldown_s > 0.0 && cooldown->last_fire_time >= 0.0) {
        if (current_time - cooldown->last_fire_time < cooldown->cooldown_s) {
            return flecs::entity::null();
        }
    }

    // Require an active track on the target to fire (prevents blind spam).
    const ContactList* contacts = attacker.get<ContactList>();
    if (!contacts) {
        return flecs::entity::null();
    }
    bool has_track = false;
    Detection det{};
    for (const auto& c : contacts->contacts) {
        if (c.target_id != target_id) continue;
        det = c;
        has_track = true;
        break;
    }
    if (!has_track) {
        return flecs::entity::null();
    }

    if (ammo) {
        if (ammo->missiles_remaining <= 0) {
            spdlog::warn("Attacker {} has no missiles remaining.", attacker_id);
            return flecs::entity::null();
        }
        ammo->missiles_remaining -= 1;
    }
    if (score) {
        score->missiles_fired += 1;
    }
    if (cooldown) {
        cooldown->last_fire_time = current_time;
    }
    
    double missile_max_speed = 1000.0;
    double missile_turn_rate = 35.0;
    double missile_fuse_distance = 300.0;
    double missile_damage = 120.0;
    double missile_seeker_fov = 180.0;
    double missile_seeker_range = 30000.0;
    double missile_guidance_delay = 0.0;
    double missile_guidance_period = 0.0;
    double missile_max_flight_time = 15.0;
    double missile_nav_gain = 3.0;

    if (std::isfinite(missile_tuning_.max_speed)) missile_max_speed = missile_tuning_.max_speed;
    if (std::isfinite(missile_tuning_.turn_rate)) missile_turn_rate = missile_tuning_.turn_rate;
    if (std::isfinite(missile_tuning_.fuse_distance)) missile_fuse_distance = missile_tuning_.fuse_distance;
    if (std::isfinite(missile_tuning_.damage)) missile_damage = missile_tuning_.damage;
    if (std::isfinite(missile_tuning_.seeker_fov_deg)) missile_seeker_fov = missile_tuning_.seeker_fov_deg;
    if (std::isfinite(missile_tuning_.seeker_lock_range)) missile_seeker_range = missile_tuning_.seeker_lock_range;
    if (std::isfinite(missile_tuning_.guidance_delay_s)) missile_guidance_delay = missile_tuning_.guidance_delay_s;
    if (std::isfinite(missile_tuning_.guidance_update_period_s)) missile_guidance_period = missile_tuning_.guidance_update_period_s;
    if (std::isfinite(missile_tuning_.max_flight_time_s)) missile_max_flight_time = missile_tuning_.max_flight_time_s;
    if (std::isfinite(missile_tuning_.nav_gain)) missile_nav_gain = missile_tuning_.nav_gain;

    double sensor_max_range = missile_seeker_range;
    double sensor_fov_deg = missile_seeker_fov;
    double sensor_scan_period = 0.05;
    double sensor_detection_prob = 0.98;
    double sensor_bearing_noise = 0.2;
    double sensor_range_noise = 10.0;
    double sensor_track_memory = 2.0;

    if (std::isfinite(missile_tuning_.sensor_max_range)) sensor_max_range = missile_tuning_.sensor_max_range;
    if (std::isfinite(missile_tuning_.sensor_fov_deg)) sensor_fov_deg = missile_tuning_.sensor_fov_deg;
    if (std::isfinite(missile_tuning_.sensor_scan_period)) sensor_scan_period = missile_tuning_.sensor_scan_period;
    if (std::isfinite(missile_tuning_.sensor_detection_prob)) sensor_detection_prob = missile_tuning_.sensor_detection_prob;
    if (std::isfinite(missile_tuning_.sensor_bearing_noise_std)) sensor_bearing_noise = missile_tuning_.sensor_bearing_noise_std;
    if (std::isfinite(missile_tuning_.sensor_range_noise_std)) sensor_range_noise = missile_tuning_.sensor_range_noise_std;
    if (std::isfinite(missile_tuning_.sensor_track_memory_s)) sensor_track_memory = missile_tuning_.sensor_track_memory_s;

    // Spawn Missile slightly in front
    double heading = std::atan2(v->vy, v->vx);
    double launch_x = p->x + 20.0 * std::cos(heading);
    double launch_y = p->y + 20.0 * std::sin(heading);

    uint64_t missile_seed = splitmix64(static_cast<uint64_t>(current_time * 1000.0) ^
                                       (attacker_id * 0x9e3779b97f4a7c15ULL) ^
                                       (target_id * 0xbf58476d1ce4e5b9ULL));
    
    auto m = ecs.entity()
        .set<Transform>({launch_x, launch_y, p->z, p->heading, 0, 0})
        .set<Velocity>({v->vx, v->vy, v->vz}) // Inherit platform velocity
        .set<Alliance>({side->side})
        .set<KeyEntity>({UnitType::Missile})
        .set<Missile>({
            attacker_id,
            target_id,
            missile_max_speed,
            missile_turn_rate,
            missile_fuse_distance,
            missile_damage,
            missile_seeker_fov,
            missile_seeker_range,
            missile_guidance_delay,
            missile_guidance_period,
            -1.0,
            current_time,
            missile_max_flight_time,
            missile_nav_gain,
            true,
            missile_seed,
            std::numeric_limits<double>::infinity(),
            std::numeric_limits<double>::infinity(),
            false
        }) // 1000m/s, 35deg/s, 300m fuse, 120 DMG
        .set<Sensor>({sensor_max_range, sensor_fov_deg, sensor_scan_period, -1.0,
                      sensor_detection_prob, 2.0, sensor_bearing_noise,
                      sensor_range_noise, sensor_track_memory, 0.2,
                      20.0, // doppler_notch_width (m/s)
                      static_cast<int>(sensor_max_range > 8000.0 ? SensorType::Radar : SensorType::Infrared)}) // Seeker sensor
        .set<ContactList>({})
        .add<SimObject>(); // Tag for cleanup
        
    spdlog::info("FOX 2! Missile {} fired by {} at {}", m.id(), attacker_id, target_id);
    return m;
}
