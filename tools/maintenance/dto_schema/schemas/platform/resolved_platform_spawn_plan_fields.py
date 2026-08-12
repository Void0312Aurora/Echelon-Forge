"""Declarative DTO schema for runtime::platform_capabilities::ResolvedPlatformSpawnPlan fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of runtime::platform_capabilities::ResolvedPlatformSpawnPlan\n'
    '// fields.\n'
    '//\n'
    '// Consumers define EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD\n'
)


SCHEMA = DtoSchema(
    name='resolved_platform_spawn_plan',
    output_path='src/runtime/contracts/detail/platform/resolved_platform_spawn_plan.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='plan_id', cpp_type='std::string', default='{}', group='EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD'),
        Field(name='source_request_kind', cpp_type='std::string', default='std::string(kPlatformSpawnRequestKindTypeNameProjection)', group='EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD'),
        Field(name='source_type_name', cpp_type='std::string', default='{}', group='EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD'),
        Field(name='capability_bundle_id', cpp_type='std::string', default='{}', group='EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD'),
        Field(name='resolved_platform_definition_ref', cpp_type='std::string', default='{}', group='EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD'),
        Field(name='materialization_strategy', cpp_type='std::string', default='std::string(kPlatformMaterializationStrategyFactoryProjection)', group='EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD'),
        Field(name='template_evidence_ref', cpp_type='std::string', default='{}', group='EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD'),
        Field(name='resolution_evidence_ref', cpp_type='std::string', default='{}', group='EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD'),
        Field(name='materialization_evidence_ref', cpp_type='std::string', default='{}', group='EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD'),
        Field(name='evidence_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD'),
        Field(name='resolved_capabilities', cpp_type='std::vector<Capability>', default='{}', group='EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD'),
        Field(name='rejected_capability_ids', cpp_type='std::vector<std::string>', default='{}', group='EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD'),
        Field(name='type_name_projection_preserved', cpp_type='bool', default='true', group='EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD'),
        Field(name='admitted', cpp_type='bool', default='false', group='EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD'),
        Field(name='rejection_reason', cpp_type='std::string', default='{}', group='EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD'),
        Field(name='diagnostics_reason', cpp_type='std::string', default='{}', group='EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
