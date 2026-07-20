"""Declarative DTO schema for KillChainWarheadLoadField fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of KillChainWarheadLoadField fields.\n'
    '//\n'
    '// Consumers define EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD\n'
)


SCHEMA = DtoSchema(
    name='kill_chain_warhead_load_field',
    output_path='src/runtime/contracts/detail/kill_chain_warhead_load_field.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='owner_stage', cpp_type='std::string', default='"warhead_load_field"', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='effect_family', cpp_type='std::string', default='"unknown"', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='warhead_mass_kg', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='lethal_radius_m', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='spatial_effect_scale', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='armor_transmission', cpp_type='double', default='1.0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='receiver_exposure_fraction', cpp_type='double', default='1.0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='mechanism_effect_scale', cpp_type='double', default='1.0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='projected_hitbox_count', cpp_type='std::uint32_t', default='0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='spatial_sample_count', cpp_type='std::uint32_t', default='0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='spatial_hit_estimate', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='spatial_hit_fraction', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='spatial_energy_scale', cpp_type='double', default='1.0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='spatial_pattern_scale', cpp_type='double', default='1.0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='orientation_pattern_scale', cpp_type='double', default='1.0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='fragment_energy_j', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='fragment_areal_density_per_m2', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='penetration_margin', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='blast_overpressure_kpa', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='blast_impulse_kpa_ms', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='blast_scaled_distance_m_kg13', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='rod_cut_margin', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='surface_incidence_cos', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
        Field(name='component_loads', cpp_type='std::vector<KillChainComponentLoadFact>', default='{}', group='EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
