// X-macro list of EngagementEventPacket fields.
//
// Consumers define EF_ENGAGEMENT_EVENT_PACKET_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::uint64_t, snapshot_version, 0)
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::string, barrier_id, "export")
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::uint64_t, barrier_sequence, 0)
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::string, barrier_detail, "maintained_facade_export")
EF_ENGAGEMENT_EVENT_PACKET_FIELD(double, source_time_s, 0.0)
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::string, producer_node_id, {})
EF_ENGAGEMENT_EVENT_PACKET_FIELD(InformationStateSource, packet_provenance, make_information_state_source(kPolicyInformationStateTrackState, kPolicySourceLabelTrackStatePacket, kPolicyMaintainedStatusMaintained))
EF_ENGAGEMENT_EVENT_PACKET_FIELD(InformationStateSource, diagnostics_provenance, make_information_state_source(kPolicyInformationStateDecisionBelief, kPolicySourceLabelWorldTruthDiagnostics, kPolicyMaintainedStatusDiagnosticsOnly))
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::vector<EngagementEntityRef>, refs, {})
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::vector<std::uint64_t>, trace_ids, {})
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::vector<TrackPacket>, track_packets, {})
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::vector<LaunchRequest>, launch_requests, {})
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::vector<LaunchEvent>, launch_events, {})
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::vector<MunitionLifecyclePacket>, munition_lifecycle_packets, {})
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::vector<EffectsEvent>, effects_events, {})
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::vector<NearestApproachEvent>, nearest_approach_events, {})
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::vector<FuzeEvaluationEvent>, fuze_evaluation_events, {})
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::vector<WarheadMechanismEvent>, warhead_mechanism_events, {})
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::vector<SpatialCoverageEvent>, spatial_coverage_events, {})
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::vector<ComponentLoadEvent>, component_load_events, {})
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::vector<ComponentDamageEvent>, component_damage_events, {})
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::vector<PlatformConsequenceEvent>, platform_consequence_events, {})
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::vector<StructuralBreakupEvent>, structural_breakup_events, {})
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::vector<LifecycleTransitionEvent>, lifecycle_transition_events, {})
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::vector<TrainingProjectionEvent>, training_projection_events, {})
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::vector<DamageReport>, damage_reports, {})
EF_ENGAGEMENT_EVENT_PACKET_FIELD(std::vector<DiagnosticsTrace>, diagnostics_traces, {})

#undef EF_ENGAGEMENT_EVENT_PACKET_FIELD
