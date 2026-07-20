"""Declarative DTO schema for TypedPlatformSpawnValidationResult fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of TypedPlatformSpawnValidationResult fields.\n'
    '//\n'
    '// Consumers define EF_TYPED_PLATFORM_SPAWN_VALIDATION_RESULT_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    '// #undef\'d here after expansion. The reject()/add_error() helper methods\n'
    '// are hand-written and declared after this X-macro block.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_TYPED_PLATFORM_SPAWN_VALIDATION_RESULT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='typed_platform_spawn_validation_result',
    output_path='src/runtime/contracts/detail/typed_platform_spawn_validation_result.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='valid', cpp_type='bool', default='false', group='EF_TYPED_PLATFORM_SPAWN_VALIDATION_RESULT_FIELD'),
        Field(name='fail_closed', cpp_type='bool', default='false', group='EF_TYPED_PLATFORM_SPAWN_VALIDATION_RESULT_FIELD'),
        Field(name='rejection_reason', cpp_type='std::string', default='{}', group='EF_TYPED_PLATFORM_SPAWN_VALIDATION_RESULT_FIELD'),
        Field(name='errors', cpp_type='std::vector<std::string>', default='{}', group='EF_TYPED_PLATFORM_SPAWN_VALIDATION_RESULT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
