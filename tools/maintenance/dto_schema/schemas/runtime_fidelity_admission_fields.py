"""Declarative DTO schema for RuntimeFidelityAdmission fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeFidelityAdmission fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_FIDELITY_ADMISSION_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_FIDELITY_ADMISSION_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_fidelity_admission',
    output_path='src/runtime/facade/detail/runtime_fidelity_admission.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='admitted', cpp_type='bool', default='false', group='EF_RUNTIME_FIDELITY_ADMISSION_FIELD'),
        Field(name='baseline_exact_evaluation', cpp_type='bool', default='false', group='EF_RUNTIME_FIDELITY_ADMISSION_FIELD'),
        Field(name='request_label', cpp_type='std::string', default='{}', group='EF_RUNTIME_FIDELITY_ADMISSION_FIELD'),
        Field(name='backend_profile_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_FIDELITY_ADMISSION_FIELD'),
        Field(name='parity_budget_ref', cpp_type='std::string', default='{}', group='EF_RUNTIME_FIDELITY_ADMISSION_FIELD'),
        Field(name='requested_provider_family', cpp_type='std::string', default='"none"', group='EF_RUNTIME_FIDELITY_ADMISSION_FIELD'),
        Field(name='selected_provider_family', cpp_type='std::string', default='"none"', group='EF_RUNTIME_FIDELITY_ADMISSION_FIELD'),
        Field(name='selected_stage_node_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_FIDELITY_ADMISSION_FIELD'),
        Field(name='rejection_reason', cpp_type='std::string', default='{}', group='EF_RUNTIME_FIDELITY_ADMISSION_FIELD'),
        Field(name='errors', cpp_type='std::vector<std::string>', default='{}', group='EF_RUNTIME_FIDELITY_ADMISSION_FIELD'),
        Field(name='evidence_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_RUNTIME_FIDELITY_ADMISSION_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
