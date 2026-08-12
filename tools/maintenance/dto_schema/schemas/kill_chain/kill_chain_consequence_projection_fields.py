"""Declarative DTO schema for KillChainConsequenceProjection fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of KillChainConsequenceProjection fields.\n'
    '//\n'
    '// Consumers define EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD\n'
)


SCHEMA = DtoSchema(
    name='kill_chain_consequence_projection',
    output_path='src/runtime/contracts/detail/kill_chain/kill_chain_consequence_projection.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='owner_stage', cpp_type='std::string', default='"consequence_projection"', group='EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD'),
        Field(name='outcome_state', cpp_type='std::string', default='"unknown"', group='EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD'),
        Field(name='component_hit_count', cpp_type='std::uint32_t', default='0', group='EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD'),
        Field(name='component_failure_count', cpp_type='std::uint32_t', default='0', group='EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD'),
        Field(name='primary_component_name', cpp_type='std::string', default='{}', group='EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD'),
        Field(name='primary_component_system', cpp_type='std::string', default='{}', group='EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD'),
        Field(name='primary_component_integrity', cpp_type='double', default='1.0', group='EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD'),
        Field(name='redundancy_group_availability', cpp_type='double', default='1.0', group='EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD'),
        Field(name='air_system_hit_flags', cpp_type='std::string', default='{}', group='EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD'),
        Field(name='air_system_spatial_scales', cpp_type='std::string', default='{}', group='EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD'),
        Field(name='vulnerability_scale_trace', cpp_type='std::string', default='{}', group='EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
