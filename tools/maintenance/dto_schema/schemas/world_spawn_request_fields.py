"""Declarative DTO schema for WorldSpawnRequest fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of WorldSpawnRequest fields.\n'
    '//\n'
    '// Consumers define EF_WORLD_SPAWN_REQUEST_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_WORLD_SPAWN_REQUEST_FIELD\n'
)


SCHEMA = DtoSchema(
    name='world_spawn_request',
    output_path='src/runtime/contracts/detail/world_spawn_request.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='world_index', cpp_type='std::uint64_t', default='0', group='EF_WORLD_SPAWN_REQUEST_FIELD'),
        Field(name='side', cpp_type='Side', default='Side::Neutral', group='EF_WORLD_SPAWN_REQUEST_FIELD'),
        Field(name='type_name', cpp_type='std::string', default='{}', group='EF_WORLD_SPAWN_REQUEST_FIELD'),
        Field(name='entity_name', cpp_type='std::string', default='{}', group='EF_WORLD_SPAWN_REQUEST_FIELD'),
        Field(name='is_agent', cpp_type='bool', default='false', group='EF_WORLD_SPAWN_REQUEST_FIELD'),
        Field(name='x', cpp_type='double', default='0.0', group='EF_WORLD_SPAWN_REQUEST_FIELD'),
        Field(name='y', cpp_type='double', default='0.0', group='EF_WORLD_SPAWN_REQUEST_FIELD'),
        Field(name='z', cpp_type='double', default='0.0', group='EF_WORLD_SPAWN_REQUEST_FIELD'),
        Field(name='heading', cpp_type='double', default='0.0', group='EF_WORLD_SPAWN_REQUEST_FIELD'),
        Field(name='pitch', cpp_type='double', default='0.0', group='EF_WORLD_SPAWN_REQUEST_FIELD'),
        Field(name='roll', cpp_type='double', default='0.0', group='EF_WORLD_SPAWN_REQUEST_FIELD'),
        Field(name='vx', cpp_type='double', default='0.0', group='EF_WORLD_SPAWN_REQUEST_FIELD'),
        Field(name='vy', cpp_type='double', default='0.0', group='EF_WORLD_SPAWN_REQUEST_FIELD'),
        Field(name='vz', cpp_type='double', default='0.0', group='EF_WORLD_SPAWN_REQUEST_FIELD'),
        Field(name='ammo_override_enabled', cpp_type='bool', default='false', group='EF_WORLD_SPAWN_REQUEST_FIELD'),
        Field(name='missiles_remaining', cpp_type='int', default='0', group='EF_WORLD_SPAWN_REQUEST_FIELD'),
        Field(name='max_missiles', cpp_type='int', default='0', group='EF_WORLD_SPAWN_REQUEST_FIELD'),
        Field(name='weapon_cooldown_override_enabled', cpp_type='bool', default='false', group='EF_WORLD_SPAWN_REQUEST_FIELD'),
        Field(name='weapon_cooldown_s', cpp_type='double', default='2.0', group='EF_WORLD_SPAWN_REQUEST_FIELD'),
        Field(name='weapon_last_fire_time', cpp_type='double', default='-1.0', group='EF_WORLD_SPAWN_REQUEST_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
