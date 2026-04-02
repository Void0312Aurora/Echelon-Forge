#include "gpu/gpu_exact_world_step_missile_guidance_cuda_runtime.h"
#include "gpu/gpu_exact_world_step_missile_guidance_cuda_runtime_types.h"

#include <cuda_runtime_api.h>

#include <chrono>
#include <cmath>
#include <vector>

namespace {

constexpr double kPi = 3.14159265358979323846;

using Detection = gpu::missile_guidance_cuda::Detection;
using Missile = gpu::missile_guidance_cuda::Missile;
using MissileGuidanceState = gpu::missile_guidance_cuda::ExactWorldStepMissileGuidanceCudaState;
using Transform = gpu::missile_guidance_cuda::Transform;
using Velocity = gpu::missile_guidance_cuda::Velocity;

template <typename T>
void free_device_ptr(T*& ptr) {
    if (ptr != nullptr) {
        cudaFree(ptr);
        ptr = nullptr;
    }
}

__device__ __forceinline__ double to_radians(double deg) {
    return deg * kPi / 180.0;
}

__global__ void exact_world_step_missile_guidance_cuda_kernel(
    MissileGuidanceState* states,
    std::size_t count,
    std::size_t* missile_counter
) {
    const std::size_t idx = static_cast<std::size_t>(blockIdx.x) * static_cast<std::size_t>(blockDim.x) +
        static_cast<std::size_t>(threadIdx.x);
    if (idx >= count || states == nullptr) {
        return;
    }

    auto& state = states[idx];
    if (!state.has_missile) {
        return;
    }

    atomicAdd(reinterpret_cast<unsigned long long*>(missile_counter), 1ull);

    auto& missile = state.missile;
    if (!missile.active) {
        return;
    }

    const double delta_time = static_cast<double>(static_cast<float>(state.time_step_s));
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

    const MissileGuidanceState* target_state = nullptr;
    for (std::size_t other = 0; other < count; ++other) {
        if (states[other].entity_id == missile.target_id) {
            target_state = &states[other];
            break;
        }
    }

    auto& velocity = state.velocity;
    const auto& transform = state.transform;
    const Transform* target_transform = target_state != nullptr ? &target_state->transform : nullptr;
    const Velocity* target_velocity = target_state != nullptr ? &target_state->velocity : nullptr;

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

}  // namespace

namespace gpu::detail {

bool step_exact_world_step_missile_guidance_cuda_inplace(
    std::vector<missile_guidance_cuda::ExactWorldStepMissileGuidanceCudaState>& states,
    ExactWorldStepMissileGuidanceCudaStats* stats
) {
    if (stats != nullptr) {
        stats->state_count = states.size();
        stats->missile_count = 0;
        stats->used_cuda = false;
        stats->host_to_device_ms = 0.0;
        stats->kernel_ms = 0.0;
        stats->device_to_host_ms = 0.0;
        stats->cpu_fallback_ms = 0.0;
    }
    if (states.empty()) {
        return true;
    }

    MissileGuidanceState* device_states = nullptr;
    std::size_t* device_missile_counter = nullptr;
    std::size_t missile_count = 0;
    const auto h2d_start = std::chrono::steady_clock::now();
    if (cudaMalloc(&device_states, states.size() * sizeof(MissileGuidanceState)) != cudaSuccess) {
        free_device_ptr(device_states);
        return false;
    }
    if (cudaMalloc(&device_missile_counter, sizeof(std::size_t)) != cudaSuccess) {
        free_device_ptr(device_states);
        free_device_ptr(device_missile_counter);
        return false;
    }
    if (cudaMemcpy(
            device_states,
            states.data(),
            states.size() * sizeof(MissileGuidanceState),
            cudaMemcpyHostToDevice
        ) != cudaSuccess) {
        free_device_ptr(device_states);
        free_device_ptr(device_missile_counter);
        return false;
    }
    if (cudaMemcpy(
            device_missile_counter,
            &missile_count,
            sizeof(std::size_t),
            cudaMemcpyHostToDevice
        ) != cudaSuccess) {
        free_device_ptr(device_states);
        free_device_ptr(device_missile_counter);
        return false;
    }
    const auto h2d_end = std::chrono::steady_clock::now();

    const auto kernel_start = std::chrono::steady_clock::now();
    const int block_size = 128;
    const int grid_size = static_cast<int>((states.size() + static_cast<std::size_t>(block_size) - 1u) /
                                           static_cast<std::size_t>(block_size));
    exact_world_step_missile_guidance_cuda_kernel<<<grid_size, block_size>>>(
        device_states,
        states.size(),
        device_missile_counter
    );
    if (cudaGetLastError() != cudaSuccess || cudaDeviceSynchronize() != cudaSuccess) {
        free_device_ptr(device_states);
        free_device_ptr(device_missile_counter);
        return false;
    }
    const auto kernel_end = std::chrono::steady_clock::now();

    const auto d2h_start = std::chrono::steady_clock::now();
    if (cudaMemcpy(
            states.data(),
            device_states,
            states.size() * sizeof(MissileGuidanceState),
            cudaMemcpyDeviceToHost
        ) != cudaSuccess) {
        free_device_ptr(device_states);
        free_device_ptr(device_missile_counter);
        return false;
    }
    if (cudaMemcpy(
            &missile_count,
            device_missile_counter,
            sizeof(std::size_t),
            cudaMemcpyDeviceToHost
        ) != cudaSuccess) {
        free_device_ptr(device_states);
        free_device_ptr(device_missile_counter);
        return false;
    }
    const auto d2h_end = std::chrono::steady_clock::now();
    free_device_ptr(device_states);
    free_device_ptr(device_missile_counter);

    if (stats != nullptr) {
        stats->used_cuda = true;
        stats->missile_count = missile_count;
        stats->host_to_device_ms = std::chrono::duration<double, std::milli>(h2d_end - h2d_start).count();
        stats->kernel_ms = std::chrono::duration<double, std::milli>(kernel_end - kernel_start).count();
        stats->device_to_host_ms = std::chrono::duration<double, std::milli>(d2h_end - d2h_start).count();
    }
    return true;
}

}  // namespace gpu::detail
