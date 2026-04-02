#include "components/systems/sensor.h"
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
    int targets = 1024;
    int sensors = 256;
    double cell_size_m = 5000.0;
    double max_target_radius_m = 50.0;
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
        } else if (flag == "--targets") {
            args.targets = parse_int(require_value("--targets"), "--targets");
        } else if (flag == "--sensors") {
            args.sensors = parse_int(require_value("--sensors"), "--sensors");
        } else if (flag == "--cell-size") {
            args.cell_size_m = parse_double(require_value("--cell-size"), "--cell-size");
        } else if (flag == "--max-target-radius") {
            args.max_target_radius_m = parse_double(require_value("--max-target-radius"), "--max-target-radius");
        } else if (flag == "--bucket-count") {
            args.bucket_count = parse_int(require_value("--bucket-count"), "--bucket-count");
        } else if (flag == "--bucket-capacity") {
            args.bucket_capacity = parse_int(require_value("--bucket-capacity"), "--bucket-capacity");
        } else if (flag == "--seed") {
            args.seed = parse_int(require_value("--seed"), "--seed");
        } else if (flag == "--help" || flag == "-h") {
            std::cout
                << "Usage: ef_gpu_sensor_candidate_phase0_probe [options]\n"
                << "  --worlds N             worlds in batch (default 16)\n"
                << "  --targets N            targets per world (default 1024)\n"
                << "  --sensors N            sensors per world (default 256)\n"
                << "  --cell-size X          grid cell size meters (default 5000)\n"
                << "  --max-target-radius X  conservative target radius meters (default 50)\n"
                << "  --bucket-count N       hash bucket count (default 32768)\n"
                << "  --bucket-capacity N    entries per bucket before overflow fallback (default 64)\n"
                << "  --seed N               rng seed (default 7)\n";
            std::exit(0);
        } else {
            throw std::invalid_argument("unknown flag: " + flag);
        }
    }
    args.worlds = std::max(1, args.worlds);
    args.targets = std::max(1, args.targets);
    args.sensors = std::max(1, args.sensors);
    args.cell_size_m = std::max(1.0, args.cell_size_m);
    args.max_target_radius_m = std::max(0.0, args.max_target_radius_m);
    args.bucket_count = std::max(1, args.bucket_count);
    args.bucket_capacity = std::max(1, args.bucket_capacity);
    return args;
}

struct GeneratedBatch {
    std::vector<gpu::InteractionEntityPacked> entities;
    std::vector<gpu::InteractionQueryPacked> queries;
    std::vector<Sensor> sensors;
};

GeneratedBatch make_batch(const Args& args) {
    GeneratedBatch batch{};
    batch.entities.reserve(static_cast<std::size_t>(args.worlds) * static_cast<std::size_t>(args.targets));
    batch.queries.reserve(static_cast<std::size_t>(args.worlds) * static_cast<std::size_t>(args.sensors));
    batch.sensors.reserve(static_cast<std::size_t>(args.worlds) * static_cast<std::size_t>(args.sensors));

    std::mt19937 rng(static_cast<std::uint32_t>(args.seed));
    std::uniform_real_distribution<double> pos_xy(-25000.0, 25000.0);
    std::uniform_real_distribution<double> pos_z(0.0, 12000.0);
    std::uniform_real_distribution<double> radius(10.0, args.max_target_radius_m > 0.0 ? args.max_target_radius_m : 1.0);
    std::uniform_real_distribution<double> max_range(5000.0, 45000.0);
    std::uniform_real_distribution<double> fov_deg(30.0, 180.0);

    for (int world_idx = 0; world_idx < args.worlds; ++world_idx) {
        const double world_x_offset = static_cast<double>(world_idx % 8) * 100000.0;
        const double world_y_offset = static_cast<double>(world_idx / 8) * 100000.0;
        for (int target_idx = 0; target_idx < args.targets; ++target_idx) {
            gpu::InteractionEntityPacked entity{};
            entity.world_index = world_idx;
            entity.local_index = target_idx;
            entity.x = world_x_offset + pos_xy(rng);
            entity.y = world_y_offset + pos_xy(rng);
            entity.z = pos_z(rng);
            entity.bounding_radius_m = radius(rng);
            batch.entities.push_back(entity);
        }
        for (int sensor_idx = 0; sensor_idx < args.sensors; ++sensor_idx) {
            Sensor sensor{};
            sensor.type = static_cast<int>(SensorType::Radar);
            sensor.max_range = max_range(rng);
            sensor.fov_deg = fov_deg(rng);
            batch.sensors.push_back(sensor);

            gpu::InteractionQueryPacked query{};
            query.world_index = world_idx;
            query.x = world_x_offset + pos_xy(rng);
            query.y = world_y_offset + pos_xy(rng);
            query.z = pos_z(rng);
            query.range_m = sensor.max_range;
            batch.queries.push_back(query);
        }
    }
    return batch;
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
        config.max_entity_radius_m = args.max_target_radius_m;
        config.entities_per_world = args.targets;
        config.hash_bucket_count = args.bucket_count;
        config.bucket_capacity = args.bucket_capacity;

        std::cout << "GPU Sensor Candidate Phase-0 Probe\n";
        std::cout << "==================================\n";
        std::cout << "CUDA built: " << (device.cuda_runtime_built ? "yes" : "no") << '\n';
        std::cout << "CUDA runtime available: " << (device.cuda_runtime_available ? "yes" : "no") << '\n';
        std::cout << "Worlds: " << args.worlds
                  << ", targets/world: " << args.targets
                  << ", sensors/world: " << args.sensors << "\n\n";

        const auto cpu_start = std::chrono::steady_clock::now();
        const auto cpu_reference = gpu::build_interaction_broadphase_reference_cpu_batch(
            batch.entities,
            batch.queries,
            config
        );
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
        std::cout << "CPU reference: " << cpu_ms << " ms\n";
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
