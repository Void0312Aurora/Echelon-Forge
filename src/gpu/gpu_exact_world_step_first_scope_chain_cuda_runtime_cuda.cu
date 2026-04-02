#include "gpu/gpu_exact_world_step_first_scope_chain_cuda_runtime.h"
#include "gpu/gpu_exact_world_step_first_scope_chain_cuda_runtime_types.h"

#include <cuda_runtime_api.h>

#include <chrono>
#include <cmath>
#include <vector>

#define EF_AIRCRAFT_CHAIN_CUDA_DEVICE_ONLY 1
#include "gpu/gpu_exact_world_step_aircraft_chain_cuda_runtime_cuda.cu"
#undef EF_AIRCRAFT_CHAIN_CUDA_DEVICE_ONLY

namespace {

using Detection = gpu::missile_guidance_cuda::Detection;
using FirstScopeChainState = gpu::first_scope_chain_cuda::ExactWorldStepFirstScopeChainCudaState;
using Missile = gpu::missile_guidance_cuda::Missile;
using Projection = gpu::ExactWorldStepFirstScopeChainCudaResidentProjection;
using PilotTimeProjection = gpu::ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection;

gpu::ExactWorldStepFirstScopeChainCudaStats g_last_cuda_stats{};
const void* g_last_output_device_ptr = nullptr;
std::size_t g_last_output_state_count = 0;

struct DeviceFirstScopeChainCache {
    FirstScopeChainState* d_initial_states = nullptr;
    FirstScopeChainState* d_active_states = nullptr;
    Projection* d_resident_projection = nullptr;
    PilotTimeProjection* d_resident_pilot_time_projection = nullptr;
    PilotTimeProjection* h_resident_pilot_time_projection = nullptr;
    std::size_t* d_missile_counter = nullptr;
    std::size_t state_capacity = 0;
    std::size_t uploaded_state_count = 0;
    std::size_t uploaded_missile_count = 0;
    std::size_t resident_pilot_time_host_capacity = 0;
    cudaStream_t stream = nullptr;
    cudaEvent_t timing_event0 = nullptr;
    cudaEvent_t timing_event1 = nullptr;
    cudaEvent_t timing_event2 = nullptr;
    cudaGraph_t resident_pilot_time_graph = nullptr;
    cudaGraphExec_t resident_pilot_time_graph_exec = nullptr;
    cudaGraphNode_t resident_pilot_time_graph_memcpy_node = nullptr;
    std::size_t resident_pilot_time_graph_state_count = 0;
    int resident_pilot_time_graph_fbw_mode_code = 0;
    RotationalParams resident_pilot_time_graph_params{};
    const PilotTimeProjection* resident_pilot_time_graph_host_projection_ptr = nullptr;
    bool resident_pilot_time_graph_params_valid = false;
    cudaGraph_t resident_aircraft_only_advance_time_graph = nullptr;
    cudaGraphExec_t resident_aircraft_only_advance_time_graph_exec = nullptr;
    std::size_t resident_aircraft_only_advance_time_graph_state_count = 0;
    int resident_aircraft_only_advance_time_graph_fbw_mode_code = 0;
    RotationalParams resident_aircraft_only_advance_time_graph_params{};
    bool resident_aircraft_only_advance_time_graph_params_valid = false;
};

DeviceFirstScopeChainCache g_cache{};

bool ensure_stream();
bool ensure_timing_events();

__global__ void apply_first_scope_chain_resident_pilot_time_projection_aircraft_only_kernel(
    FirstScopeChainState* states,
    const PilotTimeProjection* projections,
    int count,
    int fbw_mode_code,
    RotationalParams params
);

__global__ void exact_world_step_first_scope_chain_aircraft_only_advance_time_kernel(
    FirstScopeChainState* states,
    std::size_t count,
    int fbw_mode_code,
    RotationalParams params
);

bool measure_event_elapsed_ms(cudaEvent_t start, cudaEvent_t stop, double* out_ms) {
    if (out_ms == nullptr) {
        return false;
    }
    float elapsed_ms = 0.0f;
    if (cudaEventElapsedTime(&elapsed_ms, start, stop) != cudaSuccess) {
        return false;
    }
    *out_ms = static_cast<double>(elapsed_ms);
    return true;
}

bool rotational_params_equal(const RotationalParams& lhs, const RotationalParams& rhs) {
    return lhs.max_rate_cross_rad_s == rhs.max_rate_cross_rad_s &&
        lhs.max_torque_nm == rhs.max_torque_nm &&
        lhs.max_ang_accel_rad_s2 == rhs.max_ang_accel_rad_s2 &&
        lhs.max_rate_rad_s == rhs.max_rate_rad_s &&
        lhs.min_abs_cos_theta == rhs.min_abs_cos_theta &&
        lhs.pitch_limit_deg == rhs.pitch_limit_deg;
}

void release_resident_pilot_time_graph() {
    if (g_cache.resident_pilot_time_graph_exec != nullptr) {
        cudaGraphExecDestroy(g_cache.resident_pilot_time_graph_exec);
        g_cache.resident_pilot_time_graph_exec = nullptr;
    }
    if (g_cache.resident_pilot_time_graph != nullptr) {
        cudaGraphDestroy(g_cache.resident_pilot_time_graph);
        g_cache.resident_pilot_time_graph = nullptr;
    }
    g_cache.resident_pilot_time_graph_memcpy_node = nullptr;
    g_cache.resident_pilot_time_graph_state_count = 0;
    g_cache.resident_pilot_time_graph_fbw_mode_code = 0;
    g_cache.resident_pilot_time_graph_params = RotationalParams{};
    g_cache.resident_pilot_time_graph_host_projection_ptr = nullptr;
    g_cache.resident_pilot_time_graph_params_valid = false;
}

void release_resident_aircraft_only_advance_time_graph() {
    if (g_cache.resident_aircraft_only_advance_time_graph_exec != nullptr) {
        cudaGraphExecDestroy(g_cache.resident_aircraft_only_advance_time_graph_exec);
        g_cache.resident_aircraft_only_advance_time_graph_exec = nullptr;
    }
    if (g_cache.resident_aircraft_only_advance_time_graph != nullptr) {
        cudaGraphDestroy(g_cache.resident_aircraft_only_advance_time_graph);
        g_cache.resident_aircraft_only_advance_time_graph = nullptr;
    }
    g_cache.resident_aircraft_only_advance_time_graph_state_count = 0;
    g_cache.resident_aircraft_only_advance_time_graph_fbw_mode_code = 0;
    g_cache.resident_aircraft_only_advance_time_graph_params = RotationalParams{};
    g_cache.resident_aircraft_only_advance_time_graph_params_valid = false;
}

bool ensure_resident_pilot_time_graph(
    std::size_t state_count,
    int fbw_mode_code,
    const RotationalParams& params,
    const PilotTimeProjection* host_projection_ptr
) {
    if (!ensure_stream() || host_projection_ptr == nullptr) {
        return false;
    }

    if (g_cache.resident_pilot_time_graph_exec != nullptr &&
        g_cache.resident_pilot_time_graph_state_count == state_count &&
        g_cache.resident_pilot_time_graph_fbw_mode_code == fbw_mode_code &&
        g_cache.resident_pilot_time_graph_host_projection_ptr == host_projection_ptr &&
        g_cache.resident_pilot_time_graph_params_valid &&
        rotational_params_equal(g_cache.resident_pilot_time_graph_params, params)) {
        return true;
    }

    release_resident_pilot_time_graph();

    const int block_size = 128;
    int state_count_int = static_cast<int>(state_count);
    const int grid_size = static_cast<int>(
        (state_count + static_cast<std::size_t>(block_size) - 1u) /
        static_cast<std::size_t>(block_size)
    );
    const std::size_t projection_bytes = state_count * sizeof(PilotTimeProjection);

    cudaGraph_t captured_graph = nullptr;
    if (cudaGraphCreate(&captured_graph, 0) != cudaSuccess) {
        return false;
    }

    if (cudaGraphAddMemcpyNode1D(
            &g_cache.resident_pilot_time_graph_memcpy_node,
            captured_graph,
            nullptr,
            0,
            g_cache.d_resident_pilot_time_projection,
            host_projection_ptr,
            projection_bytes,
            cudaMemcpyHostToDevice
        ) != cudaSuccess) {
        cudaGraphDestroy(captured_graph);
        return false;
    }

    FirstScopeChainState* active_states_arg = g_cache.d_active_states;
    PilotTimeProjection* resident_projection_arg = g_cache.d_resident_pilot_time_projection;
    int fbw_mode_code_arg = fbw_mode_code;
    RotationalParams params_arg = params;
    void* kernel_args[] = {
        &active_states_arg,
        &resident_projection_arg,
        &state_count_int,
        &fbw_mode_code_arg,
        &params_arg,
    };
    cudaKernelNodeParams kernel_params{};
    kernel_params.func = reinterpret_cast<void*>(apply_first_scope_chain_resident_pilot_time_projection_aircraft_only_kernel);
    kernel_params.gridDim = dim3(static_cast<unsigned int>(grid_size), 1u, 1u);
    kernel_params.blockDim = dim3(static_cast<unsigned int>(block_size), 1u, 1u);
    kernel_params.sharedMemBytes = 0;
    kernel_params.kernelParams = kernel_args;
    kernel_params.extra = nullptr;

    cudaGraphNode_t kernel_node = nullptr;
    if (cudaGraphAddKernelNode(
            &kernel_node,
            captured_graph,
            &g_cache.resident_pilot_time_graph_memcpy_node,
            1,
            &kernel_params
        ) != cudaSuccess) {
        cudaGraphDestroy(captured_graph);
        g_cache.resident_pilot_time_graph_memcpy_node = nullptr;
        return false;
    }

    if (cudaGraphInstantiate(
            &g_cache.resident_pilot_time_graph_exec,
            captured_graph,
            nullptr,
            nullptr,
            0
        ) != cudaSuccess) {
        if (captured_graph != nullptr) {
            cudaGraphDestroy(captured_graph);
        }
        release_resident_pilot_time_graph();
        return false;
    }

    g_cache.resident_pilot_time_graph = captured_graph;
    g_cache.resident_pilot_time_graph_state_count = state_count;
    g_cache.resident_pilot_time_graph_fbw_mode_code = fbw_mode_code;
    g_cache.resident_pilot_time_graph_params = params;
    g_cache.resident_pilot_time_graph_host_projection_ptr = host_projection_ptr;
    g_cache.resident_pilot_time_graph_params_valid = true;
    return true;
}

bool ensure_resident_aircraft_only_advance_time_graph(
    std::size_t state_count,
    int fbw_mode_code,
    const RotationalParams& params
) {
    if (!ensure_stream()) {
        return false;
    }

    if (g_cache.resident_aircraft_only_advance_time_graph_exec != nullptr &&
        g_cache.resident_aircraft_only_advance_time_graph_state_count == state_count &&
        g_cache.resident_aircraft_only_advance_time_graph_fbw_mode_code == fbw_mode_code &&
        g_cache.resident_aircraft_only_advance_time_graph_params_valid &&
        rotational_params_equal(g_cache.resident_aircraft_only_advance_time_graph_params, params)) {
        return true;
    }

    release_resident_aircraft_only_advance_time_graph();

    const int block_size = 128;
    std::size_t state_count_arg = state_count;
    const int grid_size = static_cast<int>(
        (state_count + static_cast<std::size_t>(block_size) - 1u) /
        static_cast<std::size_t>(block_size)
    );

    cudaGraph_t captured_graph = nullptr;
    if (cudaGraphCreate(&captured_graph, 0) != cudaSuccess) {
        return false;
    }

    FirstScopeChainState* active_states_arg = g_cache.d_active_states;
    int fbw_mode_code_arg = fbw_mode_code;
    RotationalParams params_arg = params;
    void* kernel_args[] = {
        &active_states_arg,
        &state_count_arg,
        &fbw_mode_code_arg,
        &params_arg,
    };
    cudaKernelNodeParams kernel_params{};
    kernel_params.func = reinterpret_cast<void*>(exact_world_step_first_scope_chain_aircraft_only_advance_time_kernel);
    kernel_params.gridDim = dim3(static_cast<unsigned int>(grid_size), 1u, 1u);
    kernel_params.blockDim = dim3(static_cast<unsigned int>(block_size), 1u, 1u);
    kernel_params.sharedMemBytes = 0;
    kernel_params.kernelParams = kernel_args;
    kernel_params.extra = nullptr;

    cudaGraphNode_t kernel_node = nullptr;
    if (cudaGraphAddKernelNode(
            &kernel_node,
            captured_graph,
            nullptr,
            0,
            &kernel_params
        ) != cudaSuccess) {
        cudaGraphDestroy(captured_graph);
        return false;
    }

    if (cudaGraphInstantiate(
            &g_cache.resident_aircraft_only_advance_time_graph_exec,
            captured_graph,
            nullptr,
            nullptr,
            0
        ) != cudaSuccess) {
        if (captured_graph != nullptr) {
            cudaGraphDestroy(captured_graph);
        }
        release_resident_aircraft_only_advance_time_graph();
        return false;
    }

    g_cache.resident_aircraft_only_advance_time_graph = captured_graph;
    g_cache.resident_aircraft_only_advance_time_graph_state_count = state_count;
    g_cache.resident_aircraft_only_advance_time_graph_fbw_mode_code = fbw_mode_code;
    g_cache.resident_aircraft_only_advance_time_graph_params = params;
    g_cache.resident_aircraft_only_advance_time_graph_params_valid = true;
    return true;
}

void destroy_timing_events() {
    if (g_cache.timing_event0 != nullptr) {
        cudaEventDestroy(g_cache.timing_event0);
        g_cache.timing_event0 = nullptr;
    }
    if (g_cache.timing_event1 != nullptr) {
        cudaEventDestroy(g_cache.timing_event1);
        g_cache.timing_event1 = nullptr;
    }
    if (g_cache.timing_event2 != nullptr) {
        cudaEventDestroy(g_cache.timing_event2);
        g_cache.timing_event2 = nullptr;
    }
}

bool ensure_timing_events() {
    if (g_cache.timing_event0 != nullptr &&
        g_cache.timing_event1 != nullptr &&
        g_cache.timing_event2 != nullptr) {
        return true;
    }
    destroy_timing_events();
    if (cudaEventCreate(&g_cache.timing_event0) != cudaSuccess) {
        destroy_timing_events();
        return false;
    }
    if (cudaEventCreate(&g_cache.timing_event1) != cudaSuccess) {
        destroy_timing_events();
        return false;
    }
    if (cudaEventCreate(&g_cache.timing_event2) != cudaSuccess) {
        destroy_timing_events();
        return false;
    }
    return true;
}

bool ensure_stream() {
    if (g_cache.stream != nullptr) {
        return true;
    }
    return cudaStreamCreate(&g_cache.stream) == cudaSuccess;
}

void free_host_pinned_projection_ptr(PilotTimeProjection*& ptr) {
    if (ptr != nullptr) {
        cudaFreeHost(ptr);
        ptr = nullptr;
    }
}

bool ensure_resident_pilot_time_host_capacity(std::size_t state_count) {
    if (state_count == 0) {
        return true;
    }
    if (g_cache.h_resident_pilot_time_projection != nullptr &&
        g_cache.resident_pilot_time_host_capacity >= state_count) {
        return true;
    }

    release_resident_pilot_time_graph();
    free_host_pinned_projection_ptr(g_cache.h_resident_pilot_time_projection);
    g_cache.resident_pilot_time_host_capacity = 0;

    if (cudaHostAlloc(
            reinterpret_cast<void**>(&g_cache.h_resident_pilot_time_projection),
            state_count * sizeof(PilotTimeProjection),
            cudaHostAllocDefault
        ) != cudaSuccess) {
        free_host_pinned_projection_ptr(g_cache.h_resident_pilot_time_projection);
        return false;
    }

    g_cache.resident_pilot_time_host_capacity = state_count;
    return true;
}

void release_cache_allocations() {
    if (g_cache.stream != nullptr) {
        cudaStreamSynchronize(g_cache.stream);
    }
    release_resident_pilot_time_graph();
    release_resident_aircraft_only_advance_time_graph();
    free_device_ptr(g_cache.d_initial_states);
    free_device_ptr(g_cache.d_active_states);
    free_device_ptr(g_cache.d_resident_projection);
    free_device_ptr(g_cache.d_resident_pilot_time_projection);
    free_host_pinned_projection_ptr(g_cache.h_resident_pilot_time_projection);
    free_device_ptr(g_cache.d_missile_counter);
    g_cache.state_capacity = 0;
    g_cache.uploaded_state_count = 0;
    g_cache.uploaded_missile_count = 0;
    g_cache.resident_pilot_time_host_capacity = 0;
}

void release_cache() {
    release_cache_allocations();
    destroy_timing_events();
    if (g_cache.stream != nullptr) {
        cudaStreamDestroy(g_cache.stream);
        g_cache.stream = nullptr;
    }
}

struct CacheCleanupGuard {
    ~CacheCleanupGuard() {
        release_cache();
    }
};

CacheCleanupGuard g_cache_cleanup_guard{};

__global__ void copy_first_scope_chain_states_kernel(
    FirstScopeChainState* dst,
    const FirstScopeChainState* src,
    int count
) {
    const int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= count || dst == nullptr || src == nullptr) {
        return;
    }
    dst[idx] = src[idx];
}

__global__ void apply_first_scope_chain_resident_projection_kernel(
    FirstScopeChainState* states,
    const Projection* projections,
    int count
) {
    const int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= count || states == nullptr || projections == nullptr) {
        return;
    }

    auto& state = states[idx];
    const auto& projection = projections[idx];
    state.world_time_s = projection.world_time_s;
    state.aircraft.pilot_action = projection.pilot_action;
    state.aircraft.mission_command = projection.mission_command;
    state.aircraft.movement_command = projection.movement_command;
    state.aircraft.has_pilot_action = projection.has_pilot_action;
    state.aircraft.has_mission_command = projection.has_mission_command;
    state.aircraft.has_movement_command = projection.has_movement_command;
}

__global__ void apply_first_scope_chain_resident_pilot_time_projection_kernel(
    FirstScopeChainState* states,
    const PilotTimeProjection* projections,
    int count
) {
    const int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= count || states == nullptr || projections == nullptr) {
        return;
    }

    auto& state = states[idx];
    const auto& projection = projections[idx];
    state.world_time_s = projection.world_time_s;
    state.aircraft.pilot_action = projection.pilot_action;
    state.aircraft.has_pilot_action = projection.has_pilot_action;
}

__global__ void apply_first_scope_chain_resident_pilot_time_projection_aircraft_only_kernel(
    FirstScopeChainState* states,
    const PilotTimeProjection* projections,
    int count,
    int fbw_mode_code,
    RotationalParams params
) {
    const int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= count || states == nullptr || projections == nullptr) {
        return;
    }

    auto& state = states[idx];
    const auto& projection = projections[idx];
    state.world_time_s = projection.world_time_s;
    state.aircraft.pilot_action = projection.pilot_action;
    state.aircraft.has_pilot_action = projection.has_pilot_action;

    auto& aircraft = state.aircraft;
    run_flight_control_stage(aircraft, static_cast<FbwProtectionMode>(fbw_mode_code));
    run_clear_forces_stage(aircraft);
    run_compute_aero_state_stage(aircraft);
    run_compute_forces_stage(aircraft);
    run_compute_aerodynamics_stage(aircraft);
    run_ground_contact_stage(aircraft);
    run_rotational_integrate_stage(aircraft, params);
    run_leapfrog_integrate_stage(aircraft);
    refresh_environment_sample_from_transform(aircraft);
    run_navigation_system_stage(aircraft);
    run_update_instruments_stage(aircraft);
    run_fuel_consumption_stage(aircraft);
    run_mass_update_stage(aircraft);
}

__global__ void exact_world_step_first_scope_chain_front_kernel(
    FirstScopeChainState* states,
    std::size_t count,
    int fbw_mode_code
);

__global__ void exact_world_step_first_scope_chain_aircraft_only_kernel(
    FirstScopeChainState* states,
    std::size_t count,
    int fbw_mode_code,
    RotationalParams params
);

__global__ void exact_world_step_first_scope_chain_guidance_kernel(
    FirstScopeChainState* states,
    std::size_t count,
    std::size_t* missile_counter
);

__global__ void exact_world_step_first_scope_chain_tail_kernel(
    FirstScopeChainState* states,
    std::size_t count,
    RotationalParams params
);

bool replay_chain_on_active_states(bool copy_from_initial);

bool ensure_cache_capacity(std::size_t state_count) {
    if (!ensure_stream()) {
        return false;
    }
    if (!ensure_timing_events()) {
        return false;
    }
    if (state_count <= g_cache.state_capacity) {
        return ensure_resident_pilot_time_host_capacity(state_count);
    }
    release_cache_allocations();

    if (cudaMalloc(&g_cache.d_initial_states, state_count * sizeof(FirstScopeChainState)) != cudaSuccess) {
        release_cache_allocations();
        return false;
    }
    if (cudaMalloc(&g_cache.d_active_states, state_count * sizeof(FirstScopeChainState)) != cudaSuccess) {
        release_cache_allocations();
        return false;
    }
    if (cudaMalloc(&g_cache.d_resident_projection, state_count * sizeof(Projection)) != cudaSuccess) {
        release_cache_allocations();
        return false;
    }
    if (cudaMalloc(&g_cache.d_resident_pilot_time_projection, state_count * sizeof(PilotTimeProjection)) != cudaSuccess) {
        release_cache_allocations();
        return false;
    }
    if (cudaMalloc(&g_cache.d_missile_counter, sizeof(std::size_t)) != cudaSuccess) {
        release_cache_allocations();
        return false;
    }
    if (!ensure_resident_pilot_time_host_capacity(state_count)) {
        release_cache_allocations();
        return false;
    }
    g_cache.state_capacity = state_count;
    return true;
}

std::size_t count_uploaded_missiles(const std::vector<FirstScopeChainState>& states) {
    std::size_t missile_count = 0;
    for (const auto& state : states) {
        if (state.has_missile) {
            ++missile_count;
        }
    }
    return missile_count;
}

bool upload_initial_states(const std::vector<FirstScopeChainState>& initial_states) {
    const std::size_t state_count = initial_states.size();
    g_last_cuda_stats = gpu::ExactWorldStepFirstScopeChainCudaStats{};
    g_last_cuda_stats.state_count = state_count;
    g_last_cuda_stats.missile_count = count_uploaded_missiles(initial_states);
    g_last_cuda_stats.used_cuda = true;

    if (state_count == 0) {
        g_cache.uploaded_state_count = 0;
        g_cache.uploaded_missile_count = 0;
        g_last_output_device_ptr = nullptr;
        g_last_output_state_count = 0;
        return true;
    }
    if (!ensure_cache_capacity(state_count)) {
        return false;
    }

    const auto h2d_start = std::chrono::steady_clock::now();
    if (cudaMemcpy(
            g_cache.d_initial_states,
            initial_states.data(),
            state_count * sizeof(FirstScopeChainState),
            cudaMemcpyHostToDevice
        ) != cudaSuccess) {
        return false;
    }
    const auto h2d_end = std::chrono::steady_clock::now();

    g_cache.uploaded_state_count = state_count;
    g_cache.uploaded_missile_count = g_last_cuda_stats.missile_count;
    g_last_output_device_ptr = g_cache.d_active_states;
    g_last_output_state_count = state_count;
    g_last_cuda_stats.host_to_device_ms =
        std::chrono::duration<double, std::milli>(h2d_end - h2d_start).count();
    g_last_cuda_stats.total_ms = g_last_cuda_stats.host_to_device_ms;
    return true;
}

bool upload_raw_states(const std::vector<FirstScopeChainState>& initial_states) {
    const std::size_t state_count = initial_states.size();
    g_last_cuda_stats = gpu::ExactWorldStepFirstScopeChainCudaStats{};
    g_last_cuda_stats.state_count = state_count;
    g_last_cuda_stats.missile_count = count_uploaded_missiles(initial_states);
    g_last_cuda_stats.used_cuda = true;

    if (state_count == 0) {
        g_cache.uploaded_state_count = 0;
        g_cache.uploaded_missile_count = 0;
        g_last_output_device_ptr = nullptr;
        g_last_output_state_count = 0;
        return true;
    }
    if (!ensure_cache_capacity(state_count)) {
        return false;
    }

    const auto h2d_start = std::chrono::steady_clock::now();
    if (cudaMemcpy(
            g_cache.d_active_states,
            initial_states.data(),
            state_count * sizeof(FirstScopeChainState),
            cudaMemcpyHostToDevice
        ) != cudaSuccess) {
        return false;
    }
    const auto h2d_end = std::chrono::steady_clock::now();

    g_cache.uploaded_state_count = state_count;
    g_cache.uploaded_missile_count = g_last_cuda_stats.missile_count;
    g_last_output_device_ptr = g_cache.d_active_states;
    g_last_output_state_count = state_count;
    g_last_cuda_stats.host_to_device_ms =
        std::chrono::duration<double, std::milli>(h2d_end - h2d_start).count();
    g_last_cuda_stats.total_ms = g_last_cuda_stats.host_to_device_ms;
    return true;
}

bool sync_resident_projection(const std::vector<Projection>& projections) {
    const std::size_t state_count = projections.size();
    g_last_cuda_stats = gpu::ExactWorldStepFirstScopeChainCudaStats{};
    g_last_cuda_stats.state_count = state_count;
    g_last_cuda_stats.used_cuda = true;

    if (state_count == 0) {
        g_cache.uploaded_state_count = 0;
        g_cache.uploaded_missile_count = 0;
        g_last_output_device_ptr = nullptr;
        g_last_output_state_count = 0;
        return true;
    }
    if (!ensure_cache_capacity(state_count) || g_cache.uploaded_state_count != state_count) {
        return false;
    }

    const int block_size = 128;
    const int grid_size = static_cast<int>(
        (state_count + static_cast<std::size_t>(block_size) - 1u) /
        static_cast<std::size_t>(block_size)
    );

    if (cudaEventRecord(g_cache.timing_event0, g_cache.stream) != cudaSuccess) {
        return false;
    }
    if (cudaMemcpyAsync(
            g_cache.d_resident_projection,
            projections.data(),
            state_count * sizeof(Projection),
            cudaMemcpyHostToDevice,
            g_cache.stream
        ) != cudaSuccess) {
        return false;
    }
    if (cudaEventRecord(g_cache.timing_event1, g_cache.stream) != cudaSuccess) {
        return false;
    }
    apply_first_scope_chain_resident_projection_kernel<<<grid_size, block_size, 0, g_cache.stream>>>(
        g_cache.d_active_states,
        g_cache.d_resident_projection,
        static_cast<int>(state_count)
    );
    if (cudaGetLastError() != cudaSuccess) {
        return false;
    }
    if (cudaEventRecord(g_cache.timing_event2, g_cache.stream) != cudaSuccess) {
        return false;
    }
    if (cudaStreamSynchronize(g_cache.stream) != cudaSuccess) {
        return false;
    }

    double host_to_device_ms = 0.0;
    double kernel_ms = 0.0;
    if (!measure_event_elapsed_ms(g_cache.timing_event0, g_cache.timing_event1, &host_to_device_ms) ||
        !measure_event_elapsed_ms(g_cache.timing_event1, g_cache.timing_event2, &kernel_ms)) {
        return false;
    }

    g_last_output_device_ptr = g_cache.d_active_states;
    g_last_output_state_count = state_count;
    g_last_cuda_stats.host_to_device_ms = host_to_device_ms;
    g_last_cuda_stats.kernel_ms = kernel_ms;
    g_last_cuda_stats.total_ms = g_last_cuda_stats.host_to_device_ms + g_last_cuda_stats.kernel_ms;
    return true;
}

bool sync_resident_pilot_time_projection_raw(
    const PilotTimeProjection* projections,
    std::size_t state_count
) {
    g_last_cuda_stats = gpu::ExactWorldStepFirstScopeChainCudaStats{};
    g_last_cuda_stats.state_count = state_count;
    g_last_cuda_stats.used_cuda = true;

    if (state_count == 0) {
        g_cache.uploaded_state_count = 0;
        g_cache.uploaded_missile_count = 0;
        g_last_output_device_ptr = nullptr;
        g_last_output_state_count = 0;
        return true;
    }
    if (!ensure_cache_capacity(state_count) || g_cache.uploaded_state_count != state_count) {
        return false;
    }
    if (projections == nullptr) {
        return false;
    }

    const int block_size = 128;
    const int grid_size = static_cast<int>(
        (state_count + static_cast<std::size_t>(block_size) - 1u) /
        static_cast<std::size_t>(block_size)
    );

    if (cudaEventRecord(g_cache.timing_event0, g_cache.stream) != cudaSuccess) {
        return false;
    }
    if (cudaMemcpyAsync(
            g_cache.d_resident_pilot_time_projection,
            projections,
            state_count * sizeof(PilotTimeProjection),
            cudaMemcpyHostToDevice,
            g_cache.stream
        ) != cudaSuccess) {
        return false;
    }
    if (cudaEventRecord(g_cache.timing_event1, g_cache.stream) != cudaSuccess) {
        return false;
    }
    apply_first_scope_chain_resident_pilot_time_projection_kernel<<<grid_size, block_size, 0, g_cache.stream>>>(
        g_cache.d_active_states,
        g_cache.d_resident_pilot_time_projection,
        static_cast<int>(state_count)
    );
    if (cudaGetLastError() != cudaSuccess) {
        return false;
    }
    if (cudaEventRecord(g_cache.timing_event2, g_cache.stream) != cudaSuccess) {
        return false;
    }
    if (cudaStreamSynchronize(g_cache.stream) != cudaSuccess) {
        return false;
    }

    double host_to_device_ms = 0.0;
    double kernel_ms = 0.0;
    if (!measure_event_elapsed_ms(g_cache.timing_event0, g_cache.timing_event1, &host_to_device_ms) ||
        !measure_event_elapsed_ms(g_cache.timing_event1, g_cache.timing_event2, &kernel_ms)) {
        return false;
    }

    g_last_output_device_ptr = g_cache.d_active_states;
    g_last_output_state_count = state_count;
    g_last_cuda_stats.host_to_device_ms = host_to_device_ms;
    g_last_cuda_stats.kernel_ms = kernel_ms;
    g_last_cuda_stats.total_ms = g_last_cuda_stats.host_to_device_ms + g_last_cuda_stats.kernel_ms;
    return true;
}

bool sync_resident_pilot_time_projection(const std::vector<PilotTimeProjection>& projections) {
    return sync_resident_pilot_time_projection_raw(projections.data(), projections.size());
}

bool sync_replay_resident_pilot_time_projection_current_raw(
    const PilotTimeProjection* projections,
    std::size_t state_count
) {
    g_last_cuda_stats = gpu::ExactWorldStepFirstScopeChainCudaStats{};
    g_last_cuda_stats.state_count = state_count;
    g_last_cuda_stats.used_cuda = true;

    if (state_count == 0) {
        g_cache.uploaded_state_count = 0;
        g_cache.uploaded_missile_count = 0;
        g_last_output_device_ptr = nullptr;
        g_last_output_state_count = 0;
        return true;
    }
    if (!ensure_cache_capacity(state_count) ||
        g_cache.uploaded_state_count != state_count ||
        g_cache.uploaded_missile_count != 0) {
        return false;
    }
    if (projections == nullptr) {
        return false;
    }

    const int block_size = 128;
    const int grid_size = static_cast<int>(
        (state_count + static_cast<std::size_t>(block_size) - 1u) /
        static_cast<std::size_t>(block_size)
    );
    const int fbw_mode_code = static_cast<int>(get_fbw_protection_mode());
    const RotationalParams params = rotational_params_host();

    bool use_graph = false;
    if (ensure_resident_pilot_time_graph(state_count, fbw_mode_code, params, projections) &&
        g_cache.resident_pilot_time_graph_memcpy_node != nullptr) {
        if (cudaEventRecord(g_cache.timing_event0, g_cache.stream) == cudaSuccess &&
            cudaGraphLaunch(g_cache.resident_pilot_time_graph_exec, g_cache.stream) == cudaSuccess &&
            cudaEventRecord(g_cache.timing_event1, g_cache.stream) == cudaSuccess) {
            use_graph = true;
        } else {
            release_resident_pilot_time_graph();
        }
    }
    if (!use_graph) {
        if (cudaEventRecord(g_cache.timing_event0, g_cache.stream) != cudaSuccess) {
            return false;
        }
        if (cudaMemcpyAsync(
                g_cache.d_resident_pilot_time_projection,
                projections,
                state_count * sizeof(PilotTimeProjection),
                cudaMemcpyHostToDevice,
                g_cache.stream
            ) != cudaSuccess) {
            return false;
        }
        if (cudaEventRecord(g_cache.timing_event1, g_cache.stream) != cudaSuccess) {
            return false;
        }
        apply_first_scope_chain_resident_pilot_time_projection_aircraft_only_kernel<<<grid_size, block_size, 0, g_cache.stream>>>(
            g_cache.d_active_states,
            g_cache.d_resident_pilot_time_projection,
            static_cast<int>(state_count),
            fbw_mode_code,
            params
        );
        if (cudaGetLastError() != cudaSuccess) {
            return false;
        }
        if (cudaEventRecord(g_cache.timing_event2, g_cache.stream) != cudaSuccess) {
            return false;
        }
    }
    if (cudaStreamSynchronize(g_cache.stream) != cudaSuccess) {
        return false;
    }

    double host_to_device_ms = 0.0;
    double kernel_ms = 0.0;
    if (use_graph) {
        if (!measure_event_elapsed_ms(g_cache.timing_event0, g_cache.timing_event1, &kernel_ms)) {
            return false;
        }
    } else {
        if (!measure_event_elapsed_ms(g_cache.timing_event0, g_cache.timing_event1, &host_to_device_ms) ||
            !measure_event_elapsed_ms(g_cache.timing_event1, g_cache.timing_event2, &kernel_ms)) {
            return false;
        }
    }

    g_last_output_device_ptr = g_cache.d_active_states;
    g_last_output_state_count = state_count;
    g_last_cuda_stats.missile_count = 0;
    g_last_cuda_stats.host_to_device_ms = host_to_device_ms;
    g_last_cuda_stats.kernel_ms = kernel_ms;
    g_last_cuda_stats.front_kernel_ms = g_last_cuda_stats.kernel_ms;
    g_last_cuda_stats.guidance_kernel_ms = 0.0;
    g_last_cuda_stats.tail_kernel_ms = 0.0;
    g_last_cuda_stats.total_ms = g_last_cuda_stats.host_to_device_ms + g_last_cuda_stats.kernel_ms;
    return true;
}

bool sync_replay_resident_pilot_time_projection_current(const std::vector<PilotTimeProjection>& projections) {
    return sync_replay_resident_pilot_time_projection_current_raw(projections.data(), projections.size());
}

bool replay_uploaded_states() {
    return replay_chain_on_active_states(true);
}

bool replay_active_states_aircraft_only_advance_time() {
    g_last_cuda_stats = gpu::ExactWorldStepFirstScopeChainCudaStats{};
    g_last_cuda_stats.state_count = g_cache.uploaded_state_count;
    g_last_cuda_stats.used_cuda = true;

    if (g_cache.uploaded_state_count == 0) {
        g_last_output_device_ptr = nullptr;
        g_last_output_state_count = 0;
        return true;
    }
    if (!ensure_stream() || !ensure_timing_events() || g_cache.uploaded_missile_count != 0) {
        return false;
    }

    const int block_size = 128;
    const int grid_size = static_cast<int>(
        (g_cache.uploaded_state_count + static_cast<std::size_t>(block_size) - 1u) /
        static_cast<std::size_t>(block_size)
    );
    const int fbw_mode_code = static_cast<int>(get_fbw_protection_mode());
    const RotationalParams params = rotational_params_host();

    bool use_graph = false;
    if (cudaEventRecord(g_cache.timing_event0, g_cache.stream) != cudaSuccess) {
        return false;
    }
    if (ensure_resident_aircraft_only_advance_time_graph(g_cache.uploaded_state_count, fbw_mode_code, params)) {
        if (cudaGraphLaunch(g_cache.resident_aircraft_only_advance_time_graph_exec, g_cache.stream) == cudaSuccess) {
            use_graph = true;
        } else {
            release_resident_aircraft_only_advance_time_graph();
        }
    }
    if (!use_graph) {
        exact_world_step_first_scope_chain_aircraft_only_advance_time_kernel<<<grid_size, block_size, 0, g_cache.stream>>>(
            g_cache.d_active_states,
            g_cache.uploaded_state_count,
            fbw_mode_code,
            params
        );
        if (cudaGetLastError() != cudaSuccess) {
            return false;
        }
    }
    if (cudaEventRecord(g_cache.timing_event1, g_cache.stream) != cudaSuccess) {
        return false;
    }
    if (cudaStreamSynchronize(g_cache.stream) != cudaSuccess) {
        return false;
    }

    double kernel_ms = 0.0;
    if (!measure_event_elapsed_ms(g_cache.timing_event0, g_cache.timing_event1, &kernel_ms)) {
        return false;
    }

    g_last_output_device_ptr = g_cache.d_active_states;
    g_last_output_state_count = g_cache.uploaded_state_count;
    g_last_cuda_stats.missile_count = 0;
    g_last_cuda_stats.host_to_device_ms = 0.0;
    g_last_cuda_stats.kernel_ms = kernel_ms;
    g_last_cuda_stats.front_kernel_ms = kernel_ms;
    g_last_cuda_stats.guidance_kernel_ms = 0.0;
    g_last_cuda_stats.tail_kernel_ms = 0.0;
    g_last_cuda_stats.total_ms = kernel_ms;
    return true;
}

bool replay_chain_on_active_states(bool copy_from_initial) {
    if (g_cache.uploaded_state_count == 0) {
        g_last_cuda_stats.used_cuda = true;
        return true;
    }

    const int block_size = 128;
    const int grid_size = static_cast<int>(
        (g_cache.uploaded_state_count + static_cast<std::size_t>(block_size) - 1u) /
        static_cast<std::size_t>(block_size)
    );
    const int fbw_mode_code = static_cast<int>(get_fbw_protection_mode());
    const RotationalParams params = rotational_params_host();
    const bool has_uploaded_missiles = g_cache.uploaded_missile_count > 0;

    if (has_uploaded_missiles &&
        cudaMemsetAsync(g_cache.d_missile_counter, 0, sizeof(std::size_t), g_cache.stream) != cudaSuccess) {
        return false;
    }

    if (cudaEventRecord(g_cache.timing_event0, g_cache.stream) != cudaSuccess) {
        return false;
    }
    if (copy_from_initial) {
        copy_first_scope_chain_states_kernel<<<grid_size, block_size, 0, g_cache.stream>>>(
            g_cache.d_active_states,
            g_cache.d_initial_states,
            static_cast<int>(g_cache.uploaded_state_count)
        );
        if (cudaGetLastError() != cudaSuccess) {
            return false;
        }
    }
    if (has_uploaded_missiles) {
        exact_world_step_first_scope_chain_front_kernel<<<grid_size, block_size, 0, g_cache.stream>>>(
            g_cache.d_active_states,
            g_cache.uploaded_state_count,
            fbw_mode_code
        );
        if (cudaGetLastError() != cudaSuccess) {
            return false;
        }
        exact_world_step_first_scope_chain_guidance_kernel<<<grid_size, block_size, 0, g_cache.stream>>>(
            g_cache.d_active_states,
            g_cache.uploaded_state_count,
            g_cache.d_missile_counter
        );
        if (cudaGetLastError() != cudaSuccess) {
            return false;
        }
        exact_world_step_first_scope_chain_tail_kernel<<<grid_size, block_size, 0, g_cache.stream>>>(
            g_cache.d_active_states,
            g_cache.uploaded_state_count,
            params
        );
        if (cudaGetLastError() != cudaSuccess) {
            return false;
        }
    } else {
        exact_world_step_first_scope_chain_aircraft_only_kernel<<<grid_size, block_size, 0, g_cache.stream>>>(
            g_cache.d_active_states,
            g_cache.uploaded_state_count,
            fbw_mode_code,
            params
        );
        if (cudaGetLastError() != cudaSuccess) {
            return false;
        }
    }
    if (cudaEventRecord(g_cache.timing_event1, g_cache.stream) != cudaSuccess) {
        return false;
    }

    std::size_t missile_count = 0;
    if (has_uploaded_missiles) {
        if (cudaMemcpyAsync(
                &missile_count,
                g_cache.d_missile_counter,
                sizeof(std::size_t),
                cudaMemcpyDeviceToHost,
                g_cache.stream
            ) != cudaSuccess) {
            return false;
        }
    }
    if (cudaStreamSynchronize(g_cache.stream) != cudaSuccess) {
        return false;
    }

    double kernel_ms = 0.0;
    if (!measure_event_elapsed_ms(g_cache.timing_event0, g_cache.timing_event1, &kernel_ms)) {
        return false;
    }

    g_last_output_device_ptr = g_cache.d_active_states;
    g_last_output_state_count = g_cache.uploaded_state_count;
    g_last_cuda_stats.used_cuda = true;
    g_last_cuda_stats.missile_count = missile_count;
    g_last_cuda_stats.front_kernel_ms = kernel_ms;
    g_last_cuda_stats.guidance_kernel_ms = 0.0;
    g_last_cuda_stats.tail_kernel_ms = 0.0;
    g_last_cuda_stats.kernel_ms = kernel_ms;
    g_last_cuda_stats.total_ms = g_last_cuda_stats.host_to_device_ms + g_last_cuda_stats.kernel_ms;
    return true;
}

bool replay_active_states_inplace() {
    return replay_chain_on_active_states(false);
}

std::vector<FirstScopeChainState> download_active_states() {
    std::vector<FirstScopeChainState> out(g_cache.uploaded_state_count);
    if (out.empty()) {
        g_last_cuda_stats.total_ms = g_last_cuda_stats.host_to_device_ms + g_last_cuda_stats.kernel_ms;
        return out;
    }

    const auto d2h_start = std::chrono::steady_clock::now();
    if (cudaMemcpy(
            out.data(),
            g_cache.d_active_states,
            out.size() * sizeof(FirstScopeChainState),
            cudaMemcpyDeviceToHost
        ) != cudaSuccess) {
        return {};
    }
    const auto d2h_end = std::chrono::steady_clock::now();
    g_last_cuda_stats.device_to_host_ms =
        std::chrono::duration<double, std::milli>(d2h_end - d2h_start).count();
    g_last_cuda_stats.total_ms =
        g_last_cuda_stats.host_to_device_ms +
        g_last_cuda_stats.kernel_ms +
        g_last_cuda_stats.device_to_host_ms;
    return out;
}

__device__ void run_missile_guidance_stage(
    FirstScopeChainState* states,
    std::size_t count,
    std::size_t idx,
    std::size_t* missile_counter
) {
    auto& state = states[idx];
    if (!state.has_missile) {
        return;
    }
    if (missile_counter != nullptr) {
        atomicAdd(reinterpret_cast<unsigned long long*>(missile_counter), 1ull);
    }

    auto& missile = state.missile;
    if (!missile.active) {
        return;
    }

    const double delta_time = static_cast<double>(static_cast<float>(state.aircraft.time_step_s));
    const double current_time = state.world_time_s;
    if (missile.launch_time <= 0.0) {
        missile.launch_time = current_time;
    }
    if (missile.max_flight_time_s > 0.0 && (current_time - missile.launch_time) > missile.max_flight_time_s) {
        missile.active = false;
        return;
    }
    if ((current_time - missile.launch_time) < missile.guidance_delay_s) {
        return;
    }
    if (missile.guidance_update_period_s > 0.0 &&
        (current_time - missile.last_guidance_time) < missile.guidance_update_period_s) {
        return;
    }
    missile.last_guidance_time = current_time;

    if (!state.has_contact_list_summary || state.contact_list_summary.count == 0) {
        return;
    }

    const Detection* best_det = nullptr;
    double max_sig = -1.0;
    const std::size_t det_count = static_cast<std::size_t>(state.contact_list_summary.count) <
            gpu::missile_guidance_cuda::kContactSummaryCapacity
        ? static_cast<std::size_t>(state.contact_list_summary.count)
        : gpu::missile_guidance_cuda::kContactSummaryCapacity;
    for (std::size_t det_index = 0; det_index < det_count; ++det_index) {
        const auto& detection = state.contact_list_summary.contacts[det_index];
        const double dist = detection.range;
        if (missile.seeker_lock_range > 0.0 && dist > missile.seeker_lock_range) {
            continue;
        }
        const double rel_bearing = detection.bearing;
        if (missile.seeker_fov_deg > 0.0 && fabs(rel_bearing) > missile.seeker_fov_deg * 0.5) {
            continue;
        }
        if (detection.signal_strength > max_sig) {
            max_sig = detection.signal_strength;
            best_det = &detection;
        }
    }
    if (best_det == nullptr) {
        return;
    }

    missile.target_id = best_det->target_id;

    const FirstScopeChainState* target_state = nullptr;
    for (std::size_t other = 0; other < count; ++other) {
        if (states[other].entity_id == missile.target_id) {
            target_state = &states[other];
            break;
        }
    }

    auto& velocity = state.aircraft.velocity;
    const auto& transform = state.aircraft.transform;
    const auto* target_transform = target_state != nullptr ? &target_state->aircraft.transform : nullptr;
    const auto* target_velocity = target_state != nullptr ? &target_state->aircraft.velocity : nullptr;

    const double speed = sqrt(
        velocity.vx * velocity.vx + velocity.vy * velocity.vy + velocity.vz * velocity.vz
    );
    const double rx = target_transform != nullptr
        ? (target_transform->x - transform.x)
        : (speed * cos(to_radians(90.0 - best_det->bearing)) * delta_time);
    const double ry = target_transform != nullptr
        ? (target_transform->y - transform.y)
        : (speed * sin(to_radians(90.0 - best_det->bearing)) * delta_time);
    const double rz = target_transform != nullptr ? (target_transform->z - transform.z) : 0.0;

    const double r_sq = rx * rx + ry * ry + rz * rz;
    const double r_mag = sqrt(r_sq);
    if (r_mag <= 1.0e-8 || r_sq <= 1.0e-12) {
        return;
    }

    const double vm_x = velocity.vx;
    const double vm_y = velocity.vy;
    const double vm_z = velocity.vz;
    const double vt_x = target_velocity != nullptr ? target_velocity->vx : 0.0;
    const double vt_y = target_velocity != nullptr ? target_velocity->vy : 0.0;
    const double vt_z = target_velocity != nullptr ? target_velocity->vz : 0.0;

    const double vr_x = vt_x - vm_x;
    const double vr_y = vt_y - vm_y;
    const double vr_z = vt_z - vm_z;

    const double cx = ry * vr_z - rz * vr_y;
    const double cy = rz * vr_x - rx * vr_z;
    const double cz = rx * vr_y - ry * vr_x;

    const double omega_x = cx / r_sq;
    const double omega_y = cy / r_sq;
    const double omega_z = cz / r_sq;

    double v_mag = sqrt(vm_x * vm_x + vm_y * vm_y + vm_z * vm_z);
    if (v_mag < 0.1) {
        v_mag = 0.1;
    }
    const double v_dir_x = vm_x / v_mag;
    const double v_dir_y = vm_y / v_mag;
    const double v_dir_z = vm_z / v_mag;

    const double nav_gain = missile.nav_gain > 0.0 ? missile.nav_gain : 3.0;
    double rate_x = nav_gain * omega_x;
    double rate_y = nav_gain * omega_y;
    double rate_z = nav_gain * omega_z;

    double rate_mag = sqrt(rate_x * rate_x + rate_y * rate_y + rate_z * rate_z);
    const double max_rate_rad = to_radians(missile.turn_rate);
    if (rate_mag > max_rate_rad && rate_mag > 1.0e-12) {
        const double scale = max_rate_rad / rate_mag;
        rate_x *= scale;
        rate_y *= scale;
        rate_z *= scale;
        rate_mag = max_rate_rad;
    }

    if (rate_mag > 1.0e-8) {
        const double axis_x = rate_x / rate_mag;
        const double axis_y = rate_y / rate_mag;
        const double axis_z = rate_z / rate_mag;
        const double theta = rate_mag * delta_time;
        const double cos_t = cos(theta);
        const double sin_t = sin(theta);

        const double cross_x = axis_y * vm_z - axis_z * vm_y;
        const double cross_y = axis_z * vm_x - axis_x * vm_z;
        const double cross_z = axis_x * vm_y - axis_y * vm_x;
        const double dot = axis_x * vm_x + axis_y * vm_y + axis_z * vm_z;

        const double v_new_x = vm_x * cos_t + cross_x * sin_t + axis_x * dot * (1.0 - cos_t);
        const double v_new_y = vm_y * cos_t + cross_y * sin_t + axis_y * dot * (1.0 - cos_t);
        const double v_new_z = vm_z * cos_t + cross_z * sin_t + axis_z * dot * (1.0 - cos_t);

        double vn_norm = sqrt(v_new_x * v_new_x + v_new_y * v_new_y + v_new_z * v_new_z);
        if (vn_norm < 1.0e-8) {
            vn_norm = 1.0;
        }
        velocity.vx = (v_new_x / vn_norm) * missile.max_speed;
        velocity.vy = (v_new_y / vn_norm) * missile.max_speed;
        velocity.vz = (v_new_z / vn_norm) * missile.max_speed;
    } else {
        velocity.vx = v_dir_x * missile.max_speed;
        velocity.vy = v_dir_y * missile.max_speed;
        velocity.vz = v_dir_z * missile.max_speed;
    }
}

__global__ void exact_world_step_first_scope_chain_front_kernel(
    FirstScopeChainState* states,
    std::size_t count,
    int fbw_mode_code
) {
    const std::size_t idx = static_cast<std::size_t>(blockIdx.x) * static_cast<std::size_t>(blockDim.x) +
        static_cast<std::size_t>(threadIdx.x);
    if (idx >= count || states == nullptr) {
        return;
    }

    auto& state = states[idx].aircraft;
    run_flight_control_stage(state, static_cast<FbwProtectionMode>(fbw_mode_code));
    run_clear_forces_stage(state);
    run_compute_aero_state_stage(state);
    run_compute_forces_stage(state);
    run_compute_aerodynamics_stage(state);
    run_ground_contact_stage(state);
}

__global__ void exact_world_step_first_scope_chain_aircraft_only_kernel(
    FirstScopeChainState* states,
    std::size_t count,
    int fbw_mode_code,
    RotationalParams params
) {
    const std::size_t idx = static_cast<std::size_t>(blockIdx.x) * static_cast<std::size_t>(blockDim.x) +
        static_cast<std::size_t>(threadIdx.x);
    if (idx >= count || states == nullptr) {
        return;
    }

    auto& state = states[idx].aircraft;
    run_flight_control_stage(state, static_cast<FbwProtectionMode>(fbw_mode_code));
    run_clear_forces_stage(state);
    run_compute_aero_state_stage(state);
    run_compute_forces_stage(state);
    run_compute_aerodynamics_stage(state);
    run_ground_contact_stage(state);
    run_rotational_integrate_stage(state, params);
    run_leapfrog_integrate_stage(state);
    refresh_environment_sample_from_transform(state);
    run_navigation_system_stage(state);
    run_update_instruments_stage(state);
    run_fuel_consumption_stage(state);
    run_mass_update_stage(state);
}

__global__ void exact_world_step_first_scope_chain_aircraft_only_advance_time_kernel(
    FirstScopeChainState* states,
    std::size_t count,
    int fbw_mode_code,
    RotationalParams params
) {
    const std::size_t idx = static_cast<std::size_t>(blockIdx.x) * static_cast<std::size_t>(blockDim.x) +
        static_cast<std::size_t>(threadIdx.x);
    if (idx >= count || states == nullptr) {
        return;
    }

    auto& full_state = states[idx];
    full_state.world_time_s += static_cast<double>(static_cast<float>(full_state.aircraft.time_step_s));

    auto& state = full_state.aircraft;
    run_flight_control_stage(state, static_cast<FbwProtectionMode>(fbw_mode_code));
    run_clear_forces_stage(state);
    run_compute_aero_state_stage(state);
    run_compute_forces_stage(state);
    run_compute_aerodynamics_stage(state);
    run_ground_contact_stage(state);
    run_rotational_integrate_stage(state, params);
    run_leapfrog_integrate_stage(state);
    refresh_environment_sample_from_transform(state);
    run_navigation_system_stage(state);
    run_update_instruments_stage(state);
    run_fuel_consumption_stage(state);
    run_mass_update_stage(state);
}

__global__ void exact_world_step_first_scope_chain_guidance_kernel(
    FirstScopeChainState* states,
    std::size_t count,
    std::size_t* missile_counter
) {
    const std::size_t idx = static_cast<std::size_t>(blockIdx.x) * static_cast<std::size_t>(blockDim.x) +
        static_cast<std::size_t>(threadIdx.x);
    if (idx >= count || states == nullptr) {
        return;
    }
    run_missile_guidance_stage(states, count, idx, missile_counter);
}

__global__ void exact_world_step_first_scope_chain_tail_kernel(
    FirstScopeChainState* states,
    std::size_t count,
    RotationalParams params
) {
    const std::size_t idx = static_cast<std::size_t>(blockIdx.x) * static_cast<std::size_t>(blockDim.x) +
        static_cast<std::size_t>(threadIdx.x);
    if (idx >= count || states == nullptr) {
        return;
    }

    auto& state = states[idx].aircraft;
    run_rotational_integrate_stage(state, params);
    run_leapfrog_integrate_stage(state);
    refresh_environment_sample_from_transform(state);
    run_navigation_system_stage(state);
    run_update_instruments_stage(state);
    run_fuel_consumption_stage(state);
    run_mass_update_stage(state);
}

}  // namespace

namespace gpu::detail {

bool step_exact_world_step_first_scope_chain_cuda_inplace(
    std::vector<gpu::first_scope_chain_cuda::ExactWorldStepFirstScopeChainCudaState>& states,
    gpu::ExactWorldStepFirstScopeChainCudaStats* stats
) {
    if (!upload_initial_states(states)) {
        return false;
    }
    if (!replay_uploaded_states()) {
        return false;
    }
    states = download_active_states();
    if (states.size() != g_last_output_state_count) {
        return false;
    }
    if (stats != nullptr) {
        *stats = g_last_cuda_stats;
    }
    return true;
}

bool upload_exact_world_step_first_scope_chain_cuda_states_cuda(
    const std::vector<gpu::first_scope_chain_cuda::ExactWorldStepFirstScopeChainCudaState>& initial_states
) {
    return upload_initial_states(initial_states);
}

bool upload_exact_world_step_first_scope_chain_cuda_states_raw_cuda(
    const std::vector<gpu::first_scope_chain_cuda::ExactWorldStepFirstScopeChainCudaState>& initial_states
) {
    return upload_raw_states(initial_states);
}

bool sync_exact_world_step_first_scope_chain_cuda_resident_projection_cuda(
    const std::vector<gpu::ExactWorldStepFirstScopeChainCudaResidentProjection>& projections
) {
    return sync_resident_projection(projections);
}

bool sync_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_cuda(
    const std::vector<gpu::ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection>& projections
) {
    return sync_resident_pilot_time_projection(projections);
}

bool sync_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_raw_cuda(
    const gpu::ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection* projections,
    std::size_t state_count
) {
    return sync_resident_pilot_time_projection_raw(projections, state_count);
}

bool sync_replay_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_current_cuda(
    const std::vector<gpu::ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection>& projections
) {
    return sync_replay_resident_pilot_time_projection_current(projections);
}

bool sync_replay_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_current_raw_cuda(
    const gpu::ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection* projections,
    std::size_t state_count
) {
    return sync_replay_resident_pilot_time_projection_current_raw(projections, state_count);
}

gpu::ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection*
acquire_exact_world_step_first_scope_chain_cuda_resident_pilot_time_projection_host_buffer_cuda(
    std::size_t state_count
) {
    if (!ensure_resident_pilot_time_host_capacity(state_count)) {
        return nullptr;
    }
    return g_cache.h_resident_pilot_time_projection;
}

bool replay_exact_world_step_first_scope_chain_cuda_device_sequence_cuda() {
    return replay_uploaded_states();
}

bool replay_exact_world_step_first_scope_chain_cuda_resident_current_cuda() {
    return replay_active_states_inplace();
}

bool replay_exact_world_step_first_scope_chain_cuda_resident_aircraft_only_advance_time_current_cuda() {
    return replay_active_states_aircraft_only_advance_time();
}

std::vector<gpu::first_scope_chain_cuda::ExactWorldStepFirstScopeChainCudaState>
download_exact_world_step_first_scope_chain_cuda_states_cuda() {
    return download_active_states();
}

gpu::ExactWorldStepFirstScopeChainCudaStats last_exact_world_step_first_scope_chain_cuda_stats_cuda() {
    return g_last_cuda_stats;
}

const void* last_exact_world_step_first_scope_chain_cuda_output_device_ptr_cuda() {
    return g_last_output_device_ptr;
}

std::size_t last_exact_world_step_first_scope_chain_cuda_output_state_count_cuda() {
    return g_last_output_state_count;
}

}  // namespace gpu::detail
