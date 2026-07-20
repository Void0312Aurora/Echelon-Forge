"""Declarative DTO schema for RuntimeExperimentResult fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeExperimentResult fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_EXPERIMENT_RESULT_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_EXPERIMENT_RESULT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_experiment_result',
    output_path='src/runtime/facade/detail/runtime_experiment_result.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='admitted', cpp_type='bool', default='false', group='EF_RUNTIME_EXPERIMENT_RESULT_FIELD'),
        Field(name='rejection_reason', cpp_type='std::string', default='{}', group='EF_RUNTIME_EXPERIMENT_RESULT_FIELD'),
        Field(name='branch_result', cpp_type='RuntimeCounterfactualBranchResult', default='{}', group='EF_RUNTIME_EXPERIMENT_RESULT_FIELD'),
        Field(name='parent_observation_packet', cpp_type='ObservationBatchPacket', default='{}', group='EF_RUNTIME_EXPERIMENT_RESULT_FIELD'),
        Field(name='branch_observation_packet', cpp_type='ObservationBatchPacket', default='{}', group='EF_RUNTIME_EXPERIMENT_RESULT_FIELD'),
        Field(name='parent_step_result', cpp_type='ExecutionBatchStepResult', default='{}', group='EF_RUNTIME_EXPERIMENT_RESULT_FIELD'),
        Field(name='branch_step_result', cpp_type='ExecutionBatchStepResult', default='{}', group='EF_RUNTIME_EXPERIMENT_RESULT_FIELD'),
        Field(name='parent_diagnostics_traces', cpp_type='std::vector<DiagnosticsTrace>', default='{}', group='EF_RUNTIME_EXPERIMENT_RESULT_FIELD'),
        Field(name='branch_diagnostics_traces', cpp_type='std::vector<DiagnosticsTrace>', default='{}', group='EF_RUNTIME_EXPERIMENT_RESULT_FIELD'),
        Field(name='ancestry', cpp_type='RuntimeExperimentAncestry', default='{}', group='EF_RUNTIME_EXPERIMENT_RESULT_FIELD'),
        Field(name='evidence_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_RUNTIME_EXPERIMENT_RESULT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
