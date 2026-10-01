#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>

#include "components/domains/ground/tasking/ground_tasking_enums.h"
#include "core/interfaces/environment_model.h"

namespace ground_infantry_movement_detail {

inline double finite_nonnegative(double value) {
    return std::isfinite(value) ? std::max(0.0, value) : 0.0;
}

inline double surface_speed_multiplier(IEnvironmentModel::SurfaceType surface) {
    using Surface = IEnvironmentModel::SurfaceType;
    switch (surface) {
    case Surface::Concrete:
    case Surface::Asphalt:
        return 1.0;
    case Surface::HardPacked:
        return 0.90;
    case Surface::SoftDirt:
        return 0.75;
    case Surface::Water:
    case Surface::Obstacle:
        return 0.0;
    }
    return 0.0;
}

inline double slope_speed_multiplier(double slope) {
    if (!std::isfinite(slope) || slope < 0.0) {
        return 0.0;
    }
    return std::clamp(1.0 - slope / 60.0, 0.20, 1.0);
}

inline double vegetation_speed_multiplier(double density) {
    if (!std::isfinite(density) || density < 0.0) {
        return 0.0;
    }
    return std::clamp(1.0 - 0.25 * std::clamp(density, 0.0, 1.0), 0.50, 1.0);
}

inline double stance_speed_multiplier(GroundStance stance) {
    switch (stance) {
    case GroundStance::Stand:
        return 1.0;
    case GroundStance::Crouch:
        return 0.65;
    case GroundStance::Prone:
        return 0.35;
    }
    return 0.0;
}

struct GroundMovementEffectObservation {
    IEnvironmentModel::SurfaceType surface = IEnvironmentModel::SurfaceType::Obstacle;
    double slope_deg = 0.0;
    double vegetation_density = 1.0;
    double surface_multiplier = 0.0;
    double slope_multiplier = 0.0;
    double vegetation_multiplier = 0.0;
    double stance_multiplier = 0.0;
    double combined_multiplier = 0.0;
};

inline GroundMovementEffectObservation
evaluate_movement_effects(const IEnvironmentModel::TerrainCell &terrain, double slope_deg,
                          GroundStance stance) {
    GroundMovementEffectObservation observation;
    observation.surface = terrain.type;
    observation.slope_deg = slope_deg;
    observation.vegetation_density = terrain.vegetation_density;
    observation.surface_multiplier = surface_speed_multiplier(terrain.type);
    observation.slope_multiplier = slope_speed_multiplier(slope_deg);
    observation.vegetation_multiplier = vegetation_speed_multiplier(terrain.vegetation_density);
    observation.stance_multiplier = stance_speed_multiplier(stance);
    observation.combined_multiplier =
        observation.surface_multiplier * observation.slope_multiplier *
        observation.vegetation_multiplier * observation.stance_multiplier;
    return observation;
}

struct GroundTransitionMovementObservation {
    IEnvironmentModel::GroundTransitionObservation transition;
    double minimum_combined_multiplier = 0.0;
    double average_combined_multiplier = 0.0;
    std::uint32_t sample_count = 0;
};

// Samples the one-tick segment at 5 m spacing and reduces the stance-dependent
// multipliers. The environment owns only the domain-neutral point queries
// (terrain, slope, transition passability); the Ground movement cost built on them
// stays with this owner, so the shared IEnvironmentModel carries no Ground stance or
// cost semantics. Sample density comes from the segment geometry, not from the
// provider's transition answer, so a provider without transition support still gets
// a correctly sampled cost (its `transition` stays the provider default).
inline GroundTransitionMovementObservation
evaluate_transition_movement_effects(IEnvironmentModel &environment, double from_x, double from_y,
                                     double to_x, double to_y, GroundStance stance) {
    GroundTransitionMovementObservation observation;
    observation.transition =
        environment.get_ground_transition_observation(from_x, from_y, to_x, to_y);
    const double distance = std::hypot(to_x - from_x, to_y - from_y);
    const std::size_t sample_count =
        std::max<std::size_t>(1, static_cast<std::size_t>(std::ceil(distance / 5.0)));
    double multiplier_sum = 0.0;
    double multiplier_min = std::numeric_limits<double>::infinity();
    for (std::size_t index = 0; index <= sample_count; ++index) {
        const double fraction = static_cast<double>(index) / static_cast<double>(sample_count);
        const double x = from_x + (to_x - from_x) * fraction;
        const double y = from_y + (to_y - from_y) * fraction;
        // Terrain before slope, as the provider contract evaluated them before the
        // move; keeping the order explicit protects any caching provider.
        const auto terrain = environment.get_terrain_at(x, y);
        const double slope_deg = environment.get_ground_slope_deg(x, y);
        const auto effects = evaluate_movement_effects(terrain, slope_deg, stance);
        const double multiplier = finite_nonnegative(effects.combined_multiplier);
        multiplier_sum += multiplier;
        multiplier_min = std::min(multiplier_min, multiplier);
    }
    observation.sample_count = static_cast<std::uint32_t>(sample_count + 1);
    observation.minimum_combined_multiplier = std::isfinite(multiplier_min) ? multiplier_min : 0.0;
    observation.average_combined_multiplier =
        observation.sample_count > 0
            ? multiplier_sum / static_cast<double>(observation.sample_count)
            : 0.0;
    return observation;
}

} // namespace ground_infantry_movement_detail
