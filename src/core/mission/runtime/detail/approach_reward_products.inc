// X-macro list of ApproachRewardProducts fields.
//
// Consumers define EF_APPROACH_PRODUCT(type, name, default_value) before
// including this file; the macro is #undef'd here after expansion.

EF_APPROACH_PRODUCT(bool, valid, false)
EF_APPROACH_PRODUCT(double, approach_localizer, 0.0)
EF_APPROACH_PRODUCT(double, approach_localizer_improve, 0.0)
EF_APPROACH_PRODUCT(double, approach_glideslope, 0.0)
EF_APPROACH_PRODUCT(double, approach_glideslope_improve, 0.0)
EF_APPROACH_PRODUCT(double, approach_dme_progress, 0.0)
EF_APPROACH_PRODUCT(double, approach_capture_bonus, 0.0)
EF_APPROACH_PRODUCT(double, landing_sink_rate_penalty, 0.0)
EF_APPROACH_PRODUCT(bool, clear_history, false)
EF_APPROACH_PRODUCT(bool, next_prev_valid, false)
EF_APPROACH_PRODUCT(double, next_prev_loc_abs, 0.0)
EF_APPROACH_PRODUCT(double, next_prev_gs_abs, 0.0)
EF_APPROACH_PRODUCT(double, next_prev_dme_m, 0.0)

#undef EF_APPROACH_PRODUCT
