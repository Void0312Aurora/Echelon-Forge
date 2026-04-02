#include "gpu/gpu_exact_world_step_command_lane_runtime.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <stdexcept>

namespace gpu {

namespace {

ExactWorldStepCommandLaneStats g_last_stats{};

double wrap_angle_360(double angle_deg) {
    while (angle_deg < 0.0) {
        angle_deg += 360.0;
    }
    while (angle_deg >= 360.0) {
        angle_deg -= 360.0;
    }
    return angle_deg;
}

double shortest_angle_deg(double target_deg, double current_deg) {
    double diff = target_deg - current_deg;
    while (diff > 180.0) {
        diff -= 360.0;
    }
    while (diff < -180.0) {
        diff += 360.0;
    }
    return diff;
}

double speed_from_velocity(double vx_mps, double vy_mps, double vz_mps) {
    return std::sqrt(vx_mps * vx_mps + vy_mps * vy_mps + vz_mps * vz_mps);
}

double lerp_tau(double current, double target, double tau_s, double dt_s) {
    if (tau_s <= 1.0e-4 || dt_s <= 0.0) {
        return target;
    }
    const double alpha = 1.0 - std::exp(-dt_s / tau_s);
    return current + (target - current) * alpha;
}

double frame_delta_s(double time_step_s) {
    return static_cast<double>(static_cast<float>(time_step_s));
}

void run_command_link_stage(ExactWorldStepCommandLaneSoA& soa, std::size_t i) {
    if (soa.has_command_link[i] == 0) {
        return;
    }

    if (soa.has_movement_command[i] != 0 && soa.has_pending_movement_command[i] != 0) {
        auto& pending = soa.pending_movement_command[i];
        if (pending.active && soa.world_time_s[i] >= pending.deliver_time) {
            soa.movement_command[i] = pending.command;
            soa.movement_command[i].active = true;
            pending.active = false;
        }
    }

    if (soa.has_action_command[i] != 0 && soa.has_pending_action_command[i] != 0) {
        auto& pending = soa.pending_action_command[i];
        if (pending.active && soa.world_time_s[i] >= pending.deliver_time) {
            soa.action_command[i] = pending.command;
            soa.action_command[i].active = true;
            pending.active = false;
        }
    }

    if (soa.has_mission_command[i] != 0 && soa.has_pending_mission_command[i] != 0) {
        auto& pending = soa.pending_mission_command[i];
        if (pending.active && soa.world_time_s[i] >= pending.deliver_time) {
            soa.mission_command[i] = pending.command;
            soa.mission_command[i].active = true;
            pending.active = false;
        }
    }
}

void run_action_mapping_stage(ExactWorldStepCommandLaneSoA& soa, std::size_t i) {
    if (soa.has_movement_command[i] == 0 || soa.has_action_command[i] == 0 || soa.has_action_space_config[i] == 0) {
        return;
    }

    const ActionCommand& action = soa.action_command[i];
    if (!action.active) {
        return;
    }

    MovementCommand& movement = soa.movement_command[i];
    const ActionSpaceConfig& cfg = soa.action_space_config[i];
    const double dt_s = frame_delta_s(soa.time_step_s[i]);

    if (!movement.active) {
        movement.target_heading = wrap_angle_360(soa.heading_deg[i]);
        movement.target_speed = speed_from_velocity(soa.vx_mps[i], soa.vy_mps[i], soa.vz_mps[i]);
        movement.target_altitude = soa.altitude_m[i];
        movement.active = true;
    }

    const double turn_cmd = std::clamp(action.turn_rate_cmd, -1.0, 1.0);
    const double accel_cmd = std::clamp(action.accel_cmd, -1.0, 1.0);
    const double climb_cmd = std::clamp(action.climb_rate_cmd, -1.0, 1.0);

    const double turn_rate = turn_cmd * cfg.max_turn_rate_deg_s;
    const double accel = accel_cmd * cfg.max_accel_mps2;
    const double climb_rate = climb_cmd * cfg.max_climb_rate_mps;

    movement.target_heading = wrap_angle_360(movement.target_heading + turn_rate * dt_s);
    movement.target_speed = std::clamp(
        movement.target_speed + accel * dt_s,
        cfg.min_speed_mps,
        cfg.max_speed_mps
    );
    movement.target_altitude = std::clamp(
        movement.target_altitude + climb_rate * dt_s,
        cfg.min_alt_m,
        cfg.max_alt_m
    );
}

void run_command_lag_stage(ExactWorldStepCommandLaneSoA& soa, std::size_t i) {
    if (soa.has_lagged_command[i] == 0 || soa.has_movement_command[i] == 0 || soa.has_command_lag[i] == 0) {
        return;
    }

    const MovementCommand& target = soa.movement_command[i];
    LaggedCommand& current = soa.lagged_command[i];
    const CommandLag& lag = soa.command_lag[i];
    const double dt_s = frame_delta_s(soa.time_step_s[i]);

    if (!target.active) {
        current.active = false;
        return;
    }

    if (!current.active) {
        current.target_heading = wrap_angle_360(soa.heading_deg[i]);
        current.target_speed = speed_from_velocity(soa.vx_mps[i], soa.vy_mps[i], soa.vz_mps[i]);
        current.target_altitude = soa.altitude_m[i];
        current.active = true;
    }

    const double heading_delta = shortest_angle_deg(target.target_heading, current.target_heading);
    const double heading_step = lerp_tau(0.0, heading_delta, lag.heading_tau_s, dt_s);
    current.target_heading = wrap_angle_360(current.target_heading + heading_step);
    current.target_speed = lerp_tau(current.target_speed, target.target_speed, lag.speed_tau_s, dt_s);
    current.target_altitude = lerp_tau(current.target_altitude, target.target_altitude, lag.altitude_tau_s, dt_s);
}

}  // namespace

ExactWorldStepCommandLaneSoA pack_exact_world_step_states_v1_command_lane_soa(
    const std::vector<ExactWorldStepStateV1>& states
) {
    ExactWorldStepCommandLaneSoA soa{};
    soa.size = states.size();

    soa.time_step_s.resize(soa.size);
    soa.world_time_s.resize(soa.size);
    soa.heading_deg.resize(soa.size);
    soa.altitude_m.resize(soa.size);
    soa.vx_mps.resize(soa.size);
    soa.vy_mps.resize(soa.size);
    soa.vz_mps.resize(soa.size);

    soa.movement_command.resize(soa.size);
    soa.action_command.resize(soa.size);
    soa.mission_command.resize(soa.size);
    soa.action_space_config.resize(soa.size);
    soa.command_lag.resize(soa.size);
    soa.lagged_command.resize(soa.size);
    soa.command_link.resize(soa.size);
    soa.pending_movement_command.resize(soa.size);
    soa.pending_action_command.resize(soa.size);
    soa.pending_mission_command.resize(soa.size);

    soa.has_movement_command.resize(soa.size);
    soa.has_action_command.resize(soa.size);
    soa.has_mission_command.resize(soa.size);
    soa.has_action_space_config.resize(soa.size);
    soa.has_command_lag.resize(soa.size);
    soa.has_lagged_command.resize(soa.size);
    soa.has_command_link.resize(soa.size);
    soa.has_pending_movement_command.resize(soa.size);
    soa.has_pending_action_command.resize(soa.size);
    soa.has_pending_mission_command.resize(soa.size);

    for (std::size_t i = 0; i < soa.size; ++i) {
        const auto& state = states[i];
        soa.time_step_s[i] = state.time_step_s;
        soa.world_time_s[i] = state.world_time_s;
        soa.heading_deg[i] = state.transform.heading;
        soa.altitude_m[i] = state.transform.z;
        soa.vx_mps[i] = state.velocity.vx;
        soa.vy_mps[i] = state.velocity.vy;
        soa.vz_mps[i] = state.velocity.vz;

        soa.movement_command[i] = state.movement_command;
        soa.action_command[i] = state.action_command;
        soa.mission_command[i] = state.mission_command;
        soa.action_space_config[i] = state.action_space_config;
        soa.command_lag[i] = state.command_lag;
        soa.lagged_command[i] = state.lagged_command;
        soa.command_link[i] = state.command_link;
        soa.pending_movement_command[i] = state.pending_movement_command;
        soa.pending_action_command[i] = state.pending_action_command;
        soa.pending_mission_command[i] = state.pending_mission_command;

        soa.has_movement_command[i] = state.has_movement_command ? 1u : 0u;
        soa.has_action_command[i] = state.has_action_command ? 1u : 0u;
        soa.has_mission_command[i] = state.has_mission_command ? 1u : 0u;
        soa.has_action_space_config[i] = state.has_action_space_config ? 1u : 0u;
        soa.has_command_lag[i] = state.has_command_lag ? 1u : 0u;
        soa.has_lagged_command[i] = state.has_lagged_command ? 1u : 0u;
        soa.has_command_link[i] = state.has_command_link ? 1u : 0u;
        soa.has_pending_movement_command[i] = state.has_pending_movement_command ? 1u : 0u;
        soa.has_pending_action_command[i] = state.has_pending_action_command ? 1u : 0u;
        soa.has_pending_mission_command[i] = state.has_pending_mission_command ? 1u : 0u;
    }

    return soa;
}

std::vector<ExactWorldStepStateV1> unpack_exact_world_step_states_v1_command_lane_soa(
    const ExactWorldStepCommandLaneSoA& soa,
    const std::vector<ExactWorldStepStateV1>& basis_states
) {
    if (soa.size != basis_states.size()) {
        throw std::invalid_argument("command-lane SoA size must match basis state count");
    }

    std::vector<ExactWorldStepStateV1> out = basis_states;
    for (std::size_t i = 0; i < soa.size; ++i) {
        auto& state = out[i];
        state.time_step_s = soa.time_step_s[i];
        state.world_time_s = soa.world_time_s[i];
        state.transform.heading = soa.heading_deg[i];
        state.transform.z = soa.altitude_m[i];
        state.velocity.vx = soa.vx_mps[i];
        state.velocity.vy = soa.vy_mps[i];
        state.velocity.vz = soa.vz_mps[i];

        state.movement_command = soa.movement_command[i];
        state.action_command = soa.action_command[i];
        state.mission_command = soa.mission_command[i];
        state.action_space_config = soa.action_space_config[i];
        state.command_lag = soa.command_lag[i];
        state.lagged_command = soa.lagged_command[i];
        state.command_link = soa.command_link[i];
        state.pending_movement_command = soa.pending_movement_command[i];
        state.pending_action_command = soa.pending_action_command[i];
        state.pending_mission_command = soa.pending_mission_command[i];

        state.has_movement_command = soa.has_movement_command[i] != 0;
        state.has_action_command = soa.has_action_command[i] != 0;
        state.has_mission_command = soa.has_mission_command[i] != 0;
        state.has_action_space_config = soa.has_action_space_config[i] != 0;
        state.has_command_lag = soa.has_command_lag[i] != 0;
        state.has_lagged_command = soa.has_lagged_command[i] != 0;
        state.has_command_link = soa.has_command_link[i] != 0;
        state.has_pending_movement_command = soa.has_pending_movement_command[i] != 0;
        state.has_pending_action_command = soa.has_pending_action_command[i] != 0;
        state.has_pending_mission_command = soa.has_pending_mission_command[i] != 0;
    }
    return out;
}

std::vector<ExactWorldStepStateV1> step_exact_world_step_command_lane_reference_cpu_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
) {
    const auto start = std::chrono::steady_clock::now();
    ExactWorldStepCommandLaneSoA soa = pack_exact_world_step_states_v1_command_lane_soa(initial_states);
    for (std::size_t i = 0; i < soa.size; ++i) {
        soa.world_time_s[i] += frame_delta_s(soa.time_step_s[i]);
        run_command_link_stage(soa, i);
        run_action_mapping_stage(soa, i);
        run_command_lag_stage(soa, i);
    }
    auto out = unpack_exact_world_step_states_v1_command_lane_soa(soa, initial_states);
    const auto end = std::chrono::steady_clock::now();

    g_last_stats.state_count = initial_states.size();
    g_last_stats.total_ms = std::chrono::duration<double, std::milli>(end - start).count();
    return out;
}

const ExactWorldStepCommandLaneStats& last_exact_world_step_command_lane_stats() noexcept {
    return g_last_stats;
}

}  // namespace gpu
