// X-macro list of RuntimeExperimentStepRequest fields.
//
// Consumers define EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD(ExecutionEpisodeState, state, {})
EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD(WorldExecutionEpisodeStepRequest, request, {})
EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD(std::string, observation_ref, {})
EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD(std::string, profile_ref, {})
EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD(std::string, claim_scope, std::string(runtime::counterfactual::kExperimentProfileClaimScopeDescriptive))
EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD(std::vector<std::string>, evidence_refs, {})

#undef EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD
