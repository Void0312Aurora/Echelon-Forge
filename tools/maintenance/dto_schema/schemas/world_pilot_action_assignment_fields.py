"""Declarative DTO schema for WorldPilotActionAssignment fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of WorldPilotActionAssignment fields.\n'
    '//\n'
    '// Consumers define EF_WORLD_PILOT_ACTION_ASSIGNMENT_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_WORLD_PILOT_ACTION_ASSIGNMENT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='world_pilot_action_assignment',
    output_path='src/runtime/contracts/detail/world_pilot_action_assignment.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='world_index', cpp_type='std::uint64_t', default='0', group='EF_WORLD_PILOT_ACTION_ASSIGNMENT_FIELD'),
        Field(name='entity_id', cpp_type='std::uint64_t', default='0', group='EF_WORLD_PILOT_ACTION_ASSIGNMENT_FIELD'),
        Field(name='action', cpp_type='PilotAction', default='{}', group='EF_WORLD_PILOT_ACTION_ASSIGNMENT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
