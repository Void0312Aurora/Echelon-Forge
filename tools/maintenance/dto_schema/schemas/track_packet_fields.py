"""Declarative DTO schema for TrackPacket fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of TrackPacket fields.\n'
    '//\n'
    '// Consumers define EF_TRACK_PACKET_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_TRACK_PACKET_FIELD\n'
)


SCHEMA = DtoSchema(
    name='track_packet',
    output_path='src/runtime/contracts/detail/track_packet.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='track_id', cpp_type='std::uint64_t', default='0', group='EF_TRACK_PACKET_FIELD'),
        Field(name='correlated_entity', cpp_type='EngagementEntityRef', default='{}', group='EF_TRACK_PACKET_FIELD'),
        Field(name='has_correlated_entity', cpp_type='bool', default='false', group='EF_TRACK_PACKET_FIELD'),
        Field(name='correlation_policy', cpp_type='std::string', default='"unresolved"', group='EF_TRACK_PACKET_FIELD'),
        Field(name='source', cpp_type='std::string', default='{}', group='EF_TRACK_PACKET_FIELD'),
        Field(name='classification', cpp_type='std::string', default='"unknown"', group='EF_TRACK_PACKET_FIELD'),
        Field(name='status', cpp_type='std::string', default='"unknown"', group='EF_TRACK_PACKET_FIELD'),
        Field(name='quality', cpp_type='double', default='0.0', group='EF_TRACK_PACKET_FIELD'),
        Field(name='confidence', cpp_type='double', default='0.0', group='EF_TRACK_PACKET_FIELD'),
        Field(name='usable', cpp_type='bool', default='false', group='EF_TRACK_PACKET_FIELD'),
        Field(name='iff', cpp_type='std::string', default='"unknown"', group='EF_TRACK_PACKET_FIELD'),
        Field(name='source_time_s', cpp_type='double', default='0.0', group='EF_TRACK_PACKET_FIELD'),
        Field(name='update_age_s', cpp_type='double', default='0.0', group='EF_TRACK_PACKET_FIELD'),
        Field(name='snapshot_version', cpp_type='std::uint64_t', default='0', group='EF_TRACK_PACKET_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
