// X-macro list of ConditionalObjectiveProducts fields.
//
// Consumers define EF_OBJECTIVE_PRODUCT(type, name, default_value) before
// including this file; the macro is #undef'd here after expansion.

EF_OBJECTIVE_PRODUCT(bool, valid, false)
EF_OBJECTIVE_PRODUCT(bool, matched, false)
EF_OBJECTIVE_PRODUCT(bool, unknown_property, false)
EF_OBJECTIVE_PRODUCT(double, status0, 0.0)
EF_OBJECTIVE_PRODUCT(double, status1, 0.0)
EF_OBJECTIVE_PRODUCT(double, status2, 0.0)
EF_OBJECTIVE_PRODUCT(int, status_count, 0)
EF_OBJECTIVE_PRODUCT(double, success_runway_cross_penalty, 0.0)
EF_OBJECTIVE_PRODUCT(double, success_ground_track_error_penalty, 0.0)
EF_OBJECTIVE_PRODUCT(double, objective_bonus, 0.0)

#undef EF_OBJECTIVE_PRODUCT
