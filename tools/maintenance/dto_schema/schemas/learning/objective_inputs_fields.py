"""Declarative DTO schema for ConditionalObjectiveInputs fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of ConditionalObjectiveInputs fields.\n'
    '//\n'
    '// Consumers define EF_OBJECTIVE_INPUT(type, name, default_value) before\n'
    "// including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_OBJECTIVE_INPUT\n'
)


SCHEMA = DtoSchema(
    name='objective_inputs',
    output_path='src/core/mission/runtime/detail/objective_inputs.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='altitude_m', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='altitude_agl_m', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='speed_mps', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='ground_speed_mps', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='gear_fraction', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='heading_error_deg', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='command_code', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='ground_track_error_deg', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='has_runway_cross_m', cpp_type='bool', default='false', group='EF_OBJECTIVE_INPUT'),
        Field(name='runway_cross_m', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='has_runway_from_threshold_m', cpp_type='bool', default='false', group='EF_OBJECTIVE_INPUT'),
        Field(name='runway_from_threshold_m', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='on_runway_geom', cpp_type='bool', default='false', group='EF_OBJECTIVE_INPUT'),
        Field(name='on_runway_task', cpp_type='bool', default='false', group='EF_OBJECTIVE_INPUT'),
        Field(name='on_ground', cpp_type='bool', default='false', group='EF_OBJECTIVE_INPUT'),
        Field(name='sink_rate_abs_mps', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='ils_localizer_abs', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='ils_glideslope_abs', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='dme_m', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='heading_deg', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='x_m', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='y_m', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='target_altitude_m', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='target_speed_mps', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='target_heading_deg', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='self_active', cpp_type='bool', default='true', group='EF_OBJECTIVE_INPUT'),
        Field(name='target_active', cpp_type='bool', default='false', group='EF_OBJECTIVE_INPUT'),
        Field(name='self_health', cpp_type='double', default='100.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='target_health', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='missiles_remaining', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
        Field(name='has_target_range_m', cpp_type='bool', default='false', group='EF_OBJECTIVE_INPUT'),
        Field(name='target_range_m', cpp_type='double', default='0.0', group='EF_OBJECTIVE_INPUT'),
    ),
    file_footer=FILE_FOOTER,
)
