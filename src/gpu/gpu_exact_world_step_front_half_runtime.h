#pragma once

#include <cstddef>
#include <vector>

namespace gpu {

struct ExactWorldStepStateV1;

enum class ExactWorldStepFrontHalfStopStage {
    FlightControl = 0,
    ClearForces = 1,
    ComputeAeroState = 2,
    ComputeForces = 3,
    ComputeAerodynamics = 4,
    GroundContact = 5,
};

struct ExactWorldStepFrontHalfStats {
    std::size_t state_count = 0;
    bool used_cuda = false;
    double command_lane_ms = 0.0;
    double host_to_device_ms = 0.0;
    double kernel_ms = 0.0;
    double device_to_host_ms = 0.0;
    double cpu_post_command_ms = 0.0;
    double total_ms = 0.0;
};

std::vector<ExactWorldStepStateV1> step_exact_world_step_front_half_reference_cpu_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
);

std::vector<ExactWorldStepStateV1> step_exact_world_step_front_half_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
);

std::vector<ExactWorldStepStateV1> step_exact_world_step_front_half_until_stage_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states,
    ExactWorldStepFrontHalfStopStage stop_stage
);

const ExactWorldStepFrontHalfStats& last_exact_world_step_front_half_stats() noexcept;

}  // namespace gpu
