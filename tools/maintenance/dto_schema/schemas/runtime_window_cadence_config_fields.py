"""Declarative DTO schema for RuntimeWindowCadenceConfig fields.

The Python binding has long registered ``domains`` before
``window_duration_s`` -- the reverse of the header's declaration order --
so only the C++ struct side is expanded from this schema; the binding's
``def_rw`` block stays hand-written (see the I26 sub-family report for the
recorded partial-coverage rationale).
"""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeWindowCadenceConfig fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_WINDOW_CADENCE_CONFIG_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_WINDOW_CADENCE_CONFIG_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_window_cadence_config',
    output_path='src/runtime/facade/detail/runtime_window_cadence_config.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='window_duration_s', cpp_type='double', default='0.0', group='EF_RUNTIME_WINDOW_CADENCE_CONFIG_FIELD'),
        Field(name='domains', cpp_type='std::vector<RuntimeWindowCadence>', default='{}', group='EF_RUNTIME_WINDOW_CADENCE_CONFIG_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
