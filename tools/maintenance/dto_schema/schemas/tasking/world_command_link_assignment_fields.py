"""Declarative DTO schema for WorldCommandLinkAssignment fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of WorldCommandLinkAssignment fields.\n'
    '//\n'
    '// Consumers define EF_WORLD_COMMAND_LINK_ASSIGNMENT_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_WORLD_COMMAND_LINK_ASSIGNMENT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='world_command_link_assignment',
    output_path='src/runtime/contracts/detail/tasking/world_command_link_assignment.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='world_index', cpp_type='std::uint64_t', default='0', group='EF_WORLD_COMMAND_LINK_ASSIGNMENT_FIELD'),
        Field(name='entity_id', cpp_type='std::uint64_t', default='0', group='EF_WORLD_COMMAND_LINK_ASSIGNMENT_FIELD'),
        Field(name='latency_s', cpp_type='double', default='0.0', group='EF_WORLD_COMMAND_LINK_ASSIGNMENT_FIELD'),
        Field(name='drop_probability', cpp_type='double', default='0.0', group='EF_WORLD_COMMAND_LINK_ASSIGNMENT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
