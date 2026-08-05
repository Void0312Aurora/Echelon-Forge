"""Declarative DTO schema for RewardReport fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RewardReport fields.\n'
    '//\n'
    '// Consumers define EF_REWARD_REPORT_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_REWARD_REPORT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='reward_report',
    output_path='src/runtime/contracts/detail/learning/reward_report.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='fact_terms', cpp_type='std::vector<RewardTerm>', default='{}', group='EF_REWARD_REPORT_FIELD'),
        Field(name='shaping_terms', cpp_type='std::vector<RewardTerm>', default='{}', group='EF_REWARD_REPORT_FIELD'),
        Field(name='fact_snapshot_version', cpp_type='std::uint64_t', default='0', group='EF_REWARD_REPORT_FIELD'),
        Field(name='term_owner', cpp_type='std::string', default='"split"', group='EF_REWARD_REPORT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
