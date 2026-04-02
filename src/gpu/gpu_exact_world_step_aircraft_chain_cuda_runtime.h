#pragma once

#include <cstddef>
#include <vector>

namespace gpu {

struct ExactWorldStepStateV1;
namespace aircraft_chain_cuda {
struct ExactWorldStepAircraftChainCudaState;
}

struct ExactWorldStepAircraftChainCudaStats {
    std::size_t state_count = 0;
    bool used_cuda = false;
    double command_lane_ms = 0.0;
    double host_to_device_ms = 0.0;
    double kernel_ms = 0.0;
    double device_to_host_ms = 0.0;
    double cpu_post_command_ms = 0.0;
    double total_ms = 0.0;
};

std::vector<ExactWorldStepStateV1> step_exact_world_step_aircraft_chain_cuda_reference_cpu_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
);

std::vector<ExactWorldStepStateV1> step_exact_world_step_aircraft_chain_cuda_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
);

std::vector<aircraft_chain_cuda::ExactWorldStepAircraftChainCudaState> pack_exact_world_step_aircraft_chain_cuda_states(
    const std::vector<ExactWorldStepStateV1>& states
);

std::vector<ExactWorldStepStateV1> unpack_exact_world_step_aircraft_chain_cuda_states(
    const std::vector<aircraft_chain_cuda::ExactWorldStepAircraftChainCudaState>& states,
    const std::vector<ExactWorldStepStateV1>& basis_states
);

const ExactWorldStepAircraftChainCudaStats& last_exact_world_step_aircraft_chain_cuda_stats() noexcept;

}  // namespace gpu
