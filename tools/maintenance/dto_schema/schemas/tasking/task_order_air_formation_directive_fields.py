"""Declarative DTO schema for TaskOrderAirFormationDirective fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of TaskOrderAirFormationDirective fields.\n'
    '//\n'
    '// Consumers define EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD\n'
)


SCHEMA = DtoSchema(
    name='task_order_air_formation_directive',
    output_path='src/runtime/contracts/detail/tasking/task_order_air_formation_directive.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='formation_template_id', cpp_type='std::uint64_t', default='0', group='EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD'),
        Field(name='formation_contract_id', cpp_type='std::uint64_t', default='0', group='EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD'),
        Field(name='formation_role_id', cpp_type='FormationRole', default='FormationRole::Unspecified', group='EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD'),
        Field(name='wingman_slot_id', cpp_type='WingmanSlot', default='WingmanSlot::Unspecified', group='EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD'),
        Field(name='join_policy_id', cpp_type='int', default='0', group='EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD'),
        Field(name='rejoin_policy_id', cpp_type='int', default='0', group='EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD'),
        Field(name='mutual_support_mode', cpp_type='int', default='0', group='EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD'),
        Field(name='support_sector_id', cpp_type='std::uint64_t', default='0', group='EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
