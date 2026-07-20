// X-macro list of RuntimeFidelityAdmission fields.
//
// Consumers define EF_RUNTIME_FIDELITY_ADMISSION_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RUNTIME_FIDELITY_ADMISSION_FIELD(bool, admitted, false)
EF_RUNTIME_FIDELITY_ADMISSION_FIELD(bool, baseline_exact_evaluation, false)
EF_RUNTIME_FIDELITY_ADMISSION_FIELD(std::string, request_label, {})
EF_RUNTIME_FIDELITY_ADMISSION_FIELD(std::string, backend_profile_id, {})
EF_RUNTIME_FIDELITY_ADMISSION_FIELD(std::string, parity_budget_ref, {})
EF_RUNTIME_FIDELITY_ADMISSION_FIELD(std::string, requested_provider_family, "none")
EF_RUNTIME_FIDELITY_ADMISSION_FIELD(std::string, selected_provider_family, "none")
EF_RUNTIME_FIDELITY_ADMISSION_FIELD(std::string, selected_stage_node_id, {})
EF_RUNTIME_FIDELITY_ADMISSION_FIELD(std::string, rejection_reason, {})
EF_RUNTIME_FIDELITY_ADMISSION_FIELD(std::vector<std::string>, errors, {})
EF_RUNTIME_FIDELITY_ADMISSION_FIELD(std::vector<std::string>, evidence_refs, {})

#undef EF_RUNTIME_FIDELITY_ADMISSION_FIELD
