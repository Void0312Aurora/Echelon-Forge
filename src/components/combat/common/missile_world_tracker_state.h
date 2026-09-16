#pragma once

#include <cstdint>
#include <limits>

#include "components/basic/common.h"

namespace missile_guidance {

// This value type is embedded by Missile and therefore belongs to the
// components-visible state boundary. Tracker update and propagation logic
// remains in models/weapons/world_cv_alpha_beta_tracker.h.
struct WorldCvAlphaBetaTrackerState {
    bool position_valid = false;
    bool velocity_valid = false;
    std::uint32_t accepted_measurement_count = 0;

    Math::Vector3 corrected_position_world_m{};
    Math::Vector3 corrected_velocity_world_mps{};
    Math::Vector3 last_measurement_position_world_m{};
    Math::Vector3 first_measurement_position_world_m{};
    Math::Vector3 last_prediction_position_world_m{};
    Math::Vector3 last_residual_world_m{};

    double correction_time_s = 0.0;
    double first_measurement_time_s = -std::numeric_limits<double>::infinity();
    double last_measurement_time_s = -std::numeric_limits<double>::infinity();
    double last_update_dt_s = 0.0;
};

} // namespace missile_guidance
