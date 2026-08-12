"""Declarative DTO schema for RuntimeFidelityRequest fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeFidelityRequest fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_FIDELITY_REQUEST_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_FIDELITY_REQUEST_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_fidelity_request',
    output_path='src/runtime/facade/detail/runtime/runtime_fidelity_request.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='request_label', cpp_type='std::string', default='{}', group='EF_RUNTIME_FIDELITY_REQUEST_FIELD'),
        Field(name='backend_profile_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_FIDELITY_REQUEST_FIELD'),
        Field(name='parity_budget_ref', cpp_type='std::string', default='{}', group='EF_RUNTIME_FIDELITY_REQUEST_FIELD'),
        Field(name='provider_family', cpp_type='std::string', default='"none"', group='EF_RUNTIME_FIDELITY_REQUEST_FIELD'),
        Field(name='model_family_scope', cpp_type='std::vector<std::string>', default='{}', group='EF_RUNTIME_FIDELITY_REQUEST_FIELD'),
        Field(name='validation_gate', cpp_type='std::string', default='{}', group='EF_RUNTIME_FIDELITY_REQUEST_FIELD'),
        Field(name='facade_evidence_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_RUNTIME_FIDELITY_REQUEST_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
