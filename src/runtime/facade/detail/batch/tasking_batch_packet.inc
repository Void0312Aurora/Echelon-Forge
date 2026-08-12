// X-macro list of TaskingBatchPacket fields.
//
// Consumers define EF_TASKING_BATCH_PACKET_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_TASKING_BATCH_PACKET_FIELD(std::uint64_t, snapshot_version, 0)
EF_TASKING_BATCH_PACKET_FIELD(std::string, barrier_id, "tasking_export")
EF_TASKING_BATCH_PACKET_FIELD(double, source_time_s, 0.0)
EF_TASKING_BATCH_PACKET_FIELD(InformationStateSource, provenance, make_information_state_source(kPolicyInformationStateDecisionBelief, "facade_tasking_packet", kPolicyMaintainedStatusAdapterProjection))
EF_TASKING_BATCH_PACKET_FIELD(std::vector<WorldEntityRef>, refs, {})
EF_TASKING_BATCH_PACKET_FIELD(std::vector<MissionCommandMaintainedBatchContract>, mission_command_contracts, {})
EF_TASKING_BATCH_PACKET_FIELD(std::vector<TaskOrderMaintainedBatchContract>, task_order_contracts, {})
EF_TASKING_BATCH_PACKET_FIELD(std::vector<LeaderIntentMaintainedBatchContract>, leader_intent_contracts, {})
EF_TASKING_BATCH_PACKET_FIELD(std::vector<PilotReportMaintainedBatchContract>, pilot_report_contracts, {})

#undef EF_TASKING_BATCH_PACKET_FIELD
