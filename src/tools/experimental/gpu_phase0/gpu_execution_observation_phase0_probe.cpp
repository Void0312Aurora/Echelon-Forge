#include "gpu/gpu_execution_observation_runtime.h"
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
#include <string_view>
#include <vector>

namespace {

enum class MissionMode {
    Basic = 0,
    NavV1 = 1,
    NavV2 = 2,
};

struct Args {
    int frames = 512;
    int envs = 256;
    int contacts = 8;
    int rwr = 4;
    int max_contacts = 16;
    int max_rwr = 8;
    MissionMode mission_mode = MissionMode::NavV2;
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
        } else if (flag == "--contacts") {
            args.contacts = parse_int(require_value("--contacts"), "--contacts");
        } else if (flag == "--rwr") {
            args.rwr = parse_int(require_value("--rwr"), "--rwr");
        } else if (flag == "--max-contacts") {
            args.max_contacts = parse_int(require_value("--max-contacts"), "--max-contacts");
        } else if (flag == "--max-rwr") {
            args.max_rwr = parse_int(require_value("--max-rwr"), "--max-rwr");
        } else if (flag == "--mission-mode") {
            const std::string_view mode = require_value("--mission-mode");
            if (mode == "basic") {
                args.mission_mode = MissionMode::Basic;
            } else if (mode == "nav_v1") {
                args.mission_mode = MissionMode::NavV1;
            } else if (mode == "nav_v2") {
                args.mission_mode = MissionMode::NavV2;
            } else {
                throw std::invalid_argument("unknown value for --mission-mode, expected basic|nav_v1|nav_v2");
            }
        } else if (flag == "--help" || flag == "-h") {
            std::cout
                << "Usage: ef_gpu_execution_observation_phase0_probe [options]\n"
                << "  --frames N         benchmark frames (default 512)\n"
                << "  --envs N           batch worlds per frame (default 256)\n"
                << "  --contacts N       contacts per world (default 8)\n"
                << "  --rwr N            RWR warnings per world (default 4)\n"
                << "  --max-contacts N   padded contact width (default 16)\n"
                << "  --max-rwr N        padded RWR width (default 8)\n"
                << "  --mission-mode M   basic|nav_v1|nav_v2 (default nav_v2)\n";
            std::exit(0);
        } else {
            throw std::invalid_argument("unknown flag: " + flag);
        }
    }
    args.frames = std::max(1, args.frames);
    args.envs = std::max(1, args.envs);
    args.contacts = std::max(0, args.contacts);
    args.rwr = std::max(0, args.rwr);
    args.max_contacts = std::max(args.contacts, std::max(0, args.max_contacts));
    args.max_rwr = std::max(args.rwr, std::max(0, args.max_rwr));
    return args;
}

int mission_mode_code(MissionMode mode) {
    return static_cast<int>(mode);
}

const char* mission_mode_name(MissionMode mode) {
    switch (mode) {
        case MissionMode::Basic:
            return "basic";
        case MissionMode::NavV1:
            return "nav_v1";
        case MissionMode::NavV2:
            return "nav_v2";
    }
    return "unknown";
}

gpu::ExecutionObservationBatchRequest::InstrumentPacked make_instrument(int idx) {
    gpu::ExecutionObservationBatchRequest::InstrumentPacked inst{};
    inst.alt_baro_m = 1200.0 + idx * 3.0;
    inst.alt_radar_m = 1180.0 + idx * 2.5;
    inst.ias_mps = 180.0 + (idx % 9) * 7.5;
    inst.mach = 0.48 + (idx % 5) * 0.03;
    inst.vvi_mps = -2.0 + (idx % 11) * 0.4;
    inst.pitch_deg = -3.0 + (idx % 7) * 1.1;
    inst.roll_deg = -25.0 + (idx % 13) * 3.0;
    inst.heading_deg = std::fmod(35.0 + idx * 5.5, 360.0);
    inst.aoa_deg = 2.0 + (idx % 6) * 0.7;
    inst.beta_deg = -1.5 + (idx % 5) * 0.5;
    inst.g_load_normal = 1.0 + (idx % 4) * 0.15;
    inst.g_load_axial = 0.02 * (idx % 3);
    inst.p_deg_s = -4.0 + (idx % 9);
    inst.q_deg_s = -2.0 + (idx % 7) * 0.4;
    inst.r_deg_s = -3.0 + (idx % 11) * 0.3;
    inst.engine_rpm_pct = 72.0 + (idx % 8) * 2.0;
    inst.fuel_internal_kg = 1800.0 - (idx % 40) * 12.0;
    inst.fuel_external_kg = 150.0 + (idx % 5) * 20.0;
    inst.fuel_flow_kg_h = 1350.0 + (idx % 12) * 15.0;
    inst.gear_pos = 0.0f;
    inst.flaps_pos = 0.0f;
    inst.speedbrake_pos = (idx % 3 == 0) ? 0.1f : 0.0f;
    inst.cmd_heading_deg = std::fmod(inst.heading_deg + 8.0, 360.0);
    inst.cmd_alt_m = inst.alt_baro_m + 150.0;
    inst.cmd_speed_mps = inst.ias_mps + 12.0;
    inst.lat_deg = 30.0 + idx * 0.001;
    inst.lon_deg = 120.0 + idx * 0.0015;
    inst.vn_mps = 120.0 + (idx % 9) * 1.2;
    inst.ve_mps = 45.0 + (idx % 7) * 0.9;
    inst.vd_mps = -1.5 + (idx % 5) * 0.2;
    inst.ground_speed_mps = 128.0 + (idx % 6) * 1.0;
    inst.ground_track_deg = std::fmod(inst.heading_deg - 2.5, 360.0);
    inst.wind_speed_mps = 8.0 + (idx % 5) * 1.1;
    inst.wind_dir_deg = std::fmod(260.0 + idx * 4.0, 360.0);
    inst.oat_c = 12.0 - (idx % 6) * 0.6;
    inst.gps_available = true;
    inst.position_uncertainty_m = 6.0 + (idx % 4) * 0.75;
    inst.rwr_active = (idx % 2) == 0;
    inst.missiles_remaining = 4 - (idx % 3);
    return inst;
}

std::vector<gpu::ExecutionObservationBatchRequest> make_requests(const Args& args) {
    std::vector<gpu::ExecutionObservationBatchRequest> out;
    out.reserve(static_cast<std::size_t>(args.envs));
    for (int idx = 0; idx < args.envs; ++idx) {
        gpu::ExecutionObservationBatchRequest req{};
        req.inst = make_instrument(idx);
        req.ils_valid = 1.0;
        req.ils_loc = -0.08 + (idx % 5) * 0.03;
        req.ils_gs = 0.04 - (idx % 7) * 0.01;
        req.ils_dme = 12.0 + (idx % 11) * 0.8;
        req.contact_count = args.contacts;
        req.rwr_count = args.rwr;
        req.mission.mode_code = mission_mode_code(args.mission_mode);
        req.mission.command_code = (idx % 3 == 0) ? 3.0 : 1.0;
        req.mission.target_heading_deg = req.inst.cmd_heading_deg;
        req.mission.target_altitude_m = req.inst.cmd_alt_m;
        req.mission.target_speed_mps = req.inst.cmd_speed_mps;
        req.mission.has_route_guidance = args.mission_mode != MissionMode::Basic;
        req.mission.route_idx = idx % 7;
        req.mission.route_count = 12;
        req.mission.route_waypoint_flyover = (idx % 4) == 0;
        req.mission.route_dist_m = 9000.0 + (idx % 13) * 220.0;
        req.mission.route_reward_xtk_m = -250.0 + (idx % 11) * 55.0;
        req.mission.route_reward_dtg_m = 14000.0 + (idx % 17) * 180.0;
        req.mission.route_direct_to_track_deg = std::fmod(req.inst.heading_deg + 12.0 + idx * 0.25, 360.0);
        req.mission.route_reward_desired_track_deg = std::fmod(req.inst.heading_deg + 6.0 + idx * 0.15, 360.0);
        req.mission.route_next_turn_deg = -35.0 + (idx % 9) * 8.0;
        req.mission.route_distance_to_turn_m = 2200.0 + (idx % 10) * 140.0;
        req.mission.nav_own_altitude_m = req.inst.alt_baro_m;
        req.mission.nav_truth_heading_deg = req.inst.heading_deg - 1.5;
        req.mission.nav_truth_speed_mps = req.inst.ground_speed_mps;
        req.mission.nav_inst_heading_deg = req.inst.heading_deg;
        req.mission.nav_inst_ground_track_deg = req.inst.ground_track_deg;
        req.mission.nav_inst_ias_mps = req.inst.ias_mps;
        req.mission.nav_waypoint_altitude_m = req.inst.cmd_alt_m + 120.0;
        req.mission.nav_cdi_full_scale_m = 1500.0;
        out.push_back(req);
    }
    return out;
}

std::vector<std::vector<TrackData>> make_contacts_batch(const Args& args) {
    std::vector<std::vector<TrackData>> out;
    out.reserve(static_cast<std::size_t>(args.envs));
    for (int world = 0; world < args.envs; ++world) {
        std::vector<TrackData> contacts;
        contacts.reserve(static_cast<std::size_t>(args.contacts));
        for (int idx = 0; idx < args.contacts; ++idx) {
            TrackData track{};
            track.id = static_cast<std::uint64_t>(world * 1000 + idx);
            track.range = 3000.0 + idx * 450.0 + world * 2.0;
            track.azimuth = -45.0 + idx * 12.0;
            track.elevation = -8.0 + idx * 2.0;
            track.closing_speed = -120.0 + idx * 18.0;
            track.time_since_update = 0.05 * idx;
            track.source = 1 + (idx % 3);
            track.classification = 1 + (idx % 3);
            contacts.push_back(track);
        }
        out.push_back(std::move(contacts));
    }
    return out;
}

std::vector<std::vector<RWREvent>> make_rwr_batch(const Args& args) {
    std::vector<std::vector<RWREvent>> out;
    out.reserve(static_cast<std::size_t>(args.envs));
    for (int world = 0; world < args.envs; ++world) {
        std::vector<RWREvent> rwr;
        rwr.reserve(static_cast<std::size_t>(args.rwr));
        for (int idx = 0; idx < args.rwr; ++idx) {
            RWREvent event{};
            event.source_id = static_cast<std::uint64_t>(world * 500 + idx);
            event.bearing = -120.0 + idx * 33.0;
            event.signal_strength = 0.15 + idx * 0.2;
            event.is_lock = (idx % 2) == 0;
            event.is_launch = idx == args.rwr - 1;
            rwr.push_back(event);
        }
        out.push_back(std::move(rwr));
    }
    return out;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        const Args args = parse_args(argc, argv);
        const auto device = gpu::probe_device();
        const auto requests = make_requests(args);
        const auto contacts_batch = make_contacts_batch(args);
        const auto rwr_batch = make_rwr_batch(args);
        const std::size_t per_request_floats =
            gpu::execution_observation_output_float_count(
                args.max_contacts,
                args.max_rwr,
                mission_mode_code(args.mission_mode)
            );
        const std::size_t batch_floats = per_request_floats * static_cast<std::size_t>(args.envs);

        std::cout << "GPU Execution Observation Phase-0 Probe\n";
        std::cout << "=======================================\n";
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
        std::cout << "Contacts/world: " << args.contacts << " (max " << args.max_contacts << ")\n";
        std::cout << "RWR/world: " << args.rwr << " (max " << args.max_rwr << ")\n";
        std::cout << "Mission mode: " << mission_mode_name(args.mission_mode) << '\n';
        std::cout << "Per-world floats: " << per_request_floats << '\n';
        std::cout << "Batch bytes: " << gpu::format_bytes(batch_floats * sizeof(float)) << '\n';

        auto reference_once = gpu::compute_execution_observation_reference_cpu_batch(
            requests, contacts_batch, rwr_batch, args.max_contacts, args.max_rwr
        );
        auto gpu_once = gpu::compute_execution_observation_experiment_batch(
            requests, contacts_batch, rwr_batch, args.max_contacts, args.max_rwr
        );
        const bool device_resident_ready = gpu::compute_execution_observation_experiment_batch_device_resident(
            requests, contacts_batch, rwr_batch, args.max_contacts, args.max_rwr
        );
        const auto device_output_ptr = gpu::last_execution_observation_output_device_ptr();
        const auto device_output_float_count = gpu::last_execution_observation_output_float_count();

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

        double cpu_checksum = 0.0;
        const auto cpu_t0 = std::chrono::steady_clock::now();
        for (int frame = 0; frame < args.frames; ++frame) {
            auto rendered = gpu::compute_execution_observation_reference_cpu_batch(
                requests, contacts_batch, rwr_batch, args.max_contacts, args.max_rwr
            );
            cpu_checksum += std::accumulate(rendered.begin(), rendered.end(), 0.0);
        }
        const auto cpu_t1 = std::chrono::steady_clock::now();

        double gpu_checksum = 0.0;
        const auto gpu_t0 = std::chrono::steady_clock::now();
        for (int frame = 0; frame < args.frames; ++frame) {
            auto rendered = gpu::compute_execution_observation_experiment_batch(
                requests, contacts_batch, rwr_batch, args.max_contacts, args.max_rwr
            );
            gpu_checksum += std::accumulate(rendered.begin(), rendered.end(), 0.0);
        }
        const auto gpu_t1 = std::chrono::steady_clock::now();
        const auto gpu_stats_once = gpu::last_execution_observation_stats();

        bool device_resident_ok = device_resident_ready;
        std::chrono::steady_clock::time_point gpu_device_t0{};
        std::chrono::steady_clock::time_point gpu_device_t1{};
        if (device_resident_ready) {
            gpu_device_t0 = std::chrono::steady_clock::now();
            for (int frame = 0; frame < args.frames; ++frame) {
                device_resident_ok =
                    gpu::compute_execution_observation_experiment_batch_device_resident(
                        requests, contacts_batch, rwr_batch, args.max_contacts, args.max_rwr
                    ) && device_resident_ok;
            }
            gpu_device_t1 = std::chrono::steady_clock::now();
        }
        const auto gpu_device_stats_once = gpu::last_execution_observation_stats();

        const double cpu_total_s = std::chrono::duration<double>(cpu_t1 - cpu_t0).count();
        const double gpu_total_s = std::chrono::duration<double>(gpu_t1 - gpu_t0).count();
        const double gpu_device_total_s = device_resident_ready
            ? std::chrono::duration<double>(gpu_device_t1 - gpu_device_t0).count()
            : 0.0;

        const double cpu_ms_per_batch = 1000.0 * cpu_total_s / static_cast<double>(args.frames);
        const double cpu_ms_per_world = cpu_ms_per_batch / static_cast<double>(args.envs);
        const double gpu_ms_per_batch = 1000.0 * gpu_total_s / static_cast<double>(args.frames);
        const double gpu_ms_per_world = gpu_ms_per_batch / static_cast<double>(args.envs);
        const double gpu_device_ms_per_batch = 1000.0 * gpu_device_total_s / static_cast<double>(std::max(1, args.frames));
        const double gpu_device_ms_per_world = gpu_device_ms_per_batch / static_cast<double>(args.envs);

        std::cout << '\n';
        std::cout << "CPU reference baseline\n";
        std::cout << "----------------------\n";
        std::cout << "Frames: " << args.frames << '\n';
        std::cout << "ms/batch-frame: " << std::fixed << std::setprecision(4) << cpu_ms_per_batch << '\n';
        std::cout << "ms/world-frame: " << std::fixed << std::setprecision(4) << cpu_ms_per_world << '\n';
        std::cout << "batch-frames/s: " << std::fixed << std::setprecision(2)
                  << (static_cast<double>(args.frames) / std::max(cpu_total_s, 1.0e-9)) << '\n';
        std::cout << "world-frames/s: " << std::fixed << std::setprecision(2)
                  << (static_cast<double>(args.frames) * static_cast<double>(args.envs) / std::max(cpu_total_s, 1.0e-9)) << '\n';
        std::cout << "checksum: " << std::fixed << std::setprecision(6) << cpu_checksum << '\n';

        std::cout << '\n';
        std::cout << "GPU experiment path\n";
        std::cout << "-------------------\n";
        std::cout << "ms/batch-frame: " << std::fixed << std::setprecision(4) << gpu_ms_per_batch << '\n';
        std::cout << "ms/world-frame: " << std::fixed << std::setprecision(4) << gpu_ms_per_world << '\n';
        std::cout << "batch-frames/s: " << std::fixed << std::setprecision(2)
                  << (static_cast<double>(args.frames) / std::max(gpu_total_s, 1.0e-9)) << '\n';
        std::cout << "world-frames/s: " << std::fixed << std::setprecision(2)
                  << (static_cast<double>(args.frames) * static_cast<double>(args.envs) / std::max(gpu_total_s, 1.0e-9)) << '\n';
        std::cout << "checksum: " << std::fixed << std::setprecision(6) << gpu_checksum << '\n';
        std::cout << "speedup: " << std::fixed << std::setprecision(2)
                  << (gpu_ms_per_world > 0.0 ? cpu_ms_per_world / gpu_ms_per_world : 0.0) << "x\n";
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
            std::cout << "ms/batch-frame: " << std::fixed << std::setprecision(4) << gpu_device_ms_per_batch << '\n';
            std::cout << "ms/world-frame: " << std::fixed << std::setprecision(4) << gpu_device_ms_per_world << '\n';
            std::cout << "batch-frames/s: " << std::fixed << std::setprecision(2)
                      << (static_cast<double>(args.frames) / std::max(gpu_device_total_s, 1.0e-9)) << '\n';
            std::cout << "world-frames/s: " << std::fixed << std::setprecision(2)
                      << (static_cast<double>(args.frames) * static_cast<double>(args.envs) / std::max(gpu_device_total_s, 1.0e-9)) << '\n';
            std::cout << "speedup_vs_cpu: " << std::fixed << std::setprecision(2)
                      << (gpu_device_ms_per_world > 0.0 ? cpu_ms_per_world / gpu_device_ms_per_world : 0.0) << "x\n";
            std::cout << "uplift_vs_gpu_host: " << std::fixed << std::setprecision(2)
                      << (gpu_device_ms_per_world > 0.0 ? gpu_ms_per_world / gpu_device_ms_per_world : 0.0) << "x\n";
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
        std::cerr << "ef_gpu_execution_observation_phase0_probe failed: " << ex.what() << '\n';
        return 1;
    }
}
