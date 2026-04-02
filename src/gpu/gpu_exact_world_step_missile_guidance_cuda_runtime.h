#pragma once

#include <cstddef>
#include <vector>

namespace gpu {

struct ExactWorldStepStateV1;

struct ExactWorldStepMissileGuidanceCudaStats {
    std::size_t state_count = 0;
    std::size_t missile_count = 0;
    bool used_cuda = false;
    double host_to_device_ms = 0.0;
    double kernel_ms = 0.0;
    double device_to_host_ms = 0.0;
    double cpu_fallback_ms = 0.0;
    double total_ms = 0.0;
};

std::vector<ExactWorldStepStateV1> step_exact_world_step_missile_guidance_cuda_reference_cpu_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
);

std::vector<ExactWorldStepStateV1> step_exact_world_step_missile_guidance_cuda_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
);

const ExactWorldStepMissileGuidanceCudaStats& last_exact_world_step_missile_guidance_cuda_stats() noexcept;

}  // namespace gpu
