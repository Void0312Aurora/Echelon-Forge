// X-macro list of StepInfoProducts fields.
//
// Consumers define EF_STEP_INFO_PRODUCT(type, name, default_value) before
// including this file; the macro is #undef'd here after expansion.

EF_STEP_INFO_PRODUCT(bool, valid, false)
EF_STEP_INFO_PRODUCT(bool, on_runway, true)
EF_STEP_INFO_PRODUCT(bool, gear_collapsed, false)
EF_STEP_INFO_PRODUCT(double, gear_stress, 0.0)
EF_STEP_INFO_PRODUCT(bool, on_ground, false)
EF_STEP_INFO_PRODUCT(bool, airborne, false)
EF_STEP_INFO_PRODUCT(bool, preliftoff, true)
EF_STEP_INFO_PRODUCT(bool, has_runway_frame, false)
EF_STEP_INFO_PRODUCT(bool, on_runway_geom, false)
EF_STEP_INFO_PRODUCT(double, runway_cross_m, 0.0)
EF_STEP_INFO_PRODUCT(double, runway_along_m, 0.0)

#undef EF_STEP_INFO_PRODUCT
