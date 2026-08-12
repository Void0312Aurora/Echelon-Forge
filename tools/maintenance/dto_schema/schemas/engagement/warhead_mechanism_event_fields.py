"""Declarative DTO schema for WarheadMechanismEvent fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of WarheadMechanismEvent fields.\n'
    '//\n'
    '// Consumers define EF_WARHEAD_MECHANISM_EVENT_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_WARHEAD_MECHANISM_EVENT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='warhead_mechanism_event',
    output_path='src/runtime/contracts/detail/engagement/warhead_mechanism_event.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='header', cpp_type='LethalityChainHeader', default='{}', group='EF_WARHEAD_MECHANISM_EVENT_FIELD'),
        Field(name='mechanism_family', cpp_type='std::string', default='"unknown"', group='EF_WARHEAD_MECHANISM_EVENT_FIELD'),
        Field(name='warhead_mass_kg', cpp_type='double', default='0.0', group='EF_WARHEAD_MECHANISM_EVENT_FIELD'),
        Field(name='lethal_radius_m', cpp_type='double', default='0.0', group='EF_WARHEAD_MECHANISM_EVENT_FIELD'),
        Field(name='fragment_energy_j', cpp_type='double', default='0.0', group='EF_WARHEAD_MECHANISM_EVENT_FIELD'),
        Field(name='fragment_density_per_m2', cpp_type='double', default='0.0', group='EF_WARHEAD_MECHANISM_EVENT_FIELD'),
        Field(name='blast_overpressure_kpa', cpp_type='double', default='0.0', group='EF_WARHEAD_MECHANISM_EVENT_FIELD'),
        Field(name='blast_impulse_kpa_ms', cpp_type='double', default='0.0', group='EF_WARHEAD_MECHANISM_EVENT_FIELD'),
        Field(name='blast_scaled_distance_m_kg13', cpp_type='double', default='0.0', group='EF_WARHEAD_MECHANISM_EVENT_FIELD'),
        Field(name='rod_cut_margin', cpp_type='double', default='0.0', group='EF_WARHEAD_MECHANISM_EVENT_FIELD'),
        Field(name='penetration_margin', cpp_type='double', default='0.0', group='EF_WARHEAD_MECHANISM_EVENT_FIELD'),
        Field(name='surface_incidence_cos', cpp_type='double', default='0.0', group='EF_WARHEAD_MECHANISM_EVENT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
