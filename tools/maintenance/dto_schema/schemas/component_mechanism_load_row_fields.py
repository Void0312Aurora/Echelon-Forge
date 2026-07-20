"""Declarative DTO schema for ComponentMechanismLoadRow fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of ComponentMechanismLoadRow fields.\n'
    '//\n'
    '// Consumers define EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD\n'
)


SCHEMA = DtoSchema(
    name='component_mechanism_load_row',
    output_path='src/runtime/contracts/detail/component_mechanism_load_row.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='component_name', cpp_type='std::string', default='{}', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='component_system', cpp_type='std::string', default='{}', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='component_redundancy_group_id', cpp_type='std::string', default='{}', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='direct_hit', cpp_type='bool', default='false', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='distance_m', cpp_type='double', default='0.0', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='effect_scale', cpp_type='double', default='0.0', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='component_dependency_propagation_count', cpp_type='std::uint32_t', default='0', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='component_dependency_target_system', cpp_type='std::string', default='{}', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='component_dependency_edge_type', cpp_type='std::string', default='"none"', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='component_dependency_threshold', cpp_type='double', default='1.0', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='component_dependency_delay_s', cpp_type='double', default='0.0', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='component_dependency_direction', cpp_type='std::string', default='"one_way"', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='component_dependency_provenance', cpp_type='std::string', default='{}', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='component_dependency_source_availability', cpp_type='double', default='1.0', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='component_dependency_effective_scale', cpp_type='double', default='0.0', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='component_dependency_propagated', cpp_type='bool', default='false', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='mechanism_fragment_energy_j', cpp_type='double', default='0.0', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='mechanism_fragment_areal_density_per_m2', cpp_type='double', default='0.0', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='mechanism_penetration_margin', cpp_type='double', default='0.0', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='mechanism_blast_overpressure_kpa', cpp_type='double', default='0.0', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='mechanism_blast_impulse_kpa_ms', cpp_type='double', default='0.0', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='mechanism_blast_scaled_distance_m_kg13', cpp_type='double', default='0.0', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='mechanism_rod_cut_margin', cpp_type='double', default='0.0', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
        Field(name='mechanism_surface_incidence_cos', cpp_type='double', default='0.0', group='EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
