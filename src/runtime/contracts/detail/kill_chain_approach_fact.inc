// X-macro list of KillChainApproachFact fields.
//
// Consumers define EF_KILL_CHAIN_APPROACH_FACT_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_KILL_CHAIN_APPROACH_FACT_FIELD(std::string, owner_stage, "approach")
EF_KILL_CHAIN_APPROACH_FACT_FIELD(double, closest_distance_m, 0.0)
EF_KILL_CHAIN_APPROACH_FACT_FIELD(double, closest_point_local_forward_m, 0.0)
EF_KILL_CHAIN_APPROACH_FACT_FIELD(double, closest_point_local_right_m, 0.0)
EF_KILL_CHAIN_APPROACH_FACT_FIELD(double, closest_point_local_up_m, 0.0)
EF_KILL_CHAIN_APPROACH_FACT_FIELD(double, closure_mps, 0.0)
EF_KILL_CHAIN_APPROACH_FACT_FIELD(double, nearest_approach_time_s, 0.0)

#undef EF_KILL_CHAIN_APPROACH_FACT_FIELD
