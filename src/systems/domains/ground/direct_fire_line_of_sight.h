#pragma once

#include <cstdint>

#include "components/basic/common.h"
#include "components/command/mission_command.h"
#include "components/domains/ground/ground_capabilities.h"
#include "core/interfaces/environment_model.h"

// Ground consumer of the domain-neutral terrain line-of-sight query.
//
// The environment owns the geometry (terrain surface, raster sampling, and
// provenance). This owner decides only which heights the query is asked about
// and what a non-visible answer means for the bounded rifle: the shooter's
// authored eye height and the target's authored center-of-mass height, each
// selected by that entity's commanded stance. It does not model cover,
// concealment, exposure, or ballistics.
namespace ground_direct_fire_detail {

enum class GroundDirectFireSightGate : std::uint8_t {
    Visible = 0,
    TerrainBlocked = 1,
    TerrainUnknown = 2,
    PostureUnknown = 3,
    EnvironmentUnavailable = 4,
};

struct GroundDirectFireSightObservation {
    GroundDirectFireSightGate gate = GroundDirectFireSightGate::EnvironmentUnavailable;
    GroundStance shooter_stance = GroundStance::Stand;
    GroundStance target_stance = GroundStance::Stand;
    double shooter_eye_height_m = 0.0;
    double target_aim_height_m = 0.0;
    IEnvironmentModel::TerrainLineOfSightObservation terrain{};
};

// The posture an entity holds is its last commanded Ground stance. An entity
// that was never commanded holds the maintained command DTO's default stance,
// so this introduces no posture of its own.
[[nodiscard]] inline GroundStance held_ground_stance(const MissionCommand *command) noexcept {
    return command != nullptr ? command->stance : MissionCommandGround{}.stance;
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
    observation.target_aim_height_m = target_posture->center_of_mass_height_m;
    if (environment == nullptr) {
        observation.gate = GroundDirectFireSightGate::EnvironmentUnavailable;
        return observation;
    }
    observation.terrain = environment->get_terrain_line_of_sight_observation(
        shooter.x, shooter.y, observation.shooter_eye_height_m, target.x, target.y,
        observation.target_aim_height_m);
    switch (observation.terrain.status) {
    case IEnvironmentModel::TerrainLineOfSightStatus::Visible:
        observation.gate = GroundDirectFireSightGate::Visible;
        break;
    case IEnvironmentModel::TerrainLineOfSightStatus::Blocked:
        observation.gate = GroundDirectFireSightGate::TerrainBlocked;
        break;
    case IEnvironmentModel::TerrainLineOfSightStatus::Unknown:
        observation.gate = GroundDirectFireSightGate::TerrainUnknown;
        break;
    }
    return observation;
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
    }
    return "environment_model_unavailable";
}

} // namespace ground_direct_fire_detail
