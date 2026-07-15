#pragma once

#include <cmath>
#include <limits>
#include <vector>

#include "components/combat/common/weapon_common.h"

struct MissileTuning {
    double max_speed = std::numeric_limits<double>::quiet_NaN();
    double turn_rate = std::numeric_limits<double>::quiet_NaN();
    double fuse_distance = std::numeric_limits<double>::quiet_NaN();
    double damage = std::numeric_limits<double>::quiet_NaN();
    double seeker_fov_deg = std::numeric_limits<double>::quiet_NaN();
    double seeker_lock_range = std::numeric_limits<double>::quiet_NaN();
    double guidance_delay_s = std::numeric_limits<double>::quiet_NaN();
    double guidance_update_period_s = std::numeric_limits<double>::quiet_NaN();
    double max_flight_time_s = std::numeric_limits<double>::quiet_NaN();
    double nav_gain = std::numeric_limits<double>::quiet_NaN();
    int pn_los_rate_source = -1;
    double sensor_max_range = std::numeric_limits<double>::quiet_NaN();
    double sensor_fov_deg = std::numeric_limits<double>::quiet_NaN();
    double sensor_scan_period = std::numeric_limits<double>::quiet_NaN();
    double sensor_detection_prob = std::numeric_limits<double>::quiet_NaN();
    double sensor_bearing_noise_std = std::numeric_limits<double>::quiet_NaN();
    double sensor_range_noise_std = std::numeric_limits<double>::quiet_NaN();
    double sensor_track_memory_s = std::numeric_limits<double>::quiet_NaN();
    int seeker_type = -1;
    double seeker_activation_range_m = std::numeric_limits<double>::quiet_NaN();
    double seeker_gimbal_limit_deg = std::numeric_limits<double>::quiet_NaN();
    double seeker_ifov_deg = std::numeric_limits<double>::quiet_NaN();
    double bearing_filter_tau_s = std::numeric_limits<double>::quiet_NaN();
    double elevation_filter_tau_s = std::numeric_limits<double>::quiet_NaN();
    double range_filter_tau_s = std::numeric_limits<double>::quiet_NaN();
    double track_break_time_s = std::numeric_limits<double>::quiet_NaN();
    double boost_time_s = std::numeric_limits<double>::quiet_NaN();
    double sustain_time_s = std::numeric_limits<double>::quiet_NaN();
    double boost_thrust_n = std::numeric_limits<double>::quiet_NaN();
    double sustain_thrust_n = std::numeric_limits<double>::quiet_NaN();
    double reference_area_m2 = std::numeric_limits<double>::quiet_NaN();
    double cd0_subsonic = std::numeric_limits<double>::quiet_NaN();
    double cd0_supersonic = std::numeric_limits<double>::quiet_NaN();
    double induced_drag_k = std::numeric_limits<double>::quiet_NaN();
    std::vector<double> cd0_mach_breakpoints;
    std::vector<double> cd0_mach_values;
    std::vector<double> induced_drag_k_mach_breakpoints;
    std::vector<double> induced_drag_k_mach_values;
    double propellant_mass_kg = std::numeric_limits<double>::quiet_NaN();
    double max_lateral_g = std::numeric_limits<double>::quiet_NaN();
    double autopilot_tau_s = std::numeric_limits<double>::quiet_NaN();
    double autopilot_damping = std::numeric_limits<double>::quiet_NaN();
    int autopilot_order = 1;
    double max_accel_response_g_per_s = std::numeric_limits<double>::quiet_NaN();
    double mach_transonic_start = std::numeric_limits<double>::quiet_NaN();
    double mach_transonic_end = std::numeric_limits<double>::quiet_NaN();
    double cd0_power_on_ratio = std::numeric_limits<double>::quiet_NaN();
    double min_launch_range_m = std::numeric_limits<double>::quiet_NaN();
    double max_launch_off_boresight_deg = std::numeric_limits<double>::quiet_NaN();
    bool lobl_required = false;
    bool midcourse_datalink_supported = false;
    bool use_kalman_seeker = false;
    double apn_target_accel_gain = std::numeric_limits<double>::quiet_NaN();
    WarheadProfile warhead_profile{};
    bool has_warhead_profile = false;
    FuzeProfile fuze_profile{};
    bool has_fuze_profile = false;
};
