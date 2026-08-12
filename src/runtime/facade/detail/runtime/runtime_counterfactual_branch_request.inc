// X-macro list of RuntimeCounterfactualBranchRequest fields.
//
// Consumers define EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(BatchWorldSetupRequest, baseline_setup, {})
EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(WorldEntityRef, entity_ref, {})
EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(RuntimeFidelityRequest, fidelity_request, {})
EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(std::uint64_t, deterministic_seed, 0)
EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(std::string, replay_envelope_id, {})
EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(std::string, branch_point_id, {})
EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(std::string, branch_worldline_id, {})
EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(std::string, parent_worldline_id, {})
EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(std::string, restore_barrier_id, "counterfactual_selected_slice")
EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(std::string, cadence_reason, "selected_slice_cadence_trace_runtime_window")
EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(double, mutation_dx, 0.0)
EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(double, mutation_dy, 0.0)
EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(double, mutation_dz, 0.0)
EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(double, mutation_dvx, 0.0)
EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(double, mutation_dvy, 0.0)
EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(double, mutation_dvz, 0.0)
EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(double, mutation_dheading, 0.0)
EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(bool, allow_raw_authoritative_state_mutation, false)
EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(std::vector<std::string>, evidence_refs, {})

#undef EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD
