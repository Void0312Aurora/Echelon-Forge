// X-macro list of RuntimeCounterfactualRestoreRequest fields.
//
// Consumers define EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD(RuntimeCounterfactualSnapshot, snapshot, {})
EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD(std::string, expected_worldline_id, {})
EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD(std::string, target_worldline_id, {})
EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD(std::uint64_t, target_deterministic_seed, 0)
EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD(WorldEntityRef, target_entity_ref, {})
EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD(std::string, restore_barrier_id, "counterfactual_selected_slice")
EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD(bool, allow_raw_authoritative_state_mutation, false)
EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD(bool, request_full_clone, false)
EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD(bool, request_resident_state_restore, false)
EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD(bool, request_exact_gpu_restore, false)
EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD(std::vector<std::string>, evidence_refs, {})

#undef EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD
