"""Declarative DTO schema for SpatialCoverageEvent fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of SpatialCoverageEvent fields.\n'
    '//\n'
    '// Consumers define EF_SPATIAL_COVERAGE_EVENT_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_SPATIAL_COVERAGE_EVENT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='spatial_coverage_event',
    output_path='src/runtime/contracts/detail/engagement/spatial_coverage_event.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='header', cpp_type='LethalityChainHeader', default='{}', group='EF_SPATIAL_COVERAGE_EVENT_FIELD'),
        Field(name='projected_hitbox_count', cpp_type='std::uint32_t', default='0', group='EF_SPATIAL_COVERAGE_EVENT_FIELD'),
        Field(name='sample_count', cpp_type='std::uint32_t', default='0', group='EF_SPATIAL_COVERAGE_EVENT_FIELD'),
        Field(name='hit_estimate', cpp_type='double', default='0.0', group='EF_SPATIAL_COVERAGE_EVENT_FIELD'),
        Field(name='hit_fraction', cpp_type='double', default='0.0', group='EF_SPATIAL_COVERAGE_EVENT_FIELD'),
        Field(name='energy_scale', cpp_type='double', default='1.0', group='EF_SPATIAL_COVERAGE_EVENT_FIELD'),
        Field(name='pattern_scale', cpp_type='double', default='1.0', group='EF_SPATIAL_COVERAGE_EVENT_FIELD'),
        Field(name='orientation_axis_forward', cpp_type='double', default='0.0', group='EF_SPATIAL_COVERAGE_EVENT_FIELD'),
        Field(name='orientation_axis_right', cpp_type='double', default='0.0', group='EF_SPATIAL_COVERAGE_EVENT_FIELD'),
        Field(name='orientation_axis_up', cpp_type='double', default='0.0', group='EF_SPATIAL_COVERAGE_EVENT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
