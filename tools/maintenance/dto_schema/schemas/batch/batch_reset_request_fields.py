"""Declarative DTO schema for BatchResetRequest fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of BatchResetRequest fields.\n'
    '//\n'
    '// Consumers define EF_BATCH_RESET_REQUEST_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_BATCH_RESET_REQUEST_FIELD\n'
)


SCHEMA = DtoSchema(
    name='batch_reset_request',
    output_path='src/runtime/facade/detail/batch/batch_reset_request.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='seeds', cpp_type='std::vector<std::uint32_t>', default='{}', group='EF_BATCH_RESET_REQUEST_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
