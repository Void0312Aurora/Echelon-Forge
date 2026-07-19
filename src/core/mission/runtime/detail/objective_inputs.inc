// X-macro list of ConditionalObjectiveInputs fields.
//
// Consumers define EF_OBJECTIVE_INPUT(type, name, default_value) before
// including this file; the macro is #undef'd here after expansion.

EF_OBJECTIVE_INPUT(double, altitude_m, 0.0)
EF_OBJECTIVE_INPUT(double, altitude_agl_m, 0.0)
EF_OBJECTIVE_INPUT(double, speed_mps, 0.0)
EF_OBJECTIVE_INPUT(double, ground_speed_mps, 0.0)
EF_OBJECTIVE_INPUT(double, gear_fraction, 0.0)
EF_OBJECTIVE_INPUT(double, heading_error_deg, 0.0)
EF_OBJECTIVE_INPUT(double, command_code, 0.0)
EF_OBJECTIVE_INPUT(double, ground_track_error_deg, 0.0)
EF_OBJECTIVE_INPUT(bool, has_runway_cross_m, false)
EF_OBJECTIVE_INPUT(double, runway_cross_m, 0.0)
EF_OBJECTIVE_INPUT(bool, has_runway_from_threshold_m, false)
EF_OBJECTIVE_INPUT(double, runway_from_threshold_m, 0.0)
EF_OBJECTIVE_INPUT(bool, on_runway_geom, false)
EF_OBJECTIVE_INPUT(bool, on_runway_task, false)
EF_OBJECTIVE_INPUT(bool, on_ground, false)
EF_OBJECTIVE_INPUT(double, sink_rate_abs_mps, 0.0)
EF_OBJECTIVE_INPUT(double, ils_localizer_abs, 0.0)
EF_OBJECTIVE_INPUT(double, ils_glideslope_abs, 0.0)
EF_OBJECTIVE_INPUT(double, dme_m, 0.0)
EF_OBJECTIVE_INPUT(double, heading_deg, 0.0)
EF_OBJECTIVE_INPUT(double, x_m, 0.0)
EF_OBJECTIVE_INPUT(double, y_m, 0.0)
EF_OBJECTIVE_INPUT(double, target_altitude_m, 0.0)
EF_OBJECTIVE_INPUT(double, target_speed_mps, 0.0)
EF_OBJECTIVE_INPUT(double, target_heading_deg, 0.0)
EF_OBJECTIVE_INPUT(bool, self_active, true)
EF_OBJECTIVE_INPUT(bool, target_active, false)
EF_OBJECTIVE_INPUT(double, self_health, 100.0)
EF_OBJECTIVE_INPUT(double, target_health, 0.0)
EF_OBJECTIVE_INPUT(double, missiles_remaining, 0.0)
EF_OBJECTIVE_INPUT(bool, has_target_range_m, false)
EF_OBJECTIVE_INPUT(double, target_range_m, 0.0)

#undef EF_OBJECTIVE_INPUT
