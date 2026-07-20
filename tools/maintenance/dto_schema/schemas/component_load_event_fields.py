"""Declarative DTO schema for ComponentLoadEvent fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of ComponentLoadEvent fields.\n'
    '//\n'
    '// Consumers define EF_COMPONENT_LOAD_EVENT_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_COMPONENT_LOAD_EVENT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='component_load_event',
    output_path='src/runtime/contracts/detail/component_load_event.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='header', cpp_type='LethalityChainHeader', default='{}', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='component_name', cpp_type='std::string', default='{}', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='component_system', cpp_type='std::string', default='{}', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='component_redundancy_group_id', cpp_type='std::string', default='{}', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='direct_hit', cpp_type='bool', default='false', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='distance_m', cpp_type='double', default='0.0', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='effect_scale', cpp_type='double', default='0.0', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='spatial_intersection_fraction', cpp_type='double', default='0.0', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='pattern_weight', cpp_type='double', default='1.0', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='orientation_weight', cpp_type='double', default='1.0', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='receiver_exposure_fraction', cpp_type='double', default='1.0', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='armor_transmission', cpp_type='double', default='1.0', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='sampling_confidence', cpp_type='double', default='1.0', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='load_intensity_scale', cpp_type='double', default='1.0', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='fragment_energy_j', cpp_type='double', default='0.0', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='fragment_density_per_m2', cpp_type='double', default='0.0', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='penetration_margin', cpp_type='double', default='0.0', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='blast_overpressure_kpa', cpp_type='double', default='0.0', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='blast_impulse_kpa_ms', cpp_type='double', default='0.0', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='blast_scaled_distance_m_kg13', cpp_type='double', default='0.0', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='rod_cut_margin', cpp_type='double', default='0.0', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='surface_incidence_cos', cpp_type='double', default='0.0', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
        Field(name='load_source', cpp_type='std::string', default='"unprojected"', group='EF_COMPONENT_LOAD_EVENT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
