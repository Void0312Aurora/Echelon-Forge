"""Declarative DTO schema for RuntimeWindowCadence fields.

The Python binding has long registered these properties alphabetically
rather than in declaration order, so only the C++ struct side is expanded
from this schema; the binding's ``def_rw`` block stays hand-written (see
the I26 sub-family report for the recorded partial-coverage rationale).
"""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeWindowCadence fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_WINDOW_CADENCE_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_WINDOW_CADENCE_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_window_cadence',
    output_path='src/runtime/facade/detail/runtime_window_cadence.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='domain', cpp_type='std::string', default='"control"', group='EF_RUNTIME_WINDOW_CADENCE_FIELD'),
        Field(name='tick_count', cpp_type='std::uint32_t', default='1', group='EF_RUNTIME_WINDOW_CADENCE_FIELD'),
        Field(name='interval_s', cpp_type='double', default='0.0', group='EF_RUNTIME_WINDOW_CADENCE_FIELD'),
        Field(name='merge_policy', cpp_type='std::string', default='"nested_slot"', group='EF_RUNTIME_WINDOW_CADENCE_FIELD'),
        Field(name='barrier_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_CADENCE_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
