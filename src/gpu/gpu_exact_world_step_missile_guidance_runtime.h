#pragma once

#include <cstddef>
#include <vector>

#include "gpu/gpu_exact_world_step_contract.h"

namespace gpu {

struct ExactWorldStepMissileGuidanceStats {
    std::size_t state_count = 0;
    std::size_t missile_count = 0;
    double total_ms = 0.0;
};

std::vector<ExactWorldStepStateV1> step_exact_world_step_missile_guidance_reference_cpu_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
);

const ExactWorldStepMissileGuidanceStats& last_exact_world_step_missile_guidance_stats() noexcept;

}  // namespace gpu
