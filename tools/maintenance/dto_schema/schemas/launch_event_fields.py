"""Declarative DTO schema for LaunchEvent fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of LaunchEvent fields.\n'
    '//\n'
    '// Consumers define EF_LAUNCH_EVENT_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_LAUNCH_EVENT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='launch_event',
    output_path='src/runtime/contracts/detail/launch_event.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='event_id', cpp_type='std::uint64_t', default='0', group='EF_LAUNCH_EVENT_FIELD'),
        Field(name='request_id', cpp_type='std::uint64_t', default='0', group='EF_LAUNCH_EVENT_FIELD'),
        Field(name='accepted', cpp_type='bool', default='false', group='EF_LAUNCH_EVENT_FIELD'),
        Field(name='rejection_reason', cpp_type='std::string', default='{}', group='EF_LAUNCH_EVENT_FIELD'),
        Field(name='selected_launcher', cpp_type='std::string', default='{}', group='EF_LAUNCH_EVENT_FIELD'),
        Field(name='selected_munition', cpp_type='std::string', default='{}', group='EF_LAUNCH_EVENT_FIELD'),
        Field(name='ammo_delta', cpp_type='int', default='0', group='EF_LAUNCH_EVENT_FIELD'),
        Field(name='cooldown_delta_s', cpp_type='double', default='0.0', group='EF_LAUNCH_EVENT_FIELD'),
        Field(name='spawned_munition', cpp_type='EngagementEntityRef', default='{}', group='EF_LAUNCH_EVENT_FIELD'),
        Field(name='has_spawned_munition', cpp_type='bool', default='false', group='EF_LAUNCH_EVENT_FIELD'),
        Field(name='event_time_s', cpp_type='double', default='0.0', group='EF_LAUNCH_EVENT_FIELD'),
        Field(name='producer_node_id', cpp_type='std::string', default='{}', group='EF_LAUNCH_EVENT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
