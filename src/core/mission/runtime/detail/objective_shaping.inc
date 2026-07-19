// X-macro list of ObjectiveShapingConfig fields.
//
// Consumers define EF_OBJECTIVE_SHAPING(type, name, default_value) before
// including this file; the macro is #undef'd here after expansion.

EF_OBJECTIVE_SHAPING(double, runway_cross_penalty_weight, 0.0)
EF_OBJECTIVE_SHAPING(double, runway_cross_deadband_m, 0.0)
EF_OBJECTIVE_SHAPING(double, runway_cross_norm_m, 20.0)
EF_OBJECTIVE_SHAPING(double, runway_cross_power, 2.0)
EF_OBJECTIVE_SHAPING(double, runway_cross_clip, 0.0)
EF_OBJECTIVE_SHAPING(double, ground_track_penalty_weight, 0.0)
EF_OBJECTIVE_SHAPING(double, ground_track_deadband_deg, 0.0)
EF_OBJECTIVE_SHAPING(double, ground_track_norm_deg, 10.0)
EF_OBJECTIVE_SHAPING(double, ground_track_power, 2.0)
EF_OBJECTIVE_SHAPING(double, ground_track_clip, 0.0)

#undef EF_OBJECTIVE_SHAPING
