"""Declarative DTO schema for FuzeEvaluationEvent fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of FuzeEvaluationEvent fields.\n'
    '//\n'
    '// Consumers define EF_FUZE_EVALUATION_EVENT_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_FUZE_EVALUATION_EVENT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='fuze_evaluation_event',
    output_path='src/runtime/contracts/detail/fuze_evaluation_event.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='header', cpp_type='LethalityChainHeader', default='{}', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='fuze_type', cpp_type='std::string', default='"unknown"', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='armed', cpp_type='bool', default='false', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='triggered', cpp_type='bool', default='false', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='failure_reason', cpp_type='std::string', default='{}', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='delay_s', cpp_type='double', default='0.0', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='reliability', cpp_type='double', default='1.0', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='sample', cpp_type='double', default='1.0', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='expected_detonation_probability', cpp_type='double', default='0.0', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='sampled_outcome', cpp_type='bool', default='true', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='trigger_radius_m', cpp_type='double', default='0.0', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='contact_surface_distance_m', cpp_type='double', default='0.0', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='contact_penetration_depth_m', cpp_type='double', default='0.0', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='contact_surface_tolerance_m', cpp_type='double', default='0.0', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='contact_inside_hitbox', cpp_type='bool', default='false', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='sensor_opportunity_source', cpp_type='std::string', default='"none"', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='sensor_opportunity_score', cpp_type='double', default='0.0', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='terminal_track_valid', cpp_type='bool', default='false', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='target_detected', cpp_type='bool', default='false', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='target_detection_source', cpp_type='std::string', default='"none"', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='target_detection_confidence', cpp_type='double', default='0.0', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='target_detection_threshold', cpp_type='double', default='0.0', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='detonation_point_source', cpp_type='std::string', default='"unknown"', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='mechanism_coverage_score', cpp_type='double', default='0.0', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
        Field(name='direct_hitbox_intersection', cpp_type='bool', default='false', group='EF_FUZE_EVALUATION_EVENT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
