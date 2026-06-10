#pragma once

#include <algorithm>
#include <cmath>

#include <flecs.h>

#include "components/basic/common.h"
#include "components/command/mission_command.h"
#include "components/command/pilot_action.h"
#include "components/domains/naval/platform/ship_platform.h"
#include "core/interfaces/environment_model.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace {

inline double ship_wave_heading_factor_deg(double wave_heading_deg, double ship_heading_deg) {
    const double rel_deg = std::remainder(wave_heading_deg - ship_heading_deg, 360.0);
    return std::abs(rel_deg);
}

inline double ship_head_seas_factor(double wave_heading_deg, double ship_heading_deg) {
    const double abs_rel_deg = ship_wave_heading_factor_deg(wave_heading_deg, ship_heading_deg);
    const double head_component = std::abs(std::cos(Math::to_radians(abs_rel_deg)));
    return std::clamp(head_component, 0.0, 1.0);
}

inline double ship_beam_seas_factor(double wave_heading_deg, double ship_heading_deg) {
    const double abs_rel_deg = ship_wave_heading_factor_deg(wave_heading_deg, ship_heading_deg);
    const double beam_component = std::abs(std::sin(Math::to_radians(abs_rel_deg)));
    return std::clamp(beam_component, 0.0, 1.0);
}

inline double ship_sea_state_scale(double sea_state) {
    return std::clamp(sea_state / 6.0, 0.0, 1.0);
}

inline bool ship_pilot_action_requests_manual_takeover(const PilotAction& pilot) {
    constexpr double kPrimaryAxisDeadband = 0.05;
    constexpr double kThrottleDeadband = 0.05;
    return bool(pilot.active) && (
        std::abs(pilot.stick_roll) > kPrimaryAxisDeadband ||
        std::abs(pilot.rudder) > kPrimaryAxisDeadband ||
        std::abs(pilot.throttle - 0.5) > kThrottleDeadband
    );
}

inline double ship_station_target_bearing_deg(
    double reference_x_m,
    double reference_y_m,
    double station_bearing_deg,
    double station_radius_m,
    double own_x_m,
    double own_y_m,
    double fallback_heading_deg
) {
    const double desired_heading_rad = Math::to_radians(station_bearing_deg);
    const double desired_x = reference_x_m + std::sin(desired_heading_rad) * station_radius_m;
    const double desired_y = reference_y_m + std::cos(desired_heading_rad) * station_radius_m;
    const double dx = desired_x - own_x_m;
    const double dy = desired_y - own_y_m;
    if (std::abs(dx) < 1.0e-9 && std::abs(dy) < 1.0e-9) {
        return Math::normalize_heading_deg(fallback_heading_deg);
    }
    const double bearing_deg = std::atan2(dx, dy) * 180.0 / M_PI;
    return Math::normalize_heading_deg(bearing_deg);
}

inline bool resolve_ship_station_command(
    flecs::world world,
    const Transform& own_transform,
    const MissionCommand& mission_cmd,
    double fallback_heading_deg,
    double* commanded_heading_deg_out,
    double* commanded_speed_mps_out
) {
    if (commanded_heading_deg_out == nullptr || commanded_speed_mps_out == nullptr) {
        return false;
    }
    const auto stationing = mission_command_naval_stationing_directive(mission_cmd);
    const std::uint64_t reference_entity_id = stationing.reference_entity_id;
    const double station_radius_m = std::max(0.0, stationing.station_radius_m);
    if (reference_entity_id == 0 || station_radius_m <= 0.0) {
        return false;
    }

    const auto reference_entity = world.entity(reference_entity_id);
    if (!reference_entity.is_valid()) {
        return false;
    }

    const Transform* reference_transform = reference_entity.get<Transform>();
    const Velocity* reference_velocity = reference_entity.get<Velocity>();
    if (reference_transform == nullptr || reference_velocity == nullptr) {
        return false;
    }

    const double desired_heading_rad = Math::to_radians(stationing.station_bearing_deg);
    const double desired_x =
        reference_transform->x + std::sin(desired_heading_rad) * station_radius_m;
    const double desired_y =
        reference_transform->y + std::cos(desired_heading_rad) * station_radius_m;
    const double to_station_x = desired_x - own_transform.x;
    const double to_station_y = desired_y - own_transform.y;
    *commanded_heading_deg_out = ship_station_target_bearing_deg(
        reference_transform->x,
        reference_transform->y,
        stationing.station_bearing_deg,
        station_radius_m,
        own_transform.x,
        own_transform.y,
        fallback_heading_deg
    );

    const double reference_speed_mps =
        std::hypot(reference_velocity->vx, reference_velocity->vy);
    const double reference_speed_norm = std::max(1.0e-6, reference_speed_mps);
    const double along_track_error_m =
        (to_station_x * reference_velocity->vx + to_station_y * reference_velocity->vy) /
        reference_speed_norm;
    const double correction_mps = std::clamp(along_track_error_m * 0.0025, -3.0, 3.0);
    *commanded_speed_mps_out = std::max(0.0, reference_speed_mps + correction_mps);
    return true;
}

} // namespace

inline void register_ship_motion_system(flecs::world& ecs) {
    ecs.system<Transform, Velocity, const ShipPlatform>("ShipMotion")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto transform = it.field<Transform>(0);
                auto velocity = it.field<Velocity>(1);
                auto ship = it.field<const ShipPlatform>(2);
                const EnvironmentModelRef* env_ref = it.world().get<EnvironmentModelRef>();

                const double dt = it.delta_time() > 0.0 ? it.delta_time() : 1.0 / 60.0;
                const ecs_world_info_t* info = ecs_get_world_info(it.world().c_ptr());
                const double current_time = info ? static_cast<double>(info->world_time_total) : 0.0;

                for (auto i : it) {
                    const PilotAction* pilot = it.entity(i).get<PilotAction>();
                    const MissionCommand* mission_cmd = it.entity(i).get<MissionCommand>();

                    double commanded_heading_deg = transform[i].heading;
                    double commanded_speed_mps = std::hypot(velocity[i].vx, velocity[i].vy);
                    bool command_active = false;

                    if (pilot && ship_pilot_action_requests_manual_takeover(*pilot)) {
                        const double current_heading_deg =
                            Math::normalize_heading_deg(transform[i].heading);
                        const double manual_turn =
                            std::clamp(pilot->rudder + pilot->stick_roll, -1.0, 1.0);
                        commanded_heading_deg = Math::normalize_heading_deg(
                            current_heading_deg + manual_turn * std::max(0.0, ship[i].max_turn_rate_deg_s)
                        );
                        const double speed_ceiling = ship[i].max_speed_mps > 0.0
                            ? ship[i].max_speed_mps
                            : std::max(0.0, commanded_speed_mps);
                        commanded_speed_mps =
                            std::clamp(pilot->throttle, 0.0, 1.0) * std::max(0.0, speed_ceiling);
                        command_active = true;
                    } else if (mission_cmd && bool(mission_cmd->active)) {
                        commanded_heading_deg = Math::normalize_heading_deg(mission_cmd->cmd_heading_deg);
                        commanded_speed_mps = std::max(0.0, mission_cmd->cmd_speed_mps);
                        resolve_ship_station_command(
                            it.world(),
                            transform[i],
                            *mission_cmd,
                            commanded_heading_deg,
                            &commanded_heading_deg,
                            &commanded_speed_mps
                        );
                        command_active = true;
                    }

                    const double max_speed_mps = ship[i].max_speed_mps > 0.0
                        ? ship[i].max_speed_mps
                        : std::max(commanded_speed_mps, std::hypot(velocity[i].vx, velocity[i].vy));
                    double sea_state = ship[i].sea_state;
                    double wave_heading_deg = ship[i].wave_heading_deg;
                    double wave_period_s = ship[i].wave_period_s;
                    if (env_ref && env_ref->model) {
                        const auto maritime_state = env_ref->model->get_maritime_state();
                        if (maritime_state.configured) {
                            sea_state = maritime_state.sea_state;
                            wave_heading_deg = maritime_state.wave_heading_deg;
                            wave_period_s = maritime_state.wave_period_s;
                        }
                    }
                    const double sea_state_scale = ship_sea_state_scale(sea_state);
                    const double head_seas_factor = ship_head_seas_factor(
                        wave_heading_deg,
                        transform[i].heading
                    );
                    const double beam_seas_factor = ship_beam_seas_factor(
                        wave_heading_deg,
                        transform[i].heading
                    );
                    const double added_resistance_fraction = std::clamp(
                        std::max(0.0, ship[i].added_resistance_fraction_sea_state_6) *
                            sea_state_scale * (0.65 * head_seas_factor + 0.35 * beam_seas_factor),
                        0.0,
                        0.6
                    );
                    const double effective_max_speed_mps =
                        std::max(0.0, max_speed_mps * (1.0 - added_resistance_fraction));
                    commanded_speed_mps = std::clamp(commanded_speed_mps, 0.0, effective_max_speed_mps);

                    const double current_speed_mps = std::hypot(velocity[i].vx, velocity[i].vy);
                    const double speed_error_mps = commanded_speed_mps - current_speed_mps;
                    const double max_accel_step = std::max(0.0, ship[i].max_accel_mps2) * dt;
                    const double max_decel_step = std::max(0.0, ship[i].max_decel_mps2) * dt;
                    double next_speed_mps = current_speed_mps;
                    if (speed_error_mps >= 0.0) {
                        next_speed_mps += std::min(speed_error_mps, max_accel_step);
                    } else {
                        next_speed_mps += std::max(speed_error_mps, -max_decel_step);
                    }
                    next_speed_mps = std::clamp(
                        next_speed_mps,
                        0.0,
                        std::max(effective_max_speed_mps, current_speed_mps)
                    );

                    double next_heading_deg = Math::normalize_heading_deg(transform[i].heading);
                    if (command_active) {
                        const double steerageway_speed_mps =
                            std::max(0.0, ship[i].steerageway_speed_mps);
                        if (next_speed_mps > steerageway_speed_mps) {
                            const double speed_ref_mps = ship[i].economical_speed_mps > 0.0
                                ? ship[i].economical_speed_mps
                                : std::max(1.0, ship[i].max_speed_mps);
                            const double speed_ratio = std::clamp(
                                next_speed_mps / std::max(1.0, speed_ref_mps),
                                std::clamp(ship[i].low_speed_turn_factor, 0.05, 1.0),
                                1.0
                            );
                            const double max_turn_step_deg =
                                std::max(0.0, ship[i].max_turn_rate_deg_s) * speed_ratio * dt;
                            const double heading_error_deg =
                                std::remainder(commanded_heading_deg - next_heading_deg, 360.0);
                            const double heading_step_deg =
                                std::clamp(heading_error_deg, -max_turn_step_deg, max_turn_step_deg);
                            next_heading_deg = Math::normalize_heading_deg(next_heading_deg + heading_step_deg);
                        }
                    } else if (next_speed_mps > 0.05) {
                        next_heading_deg = Math::ground_track_deg_from_velocity(
                            velocity[i].vx,
                            velocity[i].vy,
                            next_heading_deg
                        );
                    }

                    const double heading_rad = Math::to_radians(next_heading_deg);
                    velocity[i].vx = std::sin(heading_rad) * next_speed_mps;
                    velocity[i].vy = std::cos(heading_rad) * next_speed_mps;

                    transform[i].heading = next_heading_deg;
                    transform[i].x += velocity[i].vx * dt;
                    transform[i].y += velocity[i].vy * dt;
                    transform[i].z = 0.0;
                    velocity[i].vz = 0.0;

                    if (sea_state_scale > 0.0) {
                        wave_period_s = std::max(2.0, wave_period_s > 0.0 ? wave_period_s : 8.0);
                        const double omega = (2.0 * M_PI) / wave_period_s;
                        const double roll_amplitude_deg =
                            std::max(0.0, ship[i].max_roll_deg_sea_state_6) *
                            sea_state_scale *
                            (0.35 + 0.65 * beam_seas_factor);
                        const double pitch_amplitude_deg =
                            std::max(0.0, ship[i].max_pitch_deg_sea_state_6) *
                            sea_state_scale *
                            (0.35 + 0.65 * head_seas_factor);
                        const double phase_seed = std::fmod(
                            static_cast<double>(it.entity(i).id() % 1024ULL) * 0.137,
                            2.0 * M_PI
                        );
                        transform[i].roll =
                            roll_amplitude_deg * std::sin(omega * current_time + phase_seed);
                        transform[i].pitch =
                            pitch_amplitude_deg * std::sin(
                                omega * current_time * 0.93 + phase_seed * 0.7 + M_PI / 6.0
                            );
                    } else {
                        transform[i].pitch = 0.0;
                        transform[i].roll = 0.0;
                    }
                }
            }
        });
}
