"""Declarative DTO schema for StructuralBreakupEvent fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of StructuralBreakupEvent fields.\n'
    '//\n'
    '// Consumers define EF_STRUCTURAL_BREAKUP_EVENT_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_STRUCTURAL_BREAKUP_EVENT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='structural_breakup_event',
    output_path='src/runtime/contracts/detail/structural_breakup_event.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='header', cpp_type='LethalityChainHeader', default='{}', group='EF_STRUCTURAL_BREAKUP_EVENT_FIELD'),
        Field(name='breakup_state', cpp_type='std::string', default='"none"', group='EF_STRUCTURAL_BREAKUP_EVENT_FIELD'),
        Field(name='break_mode', cpp_type='std::string', default='"none"', group='EF_STRUCTURAL_BREAKUP_EVENT_FIELD'),
        Field(name='detached_part_ref', cpp_type='std::string', default='{}', group='EF_STRUCTURAL_BREAKUP_EVENT_FIELD'),
        Field(name='detached_part_count', cpp_type='std::uint32_t', default='0', group='EF_STRUCTURAL_BREAKUP_EVENT_FIELD'),
        Field(name='airframe_breakup', cpp_type='bool', default='false', group='EF_STRUCTURAL_BREAKUP_EVENT_FIELD'),
        Field(name='cause_event_id', cpp_type='std::uint64_t', default='0', group='EF_STRUCTURAL_BREAKUP_EVENT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
