"""Declarative DTO schema for WaypointRewardProducts fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of WaypointRewardProducts fields.\n'
    '//\n'
    '// Consumers define EF_WAYPOINT_PRODUCT(type, name, default_value) before\n'
    "// including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_WAYPOINT_PRODUCT\n'
)


SCHEMA = DtoSchema(
    name='waypoint_reward_products',
    output_path='src/core/mission/runtime/detail/waypoint_reward_products.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='valid', cpp_type='bool', default='false', group='EF_WAYPOINT_PRODUCT', readonly=True),
        Field(name='waypoint_progress', cpp_type='double', default='0.0', group='EF_WAYPOINT_PRODUCT', readonly=True),
        Field(name='waypoint_distance', cpp_type='double', default='0.0', group='EF_WAYPOINT_PRODUCT', readonly=True),
        Field(name='waypoint_cross_track', cpp_type='double', default='0.0', group='EF_WAYPOINT_PRODUCT', readonly=True),
        Field(name='waypoint_proximity', cpp_type='double', default='0.0', group='EF_WAYPOINT_PRODUCT', readonly=True),
        Field(name='waypoint_reached_bonus', cpp_type='double', default='0.0', group='EF_WAYPOINT_PRODUCT', readonly=True),
        Field(name='arrived', cpp_type='bool', default='false', group='EF_WAYPOINT_PRODUCT', readonly=True),
        Field(name='next_prev_dist_valid', cpp_type='bool', default='false', group='EF_WAYPOINT_PRODUCT', readonly=True),
        Field(name='next_prev_dist_m', cpp_type='double', default='0.0', group='EF_WAYPOINT_PRODUCT', readonly=True),
    ),
    file_footer=FILE_FOOTER,
)
