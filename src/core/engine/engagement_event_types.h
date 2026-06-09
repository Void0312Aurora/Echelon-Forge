#pragma once

#include <vector>

#include "runtime/contracts/engagement_contracts.h"

struct RecentEngagementEvents {
    std::vector<LaunchEvent> launch_events;
    std::vector<EffectsEvent> effects_events;
    std::vector<NearestApproachEvent> nearest_approach_events;
    std::vector<FuzeEvaluationEvent> fuze_evaluation_events;
    std::vector<WarheadMechanismEvent> warhead_mechanism_events;
    std::vector<SpatialCoverageEvent> spatial_coverage_events;
    std::vector<ComponentLoadEvent> component_load_events;
    std::vector<ComponentDamageEvent> component_damage_events;
    std::vector<PlatformConsequenceEvent> platform_consequence_events;
    std::vector<StructuralBreakupEvent> structural_breakup_events;
    std::vector<LifecycleTransitionEvent> lifecycle_transition_events;
    std::vector<TrainingProjectionEvent> training_projection_events;
    std::vector<DamageReport> damage_reports;
    std::vector<DiagnosticsTrace> diagnostics_traces;
};
