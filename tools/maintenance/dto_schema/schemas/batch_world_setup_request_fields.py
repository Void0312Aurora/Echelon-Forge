"""Declarative DTO schema for BatchWorldSetupRequest fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of BatchWorldSetupRequest fields.\n'
    '//\n'
    '// Consumers define EF_BATCH_WORLD_SETUP_REQUEST_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_BATCH_WORLD_SETUP_REQUEST_FIELD\n'
)


SCHEMA = DtoSchema(
    name='batch_world_setup_request',
    output_path='src/runtime/facade/detail/batch_world_setup_request.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='seeds', cpp_type='std::vector<std::uint32_t>', default='{}', group='EF_BATCH_WORLD_SETUP_REQUEST_FIELD'),
        Field(name='terrain_assignments', cpp_type='std::vector<WorldTerrainAssignment>', default='{}', group='EF_BATCH_WORLD_SETUP_REQUEST_FIELD'),
        Field(name='wind_assignments', cpp_type='std::vector<WorldWindAssignment>', default='{}', group='EF_BATCH_WORLD_SETUP_REQUEST_FIELD'),
        Field(name='sun_assignments', cpp_type='std::vector<WorldSunAssignment>', default='{}', group='EF_BATCH_WORLD_SETUP_REQUEST_FIELD'),
        Field(name='zones', cpp_type='std::vector<WorldZoneDefinition>', default='{}', group='EF_BATCH_WORLD_SETUP_REQUEST_FIELD'),
        Field(name='spawn_requests', cpp_type='std::vector<WorldSpawnRequest>', default='{}', group='EF_BATCH_WORLD_SETUP_REQUEST_FIELD'),
        Field(name='typed_platform_spawn_requests', cpp_type='std::vector<TypedPlatformSpawnRequest>', default='{}', group='EF_BATCH_WORLD_SETUP_REQUEST_FIELD'),
        Field(name='time_steps', cpp_type='std::vector<double>', default='{}', group='EF_BATCH_WORLD_SETUP_REQUEST_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
