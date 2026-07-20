"""Declarative DTO schema for RuntimeWindowBarrierRecord fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeWindowBarrierRecord fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_WINDOW_BARRIER_RECORD_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_WINDOW_BARRIER_RECORD_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_window_barrier_record',
    output_path='src/runtime/facade/detail/runtime_window_barrier_record.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='sequence', cpp_type='std::uint64_t', default='0', group='EF_RUNTIME_WINDOW_BARRIER_RECORD_FIELD'),
        Field(name='barrier_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_BARRIER_RECORD_FIELD'),
        Field(name='node_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_BARRIER_RECORD_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
