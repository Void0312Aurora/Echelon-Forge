#pragma once

#include <cstddef>
#include <vector>

#include "gpu/gpu_exact_world_step_contract.h"

namespace gpu {

struct ExactWorldStepCommandLaneStats {
    std::size_t state_count = 0;
    double total_ms = 0.0;
};

struct ExactWorldStepCommandLaneSoA {
    std::size_t size = 0;

    std::vector<double> time_step_s;
    std::vector<double> world_time_s;

    std::vector<double> heading_deg;
    std::vector<double> altitude_m;
    std::vector<double> vx_mps;
    std::vector<double> vy_mps;
    std::vector<double> vz_mps;

    std::vector<MovementCommand> movement_command;
    std::vector<ActionCommand> action_command;
    std::vector<MissionCommand> mission_command;
    std::vector<ActionSpaceConfig> action_space_config;
    std::vector<CommandLag> command_lag;
    std::vector<LaggedCommand> lagged_command;
    std::vector<CommandLink> command_link;
    std::vector<PendingMovementCommand> pending_movement_command;
    std::vector<PendingActionCommand> pending_action_command;
    std::vector<PendingMissionCommand> pending_mission_command;

    std::vector<std::uint8_t> has_movement_command;
    std::vector<std::uint8_t> has_action_command;
    std::vector<std::uint8_t> has_mission_command;
    std::vector<std::uint8_t> has_action_space_config;
    std::vector<std::uint8_t> has_command_lag;
    std::vector<std::uint8_t> has_lagged_command;
    std::vector<std::uint8_t> has_command_link;
    std::vector<std::uint8_t> has_pending_movement_command;
    std::vector<std::uint8_t> has_pending_action_command;
    std::vector<std::uint8_t> has_pending_mission_command;
};

ExactWorldStepCommandLaneSoA pack_exact_world_step_states_v1_command_lane_soa(
    const std::vector<ExactWorldStepStateV1>& states
);

std::vector<ExactWorldStepStateV1> unpack_exact_world_step_states_v1_command_lane_soa(
    const ExactWorldStepCommandLaneSoA& soa,
    const std::vector<ExactWorldStepStateV1>& basis_states
);

std::vector<ExactWorldStepStateV1> step_exact_world_step_command_lane_reference_cpu_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
);

const ExactWorldStepCommandLaneStats& last_exact_world_step_command_lane_stats() noexcept;

}  // namespace gpu
