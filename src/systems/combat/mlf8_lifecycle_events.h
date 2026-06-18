#pragma once

#include "components/combat/structural_failure.h"
#include "components/systems/logistics.h"
#include "core/interfaces/engagement_event_recorder.h"
#include "runtime/contracts/engagement_contracts.h"

#include <cstdint>
#include <string>
#include <utility>

#include <flecs.h>

namespace mlf8_lifecycle {

inline bool is_terminal_wreck_lifecycle(GroundImpactLifecycle lifecycle) {
    return lifecycle == GroundImpactLifecycle::CrashedWreck ||
           lifecycle == GroundImpactLifecycle::DebrisFragmentResidue;
}

inline const char *ground_lifecycle_name(GroundImpactLifecycle lifecycle) {
    switch (lifecycle) {
    case GroundImpactLifecycle::CrashedWreck:
        return "crashed_wreck";
    case GroundImpactLifecycle::DebrisFragmentResidue:
        return "debris_fragment_residue";
    case GroundImpactLifecycle::LandedAirframe:
        return "landed_airframe";
    case GroundImpactLifecycle::None:
        break;
    }
    return "none";
}

inline void record_terminal_wreck_lifecycle_for_event(flecs::entity entity,
                                                      IEngagementEventRecorder *recorder,
                                                      GroundImpactLifecycle lifecycle,
                                                      double source_time_s,
                                                      std::uint64_t parent_event_id) {
    if (!recorder || !is_terminal_wreck_lifecycle(lifecycle) || parent_event_id == 0) {
        return;
    }

    LifecycleTransitionEvent event{};
    event.header.source_time_s = source_time_s;
    event.header.confidence = 1.0;
    event.header.reason = "generic_research_terminal_wreck_lifecycle_projection";
    event.header.producer_node_id = "damage_system.ground_lifecycle";
    event.header.consumer_visibility = std::string(kLethalityConsumerVisibilityDiagnosticsOnly);
    event.lifecycle_from = "lost_airframe_observable";
    event.lifecycle_to = "ground_crashed_wreck";
    event.ground_lifecycle = ground_lifecycle_name(lifecycle);
    event.debris_count = 0;
    event.terminal = true;
    event.terminal_projection_id = parent_event_id;

    (void)recorder->record_lifecycle_transition_event({
        .target_id = static_cast<std::uint64_t>(entity.id()),
        .parent_event_id = parent_event_id,
        .event = std::move(event),
    });
}

inline void record_terminal_wreck_lifecycle(flecs::entity entity,
                                            IEngagementEventRecorder *recorder,
                                            GroundImpactLifecycle lifecycle,
                                            double source_time_s) {
    if (!recorder || !is_terminal_wreck_lifecycle(lifecycle)) {
        return;
    }
    const StructuralBreakupState *breakup = entity.get<StructuralBreakupState>();
    if (!breakup || breakup->last_breakup_event_id == 0) {
        return;
    }
    record_terminal_wreck_lifecycle_for_event(entity, recorder, lifecycle, source_time_s,
                                             breakup->last_breakup_event_id);
}

} // namespace mlf8_lifecycle
