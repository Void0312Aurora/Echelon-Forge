// X-macro list of RuntimeCounterfactualRestoreResult fields.
//
// Consumers define EF_RUNTIME_COUNTERFACTUAL_RESTORE_RESULT_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_RUNTIME_COUNTERFACTUAL_RESTORE_RESULT_FIELD(bool, restored, false)
EF_RUNTIME_COUNTERFACTUAL_RESTORE_RESULT_FIELD(std::string, rejection_reason, {})
EF_RUNTIME_COUNTERFACTUAL_RESTORE_RESULT_FIELD(RuntimeCounterfactualSnapshot, restored_snapshot, {})
EF_RUNTIME_COUNTERFACTUAL_RESTORE_RESULT_FIELD(std::vector<std::string>, evidence_refs, {})

#undef EF_RUNTIME_COUNTERFACTUAL_RESTORE_RESULT_FIELD
