"""Declarative DTO schema for TaskOrderAirStationingDirective fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of TaskOrderAirStationingDirective fields.\n'
    '//\n'
    '// Consumers define EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD\n'
)


SCHEMA = DtoSchema(
    name='task_order_air_stationing_directive',
    output_path='src/runtime/contracts/detail/task_order_air_stationing_directive.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='anchor_x_m', cpp_type='double', default='0.0', group='EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD'),
        Field(name='anchor_y_m', cpp_type='double', default='0.0', group='EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD'),
        Field(name='anchor_z_m', cpp_type='double', default='0.0', group='EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD'),
        Field(name='station_type', cpp_type='StationType', default='StationType::Orbit', group='EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD'),
        Field(name='station_radius_m', cpp_type='double', default='0.0', group='EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD'),
        Field(name='station_leg_length_m', cpp_type='double', default='0.0', group='EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD'),
        Field(name='station_heading_deg', cpp_type='double', default='0.0', group='EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD'),
        Field(name='altitude_block_min_m', cpp_type='double', default='0.0', group='EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD'),
        Field(name='altitude_block_max_m', cpp_type='double', default='0.0', group='EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD'),
        Field(name='target_altitude_m', cpp_type='double', default='0.0', group='EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD'),
        Field(name='speed_min_mps', cpp_type='double', default='0.0', group='EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD'),
        Field(name='speed_max_mps', cpp_type='double', default='0.0', group='EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD'),
        Field(name='target_speed_mps', cpp_type='double', default='0.0', group='EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD'),
        Field(name='entry_condition_code', cpp_type='int', default='0', group='EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD'),
        Field(name='exit_condition_code', cpp_type='int', default='0', group='EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD'),
        Field(name='on_station_time_s', cpp_type='double', default='0.0', group='EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD'),
        Field(name='fuel_bingo_override_kg', cpp_type='double', default='0.0', group='EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
