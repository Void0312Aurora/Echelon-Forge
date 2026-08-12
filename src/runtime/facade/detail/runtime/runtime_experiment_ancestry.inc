// X-macro list of RuntimeExperimentAncestry fields.
//
// Consumers define EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(bool, evidence_bridge_valid, false)
EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(bool, evidence_bridge_fail_closed, false)
EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(std::string, evidence_bridge_rejection_reason, {})
EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(std::vector<std::string>, evidence_bridge_errors, {})
EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(std::string, counterfactual_request_ref, {})
EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(std::string, counterfactual_admission_ref, {})
EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(std::string, setup_ref, {})
EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(std::string, generation_ref, {})
EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(std::string, replay_envelope_ref, {})
EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(std::string, branch_point_ref, {})
EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(std::string, generated_input_ref, {})
EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(std::string, backend_profile_ref, {})
EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(std::string, fidelity_profile_ref, {})
EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(std::vector<std::string>, capability_refs, {})
EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(std::vector<std::string>, profile_observation_refs, {})
EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(std::vector<std::string>, evidence_refs, {})

#undef EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD
