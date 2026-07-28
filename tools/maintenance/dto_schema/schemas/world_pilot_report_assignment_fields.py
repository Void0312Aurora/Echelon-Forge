"""Declarative DTO schema for WorldPilotReportAssignment fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of WorldPilotReportAssignment fields.\n'
    '//\n'
    '// Consumers define EF_WORLD_PILOT_REPORT_ASSIGNMENT_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_WORLD_PILOT_REPORT_ASSIGNMENT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='world_pilot_report_assignment',
    output_path='src/runtime/contracts/detail/world_pilot_report_assignment.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='world_index', cpp_type='std::uint64_t', default='0', group='EF_WORLD_PILOT_REPORT_ASSIGNMENT_FIELD'),
        Field(name='entity_id', cpp_type='std::uint64_t', default='0', group='EF_WORLD_PILOT_REPORT_ASSIGNMENT_FIELD'),
        Field(name='report', cpp_type='shell_type', default='{}', group='EF_WORLD_PILOT_REPORT_ASSIGNMENT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
