"""Declarative DTO schema for TaskOrderAirTaskingIdentityDirective fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of TaskOrderAirTaskingIdentityDirective fields.\n'
    '//\n'
    '// Consumers define EF_TASK_ORDER_AIR_TASKING_IDENTITY_DIRECTIVE_FIELD(\n'
    '// type, name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_TASK_ORDER_AIR_TASKING_IDENTITY_DIRECTIVE_FIELD\n'
)


SCHEMA = DtoSchema(
    name='task_order_air_tasking_identity_directive',
    output_path='src/runtime/contracts/detail/tasking/task_order_air_tasking_identity_directive.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='task_type', cpp_type='TaskType', default='TaskType::Idle', group='EF_TASK_ORDER_AIR_TASKING_IDENTITY_DIRECTIVE_FIELD'),
        Field(name='element_id', cpp_type='std::uint64_t', default='0', group='EF_TASK_ORDER_AIR_TASKING_IDENTITY_DIRECTIVE_FIELD'),
        Field(name='package_id', cpp_type='std::uint64_t', default='0', group='EF_TASK_ORDER_AIR_TASKING_IDENTITY_DIRECTIVE_FIELD'),
        Field(name='lead_aircraft_id', cpp_type='std::uint64_t', default='0', group='EF_TASK_ORDER_AIR_TASKING_IDENTITY_DIRECTIVE_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
