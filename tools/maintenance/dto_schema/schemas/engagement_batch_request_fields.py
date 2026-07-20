"""Declarative DTO schema for EngagementBatchRequest fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of EngagementBatchRequest fields.\n'
    '//\n'
    '// Consumers define EF_ENGAGEMENT_BATCH_REQUEST_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_ENGAGEMENT_BATCH_REQUEST_FIELD\n'
)


SCHEMA = DtoSchema(
    name='engagement_batch_request',
    output_path='src/runtime/facade/detail/engagement_batch_request.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='refs', cpp_type='std::vector<EngagementEntityRef>', default='{}', group='EF_ENGAGEMENT_BATCH_REQUEST_FIELD'),
        Field(name='trace_ids', cpp_type='std::vector<std::uint64_t>', default='{}', group='EF_ENGAGEMENT_BATCH_REQUEST_FIELD'),
        Field(name='include_track_packets', cpp_type='bool', default='true', group='EF_ENGAGEMENT_BATCH_REQUEST_FIELD'),
        Field(name='include_launch_requests', cpp_type='bool', default='true', group='EF_ENGAGEMENT_BATCH_REQUEST_FIELD'),
        Field(name='include_launch_events', cpp_type='bool', default='true', group='EF_ENGAGEMENT_BATCH_REQUEST_FIELD'),
        Field(name='include_munition_lifecycle_packets', cpp_type='bool', default='true', group='EF_ENGAGEMENT_BATCH_REQUEST_FIELD'),
        Field(name='include_effects_events', cpp_type='bool', default='true', group='EF_ENGAGEMENT_BATCH_REQUEST_FIELD'),
        Field(name='include_damage_reports', cpp_type='bool', default='true', group='EF_ENGAGEMENT_BATCH_REQUEST_FIELD'),
        Field(name='include_diagnostics_traces', cpp_type='bool', default='true', group='EF_ENGAGEMENT_BATCH_REQUEST_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
