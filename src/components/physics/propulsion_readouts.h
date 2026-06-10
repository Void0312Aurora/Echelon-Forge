#pragma once

#include <algorithm>

#include "components/physics/dynamics.h"

namespace propulsion_readouts {

inline double fuel_flow_kg_per_s(
    const Propulsion& propulsion,
    double mil_power_flow_rate = 0.0,
    double ab_flow_rate_multiplier = 1.0
) {
    const double thrust_n = std::max(0.0, propulsion.current_thrust_n);
    const double tsfc_nh = std::max(0.0, propulsion.current_tsfc);
    if (thrust_n > 0.0 && tsfc_nh > 0.0) {
        return (thrust_n * tsfc_nh) / 3600.0;
    }
    if (mil_power_flow_rate <= 0.0) {
        return 0.0;
    }
    const double throttle_state =
        std::clamp(std::max(propulsion.throttle_state, propulsion.throttle_command), 0.0, 1.0);
    const double ab_state = std::clamp(propulsion.ab_state, 0.0, 1.0);
    const double dry_flow_rate = mil_power_flow_rate * (0.1 + (0.9 * throttle_state));
    const double ab_multiplier = std::max(1.0, ab_flow_rate_multiplier);
    return dry_flow_rate * (1.0 + ((ab_multiplier - 1.0) * ab_state));
}

inline double engine_rpm_pct(const Propulsion& propulsion) {
    const double throttle_state = std::clamp(propulsion.throttle_state, 0.0, 1.0);
    const double ab_state = std::clamp(propulsion.ab_state, 0.0, 1.0);
    return (throttle_state * 100.0) + (ab_state * 10.0);
}

}  // namespace propulsion_readouts
