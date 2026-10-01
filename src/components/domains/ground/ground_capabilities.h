#pragma once

#include <cmath>
#include <cstdint>

#include "components/domains/ground/tasking/ground_tasking_enums.h"

// Body regions of an individual infantry actor. The enumerator value is also
// the id of that region's box in the shared `HitboxConfig` compiled from the
// standing volumes, so the shared effects route and the Ground owner name the
// same region.
enum class GroundInfantryHitRegion : std::uint8_t {
    Head = 0,
    Torso = 1,
    Legs = 2,
};

inline constexpr GroundInfantryHitRegion kGroundInfantryHitRegions[] = {
    GroundInfantryHitRegion::Head,
    GroundInfantryHitRegion::Torso,
    GroundInfantryHitRegion::Legs,
};

[[nodiscard]] constexpr int ground_infantry_hit_region_hitbox_id(GroundInfantryHitRegion region) {
    return static_cast<int>(region);
}

[[nodiscard]] constexpr const char *ground_infantry_hit_region_name(GroundInfantryHitRegion region) {
    switch (region) {
    case GroundInfantryHitRegion::Head:
        return "head";
    case GroundInfantryHitRegion::Torso:
        return "torso";
    case GroundInfantryHitRegion::Legs:
        return "legs";
    }
    return "unknown";
}

// One authored axis-aligned body volume in the soldier's body frame, using the
// shared `damage_model.hitboxes` convention: `offset_*` is the box centre and
// `size_*` its full extent, in metres along [forward, right, up]. The origin is
// the ground contact point under the soldier's Transform; forward follows the
// entity heading and up is height above the terrain at that contact point.
// All zero means "not authored".
struct GroundInfantryHitVolume {
    double offset_forward_m = 0.0;
    double offset_right_m = 0.0;
    double offset_up_m = 0.0;
    double size_forward_m = 0.0;
    double size_right_m = 0.0;
    double size_up_m = 0.0;
};

[[nodiscard]] inline bool
ground_infantry_hit_volume_valid(const GroundInfantryHitVolume &volume) noexcept {
    const bool finite = std::isfinite(volume.offset_forward_m) &&
                        std::isfinite(volume.offset_right_m) && std::isfinite(volume.offset_up_m) &&
                        std::isfinite(volume.size_forward_m) && std::isfinite(volume.size_right_m) &&
                        std::isfinite(volume.size_up_m);
    // A body volume has positive extent on every axis and does not reach below
    // the terrain surface it stands on.
    return finite && volume.size_forward_m > 0.0 && volume.size_right_m > 0.0 &&
           volume.size_up_m > 0.0 && volume.offset_up_m - volume.size_up_m * 0.5 >= 0.0;
}

// Authored geometry above the local terrain surface for one infantry posture.
// `eye_height_m` is the observer/shooter sight point. `center_of_mass_height_m`
// is the torso aim height: a rifle holding on centre of mass aims at the torso
// volume's horizontal centre at this height. Zero means "not authored".
struct GroundInfantryPostureGeometry {
    double eye_height_m = 0.0;
    double center_of_mass_height_m = 0.0;
    GroundInfantryHitVolume head{};
    GroundInfantryHitVolume torso{};
    GroundInfantryHitVolume legs{};
};

[[nodiscard]] inline bool
ground_infantry_posture_geometry_valid(const GroundInfantryPostureGeometry &geometry) noexcept {
    return std::isfinite(geometry.eye_height_m) && geometry.eye_height_m > 0.0 &&
           std::isfinite(geometry.center_of_mass_height_m) &&
           geometry.center_of_mass_height_m > 0.0;
}

[[nodiscard]] inline const GroundInfantryHitVolume &
ground_infantry_hit_volume(const GroundInfantryPostureGeometry &geometry,
                           GroundInfantryHitRegion region) noexcept {
    switch (region) {
    case GroundInfantryHitRegion::Head:
        return geometry.head;
    case GroundInfantryHitRegion::Torso:
        return geometry.torso;
    case GroundInfantryHitRegion::Legs:
        return geometry.legs;
    }
    return geometry.torso;
}

// The posture's hit volumes are usable only when every region is authored and
// the authored centre-of-mass height lies inside the torso volume, so the torso
// aim point is a point of the torso.
[[nodiscard]] inline bool
ground_infantry_hit_volumes_valid(const GroundInfantryPostureGeometry &geometry) noexcept {
    for (const GroundInfantryHitRegion region : kGroundInfantryHitRegions) {
        if (!ground_infantry_hit_volume_valid(ground_infantry_hit_volume(geometry, region))) {
            return false;
        }
    }
    const double torso_bottom = geometry.torso.offset_up_m - geometry.torso.size_up_m * 0.5;
    const double torso_top = geometry.torso.offset_up_m + geometry.torso.size_up_m * 0.5;
    return geometry.center_of_mass_height_m >= torso_bottom &&
           geometry.center_of_mass_height_m <= torso_top;
}

// Authored content capability for entities that represent an individual
// dismounted infantry actor.  Ground type alone is intentionally insufficient:
// aggregates such as platoons may be Ground without owning the infantry
// movement or weapon slices. The posture geometry and hit volumes are unit
// content (`ground_infantry_posture`); the current values are labelled
// `engineering_proxy` in the unit JSON and are not calibrated anthropometry.
struct GroundInfantryCapability {
    GroundInfantryPostureGeometry stand{};
    GroundInfantryPostureGeometry crouch{};
    GroundInfantryPostureGeometry prone{};
};

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

[[nodiscard]] inline bool
ground_infantry_capability_hit_volumes_valid(const GroundInfantryCapability &capability) noexcept {
    return ground_infantry_hit_volumes_valid(capability.stand) &&
           ground_infantry_hit_volumes_valid(capability.crouch) &&
           ground_infantry_hit_volumes_valid(capability.prone);
}
