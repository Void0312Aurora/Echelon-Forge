"""Declarative DTO schema for KillChainComponentLoadFact fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of KillChainComponentLoadFact fields.\n'
    '//\n'
    '// Consumers define EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='kill_chain_component_load_fact',
    output_path='src/runtime/contracts/detail/kill_chain_component_load_fact.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='owner_stage', cpp_type='std::string', default='"warhead_load_field"', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='component_name', cpp_type='std::string', default='{}', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='component_system', cpp_type='std::string', default='{}', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='component_redundancy_group_id', cpp_type='std::string', default='{}', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='direct_hit', cpp_type='bool', default='false', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='distance_m', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='effect_scale', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='spatial_intersection_fraction', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='pattern_weight', cpp_type='double', default='1.0', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='orientation_weight', cpp_type='double', default='1.0', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='receiver_exposure_fraction', cpp_type='double', default='1.0', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='armor_transmission', cpp_type='double', default='1.0', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='sampling_confidence', cpp_type='double', default='1.0', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='load_intensity_scale', cpp_type='double', default='1.0', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='fragment_energy_j', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='fragment_areal_density_per_m2', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='penetration_margin', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='blast_overpressure_kpa', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='blast_impulse_kpa_ms', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='blast_scaled_distance_m_kg13', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='rod_cut_margin', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
        Field(name='surface_incidence_cos', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
