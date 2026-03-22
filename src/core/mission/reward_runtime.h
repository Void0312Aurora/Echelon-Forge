#pragma once

struct WaypointRewardInputs {
    bool valid = false;
    int waypoint_index = 0;
    int waypoint_count = 0;
    bool is_flyover = false;
    bool has_guidance = false;
    bool passed_fix = false;
    double dist_m = 0.0;
    double xtk_m = 0.0;
    double dtg_m = 0.0;
    double waypoint_radius_m = 500.0;
    double leg_len_m = 0.0;
    double lead_turn_m = 0.0;
    double sequence_gate_m = 500.0;
    bool has_prev_dist = false;
    double prev_dist_m = 0.0;
    double route_length_m = 0.0;
    double turn_relief_activation = 0.0;

    double progress_weight = 0.0;
    double progress_negative_scale = 1.0;
    double distance_weight = 0.0;
    double distance_clip_m = 0.0;
    bool distance_scale_by_route = false;
    double distance_route_ref_m = 55000.0;
    double distance_route_scale_min = 0.5;
    double distance_route_scale_max = 1.0;
    double cross_track_weight = 0.0;
    double cross_track_deadband_m = 0.0;
    double cross_track_norm_m = 1000.0;
    double cross_track_power = 1.0;
    double cross_track_clip = 0.0;
    double turn_relief_max = 0.0;
    double proximity_weight = 0.0;
    double proximity_ref_m = 0.0;
    double proximity_power = 1.0;
    double reached_bonus = 0.0;
};

struct WaypointRewardProducts {
    bool valid = false;
    double waypoint_progress = 0.0;
    double waypoint_distance = 0.0;
    double waypoint_cross_track = 0.0;
    double waypoint_proximity = 0.0;
    double waypoint_reached_bonus = 0.0;
    bool arrived = false;
    bool next_prev_dist_valid = false;
    double next_prev_dist_m = 0.0;
};

struct ApproachRewardInputs {
    bool valid = false;
    bool ils_valid = false;
    double ils_loc_dev = 0.0;
    double ils_gs_dev = 0.0;
    double ils_dme_m = 0.0;
    bool has_prev_loc = false;
    double prev_loc_abs = 0.0;
    bool has_prev_gs = false;
    double prev_gs_abs = 0.0;
    bool has_prev_dme = false;
    double prev_dme_m = 0.0;

    double localizer_weight = 0.0;
    double localizer_deadband = 0.0;
    double localizer_norm = 1.0;
    double localizer_power = 2.0;
    double localizer_clip = 0.0;
    double localizer_improve_weight = 0.0;

    double glideslope_weight = 0.0;
    double glideslope_deadband = 0.0;
    double glideslope_norm = 1.0;
    double glideslope_power = 2.0;
    double glideslope_clip = 0.0;
    double glideslope_improve_weight = 0.0;

    double dme_progress_weight = 0.0;
    double dme_progress_localizer_band = 0.0;
    double dme_progress_glideslope_band = 0.0;
    double dme_progress_quality_power = 1.0;

    double capture_bonus = 0.0;
    double capture_localizer_band = 0.20;
    double capture_glideslope_band = 0.20;

    double sink_rate_weight = 0.0;
    double flare_agl_m = 20.0;
    double curr_alt_agl_m = 0.0;
    double sink_rate_mps = 0.0;
    double sink_rate_deadband_mps = 0.0;
    double sink_rate_norm_mps = 2.0;
    double sink_rate_power = 2.0;
    double sink_rate_clip = 0.0;
};

struct ApproachRewardProducts {
    bool valid = false;
    double approach_localizer = 0.0;
    double approach_localizer_improve = 0.0;
    double approach_glideslope = 0.0;
    double approach_glideslope_improve = 0.0;
    double approach_dme_progress = 0.0;
    double approach_capture_bonus = 0.0;
    double landing_sink_rate_penalty = 0.0;
    bool clear_history = false;
    bool next_prev_valid = false;
    double next_prev_loc_abs = 0.0;
    double next_prev_gs_abs = 0.0;
    double next_prev_dme_m = 0.0;
};

struct FlightShapingRuntimeInputs {
    double truth_altitude_m = 0.0;
    double truth_speed_mps = 0.0;
    double prev_altitude_m = 0.0;
    double prev_ias_mps = 0.0;
    double curr_ias_mps = 0.0;
    double curr_alt_baro_m = 0.0;
    double curr_alt_agl_m = 0.0;
    double curr_gear_fraction = 0.0;
    double curr_roll_deg = 0.0;
    double curr_pitch_deg = 0.0;
    double curr_beta_deg = 0.0;
    double curr_yaw_rate_deg_s = 0.0;
    double curr_g_load = 1.0;
    int step_count = 0;

    double target_altitude_m = 0.0;
    double target_speed_mps = 0.0;
    double heading_error_deg = 0.0;
    double ground_track_error_deg = 0.0;
    double waypoint_turn_relief_activation = 0.0;

    bool preliftoff = false;
    bool on_runway_task = false;
    bool airborne = false;
    bool has_runway_cross_m = false;
    double runway_cross_m = 0.0;
    double runway_width_m = 0.0;
    bool ils_valid = false;
    double ils_loc_dev = 0.0;

    bool liftoff_awarded = false;
    bool gear_bonus_awarded = false;

    double altitude_progress_weight = 0.0;
    double speed_progress_weight = 0.0;
    double speed_progress_negative_weight = 0.0;
    double stationary_penalty = 0.0;
    int stationary_grace_steps = 20;
    double stationary_speed_threshold_mps = 5.0;
    double stationary_alt_threshold_m = 5.0;
    double liftoff_bonus = 0.0;
    double liftoff_speed_threshold_mps = 80.0;
    double liftoff_alt_threshold_m = 5.0;
    double rotation_reward_weight = 0.0;
    double rotation_speed_threshold_mps = 80.0;
    double rotation_alt_threshold_m = 5.0;
    double rotation_pitch_cap_deg = 15.0;
    double rotation_overpitch_penalty_weight = 0.0;
    double gear_up_bonus = 0.0;
    double gear_up_bonus_min_alt_agl_m = 50.0;
    double roll_stability_weight = 0.0;
    double heading_error_weight = 0.0;
    double heading_hold_deadband_deg = 0.0;
    double heading_hold_bonus = 0.0;
    double waypoint_turn_heading_relief_max = 0.0;

    double altitude_error_weight = 0.0;
    double altitude_error_min_alt_m = 0.0;
    double altitude_error_target_m = 0.0;
    double altitude_error_deadband_m = 0.0;
    double altitude_error_norm_m = 100.0;
    double altitude_error_power = 1.0;
    double altitude_error_clip = 0.0;
    double altitude_hold_bonus = 0.0;

    double speed_error_weight = 0.0;
    double speed_error_min_ias_mps = 0.0;
    double speed_error_target_mps = 0.0;
    double speed_error_deadband_mps = 0.0;
    double speed_error_norm_mps = 30.0;
    double speed_error_power = 1.0;
    double speed_error_clip = 0.0;
    double speed_hold_bonus = 0.0;

    double roll_abs_weight = 0.0;
    double roll_abs_deadband_deg = 0.0;
    double roll_abs_norm_deg = 30.0;
    double roll_abs_power = 1.0;
    double pitch_abs_weight = 0.0;
    double pitch_abs_deadband_deg = 0.0;
    double pitch_abs_norm_deg = 20.0;
    double pitch_abs_power = 1.0;
    double yaw_rate_abs_weight = 0.0;
    double yaw_rate_abs_deadband_deg_s = 0.0;
    double yaw_rate_abs_norm_deg_s = 10.0;
    double yaw_rate_abs_power = 1.0;
    double beta_abs_weight = 0.0;
    double beta_abs_deadband_deg = 0.0;
    double beta_abs_norm_deg = 10.0;
    double beta_abs_power = 1.0;
    double g_deviation_weight = 0.0;
    double g_deviation_deadband = 0.0;
    double g_deviation_norm = 0.5;
    double g_deviation_power = 1.0;
    double g_deviation_min_alt_agl_m = 5.0;

    double speed_reward_weight = 0.0;

    double runway_centerline_penalty_min_ias_mps = 0.0;
    double runway_centerline_penalty_max_ias_mps = 0.0;
    double runway_centerline_m_penalty_weight = 0.0;
    double runway_centerline_m_deadband_m = 0.0;
    double runway_centerline_m_norm_m = 5.0;
    double runway_centerline_m_power = 2.0;
    double runway_centerline_m_clip = 0.0;
    double runway_centerline_penalty_weight = 0.0;
    double runway_centerline_safe_frac = 0.0;
    double runway_centerline_penalty_power = 2.0;
    double runway_centerline_barrier_weight = 0.0;
    double runway_centerline_barrier_clip_frac = 0.995;

    double departure_centerline_max_alt_agl_m = 0.0;
    double departure_centerline_m_penalty_weight = 0.0;
    double departure_centerline_m_deadband_m = 0.0;
    double departure_centerline_m_norm_m = 20.0;
    double departure_centerline_m_power = 2.0;
    double departure_centerline_m_clip = 0.0;
    double departure_centerline_reward_weight = 0.0;
    double departure_centerline_reward_band_m = 1.0;
    double departure_track_error_weight = 0.0;
    double departure_track_error_deadband_deg = 0.0;
    double departure_track_error_norm_deg = 10.0;
    double departure_track_error_power = 2.0;
    double departure_track_error_clip = 0.0;
    double departure_track_reward_weight = 0.0;
    double departure_track_reward_band_deg = 10.0;

    double alignment_reward_weight = 0.0;
    double mission_alignment_min_alt_m = 120.0;
};

struct FlightShapingRuntimeProducts {
    bool valid = false;
    double altitude_progress = 0.0;
    double low_alt_descent_penalty = 0.0;
    double speed_progress = 0.0;
    double speed_regress = 0.0;
    double stationary_penalty = 0.0;
    double liftoff_bonus = 0.0;
    bool next_liftoff_awarded = false;
    double rotation_reward = 0.0;
    double rotation_overpitch_penalty = 0.0;
    double gear_up_bonus = 0.0;
    bool next_gear_bonus_awarded = false;
    double roll_stability = 0.0;
    double heading_error_penalty = 0.0;
    double heading_hold_bonus = 0.0;
    double altitude_error_penalty = 0.0;
    double altitude_hold_bonus = 0.0;
    double speed_error_penalty = 0.0;
    double speed_hold_bonus = 0.0;
    double roll_abs_penalty = 0.0;
    double pitch_abs_penalty = 0.0;
    double yaw_rate_abs_penalty = 0.0;
    double beta_abs_penalty = 0.0;
    double g_deviation_penalty = 0.0;
    double speed_reward = 0.0;
    double runway_centerline_m_penalty = 0.0;
    double runway_centerline_penalty = 0.0;
    double runway_centerline_barrier = 0.0;
    double departure_centerline_m_penalty = 0.0;
    double departure_centerline_reward = 0.0;
    double departure_track_error_penalty = 0.0;
    double departure_track_reward = 0.0;
    double alignment_reward = 0.0;
};

WaypointRewardProducts compute_waypoint_reward_terms(const WaypointRewardInputs& inputs);
ApproachRewardProducts compute_approach_reward_terms(const ApproachRewardInputs& inputs);
FlightShapingRuntimeProducts compute_flight_shaping_terms(const FlightShapingRuntimeInputs& inputs);
