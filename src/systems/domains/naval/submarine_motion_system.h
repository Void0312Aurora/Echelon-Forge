#pragma once

#include <algorithm>
#include <cmath>

#include <flecs.h>

#include "components/basic/common.h"
#include "components/combat/common/damage_common.h"
#include "components/domains/naval/command/mission_command_naval.h"
#include "components/domains/naval/platform/submarine_platform.h"
#include "core/interfaces/environment_model.h"
#include "components/physics/physics_input_policy.h"

inline void register_submarine_motion_system(flecs::world &ecs) {
    ecs.system<Transform, Velocity, const SubmarinePlatform>("SubmarineMotion")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter &it) {
            while (it.next()) {
                auto transform = it.field<Transform>(0);
                auto velocity = it.field<Velocity>(1);
                auto sub = it.field<const SubmarinePlatform>(2);
                const double dt = physics_runtime::resolve_entity_dt(it.delta_time());

                for (auto i : it) {
                    const NavalCommandIntent *naval_intent = it.entity(i).get<NavalCommandIntent>();
                    const PlatformDamageState *damage = it.entity(i).get<PlatformDamageState>();
                    const SubmarineBathymetryPolicy *bathymetry_config =
                        it.entity(i).get<SubmarineBathymetryPolicy>();
                    SubmarineBathymetryPolicy *bathymetry_policy =
                        bathymetry_config ? it.entity(i).get_mut<SubmarineBathymetryPolicy>()
                                          : nullptr;
                    const EnvironmentModelRef *environment_ref =
                        it.world().get<EnvironmentModelRef>();
                    const double mobility_factor =
                        damage ? std::clamp(damage->mobility_capability, 0.0, 1.0) : 1.0;
                    const bool mobility_kill =
                        damage && (damage->mobility_kill || mobility_factor <= 0.25);

                    double target_heading_deg = transform[i].heading;
                    double target_speed_mps = std::hypot(velocity[i].vx, velocity[i].vy);
                    double target_depth_m = std::max(0.0, -transform[i].z);
                    bool active = false;

                    if (naval_intent && naval_intent->active) {
                        target_heading_deg =
                            Math::normalize_heading_deg(naval_intent->cmd_heading_deg);
                        target_speed_mps = std::max(0.0, naval_intent->cmd_speed_mps);
                        target_depth_m = std::clamp(std::max(0.0, naval_intent->cmd_depth_m), 0.0,
                                                    std::max(0.0, sub[i].max_operating_depth_m));
                        active = true;
                    }

                    if (mobility_kill) {
                        target_speed_mps = 0.0;
                    }
                    const double mobility_speed_cap =
                        std::max(0.0, sub[i].max_speed_submerged_mps) * mobility_factor;
                    target_speed_mps = std::clamp(target_speed_mps, 0.0, mobility_speed_cap);
                    const double current_speed_mps = std::hypot(velocity[i].vx, velocity[i].vy);
                    const double speed_error = target_speed_mps - current_speed_mps;
                    const double accel_step =
                        std::max(0.0, sub[i].max_accel_mps2) * mobility_factor * dt;
                    const double decel_step = std::max(0.0, sub[i].max_decel_mps2) * dt;
                    double next_speed_mps = current_speed_mps;
                    if (speed_error >= 0.0) {
                        next_speed_mps += std::min(speed_error, accel_step);
                    } else {
                        next_speed_mps += std::max(speed_error, -decel_step);
                    }

                    double next_heading_deg = transform[i].heading;
                    if (active) {
                        const double error_deg =
                            std::remainder(target_heading_deg - next_heading_deg, 360.0);
                        const double turn_step =
                            std::max(0.0, sub[i].max_turn_rate_deg_s) * mobility_factor * dt;
                        next_heading_deg = Math::normalize_heading_deg(
                            next_heading_deg + std::clamp(error_deg, -turn_step, turn_step));
                    }

                    const double heading_rad = Math::to_radians(next_heading_deg);
                    double next_vx = std::sin(heading_rad) * next_speed_mps;
                    double next_vy = std::cos(heading_rad) * next_speed_mps;
                    const double proposed_x = transform[i].x + next_vx * dt;
                    const double proposed_y = transform[i].y + next_vy * dt;

                    const double current_depth_m = std::max(0.0, -transform[i].z);
                    double constrained_target_depth_m = target_depth_m;
                    bool allow_horizontal_step = true;
                    if (bathymetry_policy) {
                        bathymetry_policy->last_requested_depth_m = target_depth_m;
                        bathymetry_policy->last_allowed_depth_m =
                            std::max(0.0, sub[i].max_operating_depth_m);
                        bathymetry_policy->last_availability = static_cast<std::uint8_t>(
                            IEnvironmentModel::BathymetryAvailability::Unavailable);
                        bathymetry_policy->last_source.clear();
                        bathymetry_policy->last_status = SubmarineDepthConstraintStatus::Disabled;

                        if (bathymetry_policy->enabled) {
                            const IEnvironmentModel::BathymetrySegmentObservation observation =
                                (environment_ref && environment_ref->model)
                                    ? environment_ref->model->get_bathymetry_along_segment(
                                          transform[i].x, transform[i].y, proposed_x, proposed_y)
                                    : IEnvironmentModel::BathymetrySegmentObservation{};
                            const bool valid_policy =
                                std::isfinite(bathymetry_policy->min_keel_clearance_m) &&
                                bathymetry_policy->min_keel_clearance_m >= 0.0 &&
                                std::isfinite(bathymetry_policy->hull_reference_to_keel_m) &&
                                bathymetry_policy->hull_reference_to_keel_m >= 0.0 &&
                                !bathymetry_policy->horizontal_frame.empty() &&
                                !bathymetry_policy->vertical_datum.empty();
                            const bool valid_observation =
                                valid_policy &&
                                observation.availability ==
                                    IEnvironmentModel::BathymetryAvailability::Valid &&
                                std::isfinite(observation.minimum_water_depth_m) &&
                                observation.minimum_water_depth_m >= 0.0 &&
                                !observation.horizontal_frame.empty() &&
                                observation.horizontal_frame ==
                                    bathymetry_policy->horizontal_frame &&
                                !observation.vertical_datum.empty() &&
                                observation.vertical_datum == bathymetry_policy->vertical_datum &&
                                !observation.source.empty() &&
                                std::isfinite(observation.water_surface_elevation_m) &&
                                observation.water_surface_elevation_m == 0.0 &&
                                observation.time_invariant_for_step &&
                                std::isfinite(bathymetry_policy->hull_reference_to_keel_m) &&
                                bathymetry_policy->hull_reference_to_keel_m >= 0.0;
                            bathymetry_policy->last_availability =
                                static_cast<std::uint8_t>(observation.availability);
                            bathymetry_policy->last_source = observation.source;
                            if (!valid_observation) {
                                // No-data, dry/coastal, out-of-coverage, datum,
                                // frame, source, and temporal failures are
                                // conservative: hold the complete step.
                                constrained_target_depth_m = current_depth_m;
                                bathymetry_policy->last_allowed_depth_m = current_depth_m;
                                bathymetry_policy->last_status =
                                    valid_policy ? SubmarineDepthConstraintStatus::UnknownBathymetry
                                                 : SubmarineDepthConstraintStatus::InvalidPolicy;
                                allow_horizontal_step = false;
                            } else {
                                const double available_center_depth_m =
                                    observation.minimum_water_depth_m -
                                    bathymetry_policy->hull_reference_to_keel_m -
                                    std::max(0.0, bathymetry_policy->min_keel_clearance_m);
                                const double allowed_depth_m =
                                    std::clamp(available_center_depth_m, 0.0,
                                               std::max(0.0, sub[i].max_operating_depth_m));
                                constrained_target_depth_m =
                                    std::min(target_depth_m, allowed_depth_m);
                                bathymetry_policy->last_allowed_depth_m = allowed_depth_m;
                                const bool hull_fits = available_center_depth_m >= 0.0;
                                bathymetry_policy->last_status =
                                    !hull_fits ? SubmarineDepthConstraintStatus::RejectedTrajectory
                                    : current_depth_m > allowed_depth_m
                                        ? SubmarineDepthConstraintStatus::RejectedTrajectory
                                    : target_depth_m > allowed_depth_m
                                        ? SubmarineDepthConstraintStatus::LimitedBySeabed
                                        : SubmarineDepthConstraintStatus::Allowed;
                                // Never sweep horizontally while the current
                                // hull reference is already outside the
                                // admitted clearance envelope.
                                allow_horizontal_step =
                                    hull_fits && current_depth_m <= allowed_depth_m;
                            }
                        }
                    }

                    if (!allow_horizontal_step) {
                        next_vx = 0.0;
                        next_vy = 0.0;
                    }

                    const double depth_error_m = constrained_target_depth_m - current_depth_m;
                    const double depth_step =
                        std::clamp(depth_error_m,
                                   -std::max(0.0, sub[i].max_depth_rate_mps) * mobility_factor * dt,
                                   std::max(0.0, sub[i].max_depth_rate_mps) * mobility_factor * dt);
                    const double next_depth_m =
                        std::clamp(current_depth_m + depth_step, 0.0,
                                   std::max(0.0, sub[i].max_operating_depth_m));

                    velocity[i].vx = next_vx;
                    velocity[i].vy = next_vy;
                    velocity[i].vz = -(next_depth_m - current_depth_m) / dt;

                    transform[i].heading = next_heading_deg;
                    transform[i].pitch = std::clamp(velocity[i].vz * 4.0, -15.0, 15.0);
                    transform[i].roll = 0.0;
                    transform[i].x += velocity[i].vx * dt;
                    transform[i].y += velocity[i].vy * dt;
                    transform[i].z = -next_depth_m;
                }
            }
        });
}
