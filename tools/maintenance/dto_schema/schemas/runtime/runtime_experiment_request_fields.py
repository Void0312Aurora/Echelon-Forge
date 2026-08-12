"""Declarative DTO schema for RuntimeExperimentRequest fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeExperimentRequest fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_EXPERIMENT_REQUEST_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_experiment_request',
    output_path='src/runtime/facade/detail/runtime/runtime_experiment_request.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='branch_request', cpp_type='RuntimeCounterfactualBranchRequest', default='{}', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
        Field(name='parent_step_requests', cpp_type='std::vector<RuntimeExperimentStepRequest>', default='{}', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
        Field(name='branch_step_requests', cpp_type='std::vector<RuntimeExperimentStepRequest>', default='{}', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
        Field(name='trace_ids', cpp_type='std::vector<std::uint64_t>', default='{}', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
        Field(name='experiment_run_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
        Field(name='comparison_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
        Field(name='setup_ref', cpp_type='std::string', default='{}', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
        Field(name='generation_ref', cpp_type='std::string', default='{}', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
        Field(name='generated_input_ref', cpp_type='std::string', default='{}', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
        Field(name='generated_input_kind', cpp_type='std::string', default='std::string(runtime::counterfactual::kScenarioGenerationKindScenarioVariation)', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
        Field(name='generated_input_source', cpp_type='std::string', default='std::string(runtime::counterfactual::kScenarioGenerationSourceCounterfactualBranch)', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
        Field(name='generated_input_generator_version', cpp_type='std::string', default='"RuntimeFacade.run_counterfactual_experiment.counterfactual"', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
        Field(name='generated_input_baseline_scenario_ref', cpp_type='std::string', default='{}', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
        Field(name='generated_input_evidence_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
        Field(name='capability_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
        Field(name='include_observations', cpp_type='bool', default='true', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
        Field(name='include_diagnostics_traces', cpp_type='bool', default='true', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
        Field(name='include_generated_input_ref', cpp_type='bool', default='true', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
        Field(name='truth_claim', cpp_type='bool', default='false', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
        Field(name='promoted_to_support', cpp_type='bool', default='false', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
        Field(name='evidence_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_RUNTIME_EXPERIMENT_REQUEST_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
