"""Declarative DTO schema for BatchWorldSetupResult fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of BatchWorldSetupResult fields.\n'
    '//\n'
    '// Consumers define EF_BATCH_WORLD_SETUP_RESULT_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_BATCH_WORLD_SETUP_RESULT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='batch_world_setup_result',
    output_path='src/runtime/facade/detail/batch/batch_world_setup_result.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='entity_ids', cpp_type='std::vector<std::uint64_t>', default='{}', group='EF_BATCH_WORLD_SETUP_RESULT_FIELD'),
        Field(name='typed_platform_spawn_results', cpp_type='std::vector<TypedPlatformSpawnResult>', default='{}', group='EF_BATCH_WORLD_SETUP_RESULT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
