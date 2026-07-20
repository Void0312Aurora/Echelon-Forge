"""Declarative DTO schema for TaskOrderNavalStationingDirective fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of TaskOrderNavalStationingDirective fields.\n'
    '//\n'
    '// Consumers define EF_TASK_ORDER_NAVAL_STATIONING_DIRECTIVE_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_TASK_ORDER_NAVAL_STATIONING_DIRECTIVE_FIELD\n'
)


SCHEMA = DtoSchema(
    name='task_order_naval_stationing_directive',
    output_path='src/runtime/contracts/detail/task_order_naval_stationing_directive.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='naval_station_type', cpp_type='NavalStationType', default='NavalStationType::Unspecified', group='EF_TASK_ORDER_NAVAL_STATIONING_DIRECTIVE_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
