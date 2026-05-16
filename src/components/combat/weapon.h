#pragma once

#include <flecs.h>
#include <cstdint>
#include <limits>
#include <string>
#include <vector>

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

    // P0 seeker / guidance runtime state.
    bool p0_runtime_initialized = false;
    bool seeker_has_valid_track = false;
    bool seeker_has_range = true;
    int seeker_mode = 0;  // 0=Track, 1=Memory, 2=Terminal/ballistic

    double filtered_bearing_deg = 0.0;
    double filtered_elevation_deg = 0.0;
    double filtered_range_m = 0.0;
    double filtered_closing_speed_mps = 0.0;
    double bearing_rate_deg_s = 0.0;
    double elevation_rate_deg_s = 0.0;
    double last_track_time_s = -1.0;
    double track_memory_timeout_s = 0.75;

    double current_speed_mps = 0.0;
    double commanded_lateral_accel_mps2 = 0.0;
    double achieved_lateral_accel_mps2 = 0.0;
    double burnout_time_s = -1.0;
    double boost_duration_s = std::numeric_limits<double>::quiet_NaN();
    double sustain_duration_s = std::numeric_limits<double>::quiet_NaN();
    double guidance_bearing_filter_tau_s = std::numeric_limits<double>::quiet_NaN();
    double guidance_elevation_filter_tau_s = std::numeric_limits<double>::quiet_NaN();
    double guidance_range_filter_tau_s = std::numeric_limits<double>::quiet_NaN();
    double guidance_boost_thrust_n = std::numeric_limits<double>::quiet_NaN();
    double guidance_sustain_thrust_n = std::numeric_limits<double>::quiet_NaN();
    double guidance_cd0_subsonic = std::numeric_limits<double>::quiet_NaN();
    double guidance_cd0_supersonic = std::numeric_limits<double>::quiet_NaN();
    double guidance_induced_drag_k = std::numeric_limits<double>::quiet_NaN();
    double guidance_max_lateral_g = std::numeric_limits<double>::quiet_NaN();
    double guidance_autopilot_tau_s = std::numeric_limits<double>::quiet_NaN();
    double guidance_max_accel_response_g_per_s = std::numeric_limits<double>::quiet_NaN();
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

enum class NavalWeaponType : int {
    Unknown = 0,
    VlsSam = 1,
    DeckGun = 2,
    Ciws = 3,
};

struct NavalWeaponMountDefinition {
    std::string mount_id;
    NavalWeaponType weapon_type = NavalWeaponType::Unknown;
    int ready_count = 0;
    int max_ready_count = 0;
    int ammo_per_shot = 1;
    double cooldown_s = 0.0;
    double last_fire_time = -1.0;
    double engagement_range_m = 0.0;
    double projectile_speed_mps = 0.0;
    double hit_probability = 0.0;
    double damage_per_hit = 0.0;
    bool consumes_ready_count = true;
    bool can_intercept_missiles = false;
    std::string fire_control_channel;
    std::string target_domain;
    std::string provenance_note;
};

struct NavalWeaponSystem {
    std::vector<NavalWeaponMountDefinition> mounts;
};
