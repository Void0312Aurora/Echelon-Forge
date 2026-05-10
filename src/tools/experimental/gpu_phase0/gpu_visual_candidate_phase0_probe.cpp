#include "gpu/gpu_interaction_broadphase_runtime.h"
#include "gpu/gpu_visual_runtime.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <exception>
#include <iomanip>
#include <iostream>
#include <random>
#include <string>
#include <vector>

namespace {

struct Args {
    int worlds = 16;
    int objects = 1024;
    int cameras = 64;
    double far_range_m = 25000.0;
    double cell_size_m = 5000.0;
    double max_object_radius_m = 50.0;
    int bucket_count = 32768;
    int bucket_capacity = 64;
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

double parse_double(const char* value, const char* name) {
    char* end = nullptr;
    const double parsed = std::strtod(value, &end);
    if (end == value || *end != '\0') {
        throw std::invalid_argument(std::string("invalid float for ") + name);
    }
    return parsed;
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
        if (flag == "--worlds") {
            args.worlds = parse_int(require_value("--worlds"), "--worlds");
        } else if (flag == "--objects") {
            args.objects = parse_int(require_value("--objects"), "--objects");
        } else if (flag == "--cameras") {
            args.cameras = parse_int(require_value("--cameras"), "--cameras");
        } else if (flag == "--far-range") {
            args.far_range_m = parse_double(require_value("--far-range"), "--far-range");
        } else if (flag == "--cell-size") {
            args.cell_size_m = parse_double(require_value("--cell-size"), "--cell-size");
        } else if (flag == "--max-object-radius") {
            args.max_object_radius_m = parse_double(require_value("--max-object-radius"), "--max-object-radius");
        } else if (flag == "--bucket-count") {
            args.bucket_count = parse_int(require_value("--bucket-count"), "--bucket-count");
        } else if (flag == "--bucket-capacity") {
            args.bucket_capacity = parse_int(require_value("--bucket-capacity"), "--bucket-capacity");
        } else if (flag == "--seed") {
            args.seed = parse_int(require_value("--seed"), "--seed");
        } else if (flag == "--help" || flag == "-h") {
            std::cout
                << "Usage: ef_gpu_visual_candidate_phase0_probe [options]\n"
                << "  --worlds N             worlds in batch (default 16)\n"
                << "  --objects N            objects per world (default 1024)\n"
                << "  --cameras N            cameras per world (default 64)\n"
                << "  --far-range X          finite visual far range meters (default 25000)\n"
                << "  --cell-size X          grid cell size meters (default 5000)\n"
                << "  --max-object-radius X  conservative object radius meters (default 50)\n"
                << "  --bucket-count N       hash bucket count (default 32768)\n"
                << "  --bucket-capacity N    entries per bucket before overflow fallback (default 64)\n"
                << "  --seed N               rng seed (default 7)\n";
            std::exit(0);
        } else {
            throw std::invalid_argument("unknown flag: " + flag);
        }
    }
    args.worlds = std::max(1, args.worlds);
    args.objects = std::max(1, args.objects);
    args.cameras = std::max(1, args.cameras);
    args.far_range_m = std::max(1.0, args.far_range_m);
    args.cell_size_m = std::max(1.0, args.cell_size_m);
    args.max_object_radius_m = std::max(0.0, args.max_object_radius_m);
    args.bucket_count = std::max(1, args.bucket_count);
    args.bucket_capacity = std::max(1, args.bucket_capacity);
    return args;
}

struct CameraPacked {
    int world_index = 0;
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    double heading_deg = 0.0;
    double pitch_deg = 0.0;
    double fov_h_deg = 180.0;
    double fov_v_deg = 90.0;
};

struct GeneratedBatch {
    std::vector<gpu::InteractionEntityPacked> entities;
    std::vector<gpu::InteractionQueryPacked> queries;
    std::vector<CameraPacked> cameras;
};

GeneratedBatch make_batch(const Args& args) {
    GeneratedBatch batch{};
    batch.entities.reserve(static_cast<std::size_t>(args.worlds) * static_cast<std::size_t>(args.objects));
    batch.queries.reserve(static_cast<std::size_t>(args.worlds) * static_cast<std::size_t>(args.cameras));
    batch.cameras.reserve(static_cast<std::size_t>(args.worlds) * static_cast<std::size_t>(args.cameras));

    std::mt19937 rng(static_cast<std::uint32_t>(args.seed));
    std::uniform_real_distribution<double> pos_xy(-25000.0, 25000.0);
    std::uniform_real_distribution<double> pos_z(0.0, 12000.0);
    std::uniform_real_distribution<double> radius(10.0, args.max_object_radius_m > 0.0 ? args.max_object_radius_m : 1.0);
    std::uniform_real_distribution<double> heading(0.0, 360.0);
    std::uniform_real_distribution<double> pitch(-20.0, 20.0);

    for (int world_idx = 0; world_idx < args.worlds; ++world_idx) {
        const double world_x_offset = static_cast<double>(world_idx % 8) * 100000.0;
        const double world_y_offset = static_cast<double>(world_idx / 8) * 100000.0;
        for (int object_idx = 0; object_idx < args.objects; ++object_idx) {
            gpu::InteractionEntityPacked entity{};
            entity.world_index = world_idx;
            entity.local_index = object_idx;
            entity.x = world_x_offset + pos_xy(rng);
            entity.y = world_y_offset + pos_xy(rng);
            entity.z = pos_z(rng);
            entity.bounding_radius_m = radius(rng);
            batch.entities.push_back(entity);
        }
        for (int camera_idx = 0; camera_idx < args.cameras; ++camera_idx) {
            CameraPacked camera{};
            camera.world_index = world_idx;
            camera.x = world_x_offset + pos_xy(rng);
            camera.y = world_y_offset + pos_xy(rng);
            camera.z = pos_z(rng);
            camera.heading_deg = heading(rng);
            camera.pitch_deg = pitch(rng);
            camera.fov_h_deg = 180.0;
            camera.fov_v_deg = 90.0;
            batch.cameras.push_back(camera);

            gpu::InteractionQueryPacked query{};
            query.world_index = world_idx;
            query.x = camera.x;
            query.y = camera.y;
            query.z = camera.z;
            query.range_m = args.far_range_m;
            batch.queries.push_back(query);
        }
    }
    return batch;
}

double to_radians(double deg) {
    return deg * 3.14159265358979323846 / 180.0;
}

bool visual_candidate_exact(
    const CameraPacked& cam,
    const gpu::InteractionEntityPacked& obj,
    double far_range_m
) {
    const double yaw_rad = to_radians(90.0 - cam.heading_deg);
    const double pitch_rad = to_radians(cam.pitch_deg);
    const double fwd_x = std::cos(yaw_rad) * std::cos(pitch_rad);
    const double fwd_y = std::sin(yaw_rad) * std::cos(pitch_rad);
    const double fwd_z = std::sin(pitch_rad);
    const double right_x = std::sin(yaw_rad);
    const double right_y = -std::cos(yaw_rad);
    const double right_z = 0.0;
    const double up_x = -std::cos(yaw_rad) * std::sin(pitch_rad);
    const double up_y = -std::sin(yaw_rad) * std::sin(pitch_rad);
    const double up_z = std::cos(pitch_rad);

    const double dx = obj.x - cam.x;
    const double dy = obj.y - cam.y;
    const double dz = obj.z - cam.z;

    const double cam_z = dx * fwd_x + dy * fwd_y + dz * fwd_z;
    const double cam_x = dx * right_x + dy * right_y + dz * right_z;
    const double cam_y = dx * up_x + dy * up_y + dz * up_z;
    const double d = std::sqrt(dx * dx + dy * dy + dz * dz);
    const double r = std::max(0.0, obj.bounding_radius_m);

    if (d - r > far_range_m) {
        return false;
    }
    if (cam_z <= 0.1 - r) {
        return false;
    }

    const double theta = std::atan2(cam_x, cam_z);
    const double phi = std::atan2(cam_y, cam_z);
    const double alpha = std::atan2(r, std::max(d, 1.0e-6));
    const double half_fov_h = to_radians(cam.fov_h_deg / 2.0);
    const double half_fov_v = to_radians(cam.fov_v_deg / 2.0);
    if (std::abs(theta) > half_fov_h + alpha) {
        return false;
    }
    if (std::abs(phi) > half_fov_v + alpha) {
        return false;
    }
    return true;
}

std::vector<std::uint32_t> compute_visual_exact_reference(const GeneratedBatch& batch, const Args& args) {
    const std::size_t words_per_query = gpu::interaction_broadphase_word_count(args.objects);
    std::vector<std::uint32_t> out(batch.cameras.size() * words_per_query, 0u);
    for (std::size_t cam_idx = 0; cam_idx < batch.cameras.size(); ++cam_idx) {
        const auto& cam = batch.cameras[cam_idx];
        auto* dst = out.data() + cam_idx * words_per_query;
        for (const auto& obj : batch.entities) {
            if (obj.world_index != cam.world_index) {
                continue;
            }
            if (!visual_candidate_exact(cam, obj, args.far_range_m)) {
                continue;
            }
            const std::size_t word_index = static_cast<std::size_t>(obj.local_index) / 32u;
            dst[word_index] |= static_cast<std::uint32_t>(1u << (obj.local_index & 31));
        }
    }
    return out;
}

std::size_t popcount_words(const std::vector<std::uint32_t>& words) {
    std::size_t total = 0;
    for (const auto word : words) {
        total += static_cast<std::size_t>(__builtin_popcount(word));
    }
    return total;
}

struct CompareSummary {
    std::size_t reference_pairs = 0;
    std::size_t gpu_pairs = 0;
    std::size_t missing_pairs = 0;
};

CompareSummary compare_superset(
    const std::vector<std::uint32_t>& reference_bits,
    const std::vector<std::uint32_t>& gpu_bits
) {
    CompareSummary summary{};
    if (reference_bits.size() != gpu_bits.size()) {
        throw std::runtime_error("bitset size mismatch");
    }
    summary.reference_pairs = popcount_words(reference_bits);
    summary.gpu_pairs = popcount_words(gpu_bits);
    for (std::size_t idx = 0; idx < reference_bits.size(); ++idx) {
        const std::uint32_t missed = reference_bits[idx] & ~gpu_bits[idx];
        summary.missing_pairs += static_cast<std::size_t>(__builtin_popcount(missed));
    }
    return summary;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        const Args args = parse_args(argc, argv);
        const auto device = gpu::probe_device();
        const auto batch = make_batch(args);
        gpu::InteractionBroadphaseConfig config{};
        config.cell_size_m = args.cell_size_m;
        config.max_entity_radius_m = args.max_object_radius_m;
        config.entities_per_world = args.objects;
        config.hash_bucket_count = args.bucket_count;
        config.bucket_capacity = args.bucket_capacity;

        std::cout << "GPU Visual Candidate Phase-0 Probe\n";
        std::cout << "==================================\n";
        std::cout << "CUDA built: " << (device.cuda_runtime_built ? "yes" : "no") << '\n';
        std::cout << "CUDA runtime available: " << (device.cuda_runtime_available ? "yes" : "no") << '\n';
        std::cout << "Worlds: " << args.worlds
                  << ", objects/world: " << args.objects
                  << ", cameras/world: " << args.cameras << "\n\n";

        const auto cpu_start = std::chrono::steady_clock::now();
        const auto cpu_reference = compute_visual_exact_reference(batch, args);
        const auto cpu_end = std::chrono::steady_clock::now();
        const double cpu_ms = std::chrono::duration<double, std::milli>(cpu_end - cpu_start).count();

        (void)gpu::build_interaction_broadphase_experiment_batch(batch.entities, batch.queries, config);
        (void)gpu::build_interaction_broadphase_experiment_batch_device_resident(batch.entities, batch.queries, config);

        const auto gpu_host = gpu::build_interaction_broadphase_experiment_batch(
            batch.entities,
            batch.queries,
            config
        );
        const auto host_stats = gpu::last_interaction_broadphase_stats();
        const auto compare = compare_superset(cpu_reference, gpu_host);

        const bool device_ok = gpu::build_interaction_broadphase_experiment_batch_device_resident(
            batch.entities,
            batch.queries,
            config
        );
        const auto device_stats = gpu::last_interaction_broadphase_stats();

        std::cout << std::fixed << std::setprecision(4);
        std::cout << "CPU exact visual candidate reference: " << cpu_ms << " ms\n";
        std::cout << "GPU host-readback: " << host_stats.total_ms << " ms";
        if (host_stats.total_ms > 0.0) {
            std::cout << "  (" << (cpu_ms / host_stats.total_ms) << "x vs CPU)";
        }
        std::cout << "\n";
        if (device_ok) {
            std::cout << "GPU device-resident: " << device_stats.total_ms << " ms";
            if (device_stats.total_ms > 0.0) {
                std::cout << "  (" << (cpu_ms / device_stats.total_ms) << "x vs CPU)";
            }
            std::cout << "\n";
        }
        std::cout << "Reference candidate pairs: " << compare.reference_pairs << "\n";
        std::cout << "GPU candidate pairs: " << compare.gpu_pairs << "\n";
        std::cout << "Missing reference pairs: " << compare.missing_pairs << "\n";
        std::cout << "Overflow buckets / queries: "
                  << host_stats.overflow_bucket_count << " / " << host_stats.overflow_query_count << "\n";
        if (compare.reference_pairs > 0) {
            std::cout << "Expansion factor: "
                      << (static_cast<double>(compare.gpu_pairs) / static_cast<double>(compare.reference_pairs))
                      << "x\n";
        }
        if (compare.missing_pairs != 0) {
            return 2;
        }
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "error: " << ex.what() << '\n';
        return 1;
    }
}
