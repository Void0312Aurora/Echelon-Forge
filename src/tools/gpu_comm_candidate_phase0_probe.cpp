#include "components/systems/data_link.h"
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
    int nodes = 1024;
    int networks = 2;
    double cell_size_m = 10000.0;
    double max_range_km = 250.0;
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
        } else if (flag == "--nodes") {
            args.nodes = parse_int(require_value("--nodes"), "--nodes");
        } else if (flag == "--networks") {
            args.networks = parse_int(require_value("--networks"), "--networks");
        } else if (flag == "--cell-size") {
            args.cell_size_m = parse_double(require_value("--cell-size"), "--cell-size");
        } else if (flag == "--max-range-km") {
            args.max_range_km = parse_double(require_value("--max-range-km"), "--max-range-km");
        } else if (flag == "--bucket-count") {
            args.bucket_count = parse_int(require_value("--bucket-count"), "--bucket-count");
        } else if (flag == "--bucket-capacity") {
            args.bucket_capacity = parse_int(require_value("--bucket-capacity"), "--bucket-capacity");
        } else if (flag == "--seed") {
            args.seed = parse_int(require_value("--seed"), "--seed");
        } else if (flag == "--help" || flag == "-h") {
            std::cout
                << "Usage: ef_gpu_comm_candidate_phase0_probe [options]\n"
                << "  --worlds N             worlds in batch (default 16)\n"
                << "  --nodes N              datalink nodes per world (default 1024)\n"
                << "  --networks N           network partitions per world (default 2)\n"
                << "  --cell-size X          grid cell size meters (default 10000)\n"
                << "  --max-range-km X       max link range km (default 250)\n"
                << "  --bucket-count N       hash bucket count (default 32768)\n"
                << "  --bucket-capacity N    entries per bucket before overflow fallback (default 64)\n"
                << "  --seed N               rng seed (default 7)\n";
            std::exit(0);
        } else {
            throw std::invalid_argument("unknown flag: " + flag);
        }
    }
    args.worlds = std::max(1, args.worlds);
    args.nodes = std::max(1, args.nodes);
    args.networks = std::max(1, args.networks);
    args.cell_size_m = std::max(1.0, args.cell_size_m);
    args.max_range_km = std::max(0.1, args.max_range_km);
    args.bucket_count = std::max(1, args.bucket_count);
    args.bucket_capacity = std::max(1, args.bucket_capacity);
    return args;
}

struct NodePacked {
    int world_index = 0;
    int local_index = 0;
    int network_id = 0;
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    DataLink link{};
};

struct GeneratedBatch {
    std::vector<NodePacked> nodes;
    std::vector<gpu::InteractionEntityPacked> entities;
    std::vector<gpu::InteractionQueryPacked> queries;
};

GeneratedBatch make_batch(const Args& args) {
    GeneratedBatch batch{};
    batch.nodes.reserve(static_cast<std::size_t>(args.worlds) * static_cast<std::size_t>(args.nodes));
    batch.entities.reserve(static_cast<std::size_t>(args.worlds) * static_cast<std::size_t>(args.nodes));
    batch.queries.reserve(static_cast<std::size_t>(args.worlds) * static_cast<std::size_t>(args.nodes));

    std::mt19937 rng(static_cast<std::uint32_t>(args.seed));
    std::uniform_real_distribution<double> pos_xy(-180000.0, 180000.0);
    std::uniform_real_distribution<double> pos_z(0.0, 12000.0);
    std::uniform_real_distribution<double> range_km(20.0, args.max_range_km);

    for (int world_idx = 0; world_idx < args.worlds; ++world_idx) {
        const double world_x_offset = static_cast<double>(world_idx % 8) * 500000.0;
        const double world_y_offset = static_cast<double>(world_idx / 8) * 500000.0;
        for (int local_idx = 0; local_idx < args.nodes; ++local_idx) {
            NodePacked node{};
            node.world_index = world_idx;
            node.local_index = local_idx;
            node.network_id = local_idx % args.networks;
            node.x = world_x_offset + pos_xy(rng);
            node.y = world_y_offset + pos_xy(rng);
            node.z = pos_z(rng);
            node.link.active = true;
            node.link.network_id = node.network_id;
            node.link.type = LinkType::Link16;
            node.link.max_range_km = range_km(rng);
            batch.nodes.push_back(node);

            gpu::InteractionEntityPacked entity{};
            entity.world_index = world_idx * args.networks + node.network_id;
            entity.local_index = local_idx;
            entity.x = node.x;
            entity.y = node.y;
            entity.z = node.z;
            entity.bounding_radius_m = 0.0;
            batch.entities.push_back(entity);

            gpu::InteractionQueryPacked query{};
            query.world_index = world_idx * args.networks + node.network_id;
            query.x = node.x;
            query.y = node.y;
            query.z = node.z;
            query.range_m = node.link.max_range_km * 1000.0;
            batch.queries.push_back(query);
        }
    }
    return batch;
}

std::vector<std::uint32_t> compute_comm_exact_reference(const GeneratedBatch& batch, const Args& args) {
    const std::size_t words_per_query = gpu::interaction_broadphase_word_count(args.nodes);
    std::vector<std::uint32_t> out(batch.nodes.size() * words_per_query, 0u);
    for (std::size_t sender_idx = 0; sender_idx < batch.nodes.size(); ++sender_idx) {
        const auto& sender = batch.nodes[sender_idx];
        auto* dst = out.data() + sender_idx * words_per_query;
        for (const auto& receiver : batch.nodes) {
            if (receiver.world_index != sender.world_index) {
                continue;
            }
            if (receiver.local_index == sender.local_index) {
                continue;
            }
            if (receiver.network_id != sender.network_id) {
                continue;
            }
            const double dx = sender.x - receiver.x;
            const double dy = sender.y - receiver.y;
            const double dz = sender.z - receiver.z;
            const double dist_m = std::sqrt(dx * dx + dy * dy + dz * dz);
            const double dist_km = dist_m / 1000.0;
            if (dist_km > sender.link.max_range_km) {
                continue;
            }
            const double h1 = std::max(0.0, sender.z);
            const double h2 = std::max(0.0, receiver.z);
            const double horizon_km = 3.57 * (std::sqrt(h1) + std::sqrt(h2));
            if (dist_km > horizon_km) {
                continue;
            }
            const std::size_t word_index = static_cast<std::size_t>(receiver.local_index) / 32u;
            dst[word_index] |= static_cast<std::uint32_t>(1u << (receiver.local_index & 31));
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
        config.max_entity_radius_m = 0.0;
        config.entities_per_world = args.nodes;
        config.hash_bucket_count = args.bucket_count;
        config.bucket_capacity = args.bucket_capacity;

        std::cout << "GPU Communication Candidate Phase-0 Probe\n";
        std::cout << "=========================================\n";
        std::cout << "CUDA built: " << (device.cuda_runtime_built ? "yes" : "no") << '\n';
        std::cout << "CUDA runtime available: " << (device.cuda_runtime_available ? "yes" : "no") << '\n';
        std::cout << "Worlds: " << args.worlds
                  << ", nodes/world: " << args.nodes
                  << ", networks/world: " << args.networks << "\n\n";

        const auto cpu_start = std::chrono::steady_clock::now();
        const auto cpu_reference = compute_comm_exact_reference(batch, args);
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
        std::cout << "CPU exact comm reference: " << cpu_ms << " ms\n";
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
