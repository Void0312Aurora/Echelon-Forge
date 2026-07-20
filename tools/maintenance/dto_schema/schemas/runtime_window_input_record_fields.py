"""Declarative DTO schema for RuntimeWindowInputRecord fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeWindowInputRecord fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_WINDOW_INPUT_RECORD_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_WINDOW_INPUT_RECORD_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_window_input_record',
    output_path='src/runtime/facade/detail/runtime_window_input_record.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='request', cpp_type='RuntimeWindowActionRequest', default='{}', group='EF_RUNTIME_WINDOW_INPUT_RECORD_FIELD'),
        Field(name='reason', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_INPUT_RECORD_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
