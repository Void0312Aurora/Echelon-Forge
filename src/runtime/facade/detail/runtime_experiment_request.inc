// X-macro list of RuntimeExperimentRequest fields.
//
// Consumers define EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(RuntimeCounterfactualBranchRequest, branch_request, {})
EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(std::vector<RuntimeExperimentStepRequest>, parent_step_requests, {})
EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(std::vector<RuntimeExperimentStepRequest>, branch_step_requests, {})
EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(std::vector<std::uint64_t>, trace_ids, {})
EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(std::string, experiment_run_id, {})
EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(std::string, comparison_id, {})
EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(std::string, setup_ref, {})
EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(std::string, generation_ref, {})
EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(std::string, generated_input_ref, {})
EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(std::string, generated_input_kind, std::string(runtime::counterfactual::kScenarioGenerationKindScenarioVariation))
EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(std::string, generated_input_source, std::string(runtime::counterfactual::kScenarioGenerationSourceCounterfactualBranch))
EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(std::string, generated_input_generator_version, "RuntimeFacade.run_counterfactual_experiment.counterfactual")
EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(std::string, generated_input_baseline_scenario_ref, {})
EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(std::vector<std::string>, generated_input_evidence_refs, {})
EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(std::vector<std::string>, capability_refs, {})
EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(bool, include_observations, true)
EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(bool, include_diagnostics_traces, true)
EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(bool, include_generated_input_ref, true)
EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(bool, truth_claim, false)
EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(bool, promoted_to_support, false)
EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(std::vector<std::string>, evidence_refs, {})

#undef EF_RUNTIME_EXPERIMENT_REQUEST_FIELD
