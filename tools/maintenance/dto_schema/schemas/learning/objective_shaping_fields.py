"""Declarative DTO schema for ObjectiveShapingConfig fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of ObjectiveShapingConfig fields.\n'
    '//\n'
    '// Consumers define EF_OBJECTIVE_SHAPING(type, name, default_value) before\n'
    "// including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_OBJECTIVE_SHAPING\n'
)


SCHEMA = DtoSchema(
    name='objective_shaping',
    output_path='src/core/mission/runtime/detail/objective_shaping.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='runway_cross_penalty_weight', cpp_type='double', default='0.0', group='EF_OBJECTIVE_SHAPING'),
        Field(name='runway_cross_deadband_m', cpp_type='double', default='0.0', group='EF_OBJECTIVE_SHAPING'),
        Field(name='runway_cross_norm_m', cpp_type='double', default='20.0', group='EF_OBJECTIVE_SHAPING'),
        Field(name='runway_cross_power', cpp_type='double', default='2.0', group='EF_OBJECTIVE_SHAPING'),
        Field(name='runway_cross_clip', cpp_type='double', default='0.0', group='EF_OBJECTIVE_SHAPING'),
        Field(name='ground_track_penalty_weight', cpp_type='double', default='0.0', group='EF_OBJECTIVE_SHAPING'),
        Field(name='ground_track_deadband_deg', cpp_type='double', default='0.0', group='EF_OBJECTIVE_SHAPING'),
        Field(name='ground_track_norm_deg', cpp_type='double', default='10.0', group='EF_OBJECTIVE_SHAPING'),
        Field(name='ground_track_power', cpp_type='double', default='2.0', group='EF_OBJECTIVE_SHAPING'),
        Field(name='ground_track_clip', cpp_type='double', default='0.0', group='EF_OBJECTIVE_SHAPING'),
    ),
    file_footer=FILE_FOOTER,
)
