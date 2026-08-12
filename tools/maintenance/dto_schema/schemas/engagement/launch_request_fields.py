"""Declarative DTO schema for LaunchRequest fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of LaunchRequest fields.\n'
    '//\n'
    '// Consumers define EF_LAUNCH_REQUEST_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_LAUNCH_REQUEST_FIELD\n'
)


SCHEMA = DtoSchema(
    name='launch_request',
    output_path='src/runtime/contracts/detail/engagement/launch_request.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='request_id', cpp_type='std::uint64_t', default='0', group='EF_LAUNCH_REQUEST_FIELD'),
        Field(name='shooter', cpp_type='EngagementEntityRef', default='{}', group='EF_LAUNCH_REQUEST_FIELD'),
        Field(name='target_entity', cpp_type='EngagementEntityRef', default='{}', group='EF_LAUNCH_REQUEST_FIELD'),
        Field(name='has_target_entity', cpp_type='bool', default='false', group='EF_LAUNCH_REQUEST_FIELD'),
        Field(name='target_track_id', cpp_type='std::uint64_t', default='0', group='EF_LAUNCH_REQUEST_FIELD'),
        Field(name='has_target_track', cpp_type='bool', default='false', group='EF_LAUNCH_REQUEST_FIELD'),
        Field(name='station_id', cpp_type='std::string', default='{}', group='EF_LAUNCH_REQUEST_FIELD'),
        Field(name='mount_id', cpp_type='std::string', default='{}', group='EF_LAUNCH_REQUEST_FIELD'),
        Field(name='requested_munition_family', cpp_type='std::string', default='{}', group='EF_LAUNCH_REQUEST_FIELD'),
        Field(name='authority', cpp_type='std::string', default='"unspecified"', group='EF_LAUNCH_REQUEST_FIELD'),
        Field(name='requested_time_s', cpp_type='double', default='0.0', group='EF_LAUNCH_REQUEST_FIELD'),
        Field(name='merge_policy', cpp_type='std::string', default='"reject_on_conflict"', group='EF_LAUNCH_REQUEST_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
