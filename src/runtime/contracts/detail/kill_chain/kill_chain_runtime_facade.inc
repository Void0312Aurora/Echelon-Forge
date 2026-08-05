// X-macro list of KillChainRuntimeFacade fields.
//
// Consumers define EF_KILL_CHAIN_RUNTIME_FACADE_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_KILL_CHAIN_RUNTIME_FACADE_FIELD(std::uint32_t, schema_version, 1)
EF_KILL_CHAIN_RUNTIME_FACADE_FIELD(std::string, schema_name, "a2.kill_chain_runtime_facade.v1")
EF_KILL_CHAIN_RUNTIME_FACADE_FIELD(bool, runtime_dto_authority, true)
EF_KILL_CHAIN_RUNTIME_FACADE_FIELD(bool, runtime_parameter_retuning, false)
EF_KILL_CHAIN_RUNTIME_FACADE_FIELD(bool, calibration_authority, false)
EF_KILL_CHAIN_RUNTIME_FACADE_FIELD(bool, real_world_pk, false)
EF_KILL_CHAIN_RUNTIME_FACADE_FIELD(KillChainApproachFact, approach_fact, {})
EF_KILL_CHAIN_RUNTIME_FACADE_FIELD(KillChainFuzeDecision, fuze_decision, {})
EF_KILL_CHAIN_RUNTIME_FACADE_FIELD(KillChainWarheadLoadField, warhead_load_field, {})
EF_KILL_CHAIN_RUNTIME_FACADE_FIELD(KillChainTargetSusceptibility, target_susceptibility, {})
EF_KILL_CHAIN_RUNTIME_FACADE_FIELD(std::vector<KillChainComponentResponseFact>, component_responses, {})
EF_KILL_CHAIN_RUNTIME_FACADE_FIELD(KillChainConsequenceProjection, consequence_projection, {})

#undef EF_KILL_CHAIN_RUNTIME_FACADE_FIELD
