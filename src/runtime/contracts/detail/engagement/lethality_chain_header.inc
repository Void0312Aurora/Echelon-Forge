// X-macro list of LethalityChainHeader fields.
//
// Consumers define EF_LETHALITY_CHAIN_HEADER_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_LETHALITY_CHAIN_HEADER_FIELD(std::uint32_t, schema_version, kLethalityChainContractSchemaVersion)
EF_LETHALITY_CHAIN_HEADER_FIELD(std::uint64_t, chain_id, 0)
EF_LETHALITY_CHAIN_HEADER_FIELD(std::uint64_t, event_id, 0)
EF_LETHALITY_CHAIN_HEADER_FIELD(std::uint64_t, parent_event_id, 0)
EF_LETHALITY_CHAIN_HEADER_FIELD(std::string, stage, "unknown")
EF_LETHALITY_CHAIN_HEADER_FIELD(std::string, status, "not_evaluated")
EF_LETHALITY_CHAIN_HEADER_FIELD(std::string, reason, {})
EF_LETHALITY_CHAIN_HEADER_FIELD(double, source_time_s, 0.0)
EF_LETHALITY_CHAIN_HEADER_FIELD(std::uint64_t, source_frame, 0)
EF_LETHALITY_CHAIN_HEADER_FIELD(EngagementEntityRef, munition, {})
EF_LETHALITY_CHAIN_HEADER_FIELD(EngagementEntityRef, shooter, {})
EF_LETHALITY_CHAIN_HEADER_FIELD(EngagementEntityRef, target, {})
EF_LETHALITY_CHAIN_HEADER_FIELD(std::string, producer_node_id, {})
EF_LETHALITY_CHAIN_HEADER_FIELD(std::string, fidelity_mode, "unspecified")
EF_LETHALITY_CHAIN_HEADER_FIELD(std::string, evidence_level, "uncalibrated")
EF_LETHALITY_CHAIN_HEADER_FIELD(std::string, observation_mode, std::string(kLethalityObservationModeSampledRuntime))
EF_LETHALITY_CHAIN_HEADER_FIELD(std::string, consumer_visibility, std::string(kLethalityConsumerVisibilityDiagnosticsAndTraining))
EF_LETHALITY_CHAIN_HEADER_FIELD(double, confidence, 0.0)

#undef EF_LETHALITY_CHAIN_HEADER_FIELD
