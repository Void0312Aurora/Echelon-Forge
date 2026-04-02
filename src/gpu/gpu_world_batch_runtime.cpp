#include "gpu/gpu_world_batch_runtime.h"

#include <algorithm>
#include <cmath>

namespace gpu::detail {

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
std::vector<WorldBatchStepState> step_world_batch_experiment_batch_cuda(
    const std::vector<WorldBatchStepState>& initial_states,
    int steps,
    bool use_cuda_graph
);
bool upload_world_batch_step_states_cuda(
    const std::vector<WorldBatchStepState>& initial_states
);
bool replay_world_batch_step_device_sequence_cuda(
    int steps,
    bool use_cuda_graph
);
std::vector<WorldBatchStepState> download_world_batch_step_states_cuda();
WorldBatchStepExperimentStats last_world_batch_step_cuda_stats();
const void* last_world_batch_step_output_device_ptr_cuda();
std::size_t last_world_batch_step_output_state_count_cuda();
#endif

}  // namespace gpu::detail

namespace gpu {

namespace {

inline double clamp_symmetric(double value, double limit) {
    return std::clamp(value, -limit, limit);
}

inline void step_state_once(WorldBatchStepState* state) {
    auto& s = *state;
    const double dvx = clamp_symmetric(s.cmd_vx_mps - s.vx_mps, s.max_delta_vxy_mps_per_step);
    const double dvy = clamp_symmetric(s.cmd_vy_mps - s.vy_mps, s.max_delta_vxy_mps_per_step);
    const double dvz = clamp_symmetric(s.cmd_vz_mps - s.vz_mps, s.max_delta_vz_mps_per_step);

    s.vx_mps += dvx;
    s.vy_mps += dvy;
    s.vz_mps += dvz;

    const double ground_vx_mps = s.vx_mps + s.wind_vx_mps;
    const double ground_vy_mps = s.vy_mps + s.wind_vy_mps;

    s.x_m += ground_vx_mps * s.time_step_s;
    s.y_m += ground_vy_mps * s.time_step_s;
    s.z_m += s.vz_mps * s.time_step_s;
    if (s.z_m < 0.0) {
        s.z_m = 0.0;
        if (s.vz_mps < 0.0) {
            s.vz_mps = 0.0;
        }
    }

    const double speed_metric_mps = std::abs(s.vx_mps) + std::abs(s.vy_mps) + std::abs(s.vz_mps);
    const double fuel_burn_kg =
        (s.fuel_idle_burn_kgps + s.fuel_burn_per_speed_kgps_per_mps * speed_metric_mps) *
        s.time_step_s;
    s.fuel_kg = std::max(0.0, s.fuel_kg - fuel_burn_kg);
    s.mission_time_s += s.time_step_s;
}

}  // namespace

WorldBatchStepExperimentStats last_world_batch_step_stats() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::last_world_batch_step_cuda_stats();
#else
    return WorldBatchStepExperimentStats{};
#endif
}

const void* last_world_batch_step_output_device_ptr() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::last_world_batch_step_output_device_ptr_cuda();
#else
    return nullptr;
#endif
}

std::size_t last_world_batch_step_output_state_count() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::last_world_batch_step_output_state_count_cuda();
#else
    return 0;
#endif
}

std::vector<WorldBatchStepState> step_world_batch_reference_cpu_batch(
    const std::vector<WorldBatchStepState>& initial_states,
    int steps
) {
    const int bounded_steps = std::max(0, steps);
    std::vector<WorldBatchStepState> out = initial_states;
    for (int step_index = 0; step_index < bounded_steps; ++step_index) {
        for (auto& state : out) {
            step_state_once(&state);
        }
    }
    return out;
}

std::vector<WorldBatchStepState> step_world_batch_experiment_batch(
    const std::vector<WorldBatchStepState>& initial_states,
    int steps,
    bool use_cuda_graph
) {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::step_world_batch_experiment_batch_cuda(initial_states, steps, use_cuda_graph);
#else
    (void)use_cuda_graph;
    return step_world_batch_reference_cpu_batch(initial_states, steps);
#endif
}

bool upload_world_batch_step_states(
    const std::vector<WorldBatchStepState>& initial_states
) {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::upload_world_batch_step_states_cuda(initial_states);
#else
    (void)initial_states;
    return false;
#endif
}

bool replay_world_batch_step_device_sequence(
    int steps,
    bool use_cuda_graph
) {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::replay_world_batch_step_device_sequence_cuda(steps, use_cuda_graph);
#else
    (void)steps;
    (void)use_cuda_graph;
    return false;
#endif
}

std::vector<WorldBatchStepState> download_world_batch_step_states() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::download_world_batch_step_states_cuda();
#else
    return {};
#endif
}

}  // namespace gpu
