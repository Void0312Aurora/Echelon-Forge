#pragma once

#include <flecs.h>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <string>
#include <vector>

#include "components/physics/dynamics.h"
#include "components/systems/logistics.h"

struct WarheadProfile {
    std::string family = "blast_fragmentation";
    double mass_kg = std::numeric_limits<double>::quiet_NaN();
    double lethal_radius_m = std::numeric_limits<double>::quiet_NaN();
    double damage_scalar = std::numeric_limits<double>::quiet_NaN();
    bool synthetic = true;
    bool damage_scalar_synthetic = true;
    std::string provenance = "synthetic_legacy_damage";
};

struct FuzeProfile {
    std::string type = "proximity";
    double trigger_radius_m = std::numeric_limits<double>::quiet_NaN();
    double delay_s = 0.0;
    double reliability = 1.0;
    bool synthetic = true;
    std::string provenance = "synthetic_legacy_fuse_distance";
};

inline WarheadProfile make_synthetic_warhead_profile(
    double damage_scalar,
    double lethal_radius_m,
    const std::string& provenance = "synthetic_legacy_damage"
) {
    WarheadProfile profile{};
    profile.family = "blast_fragmentation";
    profile.mass_kg = std::numeric_limits<double>::quiet_NaN();
    profile.lethal_radius_m = lethal_radius_m;
    profile.damage_scalar = damage_scalar;
    profile.synthetic = true;
    profile.damage_scalar_synthetic = true;
    profile.provenance = provenance;
    return profile;
}

inline std::string warhead_effect_family(const WarheadProfile& profile) {
    return profile.family.empty() ? "blast_fragmentation" : profile.family;
}

inline FuzeProfile make_synthetic_fuze_profile(
    double trigger_radius_m,
    const std::string& provenance = "synthetic_legacy_fuse_distance"
) {
    FuzeProfile profile{};
    profile.type = "proximity";
    profile.trigger_radius_m = trigger_radius_m;
    profile.delay_s = 0.0;
    profile.reliability = 1.0;
    profile.synthetic = true;
    profile.provenance = provenance;
    return profile;
}

inline std::string fuze_profile_type(const FuzeProfile& profile) {
    return profile.type.empty() ? "proximity" : profile.type;
}

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
    bool shared_launch_initialized = false;

    // Proximity fuse bookkeeping: resolve hit once at closest approach.
    double proximity_min_dist_m = std::numeric_limits<double>::infinity();
    double proximity_last_dist_m = std::numeric_limits<double>::infinity();
    bool proximity_engaged = false;
    bool fuze_delay_armed = false;
    double fuze_nearest_approach_time_s = std::numeric_limits<double>::quiet_NaN();
    double fuze_detonation_time_s = std::numeric_limits<double>::quiet_NaN();
    double fuze_detonation_x = std::numeric_limits<double>::quiet_NaN();
    double fuze_detonation_y = std::numeric_limits<double>::quiet_NaN();
    double fuze_detonation_z = std::numeric_limits<double>::quiet_NaN();
    double fuze_quality = 0.0;
    double fuze_hit_probability = 0.0;
    double fuze_closure_mps = 0.0;
    double fuze_missile_axis_forward = 0.0;
    double fuze_missile_axis_right = 0.0;
    double fuze_missile_axis_up = 0.0;

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
    double seeker_activation_range_m = std::numeric_limits<double>::quiet_NaN();
    bool midcourse_datalink_supported = false;
    bool terminal_seeker_active = true;

    WarheadProfile warhead_profile{};
    FuzeProfile fuze_profile{};
};

struct MissileSharedLaunchRuntimeState {
    double current_time_s = 0.0;
    double launch_speed_mps = 0.0;
    bool seeker_has_valid_track = false;
    bool seeker_has_range = false;
    int seeker_mode = 0;
    double filtered_bearing_deg = 0.0;
    double filtered_elevation_deg = 0.0;
    double filtered_range_m = 0.0;
    double filtered_closing_speed_mps = 0.0;
    double last_track_time_s = -1.0;
    double track_memory_timeout_s = 0.0;
    double burnout_time_s = -1.0;
    double boost_duration_s = 0.0;
    double sustain_duration_s = 0.0;
    double bearing_filter_tau_s = 0.0;
    double elevation_filter_tau_s = 0.0;
    double range_filter_tau_s = 0.0;
    double boost_thrust_n = 0.0;
    double sustain_thrust_n = 0.0;
    double cd0_subsonic = 0.0;
    double cd0_supersonic = 0.0;
    double induced_drag_k = 0.0;
    double max_lateral_g = 0.0;
    double autopilot_tau_s = 0.0;
    double max_accel_response_g_per_s = 0.0;
    double seeker_activation_range_m = std::numeric_limits<double>::quiet_NaN();
    bool midcourse_datalink_supported = false;
    bool terminal_seeker_active = true;
};

inline double clamp_missile_propellant_mass_kg(double total_mass_kg, double propellant_mass_kg) {
    const double resolved_total_mass_kg = std::max(1.0, total_mass_kg);
    const double resolved_propellant_mass_kg =
        (std::isfinite(propellant_mass_kg) && propellant_mass_kg >= 0.0)
            ? propellant_mass_kg
            : 0.0;
    return std::clamp(
        resolved_propellant_mass_kg,
        0.0,
        std::max(0.0, resolved_total_mass_kg - 1.0));
}

inline double clamp_missile_reference_area_m2(double reference_area_m2, double fallback_m2) {
    const double resolved_reference_area_m2 =
        std::isfinite(reference_area_m2) ? reference_area_m2 : fallback_m2;
    return std::max(1.0e-4, resolved_reference_area_m2);
}

inline Mass make_missile_mass_state(double total_mass_kg, double propellant_mass_kg) {
    const double resolved_total_mass_kg = std::max(1.0, total_mass_kg);
    const double resolved_propellant_mass_kg =
        clamp_missile_propellant_mass_kg(resolved_total_mass_kg, propellant_mass_kg);

    Mass mass{};
    mass.empty_mass_kg = std::max(1.0, resolved_total_mass_kg - resolved_propellant_mass_kg);
    mass.fuel_mass_kg = resolved_propellant_mass_kg;
    mass.stores_mass_kg = 0.0;
    return mass;
}

inline MassProperties make_missile_mass_properties(const Mass& mass, double reference_area_m2) {
    return {
        mass.empty_mass_kg,
        mass.get_total_kg(),
        0.0,
        0.0,
        reference_area_m2,
    };
}

inline void sync_missile_mass_properties(
    const Mass& mass,
    MassProperties& properties,
    double reference_area_m2
) {
    properties.empty_mass_kg = mass.empty_mass_kg;
    properties.current_total_mass_kg = mass.get_total_kg();
    properties.base_drag_index = 0.0;
    properties.current_drag_index = 0.0;
    properties.reference_area_m2 = reference_area_m2;
}

inline void initialize_missile_launch_runtime(
    Missile& missile,
    const MissileSharedLaunchRuntimeState& state
) {
    missile.shared_launch_initialized = true;
    missile.p0_runtime_initialized = true;
    missile.seeker_has_valid_track = state.seeker_has_valid_track;
    missile.seeker_has_range = state.seeker_has_range;
    missile.seeker_mode = state.seeker_mode;
    missile.filtered_bearing_deg = state.filtered_bearing_deg;
    missile.filtered_elevation_deg = state.filtered_elevation_deg;
    missile.filtered_range_m = std::max(0.0, state.filtered_range_m);
    missile.filtered_closing_speed_mps = state.filtered_closing_speed_mps;
    missile.bearing_rate_deg_s = 0.0;
    missile.elevation_rate_deg_s = 0.0;
    missile.last_track_time_s = state.last_track_time_s;
    missile.track_memory_timeout_s = std::max(0.0, state.track_memory_timeout_s);
    missile.current_speed_mps = std::max(0.0, state.launch_speed_mps);
    missile.commanded_lateral_accel_mps2 = 0.0;
    missile.achieved_lateral_accel_mps2 = 0.0;
    missile.burnout_time_s = state.burnout_time_s;
    missile.boost_duration_s = std::max(0.0, state.boost_duration_s);
    missile.sustain_duration_s = std::max(0.0, state.sustain_duration_s);
    missile.guidance_bearing_filter_tau_s = state.bearing_filter_tau_s;
    missile.guidance_elevation_filter_tau_s = state.elevation_filter_tau_s;
    missile.guidance_range_filter_tau_s = state.range_filter_tau_s;
    missile.guidance_boost_thrust_n = state.boost_thrust_n;
    missile.guidance_sustain_thrust_n = state.sustain_thrust_n;
    missile.guidance_cd0_subsonic = state.cd0_subsonic;
    missile.guidance_cd0_supersonic = state.cd0_supersonic;
    missile.guidance_induced_drag_k = state.induced_drag_k;
    missile.guidance_max_lateral_g = state.max_lateral_g;
    missile.guidance_autopilot_tau_s = state.autopilot_tau_s;
    missile.guidance_max_accel_response_g_per_s = state.max_accel_response_g_per_s;
    missile.seeker_activation_range_m = state.seeker_activation_range_m;
    missile.midcourse_datalink_supported = state.midcourse_datalink_supported;
    missile.terminal_seeker_active = state.terminal_seeker_active;
}

struct Ammo {
    int missiles_remaining;
    int max_missiles;
};

struct WeaponCooldown {
    double cooldown_s;
    double last_fire_time;
};

struct PilotWeaponReleaseState {
    bool fire_weapon_was_down = false;
    bool release_consumed = false;
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
