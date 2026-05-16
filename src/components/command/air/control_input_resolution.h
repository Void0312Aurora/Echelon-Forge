#pragma once

#include <algorithm>

#include "components/command/legacy_command.h"
#include "components/command/pilot_action.h"

struct ResolvedGroundControlInput {
    bool throttle_idle = false;
    double brake_amount = 0.0;
};

inline const PilotAction* active_pilot_action(const PilotAction* pilot) {
    return (pilot && pilot->active) ? pilot : nullptr;
}

inline const MovementCommand* active_legacy_movement_command(const MovementCommand* legacy) {
    return (legacy && legacy->active) ? legacy : nullptr;
}

inline double resolved_pilot_or_legacy_throttle(
    const PilotAction* pilot,
    const MovementCommand* legacy,
    double fallback_throttle = 0.0
) {
    if (const PilotAction* active_pilot = active_pilot_action(pilot)) {
        return std::clamp(active_pilot->throttle, 0.0, 1.0);
    }
    if (const MovementCommand* active_legacy = active_legacy_movement_command(legacy)) {
        return std::clamp(active_legacy->throttle_cmd, 0.0, 1.0);
    }
    return std::clamp(fallback_throttle, 0.0, 1.0);
}

inline ResolvedGroundControlInput resolve_pilot_or_legacy_ground_control(
    const PilotAction* pilot,
    const MovementCommand* legacy
) {
    ResolvedGroundControlInput out;
    if (const PilotAction* active_pilot = active_pilot_action(pilot)) {
        out.throttle_idle = (active_pilot->throttle < 0.01);
        out.brake_amount = std::clamp(active_pilot->brake, 0.0, 1.0);
        if (active_pilot->brake_left || active_pilot->brake_right) {
            out.brake_amount = 1.0;
        }
        return out;
    }
    if (const MovementCommand* active_legacy = active_legacy_movement_command(legacy)) {
        out.throttle_idle = (active_legacy->throttle_cmd < 0.01);
        if (out.throttle_idle) {
            out.brake_amount = 1.0;
        }
    }
    return out;
}
