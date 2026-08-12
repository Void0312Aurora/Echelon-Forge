"""Declarative DTO schema for TypedPlatformSpawnResult fields.

Header field order is authoritative (ABI/aggregate-init order). The Python
binding in bindings_runtime.cpp registers ``rejection_reason`` before
``setup_surface`` -- the reverse of the header's declaration order -- so
that class's def_rw block is intentionally left hand-written rather than
expanded from this same X-macro; see the I26 sub-family report for the
recorded partial-coverage rationale.
"""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of TypedPlatformSpawnResult fields.\n'
    '//\n'
    '// Consumers define EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='typed_platform_spawn_result',
    output_path='src/runtime/contracts/detail/platform/typed_platform_spawn_result.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='request_index', cpp_type='std::uint64_t', default='0', group='EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD'),
        Field(name='world_index', cpp_type='std::uint64_t', default='0', group='EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD'),
        Field(name='entity_id', cpp_type='std::uint64_t', default='0', group='EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD'),
        Field(name='admitted', cpp_type='bool', default='false', group='EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD'),
        Field(name='materialized', cpp_type='bool', default='false', group='EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD'),
        Field(name='fail_closed', cpp_type='bool', default='false', group='EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD'),
        Field(name='request_id', cpp_type='std::string', default='{}', group='EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD'),
        Field(name='source_type_name', cpp_type='std::string', default='{}', group='EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD'),
        Field(name='plan_id', cpp_type='std::string', default='{}', group='EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD'),
        Field(name='capability_bundle_id', cpp_type='std::string', default='{}', group='EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD'),
        Field(name='setup_surface', cpp_type='std::string', default='{}', group='EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD'),
        Field(name='rejection_reason', cpp_type='std::string', default='{}', group='EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD'),
        Field(name='errors', cpp_type='std::vector<std::string>', default='{}', group='EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD'),
        Field(name='evidence_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
