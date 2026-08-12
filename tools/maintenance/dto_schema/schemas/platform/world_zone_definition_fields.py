"""Declarative DTO schema for WorldZoneDefinition fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of WorldZoneDefinition fields.\n'
    '//\n'
    '// Consumers define EF_WORLD_ZONE_DEFINITION_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_WORLD_ZONE_DEFINITION_FIELD\n'
)


SCHEMA = DtoSchema(
    name='world_zone_definition',
    output_path='src/runtime/contracts/detail/platform/world_zone_definition.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='world_index', cpp_type='std::uint64_t', default='0', group='EF_WORLD_ZONE_DEFINITION_FIELD'),
        Field(name='name', cpp_type='std::string', default='"Zone"', group='EF_WORLD_ZONE_DEFINITION_FIELD'),
        Field(name='x', cpp_type='double', default='0.0', group='EF_WORLD_ZONE_DEFINITION_FIELD'),
        Field(name='y', cpp_type='double', default='0.0', group='EF_WORLD_ZONE_DEFINITION_FIELD'),
        Field(name='width', cpp_type='double', default='1000.0', group='EF_WORLD_ZONE_DEFINITION_FIELD'),
        Field(name='length', cpp_type='double', default='1000.0', group='EF_WORLD_ZONE_DEFINITION_FIELD'),
        Field(name='heading', cpp_type='double', default='0.0', group='EF_WORLD_ZONE_DEFINITION_FIELD'),
        Field(name='surface_type', cpp_type='int', default='3', group='EF_WORLD_ZONE_DEFINITION_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
