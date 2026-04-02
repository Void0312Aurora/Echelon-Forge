#include "gpu/gpu_flight_shaping_runtime.h"
#include "gpu/gpu_visual_runtime.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <exception>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <string>

namespace {

struct Args {
    int frames = 512;
    int envs = 4096;
};

int parse_int(const char* value, const char* name) {
    char* end = nullptr;
    const long parsed = std::strtol(value, &end, 10);
    if (end == value || *end != '\0') {
        throw std::invalid_argument(std::string("invalid integer for ") + name);
    }
    return static_cast<int>(parsed);
}

Args parse_args(int argc, char** argv) {
    Args args{};
    for (int i = 1; i < argc; ++i) {
        const std::string flag = argv[i];
        auto require_value = [&](const char* name) -> const char* {
            if (i + 1 >= argc) {
                throw std::invalid_argument(std::string("missing value for ") + name);
            }
            return argv[++i];
        };
        if (flag == "--frames") {
            args.frames = parse_int(require_value("--frames"), "--frames");
        } else if (flag == "--envs") {
            args.envs = parse_int(require_value("--envs"), "--envs");
        } else if (flag == "--help" || flag == "-h") {
            std::cout
                << "Usage: ef_gpu_flight_shaping_phase0_probe [options]\n"
                << "  --frames N   benchmark frames (default 512)\n"
                << "  --envs N     batch worlds per frame (default 4096)\n";
            std::exit(0);
        } else {
            throw std::invalid_argument("unknown flag: " + flag);
        }
    }
    args.frames = std::max(1, args.frames);
    args.envs = std::max(1, args.envs);
    return args;
}

std::vector<FlightShapingRuntimeInputs> make_inputs(int envs) {
    std::vector<FlightShapingRuntimeInputs> out;
    out.reserve(static_cast<std::size_t>(envs));
    for (int idx = 0; idx < envs; ++idx) {
        FlightShapingRuntimeInputs in{};
        const bool runway_case = (idx % 3) == 0;
        const bool airborne_case = (idx % 3) != 0;
        in.truth_altitude_m = runway_case ? 20.0 + (idx % 11) * 2.0 : 800.0 + (idx % 70) * 12.0;
        in.truth_speed_mps = runway_case ? 55.0 + (idx % 13) * 2.0 : 150.0 + (idx % 40) * 1.5;
        in.prev_altitude_m = in.truth_altitude_m - ((idx % 5) - 2) * 1.5;
        in.prev_ias_mps = in.truth_speed_mps - ((idx % 7) - 3) * 0.8;
        in.curr_ias_mps = in.truth_speed_mps + ((idx % 9) - 4) * 0.7;
        in.curr_alt_baro_m = in.truth_altitude_m + ((idx % 5) - 2) * 1.2;
        in.curr_alt_agl_m = runway_case ? 1.0 + (idx % 6) * 0.8 : 200.0 + (idx % 50) * 5.0;
        in.curr_gear_fraction = runway_case ? 1.0 : ((idx % 4 == 0) ? 0.0 : 0.2);
        in.curr_roll_deg = -18.0 + (idx % 13) * 3.0;
        in.curr_pitch_deg = -5.0 + (idx % 11) * 1.4;
        in.curr_beta_deg = -4.0 + (idx % 9);
        in.curr_yaw_rate_deg_s = -6.0 + (idx % 15) * 0.9;
        in.curr_g_load = 0.85 + (idx % 10) * 0.08;
        in.step_count = 30 + (idx % 200);
        in.target_altitude_m = runway_case ? 0.0 : 1200.0;
        in.target_speed_mps = runway_case ? 85.0 : 175.0;
        in.heading_error_deg = std::abs(-20.0 + (idx % 17) * 2.5);
        in.ground_track_error_deg = std::abs(-15.0 + (idx % 13) * 2.2);
        in.waypoint_turn_relief_activation = (idx % 8) * 0.1;
        in.preliftoff = runway_case;
        in.on_runway_task = runway_case;
        in.airborne = airborne_case;
        in.has_runway_cross_m = true;
        in.runway_cross_m = -18.0 + (idx % 19) * 2.0;
        in.runway_width_m = 45.0;
        in.ils_valid = (idx % 2) == 0;
        in.ils_loc_dev = -0.4 + (idx % 9) * 0.1;
        in.liftoff_awarded = (idx % 5) == 0;
        in.gear_bonus_awarded = (idx % 7) == 0;

        in.altitude_progress_weight = 0.01;
        in.speed_progress_weight = 0.02;
        in.speed_progress_negative_weight = 0.01;
        in.stationary_penalty = -0.5;
        in.stationary_grace_steps = 10;
        in.stationary_speed_threshold_mps = 8.0;
        in.stationary_alt_threshold_m = 10.0;
        in.liftoff_bonus = 5.0;
        in.liftoff_speed_threshold_mps = 70.0;
        in.liftoff_alt_threshold_m = 3.0;
        in.rotation_reward_weight = 0.05;
        in.rotation_speed_threshold_mps = 65.0;
        in.rotation_alt_threshold_m = 8.0;
        in.rotation_pitch_cap_deg = 14.0;
        in.rotation_overpitch_penalty_weight = -0.08;
        in.gear_up_bonus = 2.0;
        in.gear_up_bonus_min_alt_agl_m = 80.0;
        in.roll_stability_weight = -0.01;
        in.heading_error_weight = -0.03;
        in.heading_hold_deadband_deg = 5.0;
        in.heading_hold_bonus = 0.5;
        in.waypoint_turn_heading_relief_max = 0.5;

        in.altitude_error_weight = -0.06;
        in.altitude_error_min_alt_m = 100.0;
        in.altitude_error_target_m = 1200.0;
        in.altitude_error_deadband_m = 40.0;
        in.altitude_error_norm_m = 200.0;
        in.altitude_error_power = 1.5;
        in.altitude_error_clip = 4.0;
        in.altitude_hold_bonus = 0.4;

        in.speed_error_weight = -0.05;
        in.speed_error_min_ias_mps = 70.0;
        in.speed_error_target_mps = 175.0;
        in.speed_error_deadband_mps = 8.0;
        in.speed_error_norm_mps = 30.0;
        in.speed_error_power = 1.5;
        in.speed_error_clip = 4.0;
        in.speed_hold_bonus = 0.3;

        in.roll_abs_weight = -0.01;
        in.roll_abs_deadband_deg = 5.0;
        in.roll_abs_norm_deg = 30.0;
        in.roll_abs_power = 1.3;
        in.pitch_abs_weight = -0.01;
        in.pitch_abs_deadband_deg = 4.0;
        in.pitch_abs_norm_deg = 20.0;
        in.pitch_abs_power = 1.3;
        in.yaw_rate_abs_weight = -0.008;
        in.yaw_rate_abs_deadband_deg_s = 1.0;
        in.yaw_rate_abs_norm_deg_s = 10.0;
        in.yaw_rate_abs_power = 1.4;
        in.beta_abs_weight = -0.009;
        in.beta_abs_deadband_deg = 1.0;
        in.beta_abs_norm_deg = 8.0;
        in.beta_abs_power = 1.4;
        in.g_deviation_weight = -0.02;
        in.g_deviation_deadband = 0.1;
        in.g_deviation_norm = 0.4;
        in.g_deviation_power = 1.5;
        in.g_deviation_min_alt_agl_m = 5.0;

        in.speed_reward_weight = 0.002;
        in.runway_centerline_penalty_min_ias_mps = 20.0;
        in.runway_centerline_penalty_max_ias_mps = 90.0;
        in.runway_centerline_m_penalty_weight = -0.04;
        in.runway_centerline_m_deadband_m = 1.0;
        in.runway_centerline_m_norm_m = 5.0;
        in.runway_centerline_m_power = 2.0;
        in.runway_centerline_m_clip = 4.0;
        in.runway_centerline_penalty_weight = -0.03;
        in.runway_centerline_safe_frac = 0.3;
        in.runway_centerline_penalty_power = 2.0;
        in.runway_centerline_barrier_weight = -0.02;
        in.runway_centerline_barrier_clip_frac = 0.98;
        in.departure_centerline_max_alt_agl_m = 120.0;
        in.departure_centerline_m_penalty_weight = -0.03;
        in.departure_centerline_m_deadband_m = 1.0;
        in.departure_centerline_m_norm_m = 18.0;
        in.departure_centerline_m_power = 1.8;
        in.departure_centerline_m_clip = 4.0;
        in.departure_centerline_reward_weight = 0.5;
        in.departure_centerline_reward_band_m = 10.0;
        in.departure_track_error_weight = -0.03;
        in.departure_track_error_deadband_deg = 2.0;
        in.departure_track_error_norm_deg = 10.0;
        in.departure_track_error_power = 1.8;
        in.departure_track_error_clip = 4.0;
        in.departure_track_reward_weight = 0.4;
        in.departure_track_reward_band_deg = 12.0;
        in.alignment_reward_weight = 0.3;
        in.mission_alignment_min_alt_m = 100.0;
        out.push_back(in);
    }
    return out;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        const Args args = parse_args(argc, argv);
        const auto device = gpu::probe_device();
        const auto inputs = make_inputs(args.envs);

        std::cout << "GPU Flight Shaping Phase-0 Probe\n";
        std::cout << "================================\n";
        std::cout << "CUDA built: " << (device.cuda_runtime_built ? "yes" : "no") << '\n';
        std::cout << "CUDA runtime available: " << (device.cuda_runtime_available ? "yes" : "no") << '\n';
        std::cout << "CUDA device count: " << device.device_count << '\n';
        if (!device.device_name.empty()) {
            std::cout << "Active device: " << device.device_name
                      << " (sm_" << device.compute_major << device.compute_minor << ")\n";
        }
        std::cout << '\n';
        std::cout << "Batch shape\n";
        std::cout << "-----------\n";
        std::cout << "Worlds/frame: " << args.envs << '\n';
        std::cout << "Per-world floats: " << gpu::kFlightShapingOutputCount << '\n';
        std::cout << "Batch bytes: "
                  << gpu::format_bytes(
                         static_cast<std::size_t>(args.envs) *
                         static_cast<std::size_t>(gpu::kFlightShapingOutputCount) *
                         sizeof(float))
                  << '\n';

        auto reference_once = gpu::compute_flight_shaping_reference_cpu_batch(inputs);
        auto gpu_once = gpu::compute_flight_shaping_experiment_batch(inputs);
        const bool device_resident_ready = gpu::compute_flight_shaping_experiment_batch_device_resident(inputs);
        const auto device_output_ptr = gpu::last_flight_shaping_output_device_ptr();
        const auto device_output_float_count = gpu::last_flight_shaping_output_float_count();

        double max_abs_diff = 0.0;
        double mean_abs_diff = 0.0;
        if (reference_once.size() == gpu_once.size() && !reference_once.empty()) {
            for (std::size_t i = 0; i < reference_once.size(); ++i) {
                const double diff = std::abs(static_cast<double>(reference_once[i]) - static_cast<double>(gpu_once[i]));
                max_abs_diff = std::max(max_abs_diff, diff);
                mean_abs_diff += diff;
            }
            mean_abs_diff /= static_cast<double>(reference_once.size());
        }

        double cpu_checksum = 0.0;
        const auto cpu_t0 = std::chrono::steady_clock::now();
        for (int frame = 0; frame < args.frames; ++frame) {
            auto rendered = gpu::compute_flight_shaping_reference_cpu_batch(inputs);
            cpu_checksum += std::accumulate(rendered.begin(), rendered.end(), 0.0);
        }
        const auto cpu_t1 = std::chrono::steady_clock::now();

        double gpu_checksum = 0.0;
        const auto gpu_t0 = std::chrono::steady_clock::now();
        for (int frame = 0; frame < args.frames; ++frame) {
            auto rendered = gpu::compute_flight_shaping_experiment_batch(inputs);
            gpu_checksum += std::accumulate(rendered.begin(), rendered.end(), 0.0);
        }
        const auto gpu_t1 = std::chrono::steady_clock::now();
        const auto gpu_stats_once = gpu::last_flight_shaping_stats();

        bool device_resident_ok = device_resident_ready;
        std::chrono::steady_clock::time_point gpu_device_t0{};
        std::chrono::steady_clock::time_point gpu_device_t1{};
        if (device_resident_ready) {
            gpu_device_t0 = std::chrono::steady_clock::now();
            for (int frame = 0; frame < args.frames; ++frame) {
                device_resident_ok =
                    gpu::compute_flight_shaping_experiment_batch_device_resident(inputs) &&
                    device_resident_ok;
            }
            gpu_device_t1 = std::chrono::steady_clock::now();
        }
        const auto gpu_device_stats_once = gpu::last_flight_shaping_stats();

        const double cpu_total_s = std::chrono::duration<double>(cpu_t1 - cpu_t0).count();
        const double gpu_total_s = std::chrono::duration<double>(gpu_t1 - gpu_t0).count();
        const double gpu_device_total_s = device_resident_ready
            ? std::chrono::duration<double>(gpu_device_t1 - gpu_device_t0).count()
            : 0.0;
        const double cpu_ms_batch = 1000.0 * cpu_total_s / static_cast<double>(args.frames);
        const double cpu_ms_world = cpu_ms_batch / static_cast<double>(args.envs);
        const double gpu_ms_batch = 1000.0 * gpu_total_s / static_cast<double>(args.frames);
        const double gpu_ms_world = gpu_ms_batch / static_cast<double>(args.envs);
        const double gpu_device_ms_batch = 1000.0 * gpu_device_total_s / static_cast<double>(std::max(1, args.frames));
        const double gpu_device_ms_world = gpu_device_ms_batch / static_cast<double>(args.envs);

        std::cout << '\n';
        std::cout << "CPU reference baseline\n";
        std::cout << "----------------------\n";
        std::cout << "Frames: " << args.frames << '\n';
        std::cout << "ms/batch-frame: " << std::fixed << std::setprecision(4) << cpu_ms_batch << '\n';
        std::cout << "ms/world-frame: " << std::fixed << std::setprecision(6) << cpu_ms_world << '\n';
        std::cout << "batch-frames/s: " << std::fixed << std::setprecision(2)
                  << (static_cast<double>(args.frames) / std::max(cpu_total_s, 1.0e-9)) << '\n';
        std::cout << "world-frames/s: " << std::fixed << std::setprecision(2)
                  << (static_cast<double>(args.frames) * static_cast<double>(args.envs) / std::max(cpu_total_s, 1.0e-9)) << '\n';
        std::cout << "checksum: " << std::fixed << std::setprecision(6) << cpu_checksum << '\n';

        std::cout << '\n';
        std::cout << "GPU experiment path\n";
        std::cout << "-------------------\n";
        std::cout << "ms/batch-frame: " << std::fixed << std::setprecision(4) << gpu_ms_batch << '\n';
        std::cout << "ms/world-frame: " << std::fixed << std::setprecision(6) << gpu_ms_world << '\n';
        std::cout << "batch-frames/s: " << std::fixed << std::setprecision(2)
                  << (static_cast<double>(args.frames) / std::max(gpu_total_s, 1.0e-9)) << '\n';
        std::cout << "world-frames/s: " << std::fixed << std::setprecision(2)
                  << (static_cast<double>(args.frames) * static_cast<double>(args.envs) / std::max(gpu_total_s, 1.0e-9)) << '\n';
        std::cout << "checksum: " << std::fixed << std::setprecision(6) << gpu_checksum << '\n';
        std::cout << "speedup: " << std::fixed << std::setprecision(2)
                  << (gpu_ms_world > 0.0 ? cpu_ms_world / gpu_ms_world : 0.0) << "x\n";
        if (gpu_stats_once.used_cuda) {
            std::cout << "last_frame_h2d_ms: " << std::fixed << std::setprecision(4) << gpu_stats_once.host_to_device_ms << '\n';
            std::cout << "last_frame_kernel_ms: " << std::fixed << std::setprecision(4) << gpu_stats_once.kernel_ms << '\n';
            std::cout << "last_frame_d2h_ms: " << std::fixed << std::setprecision(4) << gpu_stats_once.device_to_host_ms << '\n';
            std::cout << "last_frame_total_ms: " << std::fixed << std::setprecision(4) << gpu_stats_once.total_ms << '\n';
        }

        std::cout << '\n';
        std::cout << "GPU device-resident path\n";
        std::cout << "------------------------\n";
        std::cout << "ready: " << (device_resident_ok ? "yes" : "no") << '\n';
        std::cout << "device_output_ptr: " << device_output_ptr << '\n';
        std::cout << "device_output_floats: " << device_output_float_count << '\n';
        if (device_resident_ready) {
            std::cout << "ms/batch-frame: " << std::fixed << std::setprecision(4) << gpu_device_ms_batch << '\n';
            std::cout << "ms/world-frame: " << std::fixed << std::setprecision(6) << gpu_device_ms_world << '\n';
            std::cout << "batch-frames/s: " << std::fixed << std::setprecision(2)
                      << (static_cast<double>(args.frames) / std::max(gpu_device_total_s, 1.0e-9)) << '\n';
            std::cout << "world-frames/s: " << std::fixed << std::setprecision(2)
                      << (static_cast<double>(args.frames) * static_cast<double>(args.envs) / std::max(gpu_device_total_s, 1.0e-9)) << '\n';
            std::cout << "speedup_vs_cpu: " << std::fixed << std::setprecision(2)
                      << (gpu_device_ms_world > 0.0 ? cpu_ms_world / gpu_device_ms_world : 0.0) << "x\n";
            std::cout << "uplift_vs_gpu_host: " << std::fixed << std::setprecision(2)
                      << (gpu_device_ms_world > 0.0 ? gpu_ms_world / gpu_device_ms_world : 0.0) << "x\n";
        } else {
            std::cout << "status: unavailable\n";
        }
        if (device_resident_ready && gpu_device_stats_once.used_cuda) {
            std::cout << "last_frame_h2d_ms: " << std::fixed << std::setprecision(4) << gpu_device_stats_once.host_to_device_ms << '\n';
            std::cout << "last_frame_kernel_ms: " << std::fixed << std::setprecision(4) << gpu_device_stats_once.kernel_ms << '\n';
            std::cout << "last_frame_d2h_ms: " << std::fixed << std::setprecision(4) << gpu_device_stats_once.device_to_host_ms << '\n';
            std::cout << "last_frame_total_ms: " << std::fixed << std::setprecision(4) << gpu_device_stats_once.total_ms << '\n';
        }

        std::cout << '\n';
        std::cout << "Output agreement\n";
        std::cout << "----------------\n";
        std::cout << "max_abs_diff: " << std::fixed << std::setprecision(8) << max_abs_diff << '\n';
        std::cout << "mean_abs_diff: " << std::fixed << std::setprecision(8) << mean_abs_diff << '\n';
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "ef_gpu_flight_shaping_phase0_probe failed: " << ex.what() << '\n';
        return 1;
    }
}
