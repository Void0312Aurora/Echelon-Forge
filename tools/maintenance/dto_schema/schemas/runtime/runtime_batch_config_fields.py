"""Declarative DTO schema for RuntimeBatchConfig fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeBatchConfig fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_BATCH_CONFIG_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_BATCH_CONFIG_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_batch_config',
    output_path='src/runtime/facade/detail/runtime/runtime_batch_config.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='world_count', cpp_type='std::size_t', default='0', group='EF_RUNTIME_BATCH_CONFIG_FIELD'),
        Field(name='worker_threads', cpp_type='std::size_t', default='1', group='EF_RUNTIME_BATCH_CONFIG_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
