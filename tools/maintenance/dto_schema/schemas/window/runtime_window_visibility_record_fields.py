"""Declarative DTO schema for RuntimeWindowVisibilityRecord fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeWindowVisibilityRecord fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_WINDOW_VISIBILITY_RECORD_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_WINDOW_VISIBILITY_RECORD_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_window_visibility_record',
    output_path='src/runtime/facade/detail/window/runtime_window_visibility_record.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='barrier_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_VISIBILITY_RECORD_FIELD'),
        Field(name='visible_input_count', cpp_type='std::size_t', default='0', group='EF_RUNTIME_WINDOW_VISIBILITY_RECORD_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
