#pragma once

#include <string>
#include <vector>

// Internal helper split for runtime_window_coordinator.h.
// Include this companion after RuntimeWindowCoordinatorCallbacks is declared.

inline std::vector<std::string> runtime_window_collect_missing_export_callbacks(
    const RuntimeWindowRequest& request,
    const RuntimeWindowCoordinatorCallbacks& callbacks
) {
    std::vector<std::string> missing_callbacks;
    if (request.export_observation && !callbacks.export_observation_packet) {
        missing_callbacks.push_back("observation");
    }
    if (request.export_engagement && !callbacks.export_engagement_event_packet) {
        missing_callbacks.push_back("engagement");
    }
    if (request.export_diagnostics && !callbacks.export_diagnostics_traces) {
        missing_callbacks.push_back("diagnostics");
    }
    return missing_callbacks;
}

inline std::string runtime_window_export_snapshot_evidence(
    const RuntimeWindowResult& result
) {
    if (result.observation_packet.snapshot_version != 0) {
        return "observation_packet:" +
            std::to_string(result.observation_packet.snapshot_version);
    }
    if (result.engagement_packet.snapshot_version != 0) {
        return "engagement_packet:" +
            std::to_string(result.engagement_packet.snapshot_version);
    }
    return {};
}
