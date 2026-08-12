"""Declarative DTO schema for WorldEntityRef fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of WorldEntityRef fields.\n'
    '//\n'
    '// Consumers define EF_WORLD_ENTITY_REF_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_WORLD_ENTITY_REF_FIELD\n'
)


SCHEMA = DtoSchema(
    name='world_entity_ref',
    output_path='src/runtime/contracts/detail/platform/world_entity_ref.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='world_index', cpp_type='std::uint64_t', default='0', group='EF_WORLD_ENTITY_REF_FIELD'),
        Field(name='entity_id', cpp_type='std::uint64_t', default='0', group='EF_WORLD_ENTITY_REF_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
