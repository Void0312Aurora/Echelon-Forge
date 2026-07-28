// X-macro list of RuntimeCounterfactualBranchResult fields.
//
// Consumers define EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD(bool, admitted, false)
EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD(std::string, rejection_reason, {})
EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD(RuntimeFidelityAdmission, fidelity_admission, {})
EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD(RuntimeCounterfactualSnapshot, parent_snapshot, {})
EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD(RuntimeCounterfactualSnapshot, branch_snapshot, {})
EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD(RuntimeWorldlineComparison, comparison, {})
EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD(RuntimeCounterfactualRestoreResult, restore_result, {})
EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD(std::vector<std::string>, evidence_refs, {})

#undef EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD
