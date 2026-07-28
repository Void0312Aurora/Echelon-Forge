// X-macro list of RuntimeFidelityRequest fields.
//
// Consumers define EF_RUNTIME_FIDELITY_REQUEST_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RUNTIME_FIDELITY_REQUEST_FIELD(std::string, request_label, {})
EF_RUNTIME_FIDELITY_REQUEST_FIELD(std::string, backend_profile_id, {})
EF_RUNTIME_FIDELITY_REQUEST_FIELD(std::string, parity_budget_ref, {})
EF_RUNTIME_FIDELITY_REQUEST_FIELD(std::string, provider_family, "none")
EF_RUNTIME_FIDELITY_REQUEST_FIELD(std::vector<std::string>, model_family_scope, {})
EF_RUNTIME_FIDELITY_REQUEST_FIELD(std::string, validation_gate, {})
EF_RUNTIME_FIDELITY_REQUEST_FIELD(std::vector<std::string>, facade_evidence_refs, {})

#undef EF_RUNTIME_FIDELITY_REQUEST_FIELD
