// X-macro list of KillChainFuzeDecision fields.
//
// Consumers define EF_KILL_CHAIN_FUZE_DECISION_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_KILL_CHAIN_FUZE_DECISION_FIELD(std::string, owner_stage, "fuze_decision")
EF_KILL_CHAIN_FUZE_DECISION_FIELD(std::string, fuze_type, "unknown")
EF_KILL_CHAIN_FUZE_DECISION_FIELD(bool, detonated, false)
EF_KILL_CHAIN_FUZE_DECISION_FIELD(std::string, outcome_state, "unknown")
EF_KILL_CHAIN_FUZE_DECISION_FIELD(double, detonation_time_s, 0.0)
EF_KILL_CHAIN_FUZE_DECISION_FIELD(double, detonation_probability, 0.0)
EF_KILL_CHAIN_FUZE_DECISION_FIELD(double, fuze_quality, 0.0)
EF_KILL_CHAIN_FUZE_DECISION_FIELD(double, sensor_opportunity_score, 0.0)
EF_KILL_CHAIN_FUZE_DECISION_FIELD(bool, terminal_track_valid, false)
EF_KILL_CHAIN_FUZE_DECISION_FIELD(bool, target_detected, false)
EF_KILL_CHAIN_FUZE_DECISION_FIELD(double, target_detection_confidence, 0.0)
EF_KILL_CHAIN_FUZE_DECISION_FIELD(double, target_detection_threshold, 0.0)
EF_KILL_CHAIN_FUZE_DECISION_FIELD(std::string, detonation_point_source, "unknown")

#undef EF_KILL_CHAIN_FUZE_DECISION_FIELD
