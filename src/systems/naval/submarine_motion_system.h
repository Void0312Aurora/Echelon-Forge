#pragma once

#include <algorithm>
#include <cmath>

#include <flecs.h>

#include "components/basic/common.h"
#include "components/command/mission_command.h"
#include "components/naval/submarine_platform.h"

inline void register_submarine_motion_system(flecs::world& ecs) {
    ecs.system<Transform, Velocity, const SubmarinePlatform>("SubmarineMotion")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto transform = it.field<Transform>(0);
                auto velocity = it.field<Velocity>(1);
                auto sub = it.field<const SubmarinePlatform>(2);
                const double dt = it.delta_time() > 0.0 ? it.delta_time() : 1.0 / 60.0;

                for (auto i : it) {
                    const MissionCommand* mission_cmd = it.entity(i).get<MissionCommand>();

                    double target_heading_deg = transform[i].heading;
                    double target_speed_mps = std::hypot(velocity[i].vx, velocity[i].vy);
                    double target_depth_m = std::max(0.0, -transform[i].z);
                    bool active = false;

                    if (mission_cmd && mission_cmd->active) {
                        target_heading_deg = Math::normalize_heading_deg(mission_cmd->cmd_heading_deg);
                        target_speed_mps = std::max(0.0, mission_cmd->cmd_speed_mps);
                        target_depth_m = std::clamp(
                            std::max(0.0, mission_cmd->cmd_altitude_m),
                            0.0,
                            std::max(0.0, sub[i].max_operating_depth_m)
                        );
                        active = true;
                    }

                    target_speed_mps = std::clamp(target_speed_mps, 0.0, std::max(0.0, sub[i].max_speed_submerged_mps));
                    const double current_speed_mps = std::hypot(velocity[i].vx, velocity[i].vy);
                    const double speed_error = target_speed_mps - current_speed_mps;
                    const double accel_step = std::max(0.0, sub[i].max_accel_mps2) * dt;
                    const double decel_step = std::max(0.0, sub[i].max_decel_mps2) * dt;
                    double next_speed_mps = current_speed_mps;
                    if (speed_error >= 0.0) {
                        next_speed_mps += std::min(speed_error, accel_step);
                    } else {
                        next_speed_mps += std::max(speed_error, -decel_step);
                    }

                    double next_heading_deg = transform[i].heading;
                    if (active) {
                        const double error_deg = std::remainder(target_heading_deg - next_heading_deg, 360.0);
                        const double step_deg = std::clamp(
                            error_deg,
                            -std::max(0.0, sub[i].max_turn_rate_deg_s) * dt,
                            std::max(0.0, sub[i].max_turn_rate_deg_s) * dt
                        );
                        next_heading_deg = Math::normalize_heading_deg(next_heading_deg + step_deg);
                    }

                    const double current_depth_m = std::max(0.0, -transform[i].z);
                    const double depth_error_m = target_depth_m - current_depth_m;
                    const double depth_step = std::clamp(
                        depth_error_m,
                        -std::max(0.0, sub[i].max_depth_rate_mps) * dt,
                        std::max(0.0, sub[i].max_depth_rate_mps) * dt
                    );
                    const double next_depth_m = std::clamp(
                        current_depth_m + depth_step,
                        0.0,
                        std::max(0.0, sub[i].max_operating_depth_m)
                    );

                    const double heading_rad = Math::to_radians(next_heading_deg);
                    velocity[i].vx = std::sin(heading_rad) * next_speed_mps;
                    velocity[i].vy = std::cos(heading_rad) * next_speed_mps;
                    velocity[i].vz = -(next_depth_m - current_depth_m) / dt;

                    transform[i].heading = next_heading_deg;
                    transform[i].pitch = std::clamp(-velocity[i].vz * 4.0, -15.0, 15.0);
                    transform[i].roll = 0.0;
                    transform[i].x += velocity[i].vx * dt;
                    transform[i].y += velocity[i].vy * dt;
                    transform[i].z = -next_depth_m;
                }
            }
        });
}
