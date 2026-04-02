#pragma once

#include <cstddef>
#include <vector>

namespace gpu {

struct WorldBatchStepState {
    double x_m = 0.0;
    double y_m = 0.0;
    double z_m = 0.0;
    double vx_mps = 0.0;
    double vy_mps = 0.0;
    double vz_mps = 0.0;
    double wind_vx_mps = 0.0;
    double wind_vy_mps = 0.0;
    double cmd_vx_mps = 0.0;
    double cmd_vy_mps = 0.0;
    double cmd_vz_mps = 0.0;
    double max_delta_vxy_mps_per_step = 1.0;
    double max_delta_vz_mps_per_step = 1.0;
    double time_step_s = 1.0 / 20.0;
    double fuel_kg = 2500.0;
    double fuel_idle_burn_kgps = 0.2;
    double fuel_burn_per_speed_kgps_per_mps = 0.001;
    double mission_time_s = 0.0;
};

struct WorldBatchStepExperimentStats {
    bool used_cuda = false;
    bool used_cuda_graph = false;
    double host_to_device_ms = 0.0;
    double graph_capture_ms = 0.0;
    double kernel_ms = 0.0;
    double device_to_host_ms = 0.0;
    double total_ms = 0.0;
};

WorldBatchStepExperimentStats last_world_batch_step_stats();
const void* last_world_batch_step_output_device_ptr();
std::size_t last_world_batch_step_output_state_count();

std::vector<WorldBatchStepState> step_world_batch_reference_cpu_batch(
    const std::vector<WorldBatchStepState>& initial_states,
    int steps
);

std::vector<WorldBatchStepState> step_world_batch_experiment_batch(
    const std::vector<WorldBatchStepState>& initial_states,
    int steps,
    bool use_cuda_graph = false
);

bool upload_world_batch_step_states(
    const std::vector<WorldBatchStepState>& initial_states
);

bool replay_world_batch_step_device_sequence(
    int steps,
    bool use_cuda_graph = false
);

std::vector<WorldBatchStepState> download_world_batch_step_states();

}  // namespace gpu
