"""Declarative DTO schema for RuntimeWindowRequest fields.

The Python binding has long registered ``cadence_config`` immediately
after ``action_requests`` -- ahead of ``observation_request`` and
``engagement_request`` -- which differs from the header's declaration
order, so only the C++ struct side is expanded from this schema; the
binding's ``def_rw`` block stays hand-written (see the I26 sub-family
report for the recorded partial-coverage rationale).
"""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeWindowRequest fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_WINDOW_REQUEST_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_WINDOW_REQUEST_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_window_request',
    output_path='src/runtime/facade/detail/runtime_window_request.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='window_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_REQUEST_FIELD'),
        Field(name='world_id', cpp_type='std::uint64_t', default='0', group='EF_RUNTIME_WINDOW_REQUEST_FIELD'),
        Field(name='source_time_s', cpp_type='double', default='0.0', group='EF_RUNTIME_WINDOW_REQUEST_FIELD'),
        Field(name='action_requests', cpp_type='std::vector<RuntimeWindowActionRequest>', default='{}', group='EF_RUNTIME_WINDOW_REQUEST_FIELD'),
        Field(name='observation_request', cpp_type='ObservationBatchRequest', default='{}', group='EF_RUNTIME_WINDOW_REQUEST_FIELD'),
        Field(name='engagement_request', cpp_type='EngagementBatchRequest', default='{}', group='EF_RUNTIME_WINDOW_REQUEST_FIELD'),
        Field(name='cadence_config', cpp_type='RuntimeWindowCadenceConfig', default='{}', group='EF_RUNTIME_WINDOW_REQUEST_FIELD'),
        Field(name='export_observation', cpp_type='bool', default='true', group='EF_RUNTIME_WINDOW_REQUEST_FIELD'),
        Field(name='export_engagement', cpp_type='bool', default='true', group='EF_RUNTIME_WINDOW_REQUEST_FIELD'),
        Field(name='export_diagnostics', cpp_type='bool', default='true', group='EF_RUNTIME_WINDOW_REQUEST_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
