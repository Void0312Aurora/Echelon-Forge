#include "gpu/gpu_visual_runtime.h"
#include "core/interfaces/environment_model.h"

#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <exception>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <string>
#include <string_view>
#include <vector>

namespace {

enum class TerrainMode {
    Off,
    Cpu,
    Gpu,
};

struct Args {
    int frames = 512;
    int objects = 32;
    int height = arb::ARB_HEIGHT;
    int width = arb::ARB_WIDTH;
    int envs = 16;
    int history_steps = 2048;
    double altitude_m = 1200.0;
    TerrainMode terrain_mode = TerrainMode::Off;
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
        } else if (flag == "--objects") {
            args.objects = parse_int(require_value("--objects"), "--objects");
        } else if (flag == "--height") {
            args.height = parse_int(require_value("--height"), "--height");
        } else if (flag == "--width") {
            args.width = parse_int(require_value("--width"), "--width");
        } else if (flag == "--envs") {
            args.envs = parse_int(require_value("--envs"), "--envs");
        } else if (flag == "--history-steps") {
            args.history_steps = parse_int(require_value("--history-steps"), "--history-steps");
        } else if (flag == "--altitude-m") {
            args.altitude_m = std::stod(require_value("--altitude-m"));
        } else if (flag == "--terrain") {
            const std::string_view mode = require_value("--terrain");
            if (mode == "off") {
                args.terrain_mode = TerrainMode::Off;
            } else if (mode == "cpu") {
                args.terrain_mode = TerrainMode::Cpu;
            } else if (mode == "gpu") {
                args.terrain_mode = TerrainMode::Gpu;
            } else {
                throw std::invalid_argument("unknown value for --terrain, expected off|cpu|gpu");
            }
        } else if (flag == "--help" || flag == "-h") {
            std::cout
                << "Usage: ef_gpu_visual_phase0_probe [options]\n"
                << "  --frames N          benchmark frames (default 512)\n"
                << "  --objects N         synthetic visible objects (default 32)\n"
                << "  --height N          output height (default native ARB)\n"
                << "  --width N           output width (default native ARB)\n"
                << "  --envs N            batch worlds per frame and VRAM estimate (default 16)\n"
                << "  --history-steps N   history length for VRAM estimate (default 2048)\n"
                << "  --altitude-m X      camera altitude in meters (default 1200)\n"
                << "  --terrain MODE      off|cpu|gpu (default off)\n";
            std::exit(0);
        } else {
            throw std::invalid_argument("unknown flag: " + flag);
        }
    }
    args.frames = std::max(1, args.frames);
    args.objects = std::max(0, args.objects);
    args.height = std::max(1, args.height);
    args.width = std::max(1, args.width);
    args.envs = std::max(1, args.envs);
    args.history_steps = std::max(1, args.history_steps);
    return args;
}

bool include_terrain(TerrainMode mode) {
    return mode != TerrainMode::Off;
}

bool allow_gpu_terrain(TerrainMode mode) {
    return mode == TerrainMode::Gpu;
}

const char* terrain_mode_name(TerrainMode mode) {
    switch (mode) {
        case TerrainMode::Off:
            return "off";
        case TerrainMode::Cpu:
            return "cpu";
        case TerrainMode::Gpu:
            return "gpu";
    }
    return "unknown";
}

std::vector<gpu::VisibleObjectPacked> make_synthetic_objects(int count) {
    std::vector<gpu::VisibleObjectPacked> out;
    out.reserve(static_cast<std::size_t>(std::max(0, count)));
    std::mt19937 rng(1337);
    std::uniform_real_distribution<double> range_xy(-5000.0, 5000.0);
    std::uniform_real_distribution<double> range_z(50.0, 2500.0);
    std::uniform_real_distribution<double> range_v(-250.0, 250.0);
    std::uniform_real_distribution<double> range_radius(3.0, 40.0);
    for (int i = 0; i < count; ++i) {
        gpu::VisibleObjectPacked obj{};
        obj.x = range_xy(rng);
        obj.y = range_xy(rng);
        obj.z = range_z(rng);
        obj.vx = range_v(rng);
        obj.vy = range_v(rng);
        obj.vz = range_v(rng) * 0.1;
        obj.bounding_radius = range_radius(rng);
        obj.cls = i % 3;
        obj.team = (i % 3) - 1;
        out.push_back(obj);
    }
    return out;
}

std::vector<std::vector<gpu::VisibleObjectPacked>> make_batched_objects(
    int batch_count,
    int object_count
) {
    std::vector<std::vector<gpu::VisibleObjectPacked>> out;
    out.reserve(static_cast<std::size_t>(std::max(1, batch_count)));
    for (int batch_idx = 0; batch_idx < std::max(1, batch_count); ++batch_idx) {
        auto objects = make_synthetic_objects(object_count);
        const double dx = static_cast<double>(batch_idx) * 150.0;
        const double dy = static_cast<double>(batch_idx % 4) * 75.0;
        for (auto& obj : objects) {
            obj.x += dx;
            obj.y += dy;
        }
        out.push_back(std::move(objects));
    }
    return out;
}

std::vector<gpu::VisualRenderRequest> make_batched_requests(
    const Args& args,
    int batch_count
) {
    std::vector<gpu::VisualRenderRequest> out;
    out.reserve(static_cast<std::size_t>(std::max(1, batch_count)));
    for (int batch_idx = 0; batch_idx < std::max(1, batch_count); ++batch_idx) {
        gpu::VisualRenderRequest request{};
        request.cam_pos = {
            static_cast<double>(batch_idx) * 80.0,
            static_cast<double>(batch_idx % 4) * 40.0,
            args.altitude_m,
        };
        request.cam_heading_deg = std::fmod(static_cast<double>(batch_idx) * 7.5, 360.0);
        request.cam_pitch_deg = -12.0;
        request.fov_h_deg = 180.0;
        request.fov_v_deg = 90.0;
        request.out_height = args.height;
        request.out_width = args.width;
        request.include_terrain = include_terrain(args.terrain_mode);
        request.allow_gpu_terrain = allow_gpu_terrain(args.terrain_mode);
        out.push_back(request);
    }
    return out;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        const Args args = parse_args(argc, argv);
        auto device = gpu::probe_device();
        auto footprint = gpu::estimate_visual_tensor_footprint(
            args.height,
            args.width,
            args.envs,
            args.history_steps
        );

        std::cout << "GPU Visual Phase-0 Probe\n";
        std::cout << "========================\n";
        std::cout << "CUDA built: " << (device.cuda_runtime_built ? "yes" : "no") << '\n';
        std::cout << "CUDA runtime available: " << (device.cuda_runtime_available ? "yes" : "no") << '\n';
        std::cout << "CUDA device count: " << device.device_count << '\n';
        if (!device.device_name.empty()) {
            std::cout << "Active device: " << device.device_name
                      << " (sm_" << device.compute_major << device.compute_minor << ")\n";
        }
        if (device.total_global_mem_bytes > 0) {
            std::cout << "Device total memory: " << gpu::format_bytes(device.total_global_mem_bytes) << '\n';
        }
        if (device.free_global_mem_bytes > 0) {
            std::cout << "Device free memory: " << gpu::format_bytes(device.free_global_mem_bytes) << '\n';
        }
        if (!device.error_message.empty()) {
            std::cout << "CUDA probe note: " << device.error_message << '\n';
        }

        std::cout << '\n';
        std::cout << "Visual tensor footprint\n";
        std::cout << "-----------------------\n";
        std::cout << "Frame: " << args.height << "x" << args.width << "x" << footprint.channels
                  << " = " << gpu::format_bytes(footprint.frame_bytes) << '\n';
        std::cout << "Batch (" << footprint.env_count << " envs): "
                  << gpu::format_bytes(footprint.batch_bytes) << '\n';
        std::cout << "Double buffer: " << gpu::format_bytes(footprint.double_buffer_bytes) << '\n';
        std::cout << "History (" << footprint.history_steps << " steps): "
                  << gpu::format_bytes(footprint.history_bytes) << '\n';

        auto env = make_default_environment_model();
        env->set_terrain_type(include_terrain(args.terrain_mode) ? "legacy" : "flat");

        const auto requests = make_batched_requests(args, args.envs);
        const auto objects_batch = make_batched_objects(args.envs, args.objects);

        auto reference_once = gpu::render_visual_reference_cpu_batch(requests, objects_batch, env.get());
        auto gpu_once = gpu::render_visual_experiment_batch(requests, objects_batch, env.get());

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

        volatile double warmup_sum = std::accumulate(gpu_once.begin(), gpu_once.end(), 0.0);
        (void)warmup_sum;
        const bool device_resident_ready =
            gpu::render_visual_experiment_batch_device_resident(requests, objects_batch, env.get());
        const auto device_output_ptr = gpu::last_visual_output_device_ptr();
        const auto device_output_float_count = gpu::last_visual_output_float_count();

        double cpu_checksum = 0.0;
        const auto cpu_t0 = std::chrono::steady_clock::now();
        for (int frame = 0; frame < args.frames; ++frame) {
            auto rendered = gpu::render_visual_reference_cpu_batch(requests, objects_batch, env.get());
            cpu_checksum += std::accumulate(rendered.begin(), rendered.end(), 0.0);
        }
        const auto cpu_t1 = std::chrono::steady_clock::now();

        double gpu_checksum = 0.0;
        const auto gpu_t0 = std::chrono::steady_clock::now();
        for (int frame = 0; frame < args.frames; ++frame) {
            auto rendered = gpu::render_visual_experiment_batch(requests, objects_batch, env.get());
            gpu_checksum += std::accumulate(rendered.begin(), rendered.end(), 0.0);
        }
        const auto gpu_t1 = std::chrono::steady_clock::now();
        const auto gpu_stats_once = gpu::last_visual_experiment_stats();

        bool device_resident_ok = device_resident_ready;
        std::chrono::steady_clock::time_point gpu_device_t0{};
        std::chrono::steady_clock::time_point gpu_device_t1{};
        if (device_resident_ready) {
            gpu_device_t0 = std::chrono::steady_clock::now();
            for (int frame = 0; frame < args.frames; ++frame) {
                device_resident_ok =
                    gpu::render_visual_experiment_batch_device_resident(requests, objects_batch, env.get()) &&
                    device_resident_ok;
            }
            gpu_device_t1 = std::chrono::steady_clock::now();
        }
        const auto gpu_device_stats_once = gpu::last_visual_experiment_stats();

        const double cpu_total_s = std::chrono::duration<double>(cpu_t1 - cpu_t0).count();
        const double cpu_frames_per_s = static_cast<double>(args.frames) / std::max(cpu_total_s, 1.0e-9);
        const double cpu_world_frames_per_s =
            static_cast<double>(args.frames) * static_cast<double>(args.envs) / std::max(cpu_total_s, 1.0e-9);
        const double cpu_ms_per_frame = 1000.0 * cpu_total_s / static_cast<double>(args.frames);
        const double cpu_ms_per_world_frame = cpu_ms_per_frame / static_cast<double>(args.envs);
        const double cpu_megapixels_per_s =
            (static_cast<double>(args.frames) * static_cast<double>(args.envs) * static_cast<double>(args.height) * static_cast<double>(args.width) / 1.0e6)
            / std::max(cpu_total_s, 1.0e-9);

        const double gpu_total_s = std::chrono::duration<double>(gpu_t1 - gpu_t0).count();
        const double gpu_frames_per_s = static_cast<double>(args.frames) / std::max(gpu_total_s, 1.0e-9);
        const double gpu_world_frames_per_s =
            static_cast<double>(args.frames) * static_cast<double>(args.envs) / std::max(gpu_total_s, 1.0e-9);
        const double gpu_ms_per_frame = 1000.0 * gpu_total_s / static_cast<double>(args.frames);
        const double gpu_ms_per_world_frame = gpu_ms_per_frame / static_cast<double>(args.envs);
        const double gpu_megapixels_per_s =
            (static_cast<double>(args.frames) * static_cast<double>(args.envs) * static_cast<double>(args.height) * static_cast<double>(args.width) / 1.0e6)
            / std::max(gpu_total_s, 1.0e-9);

        const double gpu_device_total_s = device_resident_ready
            ? std::chrono::duration<double>(gpu_device_t1 - gpu_device_t0).count()
            : 0.0;
        const double gpu_device_frames_per_s = static_cast<double>(args.frames) / std::max(gpu_device_total_s, 1.0e-9);
        const double gpu_device_world_frames_per_s =
            static_cast<double>(args.frames) * static_cast<double>(args.envs) / std::max(gpu_device_total_s, 1.0e-9);
        const double gpu_device_ms_per_frame = 1000.0 * gpu_device_total_s / static_cast<double>(args.frames);
        const double gpu_device_ms_per_world_frame = gpu_device_ms_per_frame / static_cast<double>(args.envs);
        const double gpu_device_megapixels_per_s =
            (static_cast<double>(args.frames) * static_cast<double>(args.envs) * static_cast<double>(args.height) * static_cast<double>(args.width) / 1.0e6)
            / std::max(gpu_device_total_s, 1.0e-9);

        std::cout << '\n';
        std::cout << "Render mode\n";
        std::cout << "-----------\n";
        std::cout << "Terrain pass: " << terrain_mode_name(args.terrain_mode) << '\n';
        std::cout << "Environment terrain: " << (include_terrain(args.terrain_mode) ? "legacy" : "flat") << '\n';
        std::cout << "Batch worlds/frame: " << args.envs << '\n';
        std::cout << '\n';
        std::cout << "CPU reference baseline\n";
        std::cout << "----------------------\n";
        std::cout << "Frames: " << args.frames << '\n';
        std::cout << "Objects/world: " << args.objects << '\n';
        std::cout << "ms/batch-frame: " << std::fixed << std::setprecision(4) << cpu_ms_per_frame << '\n';
        std::cout << "ms/world-frame: " << std::fixed << std::setprecision(4) << cpu_ms_per_world_frame << '\n';
        std::cout << "batch-frames/s: " << std::fixed << std::setprecision(2) << cpu_frames_per_s << '\n';
        std::cout << "world-frames/s: " << std::fixed << std::setprecision(2) << cpu_world_frames_per_s << '\n';
        std::cout << "megapixels/s: " << std::fixed << std::setprecision(2) << cpu_megapixels_per_s << '\n';
        std::cout << "checksum: " << std::fixed << std::setprecision(6) << cpu_checksum << '\n';
        std::cout << '\n';
        std::cout << "GPU experiment path\n";
        std::cout << "-------------------\n";
        std::cout << "ms/batch-frame: " << std::fixed << std::setprecision(4) << gpu_ms_per_frame << '\n';
        std::cout << "ms/world-frame: " << std::fixed << std::setprecision(4) << gpu_ms_per_world_frame << '\n';
        std::cout << "batch-frames/s: " << std::fixed << std::setprecision(2) << gpu_frames_per_s << '\n';
        std::cout << "world-frames/s: " << std::fixed << std::setprecision(2) << gpu_world_frames_per_s << '\n';
        std::cout << "megapixels/s: " << std::fixed << std::setprecision(2) << gpu_megapixels_per_s << '\n';
        std::cout << "checksum: " << std::fixed << std::setprecision(6) << gpu_checksum << '\n';
        std::cout << "speedup: " << std::fixed << std::setprecision(2)
                  << (gpu_ms_per_world_frame > 0.0 ? cpu_ms_per_world_frame / gpu_ms_per_world_frame : 0.0) << "x\n";
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
            std::cout << "ms/batch-frame: " << std::fixed << std::setprecision(4) << gpu_device_ms_per_frame << '\n';
            std::cout << "ms/world-frame: " << std::fixed << std::setprecision(4) << gpu_device_ms_per_world_frame << '\n';
            std::cout << "batch-frames/s: " << std::fixed << std::setprecision(2) << gpu_device_frames_per_s << '\n';
            std::cout << "world-frames/s: " << std::fixed << std::setprecision(2) << gpu_device_world_frames_per_s << '\n';
            std::cout << "megapixels/s: " << std::fixed << std::setprecision(2) << gpu_device_megapixels_per_s << '\n';
            std::cout << "speedup_vs_cpu: " << std::fixed << std::setprecision(2)
                      << (gpu_device_ms_per_world_frame > 0.0 ? cpu_ms_per_world_frame / gpu_device_ms_per_world_frame : 0.0) << "x\n";
            std::cout << "uplift_vs_gpu_host: " << std::fixed << std::setprecision(2)
                      << (gpu_device_ms_per_world_frame > 0.0 ? gpu_ms_per_world_frame / gpu_device_ms_per_world_frame : 0.0) << "x\n";
        } else {
            std::cout << "status: unavailable for the current render mode\n";
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
        std::cout << '\n';
        if (args.terrain_mode == TerrainMode::Cpu) {
            std::cout << "Note: terrain=cpu forces the experiment path to fall back to the CPU reference.\n";
        } else if (args.terrain_mode == TerrainMode::Gpu) {
            std::cout << "Note: terrain=gpu benchmarks the batched CUDA terrain+object path against the\n";
            std::cout << "CPU reference on the same legacy terrain snapshot.\n";
        } else {
            std::cout << "Note: terrain=off benchmarks the batched CUDA object-raster path against the\n";
            std::cout << "CPU batch adapter on the same object-only semantics.\n";
        }
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "ef_gpu_visual_phase0_probe failed: " << ex.what() << '\n';
        return 1;
    }
}
