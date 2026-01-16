#pragma once

#include <flecs.h>

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
    double nav_gain;              // PN gain (dimensionless)
    bool active;           // If false, missile is dead/inert
};

struct Ammo {
    int missiles_remaining;
    int max_missiles;
};
