"""Declarative DTO schema for ObservationBatchPacket fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of ObservationBatchPacket fields.\n'
    '//\n'
    '// Consumers define EF_OBSERVATION_BATCH_PACKET_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_OBSERVATION_BATCH_PACKET_FIELD\n'
)


SCHEMA = DtoSchema(
    name='observation_batch_packet',
    output_path='src/runtime/facade/detail/observation_batch_packet.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='snapshot_version', cpp_type='std::uint64_t', default='0', group='EF_OBSERVATION_BATCH_PACKET_FIELD'),
        Field(name='barrier_id', cpp_type='std::string', default='"export"', group='EF_OBSERVATION_BATCH_PACKET_FIELD'),
        Field(name='source_time_s', cpp_type='double', default='0.0', group='EF_OBSERVATION_BATCH_PACKET_FIELD'),
        Field(name='provenance', cpp_type='InformationStateSource', default='make_information_state_source(kPolicyInformationStateAgentObservation, kPolicySourceLabelFacadeObservationPacket, kPolicyMaintainedStatusMaintained)', group='EF_OBSERVATION_BATCH_PACKET_FIELD'),
        Field(name='refs', cpp_type='std::vector<WorldEntityRef>', default='{}', group='EF_OBSERVATION_BATCH_PACKET_FIELD'),
        Field(name='agent_observations', cpp_type='std::vector<AgentObservation>', default='{}', group='EF_OBSERVATION_BATCH_PACKET_FIELD'),
        Field(name='instrument_states', cpp_type='std::vector<InstrumentState>', default='{}', group='EF_OBSERVATION_BATCH_PACKET_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
