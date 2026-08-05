// X-macro list of ObservationBatchPacket fields.
//
// Consumers define EF_OBSERVATION_BATCH_PACKET_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_OBSERVATION_BATCH_PACKET_FIELD(std::uint64_t, snapshot_version, 0)
EF_OBSERVATION_BATCH_PACKET_FIELD(std::string, barrier_id, "export")
EF_OBSERVATION_BATCH_PACKET_FIELD(double, source_time_s, 0.0)
EF_OBSERVATION_BATCH_PACKET_FIELD(InformationStateSource, provenance, make_information_state_source(kPolicyInformationStateAgentObservation, kPolicySourceLabelFacadeObservationPacket, kPolicyMaintainedStatusMaintained))
EF_OBSERVATION_BATCH_PACKET_FIELD(std::vector<WorldEntityRef>, refs, {})
EF_OBSERVATION_BATCH_PACKET_FIELD(std::vector<AgentObservation>, agent_observations, {})
EF_OBSERVATION_BATCH_PACKET_FIELD(std::vector<InstrumentState>, instrument_states, {})

#undef EF_OBSERVATION_BATCH_PACKET_FIELD
