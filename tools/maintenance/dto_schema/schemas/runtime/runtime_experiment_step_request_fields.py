"""Declarative DTO schema for RuntimeExperimentStepRequest fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeExperimentStepRequest fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_experiment_step_request',
    output_path='src/runtime/facade/detail/runtime/runtime_experiment_step_request.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='state', cpp_type='ExecutionEpisodeState', default='{}', group='EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD'),
        Field(name='request', cpp_type='WorldExecutionEpisodeStepRequest', default='{}', group='EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD'),
        Field(name='observation_ref', cpp_type='std::string', default='{}', group='EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD'),
        Field(name='profile_ref', cpp_type='std::string', default='{}', group='EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD'),
        Field(name='claim_scope', cpp_type='std::string', default='std::string(runtime::counterfactual::kExperimentProfileClaimScopeDescriptive)', group='EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD'),
        Field(name='evidence_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
