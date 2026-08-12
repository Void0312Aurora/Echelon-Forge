"""Declarative DTO schema for RuntimeWindowActionRequest::CadenceControl fields.

The Python binding (registered as ``RuntimeWindowCadenceControl``) has long
registered these properties alphabetically rather than in declaration
order, so only the C++ struct side is expanded from this schema; the
binding's ``def_rw`` block stays hand-written (see the I26 sub-family
report for the recorded partial-coverage rationale).
"""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeWindowActionRequest::CadenceControl fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_WINDOW_CADENCE_CONTROL_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_WINDOW_CADENCE_CONTROL_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_window_cadence_control',
    output_path='src/runtime/facade/detail/window/runtime_window_cadence_control.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='hold_policy', cpp_type='ActionHoldPolicy', default='{}', group='EF_RUNTIME_WINDOW_CADENCE_CONTROL_FIELD'),
        Field(name='enabled', cpp_type='bool', default='false', group='EF_RUNTIME_WINDOW_CADENCE_CONTROL_FIELD'),
        Field(name='has_expiry_time', cpp_type='bool', default='false', group='EF_RUNTIME_WINDOW_CADENCE_CONTROL_FIELD'),
        Field(name='expiry_time_s', cpp_type='double', default='0.0', group='EF_RUNTIME_WINDOW_CADENCE_CONTROL_FIELD'),
        Field(name='source_cadence_domain', cpp_type='std::string', default='"control"', group='EF_RUNTIME_WINDOW_CADENCE_CONTROL_FIELD'),
        Field(name='source_tick', cpp_type='std::uint32_t', default='0', group='EF_RUNTIME_WINDOW_CADENCE_CONTROL_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
