#include "gpu/gpu_world_batch_runtime.h"

#include <cuda_runtime_api.h>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <vector>

namespace {

gpu::WorldBatchStepExperimentStats g_last_stats{};
const void* g_last_output_device_ptr = nullptr;
std::size_t g_last_output_state_count = 0;

struct DeviceWorldBatchStepCache {
    gpu::WorldBatchStepState* d_initial_states = nullptr;
    gpu::WorldBatchStepState* d_active_states = nullptr;
    std::size_t state_capacity = 0;
    std::size_t uploaded_state_count = 0;
    cudaStream_t stream = nullptr;
    cudaGraph_t graph = nullptr;
    cudaGraphExec_t graph_exec = nullptr;
    std::size_t graph_state_count = 0;
    int graph_steps = -1;
};

DeviceWorldBatchStepCache g_cache{};

__host__ __device__ inline double clamp_symmetric(double value, double limit) {
    return fmin(fmax(value, -limit), limit);
}

__host__ __device__ inline void step_state_once(gpu::WorldBatchStepState* state) {
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

    const double speed_metric_mps = fabs(s.vx_mps) + fabs(s.vy_mps) + fabs(s.vz_mps);
    const double fuel_burn_kg =
        (s.fuel_idle_burn_kgps + s.fuel_burn_per_speed_kgps_per_mps * speed_metric_mps) *
        s.time_step_s;
    s.fuel_kg = fmax(0.0, s.fuel_kg - fuel_burn_kg);
    s.mission_time_s += s.time_step_s;
}

__global__ void copy_world_batch_states_kernel(
    gpu::WorldBatchStepState* dst,
    const gpu::WorldBatchStepState* src,
    int count
) {
    const int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= count) {
        return;
    }
    dst[idx] = src[idx];
}

__global__ void step_world_batch_states_kernel(
    gpu::WorldBatchStepState* states,
    int count
) {
    const int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= count) {
        return;
    }
    step_state_once(&states[idx]);
}

void release_graph() {
    if (g_cache.graph_exec != nullptr) {
        cudaGraphExecDestroy(g_cache.graph_exec);
        g_cache.graph_exec = nullptr;
    }
    if (g_cache.graph != nullptr) {
        cudaGraphDestroy(g_cache.graph);
        g_cache.graph = nullptr;
    }
    g_cache.graph_state_count = 0;
    g_cache.graph_steps = -1;
}

bool ensure_stream() {
    if (g_cache.stream != nullptr) {
        return true;
    }
    return cudaStreamCreate(&g_cache.stream) == cudaSuccess;
}

bool ensure_cache_capacity(std::size_t state_count) {
    if (state_count <= g_cache.state_capacity) {
        return true;
    }
    release_graph();
    if (g_cache.d_initial_states != nullptr) {
        cudaFree(g_cache.d_initial_states);
        g_cache.d_initial_states = nullptr;
    }
    if (g_cache.d_active_states != nullptr) {
        cudaFree(g_cache.d_active_states);
        g_cache.d_active_states = nullptr;
    }
    if (cudaMalloc(&g_cache.d_initial_states, state_count * sizeof(gpu::WorldBatchStepState)) != cudaSuccess) {
        return false;
    }
    if (cudaMalloc(&g_cache.d_active_states, state_count * sizeof(gpu::WorldBatchStepState)) != cudaSuccess) {
        cudaFree(g_cache.d_initial_states);
        g_cache.d_initial_states = nullptr;
        return false;
    }
    g_cache.state_capacity = state_count;
    return true;
}

bool ensure_graph(std::size_t state_count, int steps) {
    if (!ensure_stream()) {
        return false;
    }
    if (g_cache.graph_exec != nullptr &&
        g_cache.graph_state_count == state_count &&
        g_cache.graph_steps == steps) {
        return true;
    }

    release_graph();
    const auto capture_t0 = std::chrono::steady_clock::now();
    if (cudaStreamBeginCapture(g_cache.stream, cudaStreamCaptureModeGlobal) != cudaSuccess) {
        return false;
    }

    const int threads = 256;
    const int blocks = static_cast<int>((state_count + static_cast<std::size_t>(threads) - 1u) / static_cast<std::size_t>(threads));
    copy_world_batch_states_kernel<<<blocks, threads, 0, g_cache.stream>>>(
        g_cache.d_active_states,
        g_cache.d_initial_states,
        static_cast<int>(state_count)
    );
    for (int step_idx = 0; step_idx < steps; ++step_idx) {
        step_world_batch_states_kernel<<<blocks, threads, 0, g_cache.stream>>>(
            g_cache.d_active_states,
            static_cast<int>(state_count)
        );
    }

    if (cudaStreamEndCapture(g_cache.stream, &g_cache.graph) != cudaSuccess) {
        release_graph();
        return false;
    }
    if (cudaGraphInstantiate(&g_cache.graph_exec, g_cache.graph, nullptr, nullptr, 0) != cudaSuccess) {
        release_graph();
        return false;
    }
    const auto capture_t1 = std::chrono::steady_clock::now();
    g_last_stats.graph_capture_ms =
        std::chrono::duration<double, std::milli>(capture_t1 - capture_t0).count();
    g_cache.graph_state_count = state_count;
    g_cache.graph_steps = steps;
    return true;
}

bool upload_initial_states(
    const std::vector<gpu::WorldBatchStepState>& initial_states
) {
    const std::size_t state_count = initial_states.size();
    if (!ensure_cache_capacity(state_count)) {
        return false;
    }
    const auto t0 = std::chrono::steady_clock::now();
    if (state_count > 0) {
        if (cudaMemcpy(
                g_cache.d_initial_states,
                initial_states.data(),
                state_count * sizeof(gpu::WorldBatchStepState),
                cudaMemcpyHostToDevice
            ) != cudaSuccess) {
            return false;
        }
    }
    const auto t1 = std::chrono::steady_clock::now();
    g_cache.uploaded_state_count = state_count;
    g_last_output_device_ptr = g_cache.d_active_states;
    g_last_output_state_count = state_count;
    g_last_stats = gpu::WorldBatchStepExperimentStats{};
    g_last_stats.used_cuda = true;
    g_last_stats.host_to_device_ms =
        std::chrono::duration<double, std::milli>(t1 - t0).count();
    g_last_stats.total_ms = g_last_stats.host_to_device_ms;
    if (g_cache.graph_state_count != state_count) {
        release_graph();
    }
    return true;
}

bool replay_uploaded_states(
    int steps,
    bool use_cuda_graph
) {
    if (g_cache.uploaded_state_count == 0) {
        return true;
    }
    if (!ensure_stream()) {
        return false;
    }
    g_last_stats.used_cuda = true;
    g_last_stats.used_cuda_graph = use_cuda_graph;
    g_last_stats.kernel_ms = 0.0;
    if (!use_cuda_graph) {
        g_last_stats.graph_capture_ms = 0.0;
    }

    cudaEvent_t start_event = nullptr;
    cudaEvent_t stop_event = nullptr;
    cudaEventCreate(&start_event);
    cudaEventCreate(&stop_event);

    const auto t0 = std::chrono::steady_clock::now();
    cudaEventRecord(start_event, g_cache.stream);
    if (use_cuda_graph) {
        if (!ensure_graph(g_cache.uploaded_state_count, steps)) {
            cudaEventDestroy(start_event);
            cudaEventDestroy(stop_event);
            return false;
        }
        if (cudaGraphLaunch(g_cache.graph_exec, g_cache.stream) != cudaSuccess) {
            cudaEventDestroy(start_event);
            cudaEventDestroy(stop_event);
            return false;
        }
    } else {
        const int threads = 256;
        const int blocks = static_cast<int>(
            (g_cache.uploaded_state_count + static_cast<std::size_t>(threads) - 1u) /
            static_cast<std::size_t>(threads)
        );
        copy_world_batch_states_kernel<<<blocks, threads, 0, g_cache.stream>>>(
            g_cache.d_active_states,
            g_cache.d_initial_states,
            static_cast<int>(g_cache.uploaded_state_count)
        );
        for (int step_idx = 0; step_idx < steps; ++step_idx) {
            step_world_batch_states_kernel<<<blocks, threads, 0, g_cache.stream>>>(
                g_cache.d_active_states,
                static_cast<int>(g_cache.uploaded_state_count)
            );
        }
    }
    cudaEventRecord(stop_event, g_cache.stream);
    if (cudaStreamSynchronize(g_cache.stream) != cudaSuccess) {
        cudaEventDestroy(start_event);
        cudaEventDestroy(stop_event);
        return false;
    }
    const auto t1 = std::chrono::steady_clock::now();

    float kernel_ms = 0.0f;
    cudaEventElapsedTime(&kernel_ms, start_event, stop_event);
    cudaEventDestroy(start_event);
    cudaEventDestroy(stop_event);

    g_last_stats.kernel_ms = static_cast<double>(kernel_ms);
    g_last_stats.total_ms =
        std::chrono::duration<double, std::milli>(t1 - t0).count();
    g_last_output_device_ptr = g_cache.d_active_states;
    g_last_output_state_count = g_cache.uploaded_state_count;
    return true;
}

std::vector<gpu::WorldBatchStepState> download_active_states() {
    std::vector<gpu::WorldBatchStepState> out(g_cache.uploaded_state_count);
    const auto t0 = std::chrono::steady_clock::now();
    if (!out.empty()) {
        cudaMemcpy(
            out.data(),
            g_cache.d_active_states,
            out.size() * sizeof(gpu::WorldBatchStepState),
            cudaMemcpyDeviceToHost
        );
    }
    const auto t1 = std::chrono::steady_clock::now();
    g_last_stats.device_to_host_ms =
        std::chrono::duration<double, std::milli>(t1 - t0).count();
    g_last_stats.total_ms += g_last_stats.device_to_host_ms;
    return out;
}

}  // namespace

namespace gpu::detail {

std::vector<WorldBatchStepState> step_world_batch_experiment_batch_cuda(
    const std::vector<WorldBatchStepState>& initial_states,
    int steps,
    bool use_cuda_graph
) {
    if (!upload_initial_states(initial_states)) {
        return {};
    }
    if (!replay_uploaded_states(std::max(0, steps), use_cuda_graph)) {
        return {};
    }
    return download_active_states();
}

bool upload_world_batch_step_states_cuda(
    const std::vector<WorldBatchStepState>& initial_states
) {
    return upload_initial_states(initial_states);
}

bool replay_world_batch_step_device_sequence_cuda(
    int steps,
    bool use_cuda_graph
) {
    return replay_uploaded_states(std::max(0, steps), use_cuda_graph);
}

std::vector<WorldBatchStepState> download_world_batch_step_states_cuda() {
    return download_active_states();
}

WorldBatchStepExperimentStats last_world_batch_step_cuda_stats() {
    return g_last_stats;
}

const void* last_world_batch_step_output_device_ptr_cuda() {
    return g_last_output_device_ptr;
}

std::size_t last_world_batch_step_output_state_count_cuda() {
    return g_last_output_state_count;
}

}  // namespace gpu::detail
