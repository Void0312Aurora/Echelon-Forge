#pragma once

#include <flecs.h>
#include <cstdint>
#include <limits>

struct Missile {
    uint64_t attacker_id;  // Entity ID of the shooter
    uint64_t target_id;    // Entity ID of the target
    double max_speed;      // Maximum speed (m/s)
    double turn_rate;      // Maximum turn rate (deg/s)
    double fuse_distance;  // Lethal radius (m)
    double damage;         // Damage applied on impact
    double seeker_fov_deg;        // Seeker FOV (deg, total)
    double seeker_lock_range;     // Lock range (m)
    double guidance_delay_s;      // Delay before guidance starts (s)
    double guidance_update_period_s; // Guidance update period (s)
    double last_guidance_time;    // Last guidance update time (s)
    double launch_time;           // Launch time (s)
    double max_flight_time_s;     // Hard self-destruct time (s)
    double nav_gain;              // PN gain (dimensionless)
    bool active;           // If false, missile is dead/inert

    // Deterministic RNG state for probabilistic hit/kill logic (seeded at launch).
    uint64_t rng_state = 0;

    // Proximity fuse bookkeeping: resolve hit once at closest approach.
    double proximity_min_dist_m = std::numeric_limits<double>::infinity();
    double proximity_last_dist_m = std::numeric_limits<double>::infinity();
    bool proximity_engaged = false;
};

struct Ammo {
    int missiles_remaining;
    int max_missiles;
};

struct WeaponCooldown {
    double cooldown_s;
    double last_fire_time;
};

struct Munition {
    int station_id;
    bool is_fired;
};
