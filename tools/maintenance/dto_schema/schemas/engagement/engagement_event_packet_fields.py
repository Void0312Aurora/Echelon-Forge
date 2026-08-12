"""Declarative DTO schema for EngagementEventPacket fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of EngagementEventPacket fields.\n'
    '//\n'
    '// Consumers define EF_ENGAGEMENT_EVENT_PACKET_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_ENGAGEMENT_EVENT_PACKET_FIELD\n'
)


SCHEMA = DtoSchema(
    name='engagement_event_packet',
    output_path='src/runtime/facade/detail/batch/engagement_event_packet.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='snapshot_version', cpp_type='std::uint64_t', default='0', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='barrier_id', cpp_type='std::string', default='"export"', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='barrier_sequence', cpp_type='std::uint64_t', default='0', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='barrier_detail', cpp_type='std::string', default='"maintained_facade_export"', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='source_time_s', cpp_type='double', default='0.0', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='producer_node_id', cpp_type='std::string', default='{}', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='packet_provenance', cpp_type='InformationStateSource', default='make_information_state_source(kPolicyInformationStateTrackState, kPolicySourceLabelTrackStatePacket, kPolicyMaintainedStatusMaintained)', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='diagnostics_provenance', cpp_type='InformationStateSource', default='make_information_state_source(kPolicyInformationStateDecisionBelief, kPolicySourceLabelWorldTruthDiagnostics, kPolicyMaintainedStatusDiagnosticsOnly)', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='refs', cpp_type='std::vector<EngagementEntityRef>', default='{}', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='trace_ids', cpp_type='std::vector<std::uint64_t>', default='{}', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='track_packets', cpp_type='std::vector<TrackPacket>', default='{}', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='launch_requests', cpp_type='std::vector<LaunchRequest>', default='{}', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='launch_events', cpp_type='std::vector<LaunchEvent>', default='{}', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='munition_lifecycle_packets', cpp_type='std::vector<MunitionLifecyclePacket>', default='{}', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='effects_events', cpp_type='std::vector<EffectsEvent>', default='{}', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='nearest_approach_events', cpp_type='std::vector<NearestApproachEvent>', default='{}', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='fuze_evaluation_events', cpp_type='std::vector<FuzeEvaluationEvent>', default='{}', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='warhead_mechanism_events', cpp_type='std::vector<WarheadMechanismEvent>', default='{}', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='spatial_coverage_events', cpp_type='std::vector<SpatialCoverageEvent>', default='{}', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='component_load_events', cpp_type='std::vector<ComponentLoadEvent>', default='{}', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='component_damage_events', cpp_type='std::vector<ComponentDamageEvent>', default='{}', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='platform_consequence_events', cpp_type='std::vector<PlatformConsequenceEvent>', default='{}', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='structural_breakup_events', cpp_type='std::vector<StructuralBreakupEvent>', default='{}', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='lifecycle_transition_events', cpp_type='std::vector<LifecycleTransitionEvent>', default='{}', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='training_projection_events', cpp_type='std::vector<TrainingProjectionEvent>', default='{}', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='damage_reports', cpp_type='std::vector<DamageReport>', default='{}', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
        Field(name='diagnostics_traces', cpp_type='std::vector<DiagnosticsTrace>', default='{}', group='EF_ENGAGEMENT_EVENT_PACKET_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
