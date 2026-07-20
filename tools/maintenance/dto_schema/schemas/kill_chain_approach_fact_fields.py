"""Declarative DTO schema for KillChainApproachFact fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of KillChainApproachFact fields.\n'
    '//\n'
    '// Consumers define EF_KILL_CHAIN_APPROACH_FACT_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_KILL_CHAIN_APPROACH_FACT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='kill_chain_approach_fact',
    output_path='src/runtime/contracts/detail/kill_chain_approach_fact.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='owner_stage', cpp_type='std::string', default='"approach"', group='EF_KILL_CHAIN_APPROACH_FACT_FIELD'),
        Field(name='closest_distance_m', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_APPROACH_FACT_FIELD'),
        Field(name='closest_point_local_forward_m', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_APPROACH_FACT_FIELD'),
        Field(name='closest_point_local_right_m', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_APPROACH_FACT_FIELD'),
        Field(name='closest_point_local_up_m', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_APPROACH_FACT_FIELD'),
        Field(name='closure_mps', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_APPROACH_FACT_FIELD'),
        Field(name='nearest_approach_time_s', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_APPROACH_FACT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
