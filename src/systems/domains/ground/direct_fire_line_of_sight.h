#pragma once

#include <cmath>
#include <cstdint>
#include <optional>

#include "components/basic/common.h"
#include "components/combat/common/damage_common.h"
#include "components/command/mission_command.h"
#include "components/domains/ground/ground_capabilities.h"
#include "core/interfaces/environment_model.h"
#include "systems/domains/ground/direct_fire_hit_volume.h"

// Ground consumer of the domain-neutral terrain line-of-sight query.
//
// The environment owns the geometry (terrain surface, raster sampling, and
// provenance). This owner decides which points the query is asked about and
// what a non-visible answer means for the bounded rifle. The shot runs from the
// shooter's authored eye height to an aim point on the target's authored hit
// volumes, each selected by that entity's commanded stance. The first volume
// the sight ray enters, unless terrain clips the ray before it, is the hit
// region. It does not model cover, concealment, dispersion, or ballistics.
namespace ground_direct_fire_detail {

enum class GroundDirectFireSightGate : std::uint8_t {
    Visible = 0,
    TerrainBlocked = 1,
    TerrainUnknown = 2,
    PostureUnknown = 3,
    EnvironmentUnavailable = 4,
    HitVolumesUnknown = 5,
    SharedHitboxMismatch = 6,
};

// The rifle holds on centre of mass first. When terrain masks that aim point
// it takes the remaining regions from the top of the body down, since a crest
// that masks the torso exposes the head before the legs.
inline constexpr GroundInfantryHitRegion kGroundDirectFireAimOrder[] = {
    GroundInfantryHitRegion::Torso,
    GroundInfantryHitRegion::Head,
    GroundInfantryHitRegion::Legs,
};

// One aimed point: the terrain answer for the sight line to it and, when the
// sight ray reaches the body before any terrain, the region it enters.
struct GroundDirectFireAimResolution {
    GroundInfantryHitRegion aimed_region = GroundInfantryHitRegion::Torso;
    GroundBodyPoint aim_point{};
    IEnvironmentModel::TerrainLineOfSightObservation terrain{};
    bool terrain_unknown = false;
    bool masked = true;
    GroundInfantryHitRegion hit_region = GroundInfantryHitRegion::Torso;
    // Midpoint of the sight ray's path through the entered volume, in the
    // target's body frame for the held stance. It lies inside that volume, so a
    // closed-box containment test resolves the same region after the frame
    // round trip; the entry point itself sits on the box boundary.
    GroundBodyPoint hit_point{};
};

struct GroundDirectFireSightObservation {
    GroundDirectFireSightGate gate = GroundDirectFireSightGate::EnvironmentUnavailable;
    GroundStance shooter_stance = GroundStance::Stand;
    GroundStance target_stance = GroundStance::Stand;
    double shooter_eye_height_m = 0.0;
    double target_aim_height_m = 0.0;
    std::uint32_t masked_aim_count = 0;
    GroundInfantryHitRegion aimed_region = GroundInfantryHitRegion::Torso;
    GroundInfantryHitRegion hit_region = GroundInfantryHitRegion::Torso;
    GroundBodyPoint hit_point{};
    IEnvironmentModel::TerrainLineOfSightObservation terrain{};
};

// The posture an entity holds is its last commanded Ground stance. An entity
// that was never commanded holds the maintained command DTO's default stance,
// so this introduces no posture of its own.
[[nodiscard]] inline GroundStance held_ground_stance(const MissionCommand *command) noexcept {
    return command != nullptr ? command->stance : MissionCommandGround{}.stance;
}

// Resolves one aim point. The terrain query takes heights above the local
// terrain at each endpoint, while the body frame's up axis is above the terrain
// at the target's contact point, so the aim height is re-expressed at the aim
// point's own horizontal position.
[[nodiscard]] inline GroundDirectFireAimResolution
resolve_ground_direct_fire_aim(IEnvironmentModel &environment, const Transform &shooter,
                               double shooter_eye_height_m, const Transform &target,
                               const GroundInfantryPostureGeometry &target_posture,
                               GroundInfantryHitRegion aimed_region) {
    GroundDirectFireAimResolution resolution;
    resolution.aimed_region = aimed_region;
    resolution.aim_point = ground_direct_fire_aim_point(target_posture, aimed_region);
    const GroundWorldOffset aim_offset = upright_body_to_world_offset(
        target.heading, resolution.aim_point.forward_m, resolution.aim_point.right_m);
    const double aim_x = target.x + aim_offset.east_m;
    const double aim_y = target.y + aim_offset.north_m;
    const double aim_height_above_local_terrain =
        environment.get_terrain_elevation(target.x, target.y) + resolution.aim_point.up_m -
        environment.get_terrain_elevation(aim_x, aim_y);
    if (!std::isfinite(aim_height_above_local_terrain)) {
        resolution.terrain_unknown = true;
        return resolution;
    }
    // An aim point below the terrain at its own position is buried and masked.
    // The query is still asked about the surface there, so an unmeasured
    // surface reads unknown rather than masked.
    const bool buried = aim_height_above_local_terrain < 0.0;
    resolution.terrain = environment.get_terrain_line_of_sight_observation(
        shooter.x, shooter.y, shooter_eye_height_m, aim_x, aim_y,
        buried ? 0.0 : aim_height_above_local_terrain);
    if (resolution.terrain.status == IEnvironmentModel::TerrainLineOfSightStatus::Unknown) {
        resolution.terrain_unknown = true;
        return resolution;
    }
    if (buried) {
        return resolution;
    }

    // The sight ray in the target's body frame, built from the query's own
    // absolute endpoint heights.
    const double contact_absolute_height_m =
        resolution.terrain.to_absolute_height_m - resolution.aim_point.up_m;
    GroundBodyPoint eye =
        world_offset_to_upright_body(target.heading, shooter.x - target.x, shooter.y - target.y);
    eye.up_m = resolution.terrain.from_absolute_height_m - contact_absolute_height_m;
    std::optional<GroundRayVolumeInterval> first;
    GroundInfantryHitRegion first_region = aimed_region;
    for (const GroundInfantryHitRegion region : kGroundInfantryHitRegions) {
        const auto interval = ray_hit_volume_interval(
            eye, resolution.aim_point, ground_infantry_hit_volume(target_posture, region));
        if (interval && (!first || interval->enter < first->enter)) {
            first = interval;
            first_region = region;
        }
    }
    if (!first) {
        return resolution;
    }
    // Terrain clips the shot only when its first blocking sample lies before
    // the ray reaches the body. The ray parameter is linear in horizontal
    // distance, as the query's sample distances are.
    const double entry_distance_m = first->enter * resolution.terrain.distance_m;
    if (resolution.terrain.status == IEnvironmentModel::TerrainLineOfSightStatus::Blocked &&
        resolution.terrain.blocking_distance_m < entry_distance_m) {
        return resolution;
    }
    resolution.masked = false;
    resolution.hit_region = first_region;
    resolution.hit_point =
        point_on_ray(eye, resolution.aim_point, (first->enter + first->leave) * 0.5);
    return resolution;
}

[[nodiscard]] inline GroundDirectFireSightObservation
evaluate_ground_direct_fire_line_of_sight(IEnvironmentModel *environment, const Transform &shooter,
                                          const GroundInfantryCapability &shooter_capability,
                                          GroundStance shooter_stance, const Transform &target,
                                          const GroundInfantryCapability &target_capability,
                                          GroundStance target_stance) {
    GroundDirectFireSightObservation observation;
    observation.shooter_stance = shooter_stance;
    observation.target_stance = target_stance;
    const GroundInfantryPostureGeometry *shooter_posture =
        ground_infantry_posture_geometry(shooter_capability, shooter_stance);
    const GroundInfantryPostureGeometry *target_posture =
        ground_infantry_posture_geometry(target_capability, target_stance);
    if (shooter_posture == nullptr || target_posture == nullptr) {
        observation.gate = GroundDirectFireSightGate::PostureUnknown;
        return observation;
    }
    observation.shooter_eye_height_m = shooter_posture->eye_height_m;
    // Missing hit volumes never fall back to a body-centre point.
    if (!ground_infantry_hit_volumes_valid(*target_posture)) {
        observation.gate = GroundDirectFireSightGate::HitVolumesUnknown;
        return observation;
    }
    if (environment == nullptr) {
        observation.gate = GroundDirectFireSightGate::EnvironmentUnavailable;
        return observation;
    }
    for (const GroundInfantryHitRegion region : kGroundDirectFireAimOrder) {
        const GroundDirectFireAimResolution aim =
            resolve_ground_direct_fire_aim(*environment, shooter, observation.shooter_eye_height_m,
                                           target, *target_posture, region);
        observation.aimed_region = aim.aimed_region;
        observation.target_aim_height_m = aim.aim_point.up_m;
        observation.terrain = aim.terrain;
        if (aim.terrain_unknown) {
            observation.gate = GroundDirectFireSightGate::TerrainUnknown;
            return observation;
        }
        if (aim.masked) {
            observation.masked_aim_count += 1;
            continue;
        }
        observation.gate = GroundDirectFireSightGate::Visible;
        observation.hit_region = aim.hit_region;
        observation.hit_point = aim.hit_point;
        return observation;
    }
    observation.gate = GroundDirectFireSightGate::TerrainBlocked;
    return observation;
}

// The local impact the shared effects/damage bridge receives. The target's
// shared `HitboxConfig` is static spawn content compiled from its standing
// volumes, so the held-stance hit point is carried to the same normalised
// position inside the same region's standing box. The shared box with that
// region's id must contain the result, or the shot fails closed. The shared
// route therefore resolves exactly the region this owner chose.
[[nodiscard]] inline std::optional<GroundBodyPoint>
ground_direct_fire_shared_hitbox_impact(const GroundInfantryCapability &target_capability,
                                        const GroundDirectFireSightObservation &sight,
                                        const HitboxConfig *shared_hitboxes) {
    const GroundInfantryPostureGeometry *held =
        ground_infantry_posture_geometry(target_capability, sight.target_stance);
    if (sight.gate != GroundDirectFireSightGate::Visible || shared_hitboxes == nullptr ||
        held == nullptr || !ground_infantry_hit_volumes_valid(target_capability.stand)) {
        return std::nullopt;
    }
    const GroundBodyPoint impact = map_point_between_hit_volumes(
        sight.hit_point, ground_infantry_hit_volume(*held, sight.hit_region),
        ground_infantry_hit_volume(target_capability.stand, sight.hit_region));
    const int region_id = ground_infantry_hit_region_hitbox_id(sight.hit_region);
    for (const Hitbox &box : shared_hitboxes->hitboxes) {
        if (box.id == region_id && box_axis_contains(box.offset_x, box.dim_l, impact.forward_m) &&
            box_axis_contains(box.offset_y, box.dim_w, impact.right_m) &&
            box_axis_contains(box.offset_z, box.dim_h, impact.up_m)) {
            return impact;
        }
    }
    return std::nullopt;
}

[[nodiscard]] inline const char *
ground_direct_fire_sight_gate_name(GroundDirectFireSightGate gate) noexcept {
    switch (gate) {
    case GroundDirectFireSightGate::Visible:
        return "visible";
    case GroundDirectFireSightGate::TerrainBlocked:
        return "terrain_line_of_sight_blocked";
    case GroundDirectFireSightGate::TerrainUnknown:
        return "terrain_line_of_sight_unknown";
    case GroundDirectFireSightGate::PostureUnknown:
        return "infantry_posture_geometry_unknown";
    case GroundDirectFireSightGate::EnvironmentUnavailable:
        return "environment_model_unavailable";
    case GroundDirectFireSightGate::HitVolumesUnknown:
        return "infantry_hit_volumes_unknown";
    case GroundDirectFireSightGate::SharedHitboxMismatch:
        return "shared_hitbox_region_mismatch";
    }
    return "environment_model_unavailable";
}

} // namespace ground_direct_fire_detail
