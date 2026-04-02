#pragma once

#include <cstddef>
#include <vector>

#include "gpu/gpu_exact_world_step_aircraft_chain_cuda_runtime_types.h"

namespace gpu {

struct ExactWorldStepStateV1;

struct ExactWorldStepFirstScopeChainCudaStats {
    std::size_t state_count = 0;
    std::size_t missile_count = 0;
    bool used_cuda = false;
    double command_lane_ms = 0.0;
    double host_to_device_ms = 0.0;
    double front_kernel_ms = 0.0;
    double guidance_kernel_ms = 0.0;
    double tail_kernel_ms = 0.0;
    double kernel_ms = 0.0;
    double device_to_host_ms = 0.0;
    double cpu_fallback_ms = 0.0;
    double total_ms = 0.0;
};

struct ExactWorldStepFirstScopeChainCudaResidentProjection {
    double world_time_s = 0.0;
    aircraft_chain_cuda::PilotAction pilot_action{};
    aircraft_chain_cuda::MissionCommand mission_command{};
    aircraft_chain_cuda::MovementCommand movement_command{};
    bool has_pilot_action = false;
    bool has_mission_command = false;
    bool has_movement_command = false;
};

struct ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection {
    double world_time_s = 0.0;
    aircraft_chain_cuda::PilotAction pilot_action{};
    bool has_pilot_action = false;
};

std::vector<ExactWorldStepStateV1> step_exact_world_step_first_scope_chain_cuda_reference_cpu_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
);

std::vector<ExactWorldStepStateV1> step_exact_world_step_first_scope_chain_cuda_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
);

bool upload_exact_world_step_first_scope_chain_cuda_states(
    const std::vector<ExactWorldStepStateV1>& initial_states
);

bool upload_exact_world_step_first_scope_chain_cuda_states_raw(
    const std::vector<ExactWorldStepStateV1>& initial_states
);

bool sync_exact_world_step_first_scope_chain_cuda_resident_projection(
    const std::vector<ExactWorldStepStateV1>& projected_states
);

bool sync_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection(
    const std::vector<ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection>& projections
);

bool sync_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_raw(
    const ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection* projections,
    std::size_t state_count
);

bool sync_replay_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_current(
    const std::vector<ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection>& projections
);

bool sync_replay_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_current_raw(
    const ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection* projections,
    std::size_t state_count
);

ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection*
acquire_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_host_buffer(
    std::size_t state_count
);

bool replay_exact_world_step_first_scope_chain_cuda_device_sequence();

bool replay_exact_world_step_first_scope_chain_cuda_resident_current();

bool replay_exact_world_step_first_scope_chain_cuda_resident_aircraft_only_advance_time_current();

std::vector<ExactWorldStepStateV1> download_exact_world_step_first_scope_chain_cuda_states();

std::vector<ExactWorldStepStateV1> download_exact_world_step_first_scope_chain_cuda_states_with_basis(
    const std::vector<ExactWorldStepStateV1>& basis_states
);

const void* last_exact_world_step_first_scope_chain_cuda_output_device_ptr() noexcept;

std::size_t last_exact_world_step_first_scope_chain_cuda_output_state_count() noexcept;

const ExactWorldStepFirstScopeChainCudaStats& last_exact_world_step_first_scope_chain_cuda_stats() noexcept;

}  // namespace gpu
