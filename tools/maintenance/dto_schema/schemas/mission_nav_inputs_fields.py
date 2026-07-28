"""Declarative DTO schema for MissionNavInputs fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of MissionNavInputs fields.\n'
    '//\n'
    '// Consumers define EF_NAV_INPUT(type, name, default_value) before\n'
    "// including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_NAV_INPUT\n'
)


SCHEMA = DtoSchema(
    name='mission_nav_inputs',
    output_path='src/core/mission/runtime/detail/mission_nav_inputs.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='own_altitude_m', cpp_type='double', default='0.0', group='EF_NAV_INPUT'),
        Field(name='truth_heading_deg', cpp_type='double', default='0.0', group='EF_NAV_INPUT'),
        Field(name='truth_speed_mps', cpp_type='double', default='0.0', group='EF_NAV_INPUT'),
        Field(name='inst_heading_deg', cpp_type='double', default='0.0', group='EF_NAV_INPUT'),
        Field(name='inst_ground_track_deg', cpp_type='double', default='0.0', group='EF_NAV_INPUT'),
        Field(name='inst_ias_mps', cpp_type='double', default='0.0', group='EF_NAV_INPUT'),
        Field(name='waypoint_altitude_m', cpp_type='double', default='0.0', group='EF_NAV_INPUT'),
        Field(name='cdi_full_scale_m', cpp_type='double', default='1500.0', group='EF_NAV_INPUT'),
    ),
    file_footer=FILE_FOOTER,
)
