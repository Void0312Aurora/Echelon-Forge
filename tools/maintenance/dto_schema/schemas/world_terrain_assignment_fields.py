"""Declarative DTO schema for WorldTerrainAssignment fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of WorldTerrainAssignment fields.\n'
    '//\n'
    '// Consumers define EF_WORLD_TERRAIN_ASSIGNMENT_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_WORLD_TERRAIN_ASSIGNMENT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='world_terrain_assignment',
    output_path='src/runtime/contracts/detail/world_terrain_assignment.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='world_index', cpp_type='std::uint64_t', default='0', group='EF_WORLD_TERRAIN_ASSIGNMENT_FIELD'),
        Field(name='terrain_type', cpp_type='std::string', default='"flat"', group='EF_WORLD_TERRAIN_ASSIGNMENT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
