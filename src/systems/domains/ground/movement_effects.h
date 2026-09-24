#pragma once

#include <algorithm>
#include <cmath>

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

inline GroundMovementEffectObservation evaluate_movement_effects(
    const IEnvironmentModel::TerrainCell &terrain, double slope_deg, GroundStance stance) {
    GroundMovementEffectObservation observation;
    observation.surface = terrain.type;
    observation.slope_deg = slope_deg;
    observation.vegetation_density = terrain.vegetation_density;
    observation.surface_multiplier = surface_speed_multiplier(terrain.type);
    observation.slope_multiplier = slope_speed_multiplier(slope_deg);
    observation.vegetation_multiplier = vegetation_speed_multiplier(terrain.vegetation_density);
    observation.stance_multiplier = stance_speed_multiplier(stance);
    observation.combined_multiplier = observation.surface_multiplier * observation.slope_multiplier *
                                      observation.vegetation_multiplier * observation.stance_multiplier;
    return observation;
}

} // namespace ground_infantry_movement_detail
