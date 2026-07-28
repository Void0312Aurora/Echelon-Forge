"""Declarative DTO schema for WaypointRewardInputs fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of WaypointRewardInputs fields.\n'
    '//\n'
    '// Consumers define EF_WAYPOINT_INPUT(type, name, default_value) before\n'
    "// including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_WAYPOINT_INPUT\n'
)


SCHEMA = DtoSchema(
    name='waypoint_reward_inputs',
    output_path='src/core/mission/runtime/detail/waypoint_reward_inputs.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='valid', cpp_type='bool', default='false', group='EF_WAYPOINT_INPUT'),
        Field(name='waypoint_index', cpp_type='int', default='0', group='EF_WAYPOINT_INPUT'),
        Field(name='waypoint_count', cpp_type='int', default='0', group='EF_WAYPOINT_INPUT'),
        Field(name='is_flyover', cpp_type='bool', default='false', group='EF_WAYPOINT_INPUT'),
        Field(name='has_guidance', cpp_type='bool', default='false', group='EF_WAYPOINT_INPUT'),
        Field(name='passed_fix', cpp_type='bool', default='false', group='EF_WAYPOINT_INPUT'),
        Field(name='dist_m', cpp_type='double', default='0.0', group='EF_WAYPOINT_INPUT'),
        Field(name='xtk_m', cpp_type='double', default='0.0', group='EF_WAYPOINT_INPUT'),
        Field(name='dtg_m', cpp_type='double', default='0.0', group='EF_WAYPOINT_INPUT'),
        Field(name='waypoint_radius_m', cpp_type='double', default='500.0', group='EF_WAYPOINT_INPUT'),
        Field(name='leg_len_m', cpp_type='double', default='0.0', group='EF_WAYPOINT_INPUT'),
        Field(name='lead_turn_m', cpp_type='double', default='0.0', group='EF_WAYPOINT_INPUT'),
        Field(name='sequence_gate_m', cpp_type='double', default='500.0', group='EF_WAYPOINT_INPUT'),
        Field(name='has_prev_dist', cpp_type='bool', default='false', group='EF_WAYPOINT_INPUT'),
        Field(name='prev_dist_m', cpp_type='double', default='0.0', group='EF_WAYPOINT_INPUT'),
        Field(name='route_length_m', cpp_type='double', default='0.0', group='EF_WAYPOINT_INPUT'),
        Field(name='turn_relief_activation', cpp_type='double', default='0.0', group='EF_WAYPOINT_INPUT'),
        Field(name='progress_weight', cpp_type='double', default='0.0', group='EF_WAYPOINT_INPUT'),
        Field(name='progress_negative_scale', cpp_type='double', default='1.0', group='EF_WAYPOINT_INPUT'),
        Field(name='distance_weight', cpp_type='double', default='0.0', group='EF_WAYPOINT_INPUT'),
        Field(name='distance_clip_m', cpp_type='double', default='0.0', group='EF_WAYPOINT_INPUT'),
        Field(name='distance_scale_by_route', cpp_type='bool', default='false', group='EF_WAYPOINT_INPUT'),
        Field(name='distance_route_ref_m', cpp_type='double', default='55000.0', group='EF_WAYPOINT_INPUT'),
        Field(name='distance_route_scale_min', cpp_type='double', default='0.5', group='EF_WAYPOINT_INPUT'),
        Field(name='distance_route_scale_max', cpp_type='double', default='1.0', group='EF_WAYPOINT_INPUT'),
        Field(name='cross_track_weight', cpp_type='double', default='0.0', group='EF_WAYPOINT_INPUT'),
        Field(name='cross_track_deadband_m', cpp_type='double', default='0.0', group='EF_WAYPOINT_INPUT'),
        Field(name='cross_track_norm_m', cpp_type='double', default='1000.0', group='EF_WAYPOINT_INPUT'),
        Field(name='cross_track_power', cpp_type='double', default='1.0', group='EF_WAYPOINT_INPUT'),
        Field(name='cross_track_clip', cpp_type='double', default='0.0', group='EF_WAYPOINT_INPUT'),
        Field(name='turn_relief_max', cpp_type='double', default='0.0', group='EF_WAYPOINT_INPUT'),
        Field(name='proximity_weight', cpp_type='double', default='0.0', group='EF_WAYPOINT_INPUT'),
        Field(name='proximity_ref_m', cpp_type='double', default='0.0', group='EF_WAYPOINT_INPUT'),
        Field(name='proximity_power', cpp_type='double', default='1.0', group='EF_WAYPOINT_INPUT'),
        Field(name='reached_bonus', cpp_type='double', default='0.0', group='EF_WAYPOINT_INPUT'),
    ),
    file_footer=FILE_FOOTER,
)
