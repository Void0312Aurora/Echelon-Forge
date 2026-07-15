#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <string>
#include <vector>

#include "components/physics/dynamics.h"
#include "components/systems/logistics.h"
#include "models/weapons/kalman_seeker.h"
#include "models/weapons/world_cv_alpha_beta_tracker.h"

struct WarheadProfile {
    std::string family = "blast_fragmentation";
    double mass_kg = std::numeric_limits<double>::quiet_NaN();
    double lethal_radius_m = std::numeric_limits<double>::quiet_NaN();
    double damage_scalar = std::numeric_limits<double>::quiet_NaN();
    double explosive_mass_kg = std::numeric_limits<double>::quiet_NaN();
    double case_mass_kg = std::numeric_limits<double>::quiet_NaN();
    double gurney_constant_mps = std::numeric_limits<double>::quiet_NaN();
    double fragment_mass_kg = std::numeric_limits<double>::quiet_NaN();
    double fragment_count = std::numeric_limits<double>::quiet_NaN();
    double projection_radius_fraction = std::numeric_limits<double>::quiet_NaN();
    double projection_min_radius_m = std::numeric_limits<double>::quiet_NaN();
    double projection_max_radius_m = std::numeric_limits<double>::quiet_NaN();
    double projection_min_effect_scale = std::numeric_limits<double>::quiet_NaN();
    double projection_max_effect_scale = std::numeric_limits<double>::quiet_NaN();
    double projection_falloff_exponent = std::numeric_limits<double>::quiet_NaN();
    std::uint32_t projection_max_projected_hitboxes = 0;
    bool synthetic = true;
    bool damage_scalar_synthetic = true;
    std::string provenance = "synthetic_legacy_damage";
};

struct FuzeProfile {
    std::string type = "proximity";
    double trigger_radius_m = std::numeric_limits<double>::quiet_NaN();
    double delay_s = 0.0;
    double reliability = 1.0;
    std::string trigger_logic = "online_sensor";
    std::string coverage_profile = "omni";
    bool synthetic = true;
    std::string provenance = "synthetic_legacy_fuse_distance";
};

inline WarheadProfile
make_synthetic_warhead_profile(double damage_scalar, double lethal_radius_m,
                               const std::string &provenance = "synthetic_legacy_damage") {
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

inline std::string warhead_effect_family(const WarheadProfile &profile) {
    return profile.family.empty() ? "blast_fragmentation" : profile.family;
}

inline FuzeProfile
make_synthetic_fuze_profile(double trigger_radius_m,
                            const std::string &provenance = "synthetic_legacy_fuse_distance") {
    FuzeProfile profile{};
    profile.type = "proximity";
    profile.trigger_radius_m = trigger_radius_m;
    profile.delay_s = 0.0;
    profile.reliability = 1.0;
    profile.synthetic = true;
    profile.provenance = provenance;
    return profile;
}

inline std::string fuze_profile_type(const FuzeProfile &profile) {
    return profile.type.empty() ? "proximity" : profile.type;
}

struct MissileGuidanceAccelerationVectorDiagnostics {
    double x_mps2 = 0.0;
    double y_mps2 = 0.0;
    double z_mps2 = 0.0;
    double magnitude_mps2 = 0.0;
};

struct MissileGuidanceAccelerationDiagnostics {
    MissileGuidanceAccelerationVectorDiagnostics capture{};
    MissileGuidanceAccelerationVectorDiagnostics pn{};
    MissileGuidanceAccelerationVectorDiagnostics apn{};
    MissileGuidanceAccelerationVectorDiagnostics preclamp{};
    MissileGuidanceAccelerationVectorDiagnostics postclamp{};
};

inline MissileGuidanceAccelerationVectorDiagnostics
make_missile_guidance_acceleration_diagnostics(const Math::Vector3 &value) {
    return {
        value.x,
        value.y,
        value.z,
        std::sqrt(value.x * value.x + value.y * value.y + value.z * value.z),
    };
}

// Shared missile component used by common guidance/effects surfaces. Its
// seeker/guidance runtime remains air-shaped and should not be read as a
// complete cross-domain weapon model.
struct Missile {
    uint64_t attacker_id;            // Entity ID of the shooter
    uint64_t target_id;              // Entity ID of the target
    double max_speed;                // Maximum speed (m/s)
    double turn_rate;                // Maximum turn rate (deg/s)
    double fuse_distance;            // Lethal radius (m)
    double damage;                   // Damage applied on impact
    double seeker_fov_deg;           // Seeker FOV (deg, total)
    double seeker_lock_range;        // Lock range (m)
    double guidance_delay_s;         // Delay before guidance starts (s)
    double guidance_update_period_s; // Guidance update period (s)
    double last_guidance_time;       // Last guidance update time (s)
    double launch_time;              // Launch time (s)
    double max_flight_time_s;        // Hard self-destruct time (s)
    double nav_gain;                 // PN gain (dimensionless)
    bool active;                     // If false, missile is dead/inert

    // Selectable production PN law. Legacy remains the default until a weapon profile opts in.
    int pn_los_rate_source = 0; // 0=legacy body-frame rates, 1=world-frame LOS history
    int target_kinematics_estimator = 0; // 0=legacy polar difference, 1=world CV tracker
    int capture_guidance_mode = 1; // 0=disabled, 1=legacy pursuit schedule
    double target_tracker_alpha = std::numeric_limits<double>::quiet_NaN();
    double target_tracker_beta = std::numeric_limits<double>::quiet_NaN();

    // Deterministic RNG state for probabilistic hit/kill logic (seeded at launch).
    uint64_t rng_state = 0;
    bool shared_launch_initialized = false;

    // Proximity fuse bookkeeping: resolve hit once at closest approach.
    double proximity_min_dist_m = std::numeric_limits<double>::infinity();
    double proximity_min_time_s = std::numeric_limits<double>::quiet_NaN();
    double proximity_last_dist_m = std::numeric_limits<double>::infinity();
    double proximity_min_local_forward_m = std::numeric_limits<double>::quiet_NaN();
    double proximity_min_local_right_m = std::numeric_limits<double>::quiet_NaN();
    double proximity_min_local_up_m = std::numeric_limits<double>::quiet_NaN();
    double proximity_last_sample_time_s = std::numeric_limits<double>::quiet_NaN();
    double proximity_last_missile_x_m = std::numeric_limits<double>::quiet_NaN();
    double proximity_last_missile_y_m = std::numeric_limits<double>::quiet_NaN();
    double proximity_last_missile_z_m = std::numeric_limits<double>::quiet_NaN();
    double proximity_last_target_x_m = std::numeric_limits<double>::quiet_NaN();
    double proximity_last_target_y_m = std::numeric_limits<double>::quiet_NaN();
    double proximity_last_target_z_m = std::numeric_limits<double>::quiet_NaN();
    bool proximity_engaged = false;
    bool fuze_delay_armed = false;
    double fuze_nearest_approach_time_s = std::numeric_limits<double>::quiet_NaN();
    double fuze_detonation_time_s = std::numeric_limits<double>::quiet_NaN();
    double fuze_detonation_x = std::numeric_limits<double>::quiet_NaN();
    double fuze_detonation_y = std::numeric_limits<double>::quiet_NaN();
    double fuze_detonation_z = std::numeric_limits<double>::quiet_NaN();
    double fuze_detonation_heading_deg = std::numeric_limits<double>::quiet_NaN();
    double fuze_detonation_pitch_deg = std::numeric_limits<double>::quiet_NaN();
    double fuze_detonation_roll_deg = std::numeric_limits<double>::quiet_NaN();
    double fuze_quality = 0.0;
    double fuze_hit_probability = 0.0;
    double fuze_closure_mps = 0.0;
    double fuze_missile_axis_forward = 0.0;
    double fuze_missile_axis_right = 0.0;
    double fuze_missile_axis_up = 0.0;
    std::string fuze_signature_source = "none";
    double fuze_target_signature = 0.0;
    double fuze_signature_scale = 1.0;
    double fuze_effective_reliability = 1.0;
    double fuze_contact_surface_distance_m = 0.0;
    double fuze_contact_penetration_depth_m = 0.0;
    double fuze_contact_surface_tolerance_m = 0.0;
    bool fuze_contact_inside_hitbox = false;
    std::string fuze_sensor_opportunity_source = "none";
    double fuze_sensor_opportunity_score = 0.0;
    bool fuze_terminal_track_valid = false;
    bool fuze_target_detected = false;
    std::string fuze_target_detection_source = "none";
    double fuze_target_detection_confidence = 0.0;
    double fuze_target_detection_threshold = 0.0;
    std::string fuze_detonation_point_source = "unknown";
    double fuze_mechanism_coverage_score = 0.0;

    // P0 seeker / guidance runtime state.
    bool runtime_initialized = false;
    bool seeker_has_valid_track = false;
    bool seeker_has_range = true;
    int seeker_mode = 0; // 0=Track, 1=Memory, 2=Terminal/ballistic

    double filtered_bearing_deg = 0.0;
    double filtered_elevation_deg = 0.0;
    double filtered_range_m = 0.0;
    double filtered_closing_speed_mps = 0.0;
    double bearing_rate_deg_s = 0.0;
    double elevation_rate_deg_s = 0.0;
    bool guidance_previous_world_los_valid = false;
    double guidance_previous_world_los_x = 0.0;
    double guidance_previous_world_los_y = 0.0;
    double guidance_previous_world_los_z = 0.0;
    double guidance_previous_world_los_time_s = -1.0;
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
    std::vector<double> guidance_cd0_mach_breakpoints;
    std::vector<double> guidance_cd0_mach_values;
    std::vector<double> guidance_induced_drag_k_mach_breakpoints;
    std::vector<double> guidance_induced_drag_k_mach_values;
    double guidance_max_lateral_g = std::numeric_limits<double>::quiet_NaN();
    double guidance_autopilot_tau_s = std::numeric_limits<double>::quiet_NaN();
    double guidance_max_accel_response_g_per_s = std::numeric_limits<double>::quiet_NaN();
    double apn_target_accel_gain = std::numeric_limits<double>::quiet_NaN();
    double prev_bearing_rate_deg_s = 0.0;
    double prev_elevation_rate_deg_s = 0.0;
    bool apn_rate_history_valid = false;
    double filtered_bearing_accel_rad_s2 = 0.0;
    double filtered_elevation_accel_rad_s2 = 0.0;
    bool target_kinematics_valid = false;
    double target_kinematics_time_s = -1.0;
    double target_track_x_m = std::numeric_limits<double>::quiet_NaN();
    double target_track_y_m = std::numeric_limits<double>::quiet_NaN();
    double target_track_z_m = std::numeric_limits<double>::quiet_NaN();
    double target_track_vx_mps = 0.0;
    double target_track_vy_mps = 0.0;
    double target_track_vz_mps = 0.0;
    double target_track_ax_mps2 = 0.0;
    double target_track_ay_mps2 = 0.0;
    double target_track_az_mps2 = 0.0;
    missile_guidance::WorldCvAlphaBetaTrackerState world_cv_target_tracker{};
    bool target_measurement_fresh = false;
    bool target_measurement_rejected_nonmonotonic = false;
    std::uint32_t target_duplicate_measurement_count = 0;
    double target_measurement_age_s = std::numeric_limits<double>::infinity();
    double target_estimator_update_dt_s = 0.0;
    double target_measurement_x_m = std::numeric_limits<double>::quiet_NaN();
    double target_measurement_y_m = std::numeric_limits<double>::quiet_NaN();
    double target_measurement_z_m = std::numeric_limits<double>::quiet_NaN();
    double target_prediction_x_m = std::numeric_limits<double>::quiet_NaN();
    double target_prediction_y_m = std::numeric_limits<double>::quiet_NaN();
    double target_prediction_z_m = std::numeric_limits<double>::quiet_NaN();
    double target_residual_x_m = 0.0;
    double target_residual_y_m = 0.0;
    double target_residual_z_m = 0.0;
    double target_residual_norm_m = 0.0;
    double guidance_lead_time_s = 0.0;
    double guidance_lead_blend = 0.0;
    double guidance_apn_lateral_accel_mps2 = 0.0;
    MissileGuidanceAccelerationDiagnostics guidance_acceleration_diagnostics{};
    double autopilot_filter_state_mps2 = 0.0;
    double autopilot_rate_state_mps3 = 0.0;
    double autopilot_actuator_state_mps2 = 0.0;
    int autopilot_order = 1;
    double autopilot_damping = 1.0;
    bool use_kalman_seeker = false;
    missile_seeker::SeekerEkfState ekf_state{};
    missile_seeker::SeekerEkfParams ekf_params{};
    double guidance_mach_transonic_start = std::numeric_limits<double>::quiet_NaN();
    double guidance_mach_transonic_end = std::numeric_limits<double>::quiet_NaN();
    double guidance_cd0_power_on_ratio = std::numeric_limits<double>::quiet_NaN();
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
    std::vector<double> cd0_mach_breakpoints;
    std::vector<double> cd0_mach_values;
    std::vector<double> induced_drag_k_mach_breakpoints;
    std::vector<double> induced_drag_k_mach_values;
};

inline double clamp_missile_propellant_mass_kg(double total_mass_kg, double propellant_mass_kg) {
    const double resolved_total_mass_kg = std::max(1.0, total_mass_kg);
    const double resolved_propellant_mass_kg =
        (std::isfinite(propellant_mass_kg) && propellant_mass_kg >= 0.0) ? propellant_mass_kg : 0.0;
    return std::clamp(resolved_propellant_mass_kg, 0.0,
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

inline MassProperties make_missile_mass_properties(const Mass &mass, double reference_area_m2) {
    return {
        mass.empty_mass_kg, mass.get_total_kg(), 0.0, 0.0, reference_area_m2,
    };
}

inline void sync_missile_mass_properties(const Mass &mass, MassProperties &properties,
                                         double reference_area_m2) {
    properties.empty_mass_kg = mass.empty_mass_kg;
    properties.current_total_mass_kg = mass.get_total_kg();
    properties.base_drag_index = 0.0;
    properties.current_drag_index = 0.0;
    properties.reference_area_m2 = reference_area_m2;
}

inline void initialize_missile_launch_runtime(Missile &missile,
                                              const MissileSharedLaunchRuntimeState &state) {
    missile.shared_launch_initialized = true;
    missile.runtime_initialized = true;
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
    missile.autopilot_filter_state_mps2 = 0.0;
    missile.autopilot_rate_state_mps3 = 0.0;
    missile.autopilot_actuator_state_mps2 = 0.0;
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
    missile.guidance_cd0_mach_breakpoints = state.cd0_mach_breakpoints;
    missile.guidance_cd0_mach_values = state.cd0_mach_values;
    missile.guidance_induced_drag_k_mach_breakpoints = state.induced_drag_k_mach_breakpoints;
    missile.guidance_induced_drag_k_mach_values = state.induced_drag_k_mach_values;
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

struct Munition {
    int station_id;
    bool is_fired;
};
