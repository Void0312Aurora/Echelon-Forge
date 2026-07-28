"""Declarative DTO schema for RuntimeWorldLayoutResult fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeWorldLayoutResult fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_WORLD_LAYOUT_RESULT_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_WORLD_LAYOUT_RESULT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_world_layout_result',
    output_path='src/runtime/facade/detail/runtime_world_layout_result.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='world_index', cpp_type='std::uint64_t', default='0', group='EF_RUNTIME_WORLD_LAYOUT_RESULT_FIELD'),
        Field(name='entity_ids', cpp_type='std::vector<std::uint64_t>', default='{}', group='EF_RUNTIME_WORLD_LAYOUT_RESULT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
