#include "gpu/gpu_execution_observation_runtime.h"

#include <cuda_runtime_api.h>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <vector>

namespace {

gpu::ExecutionObservationExperimentStats g_last_stats{};
const void* g_last_output_device_ptr = nullptr;
std::size_t g_last_output_float_count = 0;

struct DeviceExecutionObservationCache {
    gpu::ExecutionObservationBatchRequest* d_requests = nullptr;
    TrackData* d_contacts = nullptr;
    RWREvent* d_rwr = nullptr;
    float* d_output = nullptr;
    std::size_t request_capacity = 0;
    std::size_t contact_capacity = 0;
    std::size_t rwr_capacity = 0;
    std::size_t output_capacity = 0;
};

DeviceExecutionObservationCache g_cache{};

__host__ __device__ inline float sanitize_scalar(double value) {
    if (!isfinite(value)) {
        return 0.0f;
    }
    const double clipped = fmax(-1.0e6, fmin(1.0e6, value));
    return static_cast<float>(clipped);
}

__host__ __device__ inline double wrap_angle_deg(double angle_deg) {
    double wrapped = fmod(angle_deg + 180.0, 360.0);
    if (wrapped < 0.0) {
        wrapped += 360.0;
    }
    return wrapped - 180.0;
}

__host__ __device__ inline double clamp_value(double value, double lo, double hi) {
    return fmin(fmax(value, lo), hi);
}

__host__ __device__ inline int mission_value_count(int mode_code) {
    switch (mode_code) {
        case 0:
            return gpu::kExecutionObservationMissionBasicCount;
        case 1:
            return gpu::kExecutionObservationMissionNavV1Count;
        case 2:
            return gpu::kExecutionObservationMissionNavV2Count;
        case 3:
            return gpu::kExecutionObservationMissionNavV2FormationV1Count;
        case 4:
            return gpu::kExecutionObservationMissionNavV2FormationRoleV1Count;
        case 5:
            return gpu::kExecutionObservationMissionNavV2CooperativeTakeoffV1Count;
        default:
            return gpu::kExecutionObservationMissionBasicCount;
    }
}

__device__ inline void pack_mission_values(
    const gpu::ExecutionObservationBatchRequest& req,
    float* dst
) {
    dst[0] = sanitize_scalar(req.mission.command_code);
    dst[1] = sanitize_scalar(req.mission.target_heading_deg);
    dst[2] = sanitize_scalar(req.mission.target_altitude_m);
    dst[3] = sanitize_scalar(req.mission.target_speed_mps);

    if (req.mission.mode_code == 0) {
        return;
    }

    const bool has_formation_tail = req.mission.mode_code == 3;
    const bool has_formation_role_tail = req.mission.mode_code == 4;
    const bool has_takeoff_tail = req.mission.mode_code == 5;
    const int nav_end = (has_formation_tail || has_formation_role_tail || has_takeoff_tail) ? 14 : mission_value_count(req.mission.mode_code);
    if (!req.mission.has_route_guidance) {
        for (int idx = 4; idx < nav_end; ++idx) {
            dst[idx] = 0.0f;
        }
        if (has_formation_tail) {
            dst[14] = sanitize_scalar(req.mission.form_offset_x);
            dst[15] = sanitize_scalar(req.mission.form_offset_y);
            dst[16] = sanitize_scalar(req.mission.form_offset_z);
        } else if (has_formation_role_tail) {
            dst[14] = sanitize_scalar(req.mission.form_offset_x);
            dst[15] = sanitize_scalar(req.mission.form_offset_y);
            dst[16] = sanitize_scalar(req.mission.form_offset_z);
            dst[17] = sanitize_scalar(req.mission.self_role_code);
            dst[18] = sanitize_scalar(req.mission.self_formation_role_code);
            dst[19] = sanitize_scalar(req.mission.relative_slot_code);
            dst[20] = sanitize_scalar(req.mission.reference_relative_slot_code);
        } else if (has_takeoff_tail) {
            dst[14] = sanitize_scalar(req.mission.takeoff_procedure_code);
            dst[15] = sanitize_scalar(req.mission.takeoff_clearance_code);
            dst[16] = sanitize_scalar(req.mission.takeoff_interval_s);
            dst[17] = sanitize_scalar(req.mission.runway_slot_code);
            dst[18] = sanitize_scalar(req.mission.form_offset_x);
            dst[19] = sanitize_scalar(req.mission.form_offset_y);
            dst[20] = sanitize_scalar(req.mission.form_offset_z);
            dst[21] = sanitize_scalar(req.mission.self_role_code);
            dst[22] = sanitize_scalar(req.mission.self_formation_role_code);
            dst[23] = sanitize_scalar(req.mission.relative_slot_code);
            dst[24] = sanitize_scalar(req.mission.reference_relative_slot_code);
        }
        return;
    }

    double own_heading_deg = req.mission.nav_truth_heading_deg;
    double ground_track_deg = req.mission.nav_truth_heading_deg;
    double reference_speed_mps = req.mission.nav_truth_speed_mps;

    if (isfinite(req.mission.nav_inst_heading_deg)) {
        own_heading_deg = req.mission.nav_inst_heading_deg;
    }
    if (isfinite(req.mission.nav_inst_ground_track_deg)) {
        ground_track_deg = req.mission.nav_inst_ground_track_deg;
    }
    if (isfinite(req.mission.nav_inst_ias_mps) && req.mission.nav_inst_ias_mps > 1.0) {
        reference_speed_mps = req.mission.nav_inst_ias_mps;
    }
    if (fabs(wrap_angle_deg(ground_track_deg - own_heading_deg)) > 85.0 && reference_speed_mps > 80.0) {
        ground_track_deg = own_heading_deg;
    }

    const double cdi_full_scale_m = fmax(1.0, req.mission.nav_cdi_full_scale_m);
    const double bearing_rel_deg = wrap_angle_deg(req.mission.route_direct_to_track_deg - own_heading_deg);
    const double altitude_delta_m = req.mission.nav_waypoint_altitude_m - req.mission.nav_own_altitude_m;
    const double cdi_norm = clamp_value(req.mission.route_reward_xtk_m / cdi_full_scale_m, -1.0, 1.0);
    const double track_angle_error_deg =
        wrap_angle_deg(req.mission.route_reward_desired_track_deg - ground_track_deg);

    if (req.mission.mode_code == 1) {
        dst[4] = sanitize_scalar(static_cast<double>(req.mission.route_idx));
        dst[5] = sanitize_scalar(static_cast<double>(req.mission.route_count));
        dst[6] = sanitize_scalar(req.mission.route_dist_m);
        dst[7] = sanitize_scalar(req.mission.route_reward_xtk_m);
        dst[8] = sanitize_scalar(req.mission.route_reward_dtg_m);
        dst[9] = sanitize_scalar(req.mission.route_direct_to_track_deg);
        dst[10] = sanitize_scalar(req.mission.route_reward_desired_track_deg);
        return;
    }

    dst[4] = sanitize_scalar(static_cast<double>(req.mission.route_idx + 1));
    dst[5] = sanitize_scalar(req.mission.route_waypoint_flyover ? 1.0 : 0.0);
    dst[6] = sanitize_scalar(req.mission.route_dist_m);
    dst[7] = sanitize_scalar(bearing_rel_deg);
    dst[8] = sanitize_scalar(altitude_delta_m);
    dst[9] = sanitize_scalar(cdi_norm);
    dst[10] = sanitize_scalar(track_angle_error_deg);
    dst[11] = sanitize_scalar(req.mission.route_reward_dtg_m);
    dst[12] = sanitize_scalar(req.mission.route_next_turn_deg);
    dst[13] = sanitize_scalar(req.mission.route_distance_to_turn_m);
    if (has_formation_tail) {
        dst[14] = sanitize_scalar(req.mission.form_offset_x);
        dst[15] = sanitize_scalar(req.mission.form_offset_y);
        dst[16] = sanitize_scalar(req.mission.form_offset_z);
    } else if (has_formation_role_tail) {
        dst[14] = sanitize_scalar(req.mission.form_offset_x);
        dst[15] = sanitize_scalar(req.mission.form_offset_y);
        dst[16] = sanitize_scalar(req.mission.form_offset_z);
        dst[17] = sanitize_scalar(req.mission.self_role_code);
        dst[18] = sanitize_scalar(req.mission.self_formation_role_code);
        dst[19] = sanitize_scalar(req.mission.relative_slot_code);
        dst[20] = sanitize_scalar(req.mission.reference_relative_slot_code);
    } else if (has_takeoff_tail) {
        dst[14] = sanitize_scalar(req.mission.takeoff_procedure_code);
        dst[15] = sanitize_scalar(req.mission.takeoff_clearance_code);
        dst[16] = sanitize_scalar(req.mission.takeoff_interval_s);
        dst[17] = sanitize_scalar(req.mission.runway_slot_code);
        dst[18] = sanitize_scalar(req.mission.form_offset_x);
        dst[19] = sanitize_scalar(req.mission.form_offset_y);
        dst[20] = sanitize_scalar(req.mission.form_offset_z);
        dst[21] = sanitize_scalar(req.mission.self_role_code);
        dst[22] = sanitize_scalar(req.mission.self_formation_role_code);
        dst[23] = sanitize_scalar(req.mission.relative_slot_code);
        dst[24] = sanitize_scalar(req.mission.reference_relative_slot_code);
    }
}

__global__ void pack_execution_observation_kernel(
    const gpu::ExecutionObservationBatchRequest* requests,
    const TrackData* contacts,
    const RWREvent* rwr,
    int request_count,
    int max_contacts,
    int max_rwr,
    int per_request_floats,
    float* out
) {
    const int request_index = blockIdx.x * blockDim.x + threadIdx.x;
    if (request_index >= request_count) {
        return;
    }

    const auto& req = requests[request_index];
    const std::size_t base = static_cast<std::size_t>(request_index) * static_cast<std::size_t>(per_request_floats);
    float* dst = out + base;

    dst[0] = sanitize_scalar(req.inst.ias_mps);
    dst[1] = sanitize_scalar(req.inst.mach);
    dst[2] = sanitize_scalar(req.inst.alt_baro_m);
    dst[3] = sanitize_scalar(req.inst.alt_radar_m);
    dst[4] = sanitize_scalar(req.inst.vvi_mps);
    dst[5] = sanitize_scalar(req.inst.aoa_deg);
    dst[6] = sanitize_scalar(req.inst.beta_deg);
    dst[7] = sanitize_scalar(req.inst.pitch_deg);
    dst[8] = sanitize_scalar(req.inst.roll_deg);
    dst[9] = sanitize_scalar(req.inst.heading_deg);
    dst[10] = sanitize_scalar(req.inst.g_load_normal);
    dst[11] = sanitize_scalar(req.inst.g_load_axial);
    dst[12] = sanitize_scalar(req.inst.p_deg_s);
    dst[13] = sanitize_scalar(req.inst.q_deg_s);
    dst[14] = sanitize_scalar(req.inst.r_deg_s);
    dst[15] = sanitize_scalar(req.inst.engine_rpm_pct);
    dst[16] = sanitize_scalar(req.inst.fuel_internal_kg + req.inst.fuel_external_kg);
    dst[17] = sanitize_scalar(req.inst.fuel_flow_kg_h);
    dst[18] = sanitize_scalar(req.inst.gear_pos);
    dst[19] = sanitize_scalar(req.inst.flaps_pos);
    dst[20] = sanitize_scalar(req.inst.speedbrake_pos);
    dst[21] = sanitize_scalar(req.inst.cmd_heading_deg);
    dst[22] = sanitize_scalar(req.inst.cmd_alt_m);
    dst[23] = sanitize_scalar(req.inst.cmd_speed_mps);
    dst[24] = sanitize_scalar(req.inst.lat_deg);
    dst[25] = sanitize_scalar(req.inst.lon_deg);
    dst[26] = sanitize_scalar(req.inst.vn_mps);
    dst[27] = sanitize_scalar(req.inst.ve_mps);
    dst[28] = sanitize_scalar(req.inst.vd_mps);
    dst[29] = sanitize_scalar(req.inst.ground_speed_mps);
    dst[30] = sanitize_scalar(req.inst.ground_track_deg);
    dst[31] = sanitize_scalar(req.inst.wind_speed_mps);
    dst[32] = sanitize_scalar(req.inst.wind_dir_deg);
    dst[33] = sanitize_scalar(req.inst.oat_c);
    dst[34] = sanitize_scalar(req.inst.gps_available ? 1.0 : 0.0);
    dst[35] = sanitize_scalar(req.inst.position_uncertainty_m);
    dst[36] = sanitize_scalar(req.inst.rwr_active ? 1.0 : 0.0);
    dst[37] = sanitize_scalar(req.inst.missiles_remaining);
    dst[38] = sanitize_scalar(req.ils_valid);
    dst[39] = sanitize_scalar(req.ils_loc);
    dst[40] = sanitize_scalar(req.ils_gs);
    dst[41] = sanitize_scalar(req.ils_dme);

    const std::size_t contact_section_base =
        base + static_cast<std::size_t>(gpu::kExecutionObservationInstrumentCount);
    const std::size_t rwr_section_base =
        contact_section_base +
        static_cast<std::size_t>(max_contacts) * static_cast<std::size_t>(gpu::kExecutionObservationContactWidth);
    const std::size_t mission_section_base =
        rwr_section_base +
        static_cast<std::size_t>(max_rwr) * static_cast<std::size_t>(gpu::kExecutionObservationRwrWidth);

    const std::size_t padded_contact_base =
        static_cast<std::size_t>(request_index) * static_cast<std::size_t>(max_contacts);
    for (int idx = 0; idx < max_contacts; ++idx) {
        const std::size_t out_base =
            contact_section_base +
            static_cast<std::size_t>(idx) * static_cast<std::size_t>(gpu::kExecutionObservationContactWidth);
        if (idx < req.contact_count) {
            const auto& track = contacts[padded_contact_base + static_cast<std::size_t>(idx)];
            dst[out_base - base + 0] = sanitize_scalar(track.range);
            dst[out_base - base + 1] = sanitize_scalar(track.azimuth);
            dst[out_base - base + 2] = sanitize_scalar(track.elevation);
            dst[out_base - base + 3] = sanitize_scalar(track.closing_speed);
            dst[out_base - base + 4] = sanitize_scalar(track.time_since_update);
        } else {
            dst[out_base - base + 0] = 0.0f;
            dst[out_base - base + 1] = 0.0f;
            dst[out_base - base + 2] = 0.0f;
            dst[out_base - base + 3] = 0.0f;
            dst[out_base - base + 4] = 0.0f;
        }
    }

    const std::size_t padded_rwr_base =
        static_cast<std::size_t>(request_index) * static_cast<std::size_t>(max_rwr);
    for (int idx = 0; idx < max_rwr; ++idx) {
        const std::size_t out_base =
            rwr_section_base +
            static_cast<std::size_t>(idx) * static_cast<std::size_t>(gpu::kExecutionObservationRwrWidth);
        if (idx < req.rwr_count) {
            const auto& warning = rwr[padded_rwr_base + static_cast<std::size_t>(idx)];
            dst[out_base - base + 0] = sanitize_scalar(warning.bearing);
            dst[out_base - base + 1] = sanitize_scalar(warning.signal_strength);
            dst[out_base - base + 2] = sanitize_scalar(warning.is_lock ? 1.0 : 0.0);
            dst[out_base - base + 3] = sanitize_scalar(warning.is_launch ? 1.0 : 0.0);
        } else {
            dst[out_base - base + 0] = 0.0f;
            dst[out_base - base + 1] = 0.0f;
            dst[out_base - base + 2] = 0.0f;
            dst[out_base - base + 3] = 0.0f;
        }
    }

    pack_mission_values(req, dst + (mission_section_base - base));
}

bool ensure_cache_capacity(
    std::size_t request_count,
    std::size_t padded_contact_count,
    std::size_t padded_rwr_count,
    std::size_t output_float_count
) {
    if (request_count > g_cache.request_capacity) {
        if (g_cache.d_requests != nullptr) {
            cudaFree(g_cache.d_requests);
            g_cache.d_requests = nullptr;
        }
        if (cudaMalloc(&g_cache.d_requests, request_count * sizeof(gpu::ExecutionObservationBatchRequest)) != cudaSuccess) {
            return false;
        }
        g_cache.request_capacity = request_count;
    }
    if (padded_contact_count > g_cache.contact_capacity) {
        if (g_cache.d_contacts != nullptr) {
            cudaFree(g_cache.d_contacts);
            g_cache.d_contacts = nullptr;
        }
        if (cudaMalloc(&g_cache.d_contacts, padded_contact_count * sizeof(TrackData)) != cudaSuccess) {
            return false;
        }
        g_cache.contact_capacity = padded_contact_count;
    }
    if (padded_rwr_count > g_cache.rwr_capacity) {
        if (g_cache.d_rwr != nullptr) {
            cudaFree(g_cache.d_rwr);
            g_cache.d_rwr = nullptr;
        }
        if (cudaMalloc(&g_cache.d_rwr, padded_rwr_count * sizeof(RWREvent)) != cudaSuccess) {
            return false;
        }
        g_cache.rwr_capacity = padded_rwr_count;
    }
    if (output_float_count > g_cache.output_capacity) {
        if (g_cache.d_output != nullptr) {
            cudaFree(g_cache.d_output);
            g_cache.d_output = nullptr;
        }
        if (cudaMalloc(&g_cache.d_output, output_float_count * sizeof(float)) != cudaSuccess) {
            return false;
        }
        g_cache.output_capacity = output_float_count;
    }
    return true;
}

bool run_execution_observation_batch_cuda_impl(
    const std::vector<gpu::ExecutionObservationBatchRequest>& requests,
    const std::vector<std::vector<TrackData>>& contacts_batch,
    const std::vector<std::vector<RWREvent>>& rwr_batch,
    int max_contacts,
    int max_rwr,
    bool copy_output_to_host,
    std::vector<float>* host_output
) {
    g_last_stats = gpu::ExecutionObservationExperimentStats{};
    g_last_output_device_ptr = nullptr;
    g_last_output_float_count = 0;
    if (host_output != nullptr) {
        host_output->clear();
    }
    if (requests.empty() || requests.size() != contacts_batch.size() || requests.size() != rwr_batch.size()) {
        return false;
    }

    int device_count = 0;
    if (cudaGetDeviceCount(&device_count) != cudaSuccess || device_count <= 0) {
        return false;
    }
    g_last_stats.used_cuda = true;

    const std::size_t request_count = requests.size();
    const int mission_mode_code = requests.front().mission.mode_code;
    for (const auto& request : requests) {
        if (request.mission.mode_code != mission_mode_code) {
            return false;
        }
    }
    const std::size_t per_request_floats =
        gpu::execution_observation_output_float_count(max_contacts, max_rwr, mission_mode_code);
    const std::size_t output_float_count = request_count * per_request_floats;
    const std::size_t padded_contact_count =
        request_count * static_cast<std::size_t>(std::max(0, max_contacts));
    const std::size_t padded_rwr_count =
        request_count * static_cast<std::size_t>(std::max(0, max_rwr));

    std::vector<gpu::ExecutionObservationBatchRequest> bounded_requests = requests;
    std::vector<TrackData> padded_contacts(padded_contact_count);
    std::vector<RWREvent> padded_rwr(padded_rwr_count);
    for (std::size_t request_index = 0; request_index < request_count; ++request_index) {
        bounded_requests[request_index].contact_count = std::min(
            std::max(0, bounded_requests[request_index].contact_count),
            std::min(max_contacts, static_cast<int>(contacts_batch[request_index].size()))
        );
        bounded_requests[request_index].rwr_count = std::min(
            std::max(0, bounded_requests[request_index].rwr_count),
            std::min(max_rwr, static_cast<int>(rwr_batch[request_index].size()))
        );
        const std::size_t contact_base =
            request_index * static_cast<std::size_t>(std::max(0, max_contacts));
        for (int idx = 0; idx < bounded_requests[request_index].contact_count; ++idx) {
            padded_contacts[contact_base + static_cast<std::size_t>(idx)] =
                contacts_batch[request_index][static_cast<std::size_t>(idx)];
        }
        const std::size_t rwr_base =
            request_index * static_cast<std::size_t>(std::max(0, max_rwr));
        for (int idx = 0; idx < bounded_requests[request_index].rwr_count; ++idx) {
            padded_rwr[rwr_base + static_cast<std::size_t>(idx)] =
                rwr_batch[request_index][static_cast<std::size_t>(idx)];
        }
    }

    const std::size_t request_bytes = request_count * sizeof(gpu::ExecutionObservationBatchRequest);
    const std::size_t contact_bytes = padded_contact_count * sizeof(TrackData);
    const std::size_t rwr_bytes = padded_rwr_count * sizeof(RWREvent);
    const std::size_t output_bytes = output_float_count * sizeof(float);

    cudaError_t status = cudaSuccess;
    cudaEvent_t ev_h2d_start = nullptr;
    cudaEvent_t ev_h2d_end = nullptr;
    cudaEvent_t ev_kernel_end = nullptr;
    cudaEvent_t ev_d2h_end = nullptr;
    cudaEventCreate(&ev_h2d_start);
    cudaEventCreate(&ev_h2d_end);
    cudaEventCreate(&ev_kernel_end);
    cudaEventCreate(&ev_d2h_end);
    cudaEventRecord(ev_h2d_start);

    if (!ensure_cache_capacity(request_count, padded_contact_count, padded_rwr_count, output_float_count)) {
        cudaEventDestroy(ev_h2d_start);
        cudaEventDestroy(ev_h2d_end);
        cudaEventDestroy(ev_kernel_end);
        cudaEventDestroy(ev_d2h_end);
        return false;
    }

    status = cudaMemcpy(g_cache.d_requests, bounded_requests.data(), request_bytes, cudaMemcpyHostToDevice);
    if (status == cudaSuccess && contact_bytes > 0) {
        status = cudaMemcpy(g_cache.d_contacts, padded_contacts.data(), contact_bytes, cudaMemcpyHostToDevice);
    }
    if (status == cudaSuccess && rwr_bytes > 0) {
        status = cudaMemcpy(g_cache.d_rwr, padded_rwr.data(), rwr_bytes, cudaMemcpyHostToDevice);
    }
    if (status != cudaSuccess) {
        cudaEventDestroy(ev_h2d_start);
        cudaEventDestroy(ev_h2d_end);
        cudaEventDestroy(ev_kernel_end);
        cudaEventDestroy(ev_d2h_end);
        return false;
    }
    cudaEventRecord(ev_h2d_end);

    const int threads = 128;
    const int blocks = static_cast<int>(
        (request_count + static_cast<std::size_t>(threads) - 1) /
        static_cast<std::size_t>(threads)
    );
    pack_execution_observation_kernel<<<blocks, threads>>>(
        g_cache.d_requests,
        g_cache.d_contacts,
        g_cache.d_rwr,
        static_cast<int>(request_count),
        max_contacts,
        max_rwr,
        static_cast<int>(per_request_floats),
        g_cache.d_output
    );
    cudaEventRecord(ev_kernel_end);

    status = cudaGetLastError();
    if (status == cudaSuccess) {
        status = cudaDeviceSynchronize();
    }
    double d2h_wall_ms = 0.0;
    if (status == cudaSuccess && copy_output_to_host && host_output != nullptr) {
        host_output->assign(output_float_count, 0.0f);
        const auto d2h_start = std::chrono::steady_clock::now();
        status = cudaMemcpy(host_output->data(), g_cache.d_output, output_bytes, cudaMemcpyDeviceToHost);
        const auto d2h_end = std::chrono::steady_clock::now();
        d2h_wall_ms = std::chrono::duration<double, std::milli>(d2h_end - d2h_start).count();
        if (status == cudaSuccess) {
            cudaEventRecord(ev_d2h_end);
        }
    } else {
        cudaEventRecord(ev_d2h_end);
    }

    if (status != cudaSuccess) {
        cudaEventDestroy(ev_h2d_start);
        cudaEventDestroy(ev_h2d_end);
        cudaEventDestroy(ev_kernel_end);
        cudaEventDestroy(ev_d2h_end);
        g_last_output_device_ptr = nullptr;
        g_last_output_float_count = 0;
        return false;
    }

    float h2d_ms = 0.0f;
    float kernel_ms = 0.0f;
    cudaEventElapsedTime(&h2d_ms, ev_h2d_start, ev_h2d_end);
    cudaEventElapsedTime(&kernel_ms, ev_h2d_end, ev_kernel_end);
    g_last_stats.host_to_device_ms = static_cast<double>(h2d_ms);
    g_last_stats.kernel_ms = static_cast<double>(kernel_ms);
    g_last_stats.device_to_host_ms = copy_output_to_host ? d2h_wall_ms : 0.0;
    g_last_stats.total_ms =
        g_last_stats.host_to_device_ms +
        g_last_stats.kernel_ms +
        g_last_stats.device_to_host_ms;
    g_last_output_device_ptr = g_cache.d_output;
    g_last_output_float_count = output_float_count;

    cudaEventDestroy(ev_h2d_start);
    cudaEventDestroy(ev_h2d_end);
    cudaEventDestroy(ev_kernel_end);
    cudaEventDestroy(ev_d2h_end);
    return true;
}

}  // namespace

namespace gpu::detail {

ExecutionObservationExperimentStats last_execution_observation_cuda_stats() {
    return g_last_stats;
}

const void* last_execution_observation_output_device_ptr_cuda() {
    return g_last_output_device_ptr;
}

std::size_t last_execution_observation_output_float_count_cuda() {
    return g_last_output_float_count;
}

std::vector<float> compute_execution_observation_experiment_batch_cuda(
    const std::vector<gpu::ExecutionObservationBatchRequest>& requests,
    const std::vector<std::vector<TrackData>>& contacts_batch,
    const std::vector<std::vector<RWREvent>>& rwr_batch,
    int max_contacts,
    int max_rwr
) {
    std::vector<float> out;
    if (!run_execution_observation_batch_cuda_impl(
            requests,
            contacts_batch,
            rwr_batch,
            max_contacts,
            max_rwr,
            true,
            &out)) {
        return {};
    }
    return out;
}

bool compute_execution_observation_experiment_batch_cuda_device_resident(
    const std::vector<gpu::ExecutionObservationBatchRequest>& requests,
    const std::vector<std::vector<TrackData>>& contacts_batch,
    const std::vector<std::vector<RWREvent>>& rwr_batch,
    int max_contacts,
    int max_rwr
) {
    return run_execution_observation_batch_cuda_impl(
        requests,
        contacts_batch,
        rwr_batch,
        max_contacts,
        max_rwr,
        false,
        nullptr
    );
}

}  // namespace gpu::detail
