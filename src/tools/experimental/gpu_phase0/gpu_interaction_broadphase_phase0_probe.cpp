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
#include <numeric>
#include <random>
#include <string>
#include <vector>

namespace {

struct Args {
    int worlds = 16;
    int entities = 1024;
    int queries = 256;
    double cell_size_m = 5000.0;
    double max_entity_radius_m = 250.0;
    int bucket_count = 1 << 15;
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
        } else if (flag == "--entities") {
            args.entities = parse_int(require_value("--entities"), "--entities");
        } else if (flag == "--queries") {
            args.queries = parse_int(require_value("--queries"), "--queries");
        } else if (flag == "--cell-size") {
            args.cell_size_m = parse_double(require_value("--cell-size"), "--cell-size");
        } else if (flag == "--max-entity-radius") {
            args.max_entity_radius_m = parse_double(require_value("--max-entity-radius"), "--max-entity-radius");
        } else if (flag == "--bucket-count") {
            args.bucket_count = parse_int(require_value("--bucket-count"), "--bucket-count");
        } else if (flag == "--bucket-capacity") {
            args.bucket_capacity = parse_int(require_value("--bucket-capacity"), "--bucket-capacity");
        } else if (flag == "--seed") {
            args.seed = parse_int(require_value("--seed"), "--seed");
        } else if (flag == "--help" || flag == "-h") {
            std::cout
                << "Usage: ef_gpu_interaction_broadphase_phase0_probe [options]\n"
                << "  --worlds N             worlds in batch (default 16)\n"
                << "  --entities N           entities per world (default 1024)\n"
                << "  --queries N            queries per world (default 256)\n"
                << "  --cell-size X          grid cell size meters (default 5000)\n"
                << "  --max-entity-radius X  conservative max entity radius meters (default 250)\n"
                << "  --bucket-count N       hash bucket count (default 32768)\n"
                << "  --bucket-capacity N    entries per bucket before overflow fallback (default 64)\n"
                << "  --seed N               rng seed (default 7)\n";
            std::exit(0);
        } else {
            throw std::invalid_argument("unknown flag: " + flag);
        }
    }
    args.worlds = std::max(1, args.worlds);
    args.entities = std::max(1, args.entities);
    args.queries = std::max(1, args.queries);
    args.cell_size_m = std::max(1.0, args.cell_size_m);
    args.max_entity_radius_m = std::max(0.0, args.max_entity_radius_m);
    args.bucket_count = std::max(1, args.bucket_count);
    args.bucket_capacity = std::max(1, args.bucket_capacity);
    return args;
}

struct GeneratedBatch {
    std::vector<gpu::InteractionEntityPacked> entities;
    std::vector<gpu::InteractionQueryPacked> queries;
};

GeneratedBatch make_batch(const Args& args) {
    GeneratedBatch batch{};
    batch.entities.reserve(static_cast<std::size_t>(args.worlds) * static_cast<std::size_t>(args.entities));
    batch.queries.reserve(static_cast<std::size_t>(args.worlds) * static_cast<std::size_t>(args.queries));

    std::mt19937 rng(static_cast<std::uint32_t>(args.seed));
    std::uniform_real_distribution<double> pos_xy(-25000.0, 25000.0);
    std::uniform_real_distribution<double> pos_z(0.0, 12000.0);
    std::uniform_real_distribution<double> radius(25.0, args.max_entity_radius_m > 0.0 ? args.max_entity_radius_m : 1.0);
    std::uniform_real_distribution<double> range(4000.0, 22000.0);

    for (int world_idx = 0; world_idx < args.worlds; ++world_idx) {
        const double world_x_offset = static_cast<double>(world_idx % 8) * 100000.0;
        const double world_y_offset = static_cast<double>(world_idx / 8) * 100000.0;
        for (int entity_idx = 0; entity_idx < args.entities; ++entity_idx) {
            gpu::InteractionEntityPacked entity{};
            entity.world_index = world_idx;
            entity.local_index = entity_idx;
            entity.x = world_x_offset + pos_xy(rng);
            entity.y = world_y_offset + pos_xy(rng);
            entity.z = pos_z(rng);
            entity.bounding_radius_m = radius(rng);
            batch.entities.push_back(entity);
        }
        for (int query_idx = 0; query_idx < args.queries; ++query_idx) {
            gpu::InteractionQueryPacked query{};
            query.world_index = world_idx;
            query.x = world_x_offset + pos_xy(rng);
            query.y = world_y_offset + pos_xy(rng);
            query.z = pos_z(rng);
            query.range_m = range(rng);
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
    std::size_t queries_with_miss = 0;
};

CompareSummary compare_superset(
    const std::vector<std::uint32_t>& reference_bits,
    const std::vector<std::uint32_t>& gpu_bits,
    std::size_t words_per_query
) {
    CompareSummary summary{};
    if (reference_bits.size() != gpu_bits.size()) {
        throw std::runtime_error("bitset size mismatch");
    }
    summary.reference_pairs = popcount_words(reference_bits);
    summary.gpu_pairs = popcount_words(gpu_bits);
    const std::size_t query_count = words_per_query == 0 ? 0 : (reference_bits.size() / words_per_query);
    for (std::size_t query_idx = 0; query_idx < query_count; ++query_idx) {
        bool query_missing = false;
        for (std::size_t word_idx = 0; word_idx < words_per_query; ++word_idx) {
            const std::size_t idx = query_idx * words_per_query + word_idx;
            const std::uint32_t missed = reference_bits[idx] & ~gpu_bits[idx];
            if (missed != 0u) {
                summary.missing_pairs += static_cast<std::size_t>(__builtin_popcount(missed));
                query_missing = true;
            }
        }
        if (query_missing) {
            summary.queries_with_miss += 1;
        }
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
        config.max_entity_radius_m = args.max_entity_radius_m;
        config.entities_per_world = args.entities;
        config.hash_bucket_count = args.bucket_count;
        config.bucket_capacity = args.bucket_capacity;

        std::cout << "GPU Interaction Broadphase Phase-0 Probe\n";
        std::cout << "========================================\n";
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
        std::cout << "Worlds: " << args.worlds << '\n';
        std::cout << "Entities/world: " << args.entities << '\n';
        std::cout << "Queries/world: " << args.queries << '\n';
        std::cout << "Total entities: " << batch.entities.size() << '\n';
        std::cout << "Total queries: " << batch.queries.size() << '\n';
        std::cout << "Cell size (m): " << args.cell_size_m << '\n';
        std::cout << "Hash buckets: " << args.bucket_count << '\n';
        std::cout << "Bucket capacity: " << args.bucket_capacity << '\n';
        std::cout << "Bitset bytes/query: "
                  << gpu::format_bytes(gpu::interaction_broadphase_word_count(args.entities) * sizeof(std::uint32_t))
                  << "\n\n";

        const auto cpu_start = std::chrono::steady_clock::now();
        const auto cpu_reference = gpu::build_interaction_broadphase_reference_cpu_batch(
            batch.entities,
            batch.queries,
            config
        );
        const auto cpu_end = std::chrono::steady_clock::now();
        const double cpu_ms =
            std::chrono::duration<double, std::milli>(cpu_end - cpu_start).count();

        // Warm the CUDA path once to avoid reporting one-time launch/setup cost as
        // steady-state broadphase throughput.
        (void)gpu::build_interaction_broadphase_experiment_batch(
            batch.entities,
            batch.queries,
            config
        );
        (void)gpu::build_interaction_broadphase_experiment_batch_device_resident(
            batch.entities,
            batch.queries,
            config
        );

        const auto gpu_host = gpu::build_interaction_broadphase_experiment_batch(
            batch.entities,
            batch.queries,
            config
        );
        const auto gpu_host_stats = gpu::last_interaction_broadphase_stats();
        const auto summary = compare_superset(
            cpu_reference,
            gpu_host,
            gpu::interaction_broadphase_word_count(args.entities)
        );

        const bool device_resident_ok = gpu::build_interaction_broadphase_experiment_batch_device_resident(
            batch.entities,
            batch.queries,
            config
        );
        const auto gpu_device_stats = gpu::last_interaction_broadphase_stats();

        std::cout << "Results\n";
        std::cout << "-------\n";
        std::cout << std::fixed << std::setprecision(4);
        std::cout << "CPU exact reference: " << cpu_ms << " ms\n";
        std::cout << "GPU host-readback: " << gpu_host_stats.total_ms << " ms";
        if (gpu_host_stats.total_ms > 0.0) {
            std::cout << "  (" << (cpu_ms / gpu_host_stats.total_ms) << "x vs CPU)";
        }
        std::cout << '\n';
        std::cout << "  H2D: " << gpu_host_stats.host_to_device_ms
                  << " ms, kernel: " << gpu_host_stats.kernel_ms
                  << " ms, D2H: " << gpu_host_stats.device_to_host_ms << " ms\n";
        if (device_resident_ok) {
            std::cout << "GPU device-resident: " << gpu_device_stats.total_ms << " ms";
            if (gpu_device_stats.total_ms > 0.0) {
                std::cout << "  (" << (cpu_ms / gpu_device_stats.total_ms) << "x vs CPU)";
            }
            std::cout << '\n';
            std::cout << "  H2D: " << gpu_device_stats.host_to_device_ms
                      << " ms, kernel: " << gpu_device_stats.kernel_ms
                      << " ms, D2H: " << gpu_device_stats.device_to_host_ms << " ms\n";
        } else {
            std::cout << "GPU device-resident: unavailable\n";
        }
        std::cout << '\n';

        std::cout << "Superset semantics\n";
        std::cout << "------------------\n";
        std::cout << "Reference candidate pairs: " << summary.reference_pairs << '\n';
        std::cout << "GPU candidate pairs: " << summary.gpu_pairs << '\n';
        std::cout << "Missing reference pairs: " << summary.missing_pairs << '\n';
        std::cout << "Queries with any miss: " << summary.queries_with_miss << '\n';
        if (summary.reference_pairs > 0) {
            std::cout << "Expansion factor: "
                      << (static_cast<double>(summary.gpu_pairs) / static_cast<double>(summary.reference_pairs))
                      << "x\n";
        }
        std::cout << "Overflow buckets: " << gpu_host_stats.overflow_bucket_count << '\n';
        std::cout << "Overflow queries: " << gpu_host_stats.overflow_query_count << '\n';
        std::cout << '\n';

        std::cout << "Verdict\n";
        std::cout << "-------\n";
        if (summary.missing_pairs == 0) {
            std::cout << "Exact superset property preserved in measured host-readback run.\n";
        } else {
            std::cout << "Superset property violated in measured host-readback run.\n";
            return 2;
        }
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "error: " << ex.what() << '\n';
        return 1;
    }
}
