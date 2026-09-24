#pragma once

#include <cmath>
#include <flecs.h>
#include <limits>
#include <numbers>

#include "components/basic/common.h"
#include "components/command/mission_command.h"
#include "components/domains/ground/ground_capabilities.h"
#include "core/interfaces/environment_model.h"
#include "systems/domains/ground/movement_effects.h"

namespace ground_infantry_movement_detail {

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
// kinematic drift for the admitted move contract. Route intent, cover, and
// observation export remain separate owners; local bridge/passability evidence
// is supplied by the shared environment transition query.
inline void register_ground_infantry_movement_system(flecs::world &ecs) {
    ecs.system<Transform, Velocity, const KeyEntity, const MissionCommand,
               const GroundInfantryCapability>("GroundInfantryMovement")
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
                            environment->get_ground_slope_deg(transform[i].x, transform[i].y));
                    const double vegetation_multiplier =
                        ground_infantry_movement_detail::vegetation_speed_multiplier(
                            terrain.vegetation_density);
                    const double stance_multiplier =
                        ground_infantry_movement_detail::stance_speed_multiplier(
                            ground_task.stance);
                    const double effective_speed =
                        ground_infantry_movement_detail::finite_nonnegative(
                            command[i].cmd_speed_mps) *
                        surface_multiplier * slope_multiplier * vegetation_multiplier *
                        stance_multiplier;
                    if (effective_speed <= 0.0) {
                        ground_infantry_movement_detail::stop(velocity[i]);
                        continue;
                    }

                    const double heading_rad =
                        Math::to_radians(Math::normalize_heading_deg(command[i].cmd_heading_deg));
                    // Ground entities are not currently admitted to the shared
                    // ForceAccumulator/Mass integration path. Advance only the
                    // horizontal kinematic slice owned by this stage.
                    const double dt = std::max(0.0, static_cast<double>(it.delta_time()));
                    const double next_vx = std::sin(heading_rad) * effective_speed;
                    const double next_vy = std::cos(heading_rad) * effective_speed;
                    if (dt > 0.0) {
                        const auto transition = environment->get_ground_transition_observation(
                            transform[i].x, transform[i].y, transform[i].x + next_vx * dt,
                            transform[i].y + next_vy * dt);
                        if (!transition.passable) {
                            ground_infantry_movement_detail::stop(velocity[i]);
                            continue;
                        }
                    }
                    velocity[i].vx = next_vx;
                    velocity[i].vy = next_vy;
                    velocity[i].vz = 0.0;
                    transform[i].x += velocity[i].vx * dt;
                    transform[i].y += velocity[i].vy * dt;
                }
            }
        });
}
