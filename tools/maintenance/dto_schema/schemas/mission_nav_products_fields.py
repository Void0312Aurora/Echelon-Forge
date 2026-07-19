"""Declarative DTO schema for MissionNavProducts fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of MissionNavProducts fields.\n'
    '//\n'
    '// Consumers define EF_NAV_PRODUCT(type, name, default_value) before\n'
    "// including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_NAV_PRODUCT\n'
)


SCHEMA = DtoSchema(
    name='mission_nav_products',
    output_path='src/core/mission/runtime/detail/mission_nav_products.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='valid', cpp_type='bool', default='false', group='EF_NAV_PRODUCT', readonly=True),
        Field(name='active_wp_idx', cpp_type='double', default='0.0', group='EF_NAV_PRODUCT', readonly=True),
        Field(name='total_wps', cpp_type='double', default='0.0', group='EF_NAV_PRODUCT', readonly=True),
        Field(name='selected_steerpoint', cpp_type='double', default='0.0', group='EF_NAV_PRODUCT', readonly=True),
        Field(name='steerpoint_mode_code', cpp_type='double', default='0.0', group='EF_NAV_PRODUCT', readonly=True),
        Field(name='dist_m', cpp_type='double', default='0.0', group='EF_NAV_PRODUCT', readonly=True),
        Field(name='xtk_m', cpp_type='double', default='0.0', group='EF_NAV_PRODUCT', readonly=True),
        Field(name='dtg_m', cpp_type='double', default='0.0', group='EF_NAV_PRODUCT', readonly=True),
        Field(name='direct_bearing_deg', cpp_type='double', default='0.0', group='EF_NAV_PRODUCT', readonly=True),
        Field(name='desired_leg_track_deg', cpp_type='double', default='0.0', group='EF_NAV_PRODUCT', readonly=True),
        Field(name='bearing_rel_deg', cpp_type='double', default='0.0', group='EF_NAV_PRODUCT', readonly=True),
        Field(name='altitude_delta_m', cpp_type='double', default='0.0', group='EF_NAV_PRODUCT', readonly=True),
        Field(name='cdi_norm', cpp_type='double', default='0.0', group='EF_NAV_PRODUCT', readonly=True),
        Field(name='track_angle_error_deg', cpp_type='double', default='0.0', group='EF_NAV_PRODUCT', readonly=True),
        Field(name='next_turn_deg', cpp_type='double', default='0.0', group='EF_NAV_PRODUCT', readonly=True),
        Field(name='distance_to_turn_m', cpp_type='double', default='0.0', group='EF_NAV_PRODUCT', readonly=True),
        Field(name='own_heading_deg', cpp_type='double', default='0.0', group='EF_NAV_PRODUCT', readonly=True),
        Field(name='ground_track_deg', cpp_type='double', default='0.0', group='EF_NAV_PRODUCT', readonly=True),
        Field(name='reference_speed_mps', cpp_type='double', default='0.0', group='EF_NAV_PRODUCT', readonly=True),
    ),
    file_footer=FILE_FOOTER,
)
