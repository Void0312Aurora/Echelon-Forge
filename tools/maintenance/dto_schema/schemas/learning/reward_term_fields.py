"""Declarative DTO schema for RewardTerm fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RewardTerm fields.\n'
    '//\n'
    '// Consumers define EF_REWARD_TERM_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_REWARD_TERM_FIELD\n'
)


SCHEMA = DtoSchema(
    name='reward_term',
    output_path='src/runtime/contracts/detail/learning/reward_term.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='name', cpp_type='std::string', default='{}', group='EF_REWARD_TERM_FIELD'),
        Field(name='value', cpp_type='double', default='0.0', group='EF_REWARD_TERM_FIELD'),
        Field(name='term_owner', cpp_type='std::string', default='"simulation"', group='EF_REWARD_TERM_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
