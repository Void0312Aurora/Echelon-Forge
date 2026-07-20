"""Declarative DTO schema for WorldMissionCommandMaintainedAssignment fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of WorldMissionCommandMaintainedAssignment fields.\n'
    '//\n'
    '// Consumers define EF_WORLD_MISSION_COMMAND_MAINTAINED_ASSIGNMENT_FIELD(\n'
    '// type, name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_WORLD_MISSION_COMMAND_MAINTAINED_ASSIGNMENT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='world_mission_command_maintained_assignment',
    output_path='src/runtime/contracts/detail/world_mission_command_maintained_assignment.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='world_index', cpp_type='std::uint64_t', default='0', group='EF_WORLD_MISSION_COMMAND_MAINTAINED_ASSIGNMENT_FIELD'),
        Field(name='entity_id', cpp_type='std::uint64_t', default='0', group='EF_WORLD_MISSION_COMMAND_MAINTAINED_ASSIGNMENT_FIELD'),
        Field(name='mission_command', cpp_type='contract_type', default='{}', group='EF_WORLD_MISSION_COMMAND_MAINTAINED_ASSIGNMENT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
