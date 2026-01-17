#pragma once

#include <algorithm>
#include <cmath>

#include <flecs.h>

#include "components/physics/action.h"
#include "components/basic/common.h"

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

inline void register_action_mapping_system(flecs::world& ecs) {
    ecs.system<MovementCommand, const ActionCommand, const ActionSpaceConfig, const Transform, const Velocity>("ActionMapping")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto cmd = it.field<MovementCommand>(0);
                auto act = it.field<const ActionCommand>(1);
                auto cfg = it.field<const ActionSpaceConfig>(2);
                auto tr = it.field<const Transform>(3);
                auto vel = it.field<const Velocity>(4);
                double dt = it.delta_time();

                for (auto i : it) {
                    if (!act[i].active) continue;

                    MovementCommand& out = cmd[i];
                    if (!out.active) {
                        out.target_heading = operation_wrap_angle_360(tr[i].heading);
                        out.target_speed = operation_speed_from_velocity(vel[i]);
                        out.target_altitude = tr[i].z;
                        out.active = true;
                    }

                    double turn_cmd = std::clamp(act[i].turn_rate_cmd, -1.0, 1.0);
                    double accel_cmd = std::clamp(act[i].accel_cmd, -1.0, 1.0);
                    double climb_cmd = std::clamp(act[i].climb_rate_cmd, -1.0, 1.0);

                    double turn_rate = turn_cmd * cfg[i].max_turn_rate_deg_s;
                    double accel = accel_cmd * cfg[i].max_accel_mps2;
                    double climb_rate = climb_cmd * cfg[i].max_climb_rate_mps;

                    out.target_heading = operation_wrap_angle_360(out.target_heading + turn_rate * dt);
                    out.target_speed = std::clamp(out.target_speed + accel * dt,
                                                  cfg[i].min_speed_mps,
                                                  cfg[i].max_speed_mps);
                    out.target_altitude = std::clamp(out.target_altitude + climb_rate * dt,
                                                     cfg[i].min_alt_m,
                                                     cfg[i].max_alt_m);
                }
            }
        });
}

inline void register_command_lag_system(flecs::world& ecs) {
    ecs.system<LaggedCommand, const MovementCommand, const CommandLag, const Transform, const Velocity>("CommandLag")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto lagged = it.field<LaggedCommand>(0);
                auto desired = it.field<const MovementCommand>(1);
                auto lag = it.field<const CommandLag>(2);
                auto tr = it.field<const Transform>(3);
                auto vel = it.field<const Velocity>(4);
                double dt = it.delta_time();

                for (auto i : it) {
                    const MovementCommand& target = desired[i];
                    LaggedCommand& current = lagged[i];

                    if (!target.active) {
                        current.active = false;
                        continue;
                    }

                    if (!current.active) {
                        current.target_heading = operation_wrap_angle_360(tr[i].heading);
                        current.target_speed = operation_speed_from_velocity(vel[i]);
                        current.target_altitude = tr[i].z;
                        current.active = true;
                    }

                    double heading_delta = operation_shortest_angle_deg(target.target_heading,
                                                                        current.target_heading);
                    double heading_step =
                        operation_lerp_tau(0.0, heading_delta, lag[i].heading_tau_s, dt);
                    current.target_heading =
                        operation_wrap_angle_360(current.target_heading + heading_step);

                    current.target_speed =
                        operation_lerp_tau(current.target_speed,
                                           target.target_speed,
                                           lag[i].speed_tau_s,
                                           dt);

                    current.target_altitude =
                        operation_lerp_tau(current.target_altitude,
                                           target.target_altitude,
                                           lag[i].altitude_tau_s,
                                           dt);
                }
            }
        });
}
