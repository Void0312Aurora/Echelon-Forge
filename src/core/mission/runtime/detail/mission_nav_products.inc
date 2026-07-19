// X-macro list of MissionNavProducts fields.
//
// Consumers define EF_NAV_PRODUCT(type, name, default_value) before
// including this file; the macro is #undef'd here after expansion.

EF_NAV_PRODUCT(bool, valid, false)
EF_NAV_PRODUCT(double, active_wp_idx, 0.0)
EF_NAV_PRODUCT(double, total_wps, 0.0)
EF_NAV_PRODUCT(double, selected_steerpoint, 0.0)
EF_NAV_PRODUCT(double, steerpoint_mode_code, 0.0)
EF_NAV_PRODUCT(double, dist_m, 0.0)
EF_NAV_PRODUCT(double, xtk_m, 0.0)
EF_NAV_PRODUCT(double, dtg_m, 0.0)
EF_NAV_PRODUCT(double, direct_bearing_deg, 0.0)
EF_NAV_PRODUCT(double, desired_leg_track_deg, 0.0)
EF_NAV_PRODUCT(double, bearing_rel_deg, 0.0)
EF_NAV_PRODUCT(double, altitude_delta_m, 0.0)
EF_NAV_PRODUCT(double, cdi_norm, 0.0)
EF_NAV_PRODUCT(double, track_angle_error_deg, 0.0)
EF_NAV_PRODUCT(double, next_turn_deg, 0.0)
EF_NAV_PRODUCT(double, distance_to_turn_m, 0.0)
EF_NAV_PRODUCT(double, own_heading_deg, 0.0)
EF_NAV_PRODUCT(double, ground_track_deg, 0.0)
EF_NAV_PRODUCT(double, reference_speed_mps, 0.0)

#undef EF_NAV_PRODUCT
