#pragma once

#include <algorithm>
#include <cmath>
#include <flecs.h>
#include <limits>
#include <numbers>

#include "components/basic/common.h"
#include "components/command/mission_command.h"
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

inline double slope_deg(IEnvironmentModel &environment, double x, double y) {
    constexpr double kSampleHalfSpanM = 5.0;
    const double east_gradient = (environment.get_terrain_elevation(x + kSampleHalfSpanM, y) -
                                  environment.get_terrain_elevation(x - kSampleHalfSpanM, y)) /
                                 (2.0 * kSampleHalfSpanM);
    const double north_gradient = (environment.get_terrain_elevation(x, y + kSampleHalfSpanM) -
                                   environment.get_terrain_elevation(x, y - kSampleHalfSpanM)) /
                                  (2.0 * kSampleHalfSpanM);
    if (!std::isfinite(east_gradient) || !std::isfinite(north_gradient)) {
        return std::numeric_limits<double>::quiet_NaN();
    }
    return std::atan(std::hypot(east_gradient, north_gradient)) * 180.0 /
           std::numbers::pi_v<double>;
}

inline double slope_speed_multiplier(double slope) {
    if (!std::isfinite(slope) || slope < 0.0) {
        return 0.0;
    }
    return std::clamp(1.0 - slope / 60.0, 0.20, 1.0);
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

inline void stop(Velocity &velocity) {
    velocity.vx = 0.0;
    velocity.vy = 0.0;
    velocity.vz = 0.0;
}

} // namespace ground_infantry_movement_detail

// Ground movement is intentionally a narrow native consumer of the maintained
// MissionCommand ground slice.  It supplies deterministic heading/speed and
// surface/slope cost for a Ground entity. Ground units do not yet participate
// in the aircraft rigid-body integrator, so this stage also owns the small
// kinematic drift for the admitted move contract. Route intent, bridge
// admission, stance, cover, and observation export remain separate owners.
inline void register_ground_infantry_movement_system(flecs::world &ecs) {
    ecs.system<Transform, Velocity, const KeyEntity, const MissionCommand>("GroundInfantryMovement")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter &it) {
            const EnvironmentModelRef *environment_ref = it.world().get<EnvironmentModelRef>();
            IEnvironmentModel *environment = environment_ref ? environment_ref->model : nullptr;
            while (it.next()) {
                auto transform = it.field<Transform>(0);
                auto velocity = it.field<Velocity>(1);
                auto key = it.field<const KeyEntity>(2);
                auto command = it.field<const MissionCommand>(3);

                for (auto i : it) {
                    if (key[i].type != UnitType::Ground || environment == nullptr) {
                        if (key[i].type == UnitType::Ground) {
                            ground_infantry_movement_detail::stop(velocity[i]);
                        }
                        continue;
                    }

                    const MissionCommandGround::StaticTaskDirective ground_task =
                        mission_command_ground_static_task_directive(command[i]);
                    if (!command[i].active ||
                        ground_task.ground_task_mode != GroundTaskMode::MoveStatic) {
                        ground_infantry_movement_detail::stop(velocity[i]);
                        continue;
                    }

                    const auto terrain =
                        environment->get_terrain_at(transform[i].x, transform[i].y);
                    const double surface_multiplier =
                        ground_infantry_movement_detail::surface_speed_multiplier(terrain.type);
                    const double slope_multiplier =
                        ground_infantry_movement_detail::slope_speed_multiplier(
                            ground_infantry_movement_detail::slope_deg(*environment, transform[i].x,
                                                                       transform[i].y));
                    const double stance_multiplier =
                        ground_infantry_movement_detail::stance_speed_multiplier(
                            ground_task.stance);
                    const double effective_speed =
                        ground_infantry_movement_detail::finite_nonnegative(
                            command[i].cmd_speed_mps) *
                        surface_multiplier * slope_multiplier * stance_multiplier;
                    if (effective_speed <= 0.0) {
                        ground_infantry_movement_detail::stop(velocity[i]);
                        continue;
                    }

                    const double heading_rad =
                        Math::to_radians(Math::normalize_heading_deg(command[i].cmd_heading_deg));
                    velocity[i].vx = std::sin(heading_rad) * effective_speed;
                    velocity[i].vy = std::cos(heading_rad) * effective_speed;
                    velocity[i].vz = 0.0;

                    // Ground entities are not currently admitted to the shared
                    // ForceAccumulator/Mass integration path. Advance only the
                    // horizontal kinematic slice owned by this stage.
                    const double dt = std::max(0.0, static_cast<double>(it.delta_time()));
                    transform[i].x += velocity[i].vx * dt;
                    transform[i].y += velocity[i].vy * dt;
                }
            }
        });
}
