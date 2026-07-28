"""Declarative DTO schema for TaskingBatchPacket fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of TaskingBatchPacket fields.\n'
    '//\n'
    '// Consumers define EF_TASKING_BATCH_PACKET_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_TASKING_BATCH_PACKET_FIELD\n'
)


SCHEMA = DtoSchema(
    name='tasking_batch_packet',
    output_path='src/runtime/facade/detail/tasking_batch_packet.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='snapshot_version', cpp_type='std::uint64_t', default='0', group='EF_TASKING_BATCH_PACKET_FIELD'),
        Field(name='barrier_id', cpp_type='std::string', default='"tasking_export"', group='EF_TASKING_BATCH_PACKET_FIELD'),
        Field(name='source_time_s', cpp_type='double', default='0.0', group='EF_TASKING_BATCH_PACKET_FIELD'),
        Field(name='provenance', cpp_type='InformationStateSource', default='make_information_state_source(kPolicyInformationStateDecisionBelief, "facade_tasking_packet", kPolicyMaintainedStatusAdapterProjection)', group='EF_TASKING_BATCH_PACKET_FIELD'),
        Field(name='refs', cpp_type='std::vector<WorldEntityRef>', default='{}', group='EF_TASKING_BATCH_PACKET_FIELD'),
        Field(name='mission_command_contracts', cpp_type='std::vector<MissionCommandMaintainedBatchContract>', default='{}', group='EF_TASKING_BATCH_PACKET_FIELD'),
        Field(name='task_order_contracts', cpp_type='std::vector<TaskOrderMaintainedBatchContract>', default='{}', group='EF_TASKING_BATCH_PACKET_FIELD'),
        Field(name='leader_intent_contracts', cpp_type='std::vector<LeaderIntentMaintainedBatchContract>', default='{}', group='EF_TASKING_BATCH_PACKET_FIELD'),
        Field(name='pilot_report_contracts', cpp_type='std::vector<PilotReportMaintainedBatchContract>', default='{}', group='EF_TASKING_BATCH_PACKET_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
