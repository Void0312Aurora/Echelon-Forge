"""Declarative DTO schema for RecentEngagementEvents fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RecentEngagementEvents fields.\n'
    '//\n'
    '// Consumers define EF_RECENT_ENGAGEMENT_EVENTS_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d\n'
    '// here after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RECENT_ENGAGEMENT_EVENTS_FIELD\n'
)


SCHEMA = DtoSchema(
    name='recent_engagement_events',
    output_path='src/core/engine/detail/recent_engagement_events.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='launch_events', cpp_type='std::vector<LaunchEvent>', default='{}', group='EF_RECENT_ENGAGEMENT_EVENTS_FIELD'),
        Field(name='effects_events', cpp_type='std::vector<EffectsEvent>', default='{}', group='EF_RECENT_ENGAGEMENT_EVENTS_FIELD'),
        Field(name='nearest_approach_events', cpp_type='std::vector<NearestApproachEvent>', default='{}', group='EF_RECENT_ENGAGEMENT_EVENTS_FIELD'),
        Field(name='fuze_evaluation_events', cpp_type='std::vector<FuzeEvaluationEvent>', default='{}', group='EF_RECENT_ENGAGEMENT_EVENTS_FIELD'),
        Field(name='warhead_mechanism_events', cpp_type='std::vector<WarheadMechanismEvent>', default='{}', group='EF_RECENT_ENGAGEMENT_EVENTS_FIELD'),
        Field(name='spatial_coverage_events', cpp_type='std::vector<SpatialCoverageEvent>', default='{}', group='EF_RECENT_ENGAGEMENT_EVENTS_FIELD'),
        Field(name='component_load_events', cpp_type='std::vector<ComponentLoadEvent>', default='{}', group='EF_RECENT_ENGAGEMENT_EVENTS_FIELD'),
        Field(name='component_damage_events', cpp_type='std::vector<ComponentDamageEvent>', default='{}', group='EF_RECENT_ENGAGEMENT_EVENTS_FIELD'),
        Field(name='platform_consequence_events', cpp_type='std::vector<PlatformConsequenceEvent>', default='{}', group='EF_RECENT_ENGAGEMENT_EVENTS_FIELD'),
        Field(name='structural_breakup_events', cpp_type='std::vector<StructuralBreakupEvent>', default='{}', group='EF_RECENT_ENGAGEMENT_EVENTS_FIELD'),
        Field(name='lifecycle_transition_events', cpp_type='std::vector<LifecycleTransitionEvent>', default='{}', group='EF_RECENT_ENGAGEMENT_EVENTS_FIELD'),
        Field(name='training_projection_events', cpp_type='std::vector<TrainingProjectionEvent>', default='{}', group='EF_RECENT_ENGAGEMENT_EVENTS_FIELD'),
        Field(name='damage_reports', cpp_type='std::vector<DamageReport>', default='{}', group='EF_RECENT_ENGAGEMENT_EVENTS_FIELD'),
        Field(name='diagnostics_traces', cpp_type='std::vector<DiagnosticsTrace>', default='{}', group='EF_RECENT_ENGAGEMENT_EVENTS_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
