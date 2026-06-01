#pragma once

#include <vector>

#include "runtime/contracts/engagement_contracts.h"

struct RecentEngagementEvents {
    std::vector<LaunchEvent> launch_events;
    std::vector<EffectsEvent> effects_events;
    std::vector<DamageReport> damage_reports;
    std::vector<DiagnosticsTrace> diagnostics_traces;
};
