#include "gpu/gpu_flight_shaping_runtime.h"

#include <cuda_runtime_api.h>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <vector>

namespace {

gpu::FlightShapingExperimentStats g_last_stats{};
const void* g_last_output_device_ptr = nullptr;
std::size_t g_last_output_float_count = 0;

struct DeviceFlightShapingCache {
    FlightShapingRuntimeInputs* d_inputs = nullptr;
    float* d_output = nullptr;
    std::size_t input_capacity = 0;
    std::size_t output_capacity = 0;
};

DeviceFlightShapingCache g_cache{};

__host__ __device__ inline double clamp_value(double value, double lo, double hi) {
    return fmin(fmax(value, lo), hi);
}

__host__ __device__ inline double clipped_power_term(double err, double norm, double power, double clip) {
    if (err <= 0.0) {
        return 0.0;
    }
    double use_norm = norm;
    if (use_norm <= 1.0e-6) {
        use_norm = 1.0;
    }
    double x = err / use_norm;
    if (clip > 0.0) {
        x = fmin(x, clip);
    }
    const double p = clamp_value(power, 1.0, 8.0);
    return pow(x, p);
}

__global__ void compute_flight_shaping_kernel(
    const FlightShapingRuntimeInputs* inputs,
    int count,
    float* out
) {
    const int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= count) {
        return;
    }

    const auto& in = inputs[idx];
    float* dst = out + static_cast<std::size_t>(idx) * static_cast<std::size_t>(gpu::kFlightShapingOutputCount);

    const double d_alt = in.truth_altitude_m - in.prev_altitude_m;
    const double d_spd = in.curr_ias_mps - in.prev_ias_mps;

    double altitude_progress = 0.0;
    double low_alt_descent_penalty = 0.0;
    double speed_progress = 0.0;
    double speed_regress = 0.0;
    double stationary_penalty = 0.0;
    double liftoff_bonus = 0.0;
    bool next_liftoff_awarded = in.liftoff_awarded;
    double rotation_reward = 0.0;
    double rotation_overpitch_penalty = 0.0;
    double gear_up_bonus = 0.0;
    bool next_gear_bonus_awarded = in.gear_bonus_awarded;
    double roll_stability = 0.0;
    double heading_error_penalty = 0.0;
    double heading_hold_bonus = 0.0;
    double altitude_error_penalty = 0.0;
    double altitude_hold_bonus = 0.0;
    double speed_error_penalty = 0.0;
    double speed_hold_bonus = 0.0;
    double roll_abs_penalty = 0.0;
    double pitch_abs_penalty = 0.0;
    double yaw_rate_abs_penalty = 0.0;
    double beta_abs_penalty = 0.0;
    double g_deviation_penalty = 0.0;
    double speed_reward = 0.0;
    double runway_centerline_m_penalty = 0.0;
    double runway_centerline_penalty = 0.0;
    double runway_centerline_barrier = 0.0;
    double departure_centerline_m_penalty = 0.0;
    double departure_centerline_reward = 0.0;
    double departure_track_error_penalty = 0.0;
    double departure_track_reward = 0.0;
    double alignment_reward = 0.0;

    if ((in.target_altitude_m <= 0.0 || in.truth_altitude_m < in.target_altitude_m) && d_alt > 0.0) {
        altitude_progress = d_alt * in.altitude_progress_weight;
    } else if (in.truth_altitude_m < 10.0 && d_alt < -1.0) {
        low_alt_descent_penalty = d_alt * 0.1;
    }

    if ((in.target_speed_mps <= 0.0 || in.curr_ias_mps < in.target_speed_mps) && d_spd > 0.0) {
        speed_progress = d_spd * in.speed_progress_weight;
    } else if (d_spd < 0.0) {
        speed_regress = d_spd * in.speed_progress_negative_weight;
    }

    if (
        in.stationary_penalty != 0.0 &&
        in.step_count > in.stationary_grace_steps &&
        in.truth_speed_mps < in.stationary_speed_threshold_mps &&
        in.truth_altitude_m < in.stationary_alt_threshold_m
    ) {
        stationary_penalty = in.stationary_penalty;
    }

    if (
        in.liftoff_bonus != 0.0 &&
        !in.liftoff_awarded &&
        in.curr_ias_mps >= in.liftoff_speed_threshold_mps &&
        in.curr_alt_agl_m >= in.liftoff_alt_threshold_m
    ) {
        liftoff_bonus = in.liftoff_bonus;
        next_liftoff_awarded = true;
    }

    if (
        in.rotation_reward_weight != 0.0 &&
        in.curr_ias_mps >= in.rotation_speed_threshold_mps &&
        in.curr_alt_agl_m <= in.rotation_alt_threshold_m
    ) {
        const double rot_pitch_cap_deg = fmax(0.0, in.rotation_pitch_cap_deg);
        const double pitch_term = clamp_value(in.curr_pitch_deg, -rot_pitch_cap_deg, rot_pitch_cap_deg);
        rotation_reward = pitch_term * in.rotation_reward_weight;
        if (in.rotation_overpitch_penalty_weight != 0.0 && in.curr_pitch_deg > rot_pitch_cap_deg) {
            rotation_overpitch_penalty =
                (in.curr_pitch_deg - rot_pitch_cap_deg) * in.rotation_overpitch_penalty_weight;
        }
    }

    if (
        in.gear_up_bonus != 0.0 &&
        !in.gear_bonus_awarded &&
        in.curr_alt_agl_m > in.gear_up_bonus_min_alt_agl_m &&
        in.curr_gear_fraction < 0.1
    ) {
        gear_up_bonus = in.gear_up_bonus;
        next_gear_bonus_awarded = true;
    }

    if (in.truth_altitude_m < 100.0) {
        roll_stability = fabs(in.curr_roll_deg) * in.roll_stability_weight;
    }

    if (in.heading_error_weight != 0.0) {
        const double turn_heading_relief_max = clamp_value(in.waypoint_turn_heading_relief_max, 0.0, 0.95);
        const double heading_penalty_scale = 1.0 - turn_heading_relief_max * in.waypoint_turn_relief_activation;
        heading_error_penalty = in.heading_error_deg * in.heading_error_weight * heading_penalty_scale;
        if (in.heading_hold_bonus != 0.0 && in.heading_error_deg <= fmax(0.0, in.heading_hold_deadband_deg)) {
            heading_hold_bonus = in.heading_hold_bonus;
        }
    }

    if (in.airborne) {
        if (in.altitude_error_weight != 0.0 && in.curr_alt_baro_m >= in.altitude_error_min_alt_m) {
            const double alt_err = fabs(in.curr_alt_baro_m - in.altitude_error_target_m)
                - fmax(0.0, in.altitude_error_deadband_m);
            if (alt_err > 0.0) {
                altitude_error_penalty = in.altitude_error_weight * clipped_power_term(
                    alt_err,
                    in.altitude_error_norm_m <= 1.0e-6 ? 100.0 : in.altitude_error_norm_m,
                    in.altitude_error_power,
                    in.altitude_error_clip
                );
            } else if (in.altitude_hold_bonus != 0.0) {
                altitude_hold_bonus = in.altitude_hold_bonus;
            }
        }

        if (in.speed_error_weight != 0.0 && in.curr_ias_mps >= in.speed_error_min_ias_mps) {
            const double speed_err = fabs(in.curr_ias_mps - in.speed_error_target_mps)
                - fmax(0.0, in.speed_error_deadband_mps);
            if (speed_err > 0.0) {
                speed_error_penalty = in.speed_error_weight * clipped_power_term(
                    speed_err,
                    in.speed_error_norm_mps <= 1.0e-6 ? 30.0 : in.speed_error_norm_mps,
                    in.speed_error_power,
                    in.speed_error_clip
                );
            } else if (in.speed_hold_bonus != 0.0) {
                speed_hold_bonus = in.speed_hold_bonus;
            }
        }

        if (in.roll_abs_weight != 0.0) {
            const double roll_err = fabs(in.curr_roll_deg) - fmax(0.0, in.roll_abs_deadband_deg);
            if (roll_err > 0.0) {
                roll_abs_penalty = in.roll_abs_weight * clipped_power_term(
                    roll_err,
                    in.roll_abs_norm_deg <= 1.0e-6 ? 30.0 : in.roll_abs_norm_deg,
                    in.roll_abs_power,
                    0.0
                );
            }
        }

        if (in.pitch_abs_weight != 0.0) {
            const double pitch_err = fabs(in.curr_pitch_deg) - fmax(0.0, in.pitch_abs_deadband_deg);
            if (pitch_err > 0.0) {
                pitch_abs_penalty = in.pitch_abs_weight * clipped_power_term(
                    pitch_err,
                    in.pitch_abs_norm_deg <= 1.0e-6 ? 20.0 : in.pitch_abs_norm_deg,
                    in.pitch_abs_power,
                    0.0
                );
            }
        }

        if (in.yaw_rate_abs_weight != 0.0) {
            const double yaw_rate_err = fabs(in.curr_yaw_rate_deg_s) - fmax(0.0, in.yaw_rate_abs_deadband_deg_s);
            if (yaw_rate_err > 0.0) {
                yaw_rate_abs_penalty = in.yaw_rate_abs_weight * clipped_power_term(
                    yaw_rate_err,
                    in.yaw_rate_abs_norm_deg_s <= 1.0e-6 ? 10.0 : in.yaw_rate_abs_norm_deg_s,
                    in.yaw_rate_abs_power,
                    0.0
                );
            }
        }

        if (in.beta_abs_weight != 0.0) {
            const double beta_err = fabs(in.curr_beta_deg) - fmax(0.0, in.beta_abs_deadband_deg);
            if (beta_err > 0.0) {
                beta_abs_penalty = in.beta_abs_weight * clipped_power_term(
                    beta_err,
                    in.beta_abs_norm_deg <= 1.0e-6 ? 10.0 : in.beta_abs_norm_deg,
                    in.beta_abs_power,
                    0.0
                );
            }
        }

        if (in.g_deviation_weight != 0.0 && in.curr_alt_agl_m > in.g_deviation_min_alt_agl_m) {
            const double g_dev_err = fabs(in.curr_g_load - 1.0) - fmax(0.0, in.g_deviation_deadband);
            if (g_dev_err > 0.0) {
                g_deviation_penalty = in.g_deviation_weight * clipped_power_term(
                    g_dev_err,
                    in.g_deviation_norm <= 1.0e-6 ? 0.5 : in.g_deviation_norm,
                    in.g_deviation_power,
                    0.0
                );
            }
        }
    }

    speed_reward = in.truth_speed_mps * in.speed_reward_weight;

    if (in.preliftoff && in.on_runway_task && in.has_runway_cross_m && in.runway_width_m > 1.0e-6) {
        const double half_w = 0.5 * in.runway_width_m;
        double frac = fabs(in.runway_cross_m) / half_w;
        frac = fmin(frac, 2.0);
        double runway_scale = 1.0;
        if (in.runway_centerline_penalty_max_ias_mps > in.runway_centerline_penalty_min_ias_mps + 1.0e-6) {
            runway_scale =
                (in.curr_ias_mps - in.runway_centerline_penalty_min_ias_mps)
                / (in.runway_centerline_penalty_max_ias_mps - in.runway_centerline_penalty_min_ias_mps);
            runway_scale = clamp_value(runway_scale, 0.0, 1.0);
        }

        if (in.runway_centerline_m_penalty_weight != 0.0) {
            const double err_m = fabs(in.runway_cross_m) - fmax(0.0, in.runway_centerline_m_deadband_m);
            if (err_m > 0.0) {
                runway_centerline_m_penalty = in.runway_centerline_m_penalty_weight * clipped_power_term(
                    err_m,
                    in.runway_centerline_m_norm_m <= 1.0e-6 ? 5.0 : in.runway_centerline_m_norm_m,
                    in.runway_centerline_m_power,
                    in.runway_centerline_m_clip
                ) * runway_scale;
            }
        }

        if (in.runway_centerline_penalty_weight != 0.0) {
            const double safe_frac = clamp_value(in.runway_centerline_safe_frac, 0.0, 0.99);
            const double x = fmax(0.0, frac - safe_frac) / fmax(1.0 - safe_frac, 1.0e-6);
            runway_centerline_penalty =
                in.runway_centerline_penalty_weight
                * pow(x, clamp_value(in.runway_centerline_penalty_power, 1.0, 8.0))
                * runway_scale;
        }

        if (in.runway_centerline_barrier_weight != 0.0) {
            const double clip_frac = clamp_value(in.runway_centerline_barrier_clip_frac, 1.0e-6, 0.999999);
            const double frac_c = clamp_value(frac, 0.0, clip_frac);
            const double barrier = -log(fmax(1.0e-6, 1.0 - frac_c));
            runway_centerline_barrier = in.runway_centerline_barrier_weight * barrier * runway_scale;
        }
    }

    if (in.has_runway_cross_m) {
        if (in.airborne && in.departure_centerline_max_alt_agl_m > 0.0 && in.curr_alt_agl_m <= in.departure_centerline_max_alt_agl_m) {
            if (in.departure_centerline_m_penalty_weight != 0.0) {
                const double dep_err_m = fabs(in.runway_cross_m) - fmax(0.0, in.departure_centerline_m_deadband_m);
                if (dep_err_m > 0.0) {
                    departure_centerline_m_penalty = in.departure_centerline_m_penalty_weight * clipped_power_term(
                        dep_err_m,
                        in.departure_centerline_m_norm_m <= 1.0e-6 ? 20.0 : in.departure_centerline_m_norm_m,
                        in.departure_centerline_m_power,
                        in.departure_centerline_m_clip
                    );
                }
            }

            if (in.departure_centerline_reward_weight != 0.0) {
                const double band_m = fmax(1.0, in.departure_centerline_reward_band_m);
                const double center_frac = fmax(0.0, 1.0 - fabs(in.runway_cross_m) / band_m);
                if (center_frac > 0.0) {
                    departure_centerline_reward = in.departure_centerline_reward_weight * center_frac;
                }
            }

            if (in.departure_track_error_weight != 0.0) {
                const double dep_track_err = in.ground_track_error_deg - fmax(0.0, in.departure_track_error_deadband_deg);
                if (dep_track_err > 0.0) {
                    departure_track_error_penalty = in.departure_track_error_weight * clipped_power_term(
                        dep_track_err,
                        in.departure_track_error_norm_deg <= 1.0e-6 ? 10.0 : in.departure_track_error_norm_deg,
                        in.departure_track_error_power,
                        in.departure_track_error_clip
                    );
                }
            }

            if (in.departure_track_reward_weight != 0.0) {
                const double band_deg = fmax(1.0e-6, in.departure_track_reward_band_deg);
                const double track_frac = fmax(0.0, 1.0 - in.ground_track_error_deg / band_deg);
                if (track_frac > 0.0) {
                    departure_track_reward = in.departure_track_reward_weight * track_frac;
                }
            }
        }
    }

    if (in.alignment_reward_weight != 0.0) {
        if (in.on_runway_task && in.preliftoff) {
            if (in.ils_valid) {
                alignment_reward =
                    (1.0 - fmin(fabs(in.ils_loc_dev), 1.0)) * in.alignment_reward_weight;
            }
        } else if (in.truth_altitude_m >= in.mission_alignment_min_alt_m) {
            const double align_factor = cos(in.heading_error_deg * 3.14159265358979323846 / 180.0);
            if (align_factor > 0.0) {
                alignment_reward = align_factor * in.alignment_reward_weight;
            }
        }
    }

    dst[0] = 1.0f;
    dst[1] = static_cast<float>(altitude_progress);
    dst[2] = static_cast<float>(low_alt_descent_penalty);
    dst[3] = static_cast<float>(speed_progress);
    dst[4] = static_cast<float>(speed_regress);
    dst[5] = static_cast<float>(stationary_penalty);
    dst[6] = static_cast<float>(liftoff_bonus);
    dst[7] = next_liftoff_awarded ? 1.0f : 0.0f;
    dst[8] = static_cast<float>(rotation_reward);
    dst[9] = static_cast<float>(rotation_overpitch_penalty);
    dst[10] = static_cast<float>(gear_up_bonus);
    dst[11] = next_gear_bonus_awarded ? 1.0f : 0.0f;
    dst[12] = static_cast<float>(roll_stability);
    dst[13] = static_cast<float>(heading_error_penalty);
    dst[14] = static_cast<float>(heading_hold_bonus);
    dst[15] = static_cast<float>(altitude_error_penalty);
    dst[16] = static_cast<float>(altitude_hold_bonus);
    dst[17] = static_cast<float>(speed_error_penalty);
    dst[18] = static_cast<float>(speed_hold_bonus);
    dst[19] = static_cast<float>(roll_abs_penalty);
    dst[20] = static_cast<float>(pitch_abs_penalty);
    dst[21] = static_cast<float>(yaw_rate_abs_penalty);
    dst[22] = static_cast<float>(beta_abs_penalty);
    dst[23] = static_cast<float>(g_deviation_penalty);
    dst[24] = static_cast<float>(speed_reward);
    dst[25] = static_cast<float>(runway_centerline_m_penalty);
    dst[26] = static_cast<float>(runway_centerline_penalty);
    dst[27] = static_cast<float>(runway_centerline_barrier);
    dst[28] = static_cast<float>(departure_centerline_m_penalty);
    dst[29] = static_cast<float>(departure_centerline_reward);
    dst[30] = static_cast<float>(departure_track_error_penalty);
    dst[31] = static_cast<float>(departure_track_reward);
    dst[32] = static_cast<float>(alignment_reward);
}

bool ensure_cache_capacity(std::size_t input_count, std::size_t output_count) {
    if (input_count > g_cache.input_capacity) {
        if (g_cache.d_inputs != nullptr) {
            cudaFree(g_cache.d_inputs);
            g_cache.d_inputs = nullptr;
        }
        if (cudaMalloc(&g_cache.d_inputs, input_count * sizeof(FlightShapingRuntimeInputs)) != cudaSuccess) {
            return false;
        }
        g_cache.input_capacity = input_count;
    }
    if (output_count > g_cache.output_capacity) {
        if (g_cache.d_output != nullptr) {
            cudaFree(g_cache.d_output);
            g_cache.d_output = nullptr;
        }
        if (cudaMalloc(&g_cache.d_output, output_count * sizeof(float)) != cudaSuccess) {
            return false;
        }
        g_cache.output_capacity = output_count;
    }
    return true;
}

bool run_flight_shaping_batch_cuda_impl(
    const std::vector<FlightShapingRuntimeInputs>& inputs_batch,
    bool copy_output_to_host,
    std::vector<float>* host_output
) {
    g_last_stats = gpu::FlightShapingExperimentStats{};
    g_last_output_device_ptr = nullptr;
    g_last_output_float_count = 0;
    if (host_output != nullptr) {
        host_output->clear();
    }
    if (inputs_batch.empty()) {
        return false;
    }

    int device_count = 0;
    if (cudaGetDeviceCount(&device_count) != cudaSuccess || device_count <= 0) {
        return false;
    }
    g_last_stats.used_cuda = true;

    const std::size_t input_count = inputs_batch.size();
    const std::size_t output_count = input_count * static_cast<std::size_t>(gpu::kFlightShapingOutputCount);
    const std::size_t input_bytes = input_count * sizeof(FlightShapingRuntimeInputs);
    const std::size_t output_bytes = output_count * sizeof(float);

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

    if (!ensure_cache_capacity(input_count, output_count)) {
        cudaEventDestroy(ev_h2d_start);
        cudaEventDestroy(ev_h2d_end);
        cudaEventDestroy(ev_kernel_end);
        cudaEventDestroy(ev_d2h_end);
        return false;
    }

    status = cudaMemcpy(g_cache.d_inputs, inputs_batch.data(), input_bytes, cudaMemcpyHostToDevice);
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
        (input_count + static_cast<std::size_t>(threads) - 1) /
        static_cast<std::size_t>(threads)
    );
    compute_flight_shaping_kernel<<<blocks, threads>>>(
        g_cache.d_inputs,
        static_cast<int>(input_count),
        g_cache.d_output
    );
    cudaEventRecord(ev_kernel_end);

    status = cudaGetLastError();
    if (status == cudaSuccess) {
        status = cudaDeviceSynchronize();
    }
    double d2h_wall_ms = 0.0;
    if (status == cudaSuccess && copy_output_to_host && host_output != nullptr) {
        host_output->assign(output_count, 0.0f);
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
    g_last_output_float_count = output_count;

    cudaEventDestroy(ev_h2d_start);
    cudaEventDestroy(ev_h2d_end);
    cudaEventDestroy(ev_kernel_end);
    cudaEventDestroy(ev_d2h_end);
    return true;
}

}  // namespace

namespace gpu::detail {

FlightShapingExperimentStats last_flight_shaping_cuda_stats() {
    return g_last_stats;
}

const void* last_flight_shaping_output_device_ptr_cuda() {
    return g_last_output_device_ptr;
}

std::size_t last_flight_shaping_output_float_count_cuda() {
    return g_last_output_float_count;
}

std::vector<float> compute_flight_shaping_experiment_batch_cuda(
    const std::vector<FlightShapingRuntimeInputs>& inputs_batch
) {
    std::vector<float> out;
    if (!run_flight_shaping_batch_cuda_impl(inputs_batch, true, &out)) {
        return {};
    }
    return out;
}

bool compute_flight_shaping_experiment_batch_cuda_device_resident(
    const std::vector<FlightShapingRuntimeInputs>& inputs_batch
) {
    return run_flight_shaping_batch_cuda_impl(inputs_batch, false, nullptr);
}

}  // namespace gpu::detail
