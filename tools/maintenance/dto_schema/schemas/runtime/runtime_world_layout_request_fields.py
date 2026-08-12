"""Declarative DTO schema for RuntimeWorldLayoutRequest fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeWorldLayoutRequest fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_world_layout_request',
    output_path='src/runtime/facade/detail/runtime/runtime_world_layout_request.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='world_index', cpp_type='std::uint64_t', default='0', group='EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD'),
        Field(name='seed', cpp_type='std::uint32_t', default='42', group='EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD'),
        Field(name='terrain_type', cpp_type='std::string', default='{}', group='EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD'),
        Field(name='wind_speed_mps', cpp_type='double', default='0.0', group='EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD'),
        Field(name='wind_dir_from_deg', cpp_type='double', default='0.0', group='EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD'),
        Field(name='wind_shear_mps_per_km', cpp_type='double', default='0.0', group='EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD'),
        Field(name='sun_azimuth_deg', cpp_type='double', default='0.0', group='EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD'),
        Field(name='sun_elevation_deg', cpp_type='double', default='45.0', group='EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD'),
        Field(name='maritime_configured', cpp_type='bool', default='false', group='EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD'),
        Field(name='sea_state', cpp_type='double', default='0.0', group='EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD'),
        Field(name='wave_heading_deg', cpp_type='double', default='0.0', group='EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD'),
        Field(name='wave_period_s', cpp_type='double', default='8.0', group='EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD'),
        Field(name='zones', cpp_type='std::vector<WorldZoneDefinition>', default='{}', group='EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD'),
        Field(name='spawn_requests', cpp_type='std::vector<WorldSpawnRequest>', default='{}', group='EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD'),
        Field(name='time_steps', cpp_type='std::vector<double>', default='{}', group='EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
