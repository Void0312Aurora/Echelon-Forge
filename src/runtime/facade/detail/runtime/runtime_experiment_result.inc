// X-macro list of RuntimeExperimentResult fields.
//
// Consumers define EF_RUNTIME_EXPERIMENT_RESULT_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RUNTIME_EXPERIMENT_RESULT_FIELD(bool, admitted, false)
EF_RUNTIME_EXPERIMENT_RESULT_FIELD(std::string, rejection_reason, {})
EF_RUNTIME_EXPERIMENT_RESULT_FIELD(RuntimeCounterfactualBranchResult, branch_result, {})
EF_RUNTIME_EXPERIMENT_RESULT_FIELD(ObservationBatchPacket, parent_observation_packet, {})
EF_RUNTIME_EXPERIMENT_RESULT_FIELD(ObservationBatchPacket, branch_observation_packet, {})
EF_RUNTIME_EXPERIMENT_RESULT_FIELD(ExecutionBatchStepResult, parent_step_result, {})
EF_RUNTIME_EXPERIMENT_RESULT_FIELD(ExecutionBatchStepResult, branch_step_result, {})
EF_RUNTIME_EXPERIMENT_RESULT_FIELD(std::vector<DiagnosticsTrace>, parent_diagnostics_traces, {})
EF_RUNTIME_EXPERIMENT_RESULT_FIELD(std::vector<DiagnosticsTrace>, branch_diagnostics_traces, {})
EF_RUNTIME_EXPERIMENT_RESULT_FIELD(RuntimeExperimentAncestry, ancestry, {})
EF_RUNTIME_EXPERIMENT_RESULT_FIELD(std::vector<std::string>, evidence_refs, {})

#undef EF_RUNTIME_EXPERIMENT_RESULT_FIELD
