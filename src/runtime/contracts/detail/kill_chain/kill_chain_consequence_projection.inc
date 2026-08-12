// X-macro list of KillChainConsequenceProjection fields.
//
// Consumers define EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD(std::string, owner_stage, "consequence_projection")
EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD(std::string, outcome_state, "unknown")
EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD(std::uint32_t, component_hit_count, 0)
EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD(std::uint32_t, component_failure_count, 0)
EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD(std::string, primary_component_name, {})
EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD(std::string, primary_component_system, {})
EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD(double, primary_component_integrity, 1.0)
EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD(double, redundancy_group_availability, 1.0)
EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD(std::string, air_system_hit_flags, {})
EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD(std::string, air_system_spatial_scales, {})
EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD(std::string, vulnerability_scale_trace, {})

#undef EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD
