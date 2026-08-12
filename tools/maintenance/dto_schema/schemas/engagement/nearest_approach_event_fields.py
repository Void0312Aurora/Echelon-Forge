"""Declarative DTO schema for NearestApproachEvent fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of NearestApproachEvent fields.\n'
    '//\n'
    '// Consumers define EF_NEAREST_APPROACH_EVENT_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_NEAREST_APPROACH_EVENT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='nearest_approach_event',
    output_path='src/runtime/contracts/detail/engagement/nearest_approach_event.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='header', cpp_type='LethalityChainHeader', default='{}', group='EF_NEAREST_APPROACH_EVENT_FIELD'),
        Field(name='nearest_approach_time_s', cpp_type='double', default='0.0', group='EF_NEAREST_APPROACH_EVENT_FIELD'),
        Field(name='miss_distance_m', cpp_type='double', default='0.0', group='EF_NEAREST_APPROACH_EVENT_FIELD'),
        Field(name='local_forward_m', cpp_type='double', default='0.0', group='EF_NEAREST_APPROACH_EVENT_FIELD'),
        Field(name='local_right_m', cpp_type='double', default='0.0', group='EF_NEAREST_APPROACH_EVENT_FIELD'),
        Field(name='local_up_m', cpp_type='double', default='0.0', group='EF_NEAREST_APPROACH_EVENT_FIELD'),
        Field(name='closure_mps', cpp_type='double', default='0.0', group='EF_NEAREST_APPROACH_EVENT_FIELD'),
        Field(name='aspect_bucket', cpp_type='std::string', default='"unknown"', group='EF_NEAREST_APPROACH_EVENT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
