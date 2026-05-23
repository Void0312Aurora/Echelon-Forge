#pragma once

#include <algorithm>
#include <cmath>

#include <flecs.h>

#include "components/command/common/mission_command_control_state.h"
#include "components/command/legacy_command_bridge.h"
#include "components/command/legacy_command.h"
#include "components/basic/common.h"

// Compatibility bridge seam: ActionCommand/MovementCommand remain quarantined
// here while maintained callers migrate away from direct legacy command truth.

inline double operation_wrap_angle_360(double angle) {
    while (angle < 0.0) angle += 360.0;
    while (angle >= 360.0) angle -= 360.0;
    return angle;
}

inline double operation_shortest_angle_deg(double target, double current) {
    double diff = target - current;
    while (diff > 180.0) diff -= 360.0;
    while (diff < -180.0) diff += 360.0;
    return diff;
}

inline double operation_speed_from_velocity(const Velocity& v) {
    return std::sqrt(v.vx * v.vx + v.vy * v.vy + v.vz * v.vz);
}

inline double operation_lerp_tau(double current, double target, double tau_s, double dt) {
    if (tau_s <= 1e-4 || dt <= 0.0) return target;
    double alpha = 1.0 - std::exp(-dt / tau_s);
    return current + (target - current) * alpha;
}

inline MissionCommandControlState operation_seed_control_state(
    const Transform& transform,
    const Velocity& velocity
) {
    return make_compatibility_control_state_seed(transform, velocity);
}

inline void register_action_mapping_system(flecs::world& ecs) {
    // MovementCommand remains a compatibility mirror here because maintained
    // consumers still observe the legacy DTO shell, but typed control-state
    // ownership must not depend on the mirror being present.
    ecs.system<MissionCommandControlState, MovementCommand, const ActionCommand, const ActionSpaceConfig, const Transform, const Velocity>("ActionMapping")
        .term_at(1).optional()
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto state = it.field<MissionCommandControlState>(0);
                auto act = it.field<const ActionCommand>(2);
                auto cfg = it.field<const ActionSpaceConfig>(3);
                auto tr = it.field<const Transform>(4);
                auto vel = it.field<const Velocity>(5);
                double dt = it.delta_time();
                MovementCommand* movement_mirror =
                    it.is_set(1) ? &it.field_at<MovementCommand>(1, 0) : nullptr;

                for (auto i : it) {
                    if (!act[i].active) continue;

                    MissionCommandControlState& out = state[i];
                    if (!out.active) {
                        out = operation_seed_control_state(tr[i], vel[i]);
                    }

                    double turn_cmd = std::clamp(act[i].turn_rate_cmd, -1.0, 1.0);
                    double accel_cmd = std::clamp(act[i].accel_cmd, -1.0, 1.0);
                    double climb_cmd = std::clamp(act[i].climb_rate_cmd, -1.0, 1.0);

                    double turn_rate = turn_cmd * cfg[i].max_turn_rate_deg_s;
                    double accel = accel_cmd * cfg[i].max_accel_mps2;
                    double climb_rate = climb_cmd * cfg[i].max_climb_rate_mps;

                    out.target_heading_deg = operation_wrap_angle_360(
                        out.target_heading_deg + turn_rate * dt
                    );
                    out.target_speed_mps = std::clamp(
                        out.target_speed_mps + accel * dt,
                        cfg[i].min_speed_mps,
                        cfg[i].max_speed_mps
                    );
                    out.target_altitude_m = std::clamp(
                        out.target_altitude_m + climb_rate * dt,
                        cfg[i].min_alt_m,
                        cfg[i].max_alt_m
                    );
                    out.active = true;
                    refresh_compatibility_typed_air_control_from_legacy_action(
                        out,
                        act[i]
                    );
                    refresh_optional_compatibility_autopilot_movement_command_from_control_state(
                        movement_mirror ? &movement_mirror[i] : nullptr,
                        out
                    );
                }
            }
        });
}

inline void register_command_lag_system(flecs::world& ecs) {
    // LaggedCommand remains a compatibility mirror here because maintained
    // consumers still observe the legacy DTO shell, but typed control-state
    // ownership must not depend on the mirror being present.
    ecs.system<MissionCommandControlState, LaggedCommand, const CommandLag, const Transform, const Velocity>("CommandLag")
        .term_at(1).optional()
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto state = it.field<MissionCommandControlState>(0);
                auto lag = it.field<const CommandLag>(2);
                auto tr = it.field<const Transform>(3);
                auto vel = it.field<const Velocity>(4);
                double dt = it.delta_time();
                LaggedCommand* lagged_mirror =
                    it.is_set(1) ? &it.field_at<LaggedCommand>(1, 0) : nullptr;

                for (auto i : it) {
                    MissionCommandControlState& desired = state[i];

                    if (!desired.active) {
                        desired.lagged_active = false;
                        if (lagged_mirror) {
                            lagged_mirror[i].active = false;
                        }
                        continue;
                    }

                    if (!desired.lagged_active) {
                        const MissionCommandControlState lag_seed =
                            operation_seed_control_state(tr[i], vel[i]);
                        set_mission_command_control_lagged(
                            desired,
                            lag_seed.lagged_heading_deg,
                            lag_seed.lagged_speed_mps,
                            lag_seed.lagged_altitude_m,
                            lag_seed.lagged_active
                        );
                    }

                    double heading_delta = operation_shortest_angle_deg(
                        desired.target_heading_deg,
                        desired.lagged_heading_deg
                    );
                    double heading_step =
                        operation_lerp_tau(0.0, heading_delta, lag[i].heading_tau_s, dt);
                    desired.lagged_heading_deg =
                        operation_wrap_angle_360(desired.lagged_heading_deg + heading_step);

                    desired.lagged_speed_mps =
                        operation_lerp_tau(
                            desired.lagged_speed_mps,
                            desired.target_speed_mps,
                            lag[i].speed_tau_s,
                            dt
                        );

                    desired.lagged_altitude_m =
                        operation_lerp_tau(
                            desired.lagged_altitude_m,
                            desired.target_altitude_m,
                            lag[i].altitude_tau_s,
                            dt
                        );
                    desired.lagged_active = true;
                    refresh_optional_compatibility_lagged_command_mirror_from_control_state(
                        lagged_mirror ? &lagged_mirror[i] : nullptr,
                        desired
                    );
                }
            }
        });
}
