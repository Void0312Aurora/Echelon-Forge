// X-macro list of RecentEngagementEvents fields.
//
// Consumers define EF_RECENT_ENGAGEMENT_EVENTS_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd
// here after expansion.

EF_RECENT_ENGAGEMENT_EVENTS_FIELD(std::vector<LaunchEvent>, launch_events, {})
EF_RECENT_ENGAGEMENT_EVENTS_FIELD(std::vector<EffectsEvent>, effects_events, {})
EF_RECENT_ENGAGEMENT_EVENTS_FIELD(std::vector<NearestApproachEvent>, nearest_approach_events, {})
EF_RECENT_ENGAGEMENT_EVENTS_FIELD(std::vector<FuzeEvaluationEvent>, fuze_evaluation_events, {})
EF_RECENT_ENGAGEMENT_EVENTS_FIELD(std::vector<WarheadMechanismEvent>, warhead_mechanism_events, {})
EF_RECENT_ENGAGEMENT_EVENTS_FIELD(std::vector<SpatialCoverageEvent>, spatial_coverage_events, {})
EF_RECENT_ENGAGEMENT_EVENTS_FIELD(std::vector<ComponentLoadEvent>, component_load_events, {})
EF_RECENT_ENGAGEMENT_EVENTS_FIELD(std::vector<ComponentDamageEvent>, component_damage_events, {})
EF_RECENT_ENGAGEMENT_EVENTS_FIELD(std::vector<PlatformConsequenceEvent>, platform_consequence_events, {})
EF_RECENT_ENGAGEMENT_EVENTS_FIELD(std::vector<StructuralBreakupEvent>, structural_breakup_events, {})
EF_RECENT_ENGAGEMENT_EVENTS_FIELD(std::vector<LifecycleTransitionEvent>, lifecycle_transition_events, {})
EF_RECENT_ENGAGEMENT_EVENTS_FIELD(std::vector<TrainingProjectionEvent>, training_projection_events, {})
EF_RECENT_ENGAGEMENT_EVENTS_FIELD(std::vector<DamageReport>, damage_reports, {})
EF_RECENT_ENGAGEMENT_EVENTS_FIELD(std::vector<DiagnosticsTrace>, diagnostics_traces, {})

#undef EF_RECENT_ENGAGEMENT_EVENTS_FIELD
