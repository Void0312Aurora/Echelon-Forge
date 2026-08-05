"""Declarative DTO schema for MunitionLifecyclePacket fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of MunitionLifecyclePacket fields.\n'
    '//\n'
    '// Consumers define EF_MUNITION_LIFECYCLE_PACKET_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_MUNITION_LIFECYCLE_PACKET_FIELD\n'
)


SCHEMA = DtoSchema(
    name='munition_lifecycle_packet',
    output_path='src/runtime/contracts/detail/engagement/munition_lifecycle_packet.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='packet_id', cpp_type='std::uint64_t', default='0', group='EF_MUNITION_LIFECYCLE_PACKET_FIELD'),
        Field(name='munition', cpp_type='EngagementEntityRef', default='{}', group='EF_MUNITION_LIFECYCLE_PACKET_FIELD'),
        Field(name='attacker', cpp_type='EngagementEntityRef', default='{}', group='EF_MUNITION_LIFECYCLE_PACKET_FIELD'),
        Field(name='target_entity', cpp_type='EngagementEntityRef', default='{}', group='EF_MUNITION_LIFECYCLE_PACKET_FIELD'),
        Field(name='has_target_entity', cpp_type='bool', default='false', group='EF_MUNITION_LIFECYCLE_PACKET_FIELD'),
        Field(name='target_track_id', cpp_type='std::uint64_t', default='0', group='EF_MUNITION_LIFECYCLE_PACKET_FIELD'),
        Field(name='has_target_track', cpp_type='bool', default='false', group='EF_MUNITION_LIFECYCLE_PACKET_FIELD'),
        Field(name='launch_event_id', cpp_type='std::uint64_t', default='0', group='EF_MUNITION_LIFECYCLE_PACKET_FIELD'),
        Field(name='active', cpp_type='bool', default='false', group='EF_MUNITION_LIFECYCLE_PACKET_FIELD'),
        Field(name='seeker_mode', cpp_type='std::string', default='"unknown"', group='EF_MUNITION_LIFECYCLE_PACKET_FIELD'),
        Field(name='guidance_cadence_s', cpp_type='double', default='0.0', group='EF_MUNITION_LIFECYCLE_PACKET_FIELD'),
        Field(name='track_memory_state', cpp_type='std::string', default='"unknown"', group='EF_MUNITION_LIFECYCLE_PACKET_FIELD'),
        Field(name='fuel_remaining_fraction', cpp_type='double', default='0.0', group='EF_MUNITION_LIFECYCLE_PACKET_FIELD'),
        Field(name='burnout', cpp_type='bool', default='false', group='EF_MUNITION_LIFECYCLE_PACKET_FIELD'),
        Field(name='max_flight_time_s', cpp_type='double', default='0.0', group='EF_MUNITION_LIFECYCLE_PACKET_FIELD'),
        Field(name='fuze_state', cpp_type='std::string', default='"unknown"', group='EF_MUNITION_LIFECYCLE_PACKET_FIELD'),
        Field(name='source_time_s', cpp_type='double', default='0.0', group='EF_MUNITION_LIFECYCLE_PACKET_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
