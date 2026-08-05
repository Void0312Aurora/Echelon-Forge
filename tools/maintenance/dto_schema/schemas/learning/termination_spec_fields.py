"""Declarative DTO schema for TerminationSpec fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of TerminationSpec fields.\n'
    '//\n'
    '// Consumers define EF_TERMINATION_SPEC_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_TERMINATION_SPEC_FIELD\n'
)


SCHEMA = DtoSchema(
    name='termination_spec',
    output_path='src/runtime/contracts/detail/learning/termination_spec.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='reason', cpp_type='std::string', default='"running"', group='EF_TERMINATION_SPEC_FIELD'),
        Field(name='reason_source', cpp_type='std::string', default='"simulation"', group='EF_TERMINATION_SPEC_FIELD'),
        Field(name='snapshot_version', cpp_type='std::uint64_t', default='0', group='EF_TERMINATION_SPEC_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
