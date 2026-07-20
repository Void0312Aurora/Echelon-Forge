"""Declarative DTO schema for TypedPlatformSpawnRequest fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of TypedPlatformSpawnRequest fields.\n'
    '//\n'
    '// Consumers define EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD\n'
)


SCHEMA = DtoSchema(
    name='typed_platform_spawn_request',
    output_path='src/runtime/contracts/detail/typed_platform_spawn_request.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='world_index', cpp_type='std::uint64_t', default='0', group='EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD'),
        Field(name='side', cpp_type='Side', default='Side::Neutral', group='EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD'),
        Field(name='request_id', cpp_type='std::string', default='{}', group='EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD'),
        Field(name='source_type_name', cpp_type='std::string', default='{}', group='EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD'),
        Field(name='entity_name', cpp_type='std::string', default='{}', group='EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD'),
        Field(name='is_agent', cpp_type='bool', default='false', group='EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD'),
        Field(name='x', cpp_type='double', default='0.0', group='EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD'),
        Field(name='y', cpp_type='double', default='0.0', group='EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD'),
        Field(name='z', cpp_type='double', default='0.0', group='EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD'),
        Field(name='heading', cpp_type='double', default='0.0', group='EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD'),
        Field(name='pitch', cpp_type='double', default='0.0', group='EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD'),
        Field(name='roll', cpp_type='double', default='0.0', group='EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD'),
        Field(name='vx', cpp_type='double', default='0.0', group='EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD'),
        Field(name='vy', cpp_type='double', default='0.0', group='EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD'),
        Field(name='vz', cpp_type='double', default='0.0', group='EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD'),
        Field(name='capability_bundle', cpp_type='runtime::platform_capabilities::CapabilityBundle', default='{}', group='EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD'),
        Field(name='resolved_spawn_plan', cpp_type='runtime::platform_capabilities::ResolvedPlatformSpawnPlan', default='{}', group='EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD'),
        Field(name='facade_evidence_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD'),
        Field(name='type_name_projection_preserved', cpp_type='bool', default='true', group='EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
