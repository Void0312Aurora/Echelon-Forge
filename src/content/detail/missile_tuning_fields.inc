// Single-source X-macro field list for MissileTuningDefinition's JSON parse
// (T11 slice 4 bundle 1 / I58). Owns the 52 keys read by
// parse_missile_tuning_json_fields (content/unit_definition_loader.cpp): each
// key's JSON name is identical to its MissileTuningDefinition member name, and
// the "missing key keeps the existing value" default semantics is carried by
// the parse-side src.value(key, current) / parse_vector expansion below, NOT by
// the default_value token recorded here (that token mirrors the struct's own
// initializer for review parity and future struct single-sourcing).
//
// Consumers define both macros before including; the footer #undef's them:
//   EF_MISSILE_TUNING_FIELD(type, name, default_value)         scalar key
//   EF_MISSILE_TUNING_VECTOR_FIELD(type, name, default_value)  std::vector<double> key
// Field order mirrors the MissileTuningDefinition declaration order and the
// historical hand-written read order (content/unit_definition.h). Read order is
// NOT observable to parsing (each key writes a distinct member and .value /
// parse_vector have no cross-key side effects), but it is preserved for
// byte-level review parity with the pre-I58 hand-written body.
//
// Authored in the tools/maintenance/dto_schema X-macro form (see the I10
// flight_shaping_shared_fields.inc precedent) but intentionally NOT registered
// in the dto_schema generator: this is a C++-only content-loader parse map with
// no scenario_loader Python builder, so it stays a hand-authored .inc pinned by
// tests/architecture/content/test_missile_tuning_fields_inc.py (key set/order ==
// the I52 survey's 52 keys). The four MissileTuningDefinition members NOT read
// here -- warhead_profile, has_warhead_profile, fuze_profile, has_fuze_profile
// -- are populated from the warhead/fuze/fuse object keys in parse_unit_json and
// stay hand-written. Cross-ref: I52 draft content JSON schema (not wired; this
// list is the live source of the parse surface).

#if !defined(EF_MISSILE_TUNING_FIELD) || !defined(EF_MISSILE_TUNING_VECTOR_FIELD)
#error "define EF_MISSILE_TUNING_FIELD and EF_MISSILE_TUNING_VECTOR_FIELD before including missile_tuning_fields.inc"
#endif

EF_MISSILE_TUNING_FIELD(double, max_speed, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, turn_rate, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, fuse_distance, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, damage, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, seeker_fov_deg, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, seeker_lock_range, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, guidance_delay_s, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, guidance_update_period_s, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, max_flight_time_s, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, nav_gain, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, apn_target_accel_gain, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, sensor_max_range, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, sensor_fov_deg, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, sensor_scan_period, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, sensor_detection_prob, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, sensor_bearing_noise_std, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, sensor_range_noise_std, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, sensor_track_memory_s, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(int, seeker_type, -1)
EF_MISSILE_TUNING_FIELD(double, seeker_activation_range_m, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, seeker_gimbal_limit_deg, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, seeker_ifov_deg, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, bearing_filter_tau_s, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, elevation_filter_tau_s, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, range_filter_tau_s, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, track_break_time_s, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, boost_time_s, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, sustain_time_s, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, boost_thrust_n, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, sustain_thrust_n, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, reference_area_m2, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, cd0_subsonic, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, cd0_supersonic, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, induced_drag_k, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_VECTOR_FIELD(std::vector<double>, cd0_mach_breakpoints, {})
EF_MISSILE_TUNING_VECTOR_FIELD(std::vector<double>, cd0_mach_values, {})
EF_MISSILE_TUNING_VECTOR_FIELD(std::vector<double>, induced_drag_k_mach_breakpoints, {})
EF_MISSILE_TUNING_VECTOR_FIELD(std::vector<double>, induced_drag_k_mach_values, {})
EF_MISSILE_TUNING_FIELD(double, propellant_mass_kg, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, max_lateral_g, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, autopilot_tau_s, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, autopilot_damping, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(int, autopilot_order, 1)
EF_MISSILE_TUNING_FIELD(double, max_accel_response_g_per_s, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, mach_transonic_start, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, mach_transonic_end, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, cd0_power_on_ratio, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, min_launch_range_m, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(double, max_launch_off_boresight_deg, std::numeric_limits<double>::quiet_NaN())
EF_MISSILE_TUNING_FIELD(bool, lobl_required, false)
EF_MISSILE_TUNING_FIELD(bool, midcourse_datalink_supported, false)
EF_MISSILE_TUNING_FIELD(bool, use_kalman_seeker, false)

#undef EF_MISSILE_TUNING_FIELD
#undef EF_MISSILE_TUNING_VECTOR_FIELD
