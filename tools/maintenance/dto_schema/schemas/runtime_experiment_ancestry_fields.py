"""Declarative DTO schema for RuntimeExperimentAncestry fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeExperimentAncestry fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_experiment_ancestry',
    output_path='src/runtime/facade/detail/runtime_experiment_ancestry.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='evidence_bridge_valid', cpp_type='bool', default='false', group='EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD'),
        Field(name='evidence_bridge_fail_closed', cpp_type='bool', default='false', group='EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD'),
        Field(name='evidence_bridge_rejection_reason', cpp_type='std::string', default='{}', group='EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD'),
        Field(name='evidence_bridge_errors', cpp_type='std::vector<std::string>', default='{}', group='EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD'),
        Field(name='counterfactual_request_ref', cpp_type='std::string', default='{}', group='EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD'),
        Field(name='counterfactual_admission_ref', cpp_type='std::string', default='{}', group='EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD'),
        Field(name='setup_ref', cpp_type='std::string', default='{}', group='EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD'),
        Field(name='generation_ref', cpp_type='std::string', default='{}', group='EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD'),
        Field(name='replay_envelope_ref', cpp_type='std::string', default='{}', group='EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD'),
        Field(name='branch_point_ref', cpp_type='std::string', default='{}', group='EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD'),
        Field(name='generated_input_ref', cpp_type='std::string', default='{}', group='EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD'),
        Field(name='backend_profile_ref', cpp_type='std::string', default='{}', group='EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD'),
        Field(name='fidelity_profile_ref', cpp_type='std::string', default='{}', group='EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD'),
        Field(name='capability_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD'),
        Field(name='profile_observation_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD'),
        Field(name='evidence_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
