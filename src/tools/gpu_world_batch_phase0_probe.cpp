#include "gpu/gpu_world_batch_runtime.h"
#include "gpu/gpu_visual_runtime.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <exception>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <string>
#include <vector>

namespace {

struct Args {
    int frames = 128;
    int worlds = 4096;
    int steps = 256;
    int seed = 7;
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
        } else if (flag == "--worlds") {
            args.worlds = parse_int(require_value("--worlds"), "--worlds");
        } else if (flag == "--steps") {
            args.steps = parse_int(require_value("--steps"), "--steps");
        } else if (flag == "--seed") {
            args.seed = parse_int(require_value("--seed"), "--seed");
        } else if (flag == "--help" || flag == "-h") {
            std::cout
                << "Usage: ef_gpu_world_batch_phase0_probe [options]\n"
                << "  --frames N   benchmark frames (default 128)\n"
                << "  --worlds N   worlds per batch (default 4096)\n"
                << "  --steps N    fixed steps per world sequence (default 256)\n"
                << "  --seed N     rng seed (default 7)\n";
            std::exit(0);
        } else {
            throw std::invalid_argument("unknown flag: " + flag);
        }
    }
    args.frames = std::max(1, args.frames);
    args.worlds = std::max(1, args.worlds);
    args.steps = std::max(1, args.steps);
    return args;
}

std::vector<gpu::WorldBatchStepState> make_initial_states(const Args& args) {
    std::vector<gpu::WorldBatchStepState> out;
    out.reserve(static_cast<std::size_t>(args.worlds));
    std::mt19937 rng(static_cast<std::uint32_t>(args.seed));
    std::uniform_real_distribution<double> pos_xy(-50000.0, 50000.0);
    std::uniform_real_distribution<double> alt_m(500.0, 9000.0);
    std::uniform_real_distribution<double> vel_xy(-220.0, 220.0);
    std::uniform_real_distribution<double> vel_z(-8.0, 8.0);
    std::uniform_real_distribution<double> wind_xy(-20.0, 20.0);

    for (int idx = 0; idx < args.worlds; ++idx) {
        gpu::WorldBatchStepState state{};
        state.x_m = pos_xy(rng);
        state.y_m = pos_xy(rng);
        state.z_m = alt_m(rng);
        state.vx_mps = vel_xy(rng);
        state.vy_mps = vel_xy(rng);
        state.vz_mps = vel_z(rng);
        state.wind_vx_mps = wind_xy(rng);
        state.wind_vy_mps = wind_xy(rng);
        state.cmd_vx_mps = vel_xy(rng);
        state.cmd_vy_mps = vel_xy(rng);
        state.cmd_vz_mps = vel_z(rng);
        state.max_delta_vxy_mps_per_step = 1.0 + (idx % 9) * 0.25;
        state.max_delta_vz_mps_per_step = 0.5 + (idx % 7) * 0.2;
        state.time_step_s = 0.05;
        state.fuel_kg = 1500.0 + (idx % 200) * 1.5;
        state.fuel_idle_burn_kgps = 0.15 + (idx % 5) * 0.01;
        state.fuel_burn_per_speed_kgps_per_mps = 0.0005 + (idx % 7) * 0.00005;
        state.mission_time_s = 0.0;
        out.push_back(state);
    }
    return out;
}

struct DiffSummary {
    double max_abs_diff = 0.0;
    double mean_abs_diff = 0.0;
};

DiffSummary compare_states(
    const std::vector<gpu::WorldBatchStepState>& lhs,
    const std::vector<gpu::WorldBatchStepState>& rhs
) {
    DiffSummary summary{};
    if (lhs.size() != rhs.size() || lhs.empty()) {
        return summary;
    }
    double accum = 0.0;
    std::size_t count = 0;
    auto fold = [&](double a, double b) {
        const double diff = std::abs(a - b);
        summary.max_abs_diff = std::max(summary.max_abs_diff, diff);
        accum += diff;
        count += 1;
    };
    for (std::size_t idx = 0; idx < lhs.size(); ++idx) {
        fold(lhs[idx].x_m, rhs[idx].x_m);
        fold(lhs[idx].y_m, rhs[idx].y_m);
        fold(lhs[idx].z_m, rhs[idx].z_m);
        fold(lhs[idx].vx_mps, rhs[idx].vx_mps);
        fold(lhs[idx].vy_mps, rhs[idx].vy_mps);
        fold(lhs[idx].vz_mps, rhs[idx].vz_mps);
        fold(lhs[idx].fuel_kg, rhs[idx].fuel_kg);
        fold(lhs[idx].mission_time_s, rhs[idx].mission_time_s);
    }
    if (count > 0) {
        summary.mean_abs_diff = accum / static_cast<double>(count);
    }
    return summary;
}

double states_checksum(const std::vector<gpu::WorldBatchStepState>& states) {
    double checksum = 0.0;
    for (const auto& state : states) {
        checksum += state.x_m * 1.0e-3;
        checksum += state.y_m * 1.0e-3;
        checksum += state.z_m * 1.0e-3;
        checksum += state.vx_mps * 1.0e-2;
        checksum += state.vy_mps * 1.0e-2;
        checksum += state.vz_mps * 1.0e-2;
        checksum += state.fuel_kg * 1.0e-4;
        checksum += state.mission_time_s * 1.0e-3;
    }
    return checksum;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        const Args args = parse_args(argc, argv);
        const auto device = gpu::probe_device();
        const auto initial_states = make_initial_states(args);

        std::cout << "GPU World Batch Phase-0 Probe\n";
        std::cout << "=============================\n";
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
        std::cout << "Worlds/frame: " << args.worlds << '\n';
        std::cout << "Steps/sequence: " << args.steps << '\n';
        std::cout << "Frames: " << args.frames << '\n';
        std::cout << "State bytes/world: "
                  << gpu::format_bytes(sizeof(gpu::WorldBatchStepState)) << '\n';
        std::cout << "Batch bytes: "
                  << gpu::format_bytes(
                         static_cast<std::size_t>(args.worlds) *
                         sizeof(gpu::WorldBatchStepState))
                  << "\n\n";

        const auto cpu_reference = gpu::step_world_batch_reference_cpu_batch(initial_states, args.steps);
        const auto gpu_host_direct =
            gpu::step_world_batch_experiment_batch(initial_states, args.steps, false);
        const auto direct_stats_once = gpu::last_world_batch_step_stats();
        const auto gpu_host_graph =
            gpu::step_world_batch_experiment_batch(initial_states, args.steps, true);
        const auto graph_stats_once = gpu::last_world_batch_step_stats();

        bool device_direct_ok = gpu::upload_world_batch_step_states(initial_states);
        if (device_direct_ok) {
            device_direct_ok = gpu::replay_world_batch_step_device_sequence(args.steps, false);
        }
        auto gpu_device_direct = device_direct_ok ? gpu::download_world_batch_step_states() : std::vector<gpu::WorldBatchStepState>{};

        bool device_graph_ok = gpu::upload_world_batch_step_states(initial_states);
        if (device_graph_ok) {
            device_graph_ok = gpu::replay_world_batch_step_device_sequence(args.steps, true);
        }
        auto gpu_device_graph = device_graph_ok ? gpu::download_world_batch_step_states() : std::vector<gpu::WorldBatchStepState>{};

        const auto diff_host_direct = compare_states(cpu_reference, gpu_host_direct);
        const auto diff_host_graph = compare_states(cpu_reference, gpu_host_graph);
        const auto diff_device_direct = compare_states(cpu_reference, gpu_device_direct);
        const auto diff_device_graph = compare_states(cpu_reference, gpu_device_graph);

        double cpu_checksum = 0.0;
        const auto cpu_t0 = std::chrono::steady_clock::now();
        for (int frame = 0; frame < args.frames; ++frame) {
            auto stepped = gpu::step_world_batch_reference_cpu_batch(initial_states, args.steps);
            cpu_checksum += states_checksum(stepped);
        }
        const auto cpu_t1 = std::chrono::steady_clock::now();

        double gpu_host_direct_checksum = 0.0;
        const auto gpu_host_direct_t0 = std::chrono::steady_clock::now();
        for (int frame = 0; frame < args.frames; ++frame) {
            auto stepped = gpu::step_world_batch_experiment_batch(initial_states, args.steps, false);
            gpu_host_direct_checksum += states_checksum(stepped);
        }
        const auto gpu_host_direct_t1 = std::chrono::steady_clock::now();

        double gpu_host_graph_checksum = 0.0;
        const auto gpu_host_graph_t0 = std::chrono::steady_clock::now();
        for (int frame = 0; frame < args.frames; ++frame) {
            auto stepped = gpu::step_world_batch_experiment_batch(initial_states, args.steps, true);
            gpu_host_graph_checksum += states_checksum(stepped);
        }
        const auto gpu_host_graph_t1 = std::chrono::steady_clock::now();

        double gpu_device_direct_checksum = 0.0;
        const auto gpu_device_direct_t0 = std::chrono::steady_clock::now();
        if (gpu::upload_world_batch_step_states(initial_states)) {
            for (int frame = 0; frame < args.frames; ++frame) {
                if (!gpu::replay_world_batch_step_device_sequence(args.steps, false)) {
                    device_direct_ok = false;
                    break;
                }
                gpu_device_direct_checksum += 1.0;
            }
        } else {
            device_direct_ok = false;
        }
        const auto gpu_device_direct_t1 = std::chrono::steady_clock::now();

        double gpu_device_graph_checksum = 0.0;
        const auto gpu_device_graph_t0 = std::chrono::steady_clock::now();
        if (gpu::upload_world_batch_step_states(initial_states)) {
            for (int frame = 0; frame < args.frames; ++frame) {
                if (!gpu::replay_world_batch_step_device_sequence(args.steps, true)) {
                    device_graph_ok = false;
                    break;
                }
                gpu_device_graph_checksum += 1.0;
            }
        } else {
            device_graph_ok = false;
        }
        const auto gpu_device_graph_t1 = std::chrono::steady_clock::now();

        const double cpu_ms =
            std::chrono::duration<double, std::milli>(cpu_t1 - cpu_t0).count() /
            static_cast<double>(args.frames);
        const double gpu_host_direct_ms =
            std::chrono::duration<double, std::milli>(gpu_host_direct_t1 - gpu_host_direct_t0).count() /
            static_cast<double>(args.frames);
        const double gpu_host_graph_ms =
            std::chrono::duration<double, std::milli>(gpu_host_graph_t1 - gpu_host_graph_t0).count() /
            static_cast<double>(args.frames);
        const double gpu_device_direct_ms =
            std::chrono::duration<double, std::milli>(gpu_device_direct_t1 - gpu_device_direct_t0).count() /
            static_cast<double>(args.frames);
        const double gpu_device_graph_ms =
            std::chrono::duration<double, std::milli>(gpu_device_graph_t1 - gpu_device_graph_t0).count() /
            static_cast<double>(args.frames);

        std::cout << std::fixed << std::setprecision(3);
        std::cout << "Equivalence check\n";
        std::cout << "-----------------\n";
        std::cout << "CPU checksum: " << states_checksum(cpu_reference) << '\n';
        std::cout << "GPU host direct checksum: " << states_checksum(gpu_host_direct) << '\n';
        std::cout << "GPU host graph checksum: " << states_checksum(gpu_host_graph) << '\n';
        if (device_direct_ok) {
            std::cout << "GPU device direct checksum: " << states_checksum(gpu_device_direct) << '\n';
        }
        if (device_graph_ok) {
            std::cout << "GPU device graph checksum: " << states_checksum(gpu_device_graph) << '\n';
        }
        std::cout << "Host direct max/mean abs diff: " << diff_host_direct.max_abs_diff
                  << " / " << diff_host_direct.mean_abs_diff << '\n';
        std::cout << "Host graph max/mean abs diff: " << diff_host_graph.max_abs_diff
                  << " / " << diff_host_graph.mean_abs_diff << '\n';
        if (device_direct_ok) {
            std::cout << "Device direct max/mean abs diff: " << diff_device_direct.max_abs_diff
                      << " / " << diff_device_direct.mean_abs_diff << '\n';
        }
        if (device_graph_ok) {
            std::cout << "Device graph max/mean abs diff: " << diff_device_graph.max_abs_diff
                      << " / " << diff_device_graph.mean_abs_diff << '\n';
        }
        std::cout << '\n';

        std::cout << "One-shot GPU stats\n";
        std::cout << "------------------\n";
        std::cout << "Direct path H2D / kernel / D2H (ms): "
                  << direct_stats_once.host_to_device_ms << " / "
                  << direct_stats_once.kernel_ms << " / "
                  << direct_stats_once.device_to_host_ms << '\n';
        std::cout << "Graph path H2D / capture / kernel / D2H (ms): "
                  << graph_stats_once.host_to_device_ms << " / "
                  << graph_stats_once.graph_capture_ms << " / "
                  << graph_stats_once.kernel_ms << " / "
                  << graph_stats_once.device_to_host_ms << '\n';
        std::cout << '\n';

        std::cout << "Steady-state throughput\n";
        std::cout << "-----------------------\n";
        std::cout << "CPU reference: " << cpu_ms << " ms/frame\n";
        std::cout << "GPU host-readback direct: " << gpu_host_direct_ms << " ms/frame"
                  << " (" << (cpu_ms / std::max(1.0e-9, gpu_host_direct_ms)) << "x)\n";
        std::cout << "GPU host-readback graph: " << gpu_host_graph_ms << " ms/frame"
                  << " (" << (cpu_ms / std::max(1.0e-9, gpu_host_graph_ms)) << "x)\n";
        if (device_direct_ok) {
            std::cout << "GPU device-resident direct: " << gpu_device_direct_ms << " ms/frame"
                      << " (" << (cpu_ms / std::max(1.0e-9, gpu_device_direct_ms)) << "x)\n";
        } else {
            std::cout << "GPU device-resident direct: unavailable\n";
        }
        if (device_graph_ok) {
            std::cout << "GPU device-resident graph: " << gpu_device_graph_ms << " ms/frame"
                      << " (" << (cpu_ms / std::max(1.0e-9, gpu_device_graph_ms)) << "x)\n";
        } else {
            std::cout << "GPU device-resident graph: unavailable\n";
        }
        std::cout << '\n';

        std::cout << "Benchmark checksums\n";
        std::cout << "-------------------\n";
        std::cout << "CPU benchmark checksum: " << cpu_checksum << '\n';
        std::cout << "GPU host direct benchmark checksum: " << gpu_host_direct_checksum << '\n';
        std::cout << "GPU host graph benchmark checksum: " << gpu_host_graph_checksum << '\n';
        std::cout << "GPU device direct benchmark checksum: " << gpu_device_direct_checksum << '\n';
        std::cout << "GPU device graph benchmark checksum: " << gpu_device_graph_checksum << '\n';
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "error: " << ex.what() << '\n';
        return 1;
    }
}
