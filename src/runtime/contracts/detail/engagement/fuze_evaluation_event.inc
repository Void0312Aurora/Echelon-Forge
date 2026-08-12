// X-macro list of FuzeEvaluationEvent fields.
//
// Consumers define EF_FUZE_EVALUATION_EVENT_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_FUZE_EVALUATION_EVENT_FIELD(LethalityChainHeader, header, {})
EF_FUZE_EVALUATION_EVENT_FIELD(std::string, fuze_type, "unknown")
EF_FUZE_EVALUATION_EVENT_FIELD(bool, armed, false)
EF_FUZE_EVALUATION_EVENT_FIELD(bool, triggered, false)
EF_FUZE_EVALUATION_EVENT_FIELD(std::string, failure_reason, {})
EF_FUZE_EVALUATION_EVENT_FIELD(double, delay_s, 0.0)
EF_FUZE_EVALUATION_EVENT_FIELD(double, reliability, 1.0)
EF_FUZE_EVALUATION_EVENT_FIELD(double, sample, 1.0)
EF_FUZE_EVALUATION_EVENT_FIELD(double, expected_detonation_probability, 0.0)
EF_FUZE_EVALUATION_EVENT_FIELD(bool, sampled_outcome, true)
EF_FUZE_EVALUATION_EVENT_FIELD(double, trigger_radius_m, 0.0)
EF_FUZE_EVALUATION_EVENT_FIELD(double, contact_surface_distance_m, 0.0)
EF_FUZE_EVALUATION_EVENT_FIELD(double, contact_penetration_depth_m, 0.0)
EF_FUZE_EVALUATION_EVENT_FIELD(double, contact_surface_tolerance_m, 0.0)
EF_FUZE_EVALUATION_EVENT_FIELD(bool, contact_inside_hitbox, false)
EF_FUZE_EVALUATION_EVENT_FIELD(std::string, sensor_opportunity_source, "none")
EF_FUZE_EVALUATION_EVENT_FIELD(double, sensor_opportunity_score, 0.0)
EF_FUZE_EVALUATION_EVENT_FIELD(bool, terminal_track_valid, false)
EF_FUZE_EVALUATION_EVENT_FIELD(bool, target_detected, false)
EF_FUZE_EVALUATION_EVENT_FIELD(std::string, target_detection_source, "none")
EF_FUZE_EVALUATION_EVENT_FIELD(double, target_detection_confidence, 0.0)
EF_FUZE_EVALUATION_EVENT_FIELD(double, target_detection_threshold, 0.0)
EF_FUZE_EVALUATION_EVENT_FIELD(std::string, detonation_point_source, "unknown")
EF_FUZE_EVALUATION_EVENT_FIELD(double, mechanism_coverage_score, 0.0)
EF_FUZE_EVALUATION_EVENT_FIELD(bool, direct_hitbox_intersection, false)

#undef EF_FUZE_EVALUATION_EVENT_FIELD
