#pragma once

#include "gpu/gpu_exact_world_step_contract.h"
#include "gpu/gpu_exact_world_step_runtime_types.h"

namespace gpu {

ExactWorldStepPrototypeStats last_exact_world_step_prototype_stats();

ExactWorldStepPrototypeSoA pack_exact_world_step_states_v1_prototype_soa(
    const std::vector<ExactWorldStepStateV1>& states
);

std::vector<ExactWorldStepStateV1> unpack_exact_world_step_states_v1_prototype_soa(
    const ExactWorldStepPrototypeSoA& soa,
    const std::vector<ExactWorldStepStateV1>& basis_states
);

std::vector<ExactWorldStepStateV1> step_exact_world_step_states_v1_prototype_reference_cpu_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states,
    int steps
);

std::vector<ExactWorldStepStateV1> step_exact_world_step_states_v1_prototype_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states,
    int steps
);

}  // namespace gpu
