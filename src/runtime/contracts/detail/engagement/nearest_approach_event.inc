// X-macro list of NearestApproachEvent fields.
//
// Consumers define EF_NEAREST_APPROACH_EVENT_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_NEAREST_APPROACH_EVENT_FIELD(LethalityChainHeader, header, {})
EF_NEAREST_APPROACH_EVENT_FIELD(double, nearest_approach_time_s, 0.0)
EF_NEAREST_APPROACH_EVENT_FIELD(double, miss_distance_m, 0.0)
EF_NEAREST_APPROACH_EVENT_FIELD(double, local_forward_m, 0.0)
EF_NEAREST_APPROACH_EVENT_FIELD(double, local_right_m, 0.0)
EF_NEAREST_APPROACH_EVENT_FIELD(double, local_up_m, 0.0)
EF_NEAREST_APPROACH_EVENT_FIELD(double, closure_mps, 0.0)
EF_NEAREST_APPROACH_EVENT_FIELD(std::string, aspect_bucket, "unknown")

#undef EF_NEAREST_APPROACH_EVENT_FIELD
