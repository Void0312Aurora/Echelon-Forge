#pragma once

#include <cmath>

#include "components/domains/ground/tasking/ground_tasking_enums.h"

// Authored heights above the local terrain surface for one infantry posture.
// `eye_height_m` is the observer/shooter sight point; `center_of_mass_height_m`
// is the point a direct-fire sight line is drawn to while the rifle hit remains
// the synthetic body-center bootstrap. Zero means "not authored".
struct GroundInfantryPostureGeometry {
    double eye_height_m = 0.0;
    double center_of_mass_height_m = 0.0;
};

// Authored content capability for entities that represent an individual
// dismounted infantry actor.  Ground type alone is intentionally insufficient:
// aggregates such as platoons may be Ground without owning the infantry
// movement or weapon slices. The posture geometry is unit content
// (`ground_infantry_posture`); the current values are labelled
// `engineering_proxy` in the unit JSON and are not calibrated anthropometry.
struct GroundInfantryCapability {
    GroundInfantryPostureGeometry stand{};
    GroundInfantryPostureGeometry crouch{};
    GroundInfantryPostureGeometry prone{};
};

[[nodiscard]] inline bool
ground_infantry_posture_geometry_valid(const GroundInfantryPostureGeometry &geometry) noexcept {
    return std::isfinite(geometry.eye_height_m) && geometry.eye_height_m > 0.0 &&
           std::isfinite(geometry.center_of_mass_height_m) &&
           geometry.center_of_mass_height_m > 0.0;
}

// Returns nullptr for an unknown stance or unauthored geometry, so a consumer
// can fail closed instead of substituting a height.
[[nodiscard]] inline const GroundInfantryPostureGeometry *
ground_infantry_posture_geometry(const GroundInfantryCapability &capability,
                                 GroundStance stance) noexcept {
    const GroundInfantryPostureGeometry *geometry = nullptr;
    switch (stance) {
    case GroundStance::Stand:
        geometry = &capability.stand;
        break;
    case GroundStance::Crouch:
        geometry = &capability.crouch;
        break;
    case GroundStance::Prone:
        geometry = &capability.prone;
        break;
    }
    return geometry != nullptr && ground_infantry_posture_geometry_valid(*geometry) ? geometry
                                                                                    : nullptr;
}
