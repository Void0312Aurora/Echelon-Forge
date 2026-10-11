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

inline bool is_static_hold_task(GroundTaskMode mode) {
    return mode == GroundTaskMode::OccupyStatic || mode == GroundTaskMode::SupportStatic;
}

// GroundInfantryMovement owns only the anchor pose for the admitted native
// infantry slice. Transform.z is absolute world elevation at the entity
// anchor; no AGL or eye-height component is implied by this projection.
inline void project_terrain_elevation(Transform &transform, IEnvironmentModel &environment) {
    const double elevation = environment.get_terrain_elevation(transform.x, transform.y);
    if (std::isfinite(elevation)) {
        transform.z = elevation;
    }
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
                    const bool move_task =
                        ground_task.ground_task_mode == GroundTaskMode::MoveStatic;
                    const bool static_hold_task =
                        ground_infantry_movement_detail::is_static_hold_task(
                            ground_task.ground_task_mode);
                    if (!command[i].active || (!move_task && !static_hold_task)) {
                        ground_infantry_movement_detail::stop(velocity[i]);
                        continue;
                    }
                    // Occupy/Support are admitted as bounded position-hold
                    // commands. They deliberately do not imply cover,
                    // concealment, sensing, or fire-control semantics.
                    if (static_hold_task) {
                        ground_infantry_movement_detail::stop(velocity[i]);
                        ground_infantry_movement_detail::project_terrain_elevation(transform[i],
                                                                                   *environment);
                        continue;
                    }

                    // MoveStatic carries the only admitted ground-facing
                    // intent. Preserve the NAV heading convention even when
                    // the requested speed is zero or a transition is blocked.
                    const double commanded_heading_deg =
                        Math::normalize_heading_deg(command[i].cmd_heading_deg);
                    transform[i].heading = commanded_heading_deg;

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
                    const double requested_speed =
                        ground_infantry_movement_detail::finite_nonnegative(
                            command[i].cmd_speed_mps);
                    const double current_effective_speed =
                        requested_speed * surface_multiplier * slope_multiplier *
                        vegetation_multiplier * stance_multiplier;
                    if (current_effective_speed <= 0.0) {
                        ground_infantry_movement_detail::stop(velocity[i]);
                        ground_infantry_movement_detail::project_terrain_elevation(transform[i],
                                                                                   *environment);
                        continue;
                    }

                    const double heading_rad = Math::to_radians(commanded_heading_deg);
                    // Ground entities are not currently admitted to the shared
                    // ForceAccumulator/Mass integration path. Advance only the
                    // horizontal kinematic slice owned by this stage.
                    const double dt = std::max(0.0, static_cast<double>(it.delta_time()));
                    double effective_speed = current_effective_speed;
                    if (dt > 0.0) {
                        const double probe_vx = std::sin(heading_rad) * current_effective_speed;
                        const double probe_vy = std::cos(heading_rad) * current_effective_speed;
                        const auto transition = environment->get_ground_transition_observation(
                            transform[i].x, transform[i].y, transform[i].x + probe_vx * dt,
                            transform[i].y + probe_vy * dt);
                        if (!transition.passable) {
                            ground_infantry_movement_detail::stop(velocity[i]);
                            ground_infantry_movement_detail::project_terrain_elevation(
                                transform[i], *environment);
                            continue;
                        }
                        const auto transition_effects =
                            ground_infantry_movement_detail::evaluate_transition_movement_effects(
                                *environment, transform[i].x, transform[i].y,
                                transform[i].x + probe_vx * dt, transform[i].y + probe_vy * dt,
                                ground_task.stance);
                        if (transition_effects.sample_count > 0 &&
                            std::isfinite(transition_effects.average_combined_multiplier)) {
                            effective_speed = requested_speed *
                                              ground_infantry_movement_detail::finite_nonnegative(
                                                  transition_effects.average_combined_multiplier);
                        }
                    }
                    if (effective_speed <= 0.0) {
                        ground_infantry_movement_detail::stop(velocity[i]);
                        ground_infantry_movement_detail::project_terrain_elevation(transform[i],
                                                                                   *environment);
                        continue;
                    }
                    const double next_vx = std::sin(heading_rad) * effective_speed;
                    const double next_vy = std::cos(heading_rad) * effective_speed;
                    velocity[i].vx = next_vx;
                    velocity[i].vy = next_vy;
                    velocity[i].vz = 0.0;
                    transform[i].x += velocity[i].vx * dt;
                    transform[i].y += velocity[i].vy * dt;
                    ground_infantry_movement_detail::project_terrain_elevation(transform[i],
                                                                               *environment);
                }
            }
        });
}
