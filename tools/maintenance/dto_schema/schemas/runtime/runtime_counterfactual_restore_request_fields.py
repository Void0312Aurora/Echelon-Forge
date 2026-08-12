"""Declarative DTO schema for RuntimeCounterfactualRestoreRequest fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeCounterfactualRestoreRequest fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_counterfactual_restore_request',
    output_path='src/runtime/facade/detail/runtime/runtime_counterfactual_restore_request.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='snapshot', cpp_type='RuntimeCounterfactualSnapshot', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD'),
        Field(name='expected_worldline_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD'),
        Field(name='target_worldline_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD'),
        Field(name='target_deterministic_seed', cpp_type='std::uint64_t', default='0', group='EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD'),
        Field(name='target_entity_ref', cpp_type='WorldEntityRef', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD'),
        Field(name='restore_barrier_id', cpp_type='std::string', default='"counterfactual_selected_slice"', group='EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD'),
        Field(name='allow_raw_authoritative_state_mutation', cpp_type='bool', default='false', group='EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD'),
        Field(name='request_full_clone', cpp_type='bool', default='false', group='EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD'),
        Field(name='request_resident_state_restore', cpp_type='bool', default='false', group='EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD'),
        Field(name='request_exact_gpu_restore', cpp_type='bool', default='false', group='EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD'),
        Field(name='evidence_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
