#include "gpu/gpu_interaction_broadphase_runtime.h"

#include <cuda_runtime_api.h>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <vector>

namespace {

gpu::InteractionBroadphaseExperimentStats g_last_stats{};
const void* g_last_output_device_ptr = nullptr;
std::size_t g_last_output_word_count = 0;

struct DeviceInteractionBroadphaseCache {
    gpu::InteractionEntityPacked* d_entities = nullptr;
    gpu::InteractionQueryPacked* d_queries = nullptr;
    int* d_bucket_counts = nullptr;
    int* d_bucket_overflow = nullptr;
    int* d_bucket_items = nullptr;
    int* d_query_overflow = nullptr;
    std::uint32_t* d_output = nullptr;
    std::size_t entity_capacity = 0;
    std::size_t query_capacity = 0;
    std::size_t bucket_capacity = 0;
    std::size_t bucket_item_capacity = 0;
    std::size_t output_word_capacity = 0;
};

DeviceInteractionBroadphaseCache g_cache{};

__host__ __device__ inline int cell_coord(double value, double cell_size) {
    return static_cast<int>(floor(value / cell_size));
}

__host__ __device__ inline std::uint64_t mix_hash(std::uint64_t x) {
    x ^= x >> 33;
    x *= 0xff51afd7ed558ccdULL;
    x ^= x >> 33;
    x *= 0xc4ceb9fe1a85ec53ULL;
    x ^= x >> 33;
    return x;
}

__host__ __device__ inline int hash_bucket_index(
    int world_index,
    int cell_x,
    int cell_y,
    int cell_z,
    int bucket_count
) {
    std::uint64_t h = 0xcbf29ce484222325ULL;
    h ^= static_cast<std::uint64_t>(static_cast<std::uint32_t>(world_index)) + 0x9e3779b97f4a7c15ULL + (h << 6) + (h >> 2);
    h ^= static_cast<std::uint64_t>(static_cast<std::uint32_t>(cell_x)) + 0x9e3779b97f4a7c15ULL + (h << 6) + (h >> 2);
    h ^= static_cast<std::uint64_t>(static_cast<std::uint32_t>(cell_y)) + 0x9e3779b97f4a7c15ULL + (h << 6) + (h >> 2);
    h ^= static_cast<std::uint64_t>(static_cast<std::uint32_t>(cell_z)) + 0x9e3779b97f4a7c15ULL + (h << 6) + (h >> 2);
    return static_cast<int>(mix_hash(h) % static_cast<std::uint64_t>(bucket_count));
}

__global__ void insert_entities_kernel(
    const gpu::InteractionEntityPacked* entities,
    int entity_count,
    double cell_size_m,
    int bucket_count,
    int bucket_capacity,
    int* bucket_counts,
    int* bucket_overflow,
    int* bucket_items
) {
    const int entity_index = blockIdx.x * blockDim.x + threadIdx.x;
    if (entity_index >= entity_count) {
        return;
    }
    const auto& entity = entities[entity_index];
    const int cx = cell_coord(entity.x, cell_size_m);
    const int cy = cell_coord(entity.y, cell_size_m);
    const int cz = cell_coord(entity.z, cell_size_m);
    const int bucket = hash_bucket_index(entity.world_index, cx, cy, cz, bucket_count);
    const int slot = atomicAdd(bucket_counts + bucket, 1);
    if (slot < bucket_capacity) {
        bucket_items[bucket * bucket_capacity + slot] = entity_index;
    } else {
        bucket_overflow[bucket] = 1;
    }
}

__global__ void build_query_bitsets_kernel(
    const gpu::InteractionEntityPacked* entities,
    const gpu::InteractionQueryPacked* queries,
    int query_count,
    double cell_size_m,
    double max_entity_radius_m,
    int entities_per_world,
    int bucket_count,
    int bucket_capacity,
    const int* bucket_counts,
    const int* bucket_overflow,
    const int* bucket_items,
    int words_per_query,
    std::uint32_t* output,
    int* query_overflow
) {
    const int query_index = blockIdx.x * blockDim.x + threadIdx.x;
    if (query_index >= query_count) {
        return;
    }

    const auto& query = queries[query_index];
    std::uint32_t* dst = output + static_cast<std::size_t>(query_index) * static_cast<std::size_t>(words_per_query);
    bool overflowed = false;

    const double query_range = fmax(0.0, query.range_m);
    const double neighborhood_range = query_range + fmax(0.0, max_entity_radius_m);
    const int min_cx = cell_coord(query.x - neighborhood_range, cell_size_m);
    const int max_cx = cell_coord(query.x + neighborhood_range, cell_size_m);
    const int min_cy = cell_coord(query.y - neighborhood_range, cell_size_m);
    const int max_cy = cell_coord(query.y + neighborhood_range, cell_size_m);
    const int min_cz = cell_coord(query.z - neighborhood_range, cell_size_m);
    const int max_cz = cell_coord(query.z + neighborhood_range, cell_size_m);

    for (int cz = min_cz; cz <= max_cz; ++cz) {
        for (int cy = min_cy; cy <= max_cy; ++cy) {
            for (int cx = min_cx; cx <= max_cx; ++cx) {
                const int bucket = hash_bucket_index(query.world_index, cx, cy, cz, bucket_count);
                if (bucket_overflow[bucket] != 0) {
                    overflowed = true;
                }
                const int count = min(bucket_counts[bucket], bucket_capacity);
                for (int slot = 0; slot < count; ++slot) {
                    const int entity_index = bucket_items[bucket * bucket_capacity + slot];
                    const auto& entity = entities[entity_index];
                    if (entity.world_index != query.world_index) {
                        continue;
                    }
                    if (entity.local_index < 0 || entity.local_index >= entities_per_world) {
                        continue;
                    }
                    const double dx = entity.x - query.x;
                    const double dy = entity.y - query.y;
                    const double dz = entity.z - query.z;
                    const double limit = query_range + fmax(0.0, entity.bounding_radius_m);
                    if ((dx * dx + dy * dy + dz * dz) <= (limit * limit)) {
                        const int word_index = entity.local_index >> 5;
                        const std::uint32_t bit = static_cast<std::uint32_t>(1u << (entity.local_index & 31));
                        dst[word_index] |= bit;
                    }
                }
            }
        }
    }

    if (overflowed) {
        for (int local_index = 0; local_index < entities_per_world; ++local_index) {
            const int word_index = local_index >> 5;
            const std::uint32_t bit = static_cast<std::uint32_t>(1u << (local_index & 31));
            dst[word_index] |= bit;
        }
        query_overflow[query_index] = 1;
    } else {
        query_overflow[query_index] = 0;
    }
}

bool ensure_cache_capacity(
    std::size_t entity_count,
    std::size_t query_count,
    std::size_t bucket_count,
    std::size_t bucket_item_count,
    std::size_t output_word_count
) {
    if (entity_count > g_cache.entity_capacity) {
        if (g_cache.d_entities != nullptr) {
            cudaFree(g_cache.d_entities);
            g_cache.d_entities = nullptr;
        }
        if (cudaMalloc(&g_cache.d_entities, entity_count * sizeof(gpu::InteractionEntityPacked)) != cudaSuccess) {
            return false;
        }
        g_cache.entity_capacity = entity_count;
    }
    if (query_count > g_cache.query_capacity) {
        if (g_cache.d_queries != nullptr) {
            cudaFree(g_cache.d_queries);
            g_cache.d_queries = nullptr;
        }
        if (g_cache.d_query_overflow != nullptr) {
            cudaFree(g_cache.d_query_overflow);
            g_cache.d_query_overflow = nullptr;
        }
        if (cudaMalloc(&g_cache.d_queries, query_count * sizeof(gpu::InteractionQueryPacked)) != cudaSuccess) {
            return false;
        }
        if (cudaMalloc(&g_cache.d_query_overflow, query_count * sizeof(int)) != cudaSuccess) {
            return false;
        }
        g_cache.query_capacity = query_count;
    }
    if (bucket_count > g_cache.bucket_capacity) {
        if (g_cache.d_bucket_counts != nullptr) {
            cudaFree(g_cache.d_bucket_counts);
            g_cache.d_bucket_counts = nullptr;
        }
        if (g_cache.d_bucket_overflow != nullptr) {
            cudaFree(g_cache.d_bucket_overflow);
            g_cache.d_bucket_overflow = nullptr;
        }
        if (cudaMalloc(&g_cache.d_bucket_counts, bucket_count * sizeof(int)) != cudaSuccess) {
            return false;
        }
        if (cudaMalloc(&g_cache.d_bucket_overflow, bucket_count * sizeof(int)) != cudaSuccess) {
            return false;
        }
        g_cache.bucket_capacity = bucket_count;
    }
    if (bucket_item_count > g_cache.bucket_item_capacity) {
        if (g_cache.d_bucket_items != nullptr) {
            cudaFree(g_cache.d_bucket_items);
            g_cache.d_bucket_items = nullptr;
        }
        if (cudaMalloc(&g_cache.d_bucket_items, bucket_item_count * sizeof(int)) != cudaSuccess) {
            return false;
        }
        g_cache.bucket_item_capacity = bucket_item_count;
    }
    if (output_word_count > g_cache.output_word_capacity) {
        if (g_cache.d_output != nullptr) {
            cudaFree(g_cache.d_output);
            g_cache.d_output = nullptr;
        }
        if (cudaMalloc(&g_cache.d_output, output_word_count * sizeof(std::uint32_t)) != cudaSuccess) {
            return false;
        }
        g_cache.output_word_capacity = output_word_count;
    }
    return true;
}

bool run_interaction_broadphase_cuda_impl(
    const std::vector<gpu::InteractionEntityPacked>& entities,
    const std::vector<gpu::InteractionQueryPacked>& queries,
    const gpu::InteractionBroadphaseConfig& config,
    bool copy_output_to_host,
    std::vector<std::uint32_t>* host_output
) {
    g_last_stats = gpu::InteractionBroadphaseExperimentStats{};
    g_last_output_device_ptr = nullptr;
    g_last_output_word_count = 0;
    if (host_output != nullptr) {
        host_output->clear();
    }
    if (queries.empty()) {
        return true;
    }
    if (entities.empty()) {
        if (host_output != nullptr) {
            host_output->assign(
                queries.size() * gpu::interaction_broadphase_word_count(config.entities_per_world),
                0u
            );
        }
        return true;
    }

    int device_count = 0;
    if (cudaGetDeviceCount(&device_count) != cudaSuccess || device_count <= 0) {
        return false;
    }
    g_last_stats.used_cuda = true;

    const std::size_t entity_count = entities.size();
    const std::size_t query_count = queries.size();
    const std::size_t bucket_count = static_cast<std::size_t>(config.hash_bucket_count);
    const std::size_t bucket_item_count =
        bucket_count * static_cast<std::size_t>(config.bucket_capacity);
    const std::size_t words_per_query = gpu::interaction_broadphase_word_count(config.entities_per_world);
    const std::size_t output_word_count = query_count * words_per_query;

    cudaEvent_t ev_h2d_start = nullptr;
    cudaEvent_t ev_h2d_end = nullptr;
    cudaEvent_t ev_kernel_end = nullptr;
    cudaEvent_t ev_d2h_end = nullptr;
    cudaEventCreate(&ev_h2d_start);
    cudaEventCreate(&ev_h2d_end);
    cudaEventCreate(&ev_kernel_end);
    cudaEventCreate(&ev_d2h_end);
    cudaEventRecord(ev_h2d_start);

    if (!ensure_cache_capacity(entity_count, query_count, bucket_count, bucket_item_count, output_word_count)) {
        cudaEventDestroy(ev_h2d_start);
        cudaEventDestroy(ev_h2d_end);
        cudaEventDestroy(ev_kernel_end);
        cudaEventDestroy(ev_d2h_end);
        return false;
    }

    cudaError_t status = cudaSuccess;
    status = cudaMemcpy(
        g_cache.d_entities,
        entities.data(),
        entity_count * sizeof(gpu::InteractionEntityPacked),
        cudaMemcpyHostToDevice
    );
    if (status == cudaSuccess) {
        status = cudaMemcpy(
            g_cache.d_queries,
            queries.data(),
            query_count * sizeof(gpu::InteractionQueryPacked),
            cudaMemcpyHostToDevice
        );
    }
    if (status == cudaSuccess) {
        status = cudaMemset(g_cache.d_bucket_counts, 0, bucket_count * sizeof(int));
    }
    if (status == cudaSuccess) {
        status = cudaMemset(g_cache.d_bucket_overflow, 0, bucket_count * sizeof(int));
    }
    if (status == cudaSuccess) {
        status = cudaMemset(g_cache.d_query_overflow, 0, query_count * sizeof(int));
    }
    if (status == cudaSuccess) {
        status = cudaMemset(g_cache.d_output, 0, output_word_count * sizeof(std::uint32_t));
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
    const int entity_blocks = static_cast<int>((entity_count + threads - 1) / threads);
    insert_entities_kernel<<<entity_blocks, threads>>>(
        g_cache.d_entities,
        static_cast<int>(entity_count),
        config.cell_size_m,
        config.hash_bucket_count,
        config.bucket_capacity,
        g_cache.d_bucket_counts,
        g_cache.d_bucket_overflow,
        g_cache.d_bucket_items
    );
    status = cudaGetLastError();
    if (status == cudaSuccess) {
        const int query_blocks = static_cast<int>((query_count + threads - 1) / threads);
        build_query_bitsets_kernel<<<query_blocks, threads>>>(
            g_cache.d_entities,
            g_cache.d_queries,
            static_cast<int>(query_count),
            config.cell_size_m,
            config.max_entity_radius_m,
            config.entities_per_world,
            config.hash_bucket_count,
            config.bucket_capacity,
            g_cache.d_bucket_counts,
            g_cache.d_bucket_overflow,
            g_cache.d_bucket_items,
            static_cast<int>(words_per_query),
            g_cache.d_output,
            g_cache.d_query_overflow
        );
        status = cudaGetLastError();
    }
    cudaEventRecord(ev_kernel_end);

    if (status == cudaSuccess) {
        status = cudaDeviceSynchronize();
    }

    std::vector<int> host_bucket_overflow;
    std::vector<int> host_query_overflow;
    double d2h_wall_ms = 0.0;
    if (status == cudaSuccess) {
        host_bucket_overflow.assign(bucket_count, 0);
        host_query_overflow.assign(query_count, 0);
        const auto d2h_start = std::chrono::steady_clock::now();
        status = cudaMemcpy(
            host_bucket_overflow.data(),
            g_cache.d_bucket_overflow,
            bucket_count * sizeof(int),
            cudaMemcpyDeviceToHost
        );
        if (status == cudaSuccess) {
            status = cudaMemcpy(
                host_query_overflow.data(),
                g_cache.d_query_overflow,
                query_count * sizeof(int),
                cudaMemcpyDeviceToHost
            );
        }
        if (status == cudaSuccess && copy_output_to_host && host_output != nullptr) {
            host_output->assign(output_word_count, 0u);
            status = cudaMemcpy(
                host_output->data(),
                g_cache.d_output,
                output_word_count * sizeof(std::uint32_t),
                cudaMemcpyDeviceToHost
            );
        }
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
        g_last_output_word_count = 0;
        return false;
    }

    float h2d_ms = 0.0f;
    float kernel_ms = 0.0f;
    cudaEventElapsedTime(&h2d_ms, ev_h2d_start, ev_h2d_end);
    cudaEventElapsedTime(&kernel_ms, ev_h2d_end, ev_kernel_end);
    g_last_stats.host_to_device_ms = static_cast<double>(h2d_ms);
    g_last_stats.kernel_ms = static_cast<double>(kernel_ms);
    g_last_stats.device_to_host_ms = d2h_wall_ms;
    g_last_stats.total_ms =
        g_last_stats.host_to_device_ms +
        g_last_stats.kernel_ms +
        g_last_stats.device_to_host_ms;
    g_last_stats.overflow_bucket_count = static_cast<int>(
        std::count(host_bucket_overflow.begin(), host_bucket_overflow.end(), 1)
    );
    g_last_stats.overflow_query_count = static_cast<int>(
        std::count(host_query_overflow.begin(), host_query_overflow.end(), 1)
    );
    g_last_output_device_ptr = g_cache.d_output;
    g_last_output_word_count = output_word_count;

    cudaEventDestroy(ev_h2d_start);
    cudaEventDestroy(ev_h2d_end);
    cudaEventDestroy(ev_kernel_end);
    cudaEventDestroy(ev_d2h_end);
    return true;
}

}  // namespace

namespace gpu::detail {

InteractionBroadphaseExperimentStats last_interaction_broadphase_cuda_stats() {
    return g_last_stats;
}

const void* last_interaction_broadphase_output_device_ptr_cuda() {
    return g_last_output_device_ptr;
}

std::size_t last_interaction_broadphase_output_word_count_cuda() {
    return g_last_output_word_count;
}

std::vector<std::uint32_t> build_interaction_broadphase_experiment_batch_cuda(
    const std::vector<gpu::InteractionEntityPacked>& entities,
    const std::vector<gpu::InteractionQueryPacked>& queries,
    const gpu::InteractionBroadphaseConfig& config
) {
    std::vector<std::uint32_t> out;
    if (!run_interaction_broadphase_cuda_impl(entities, queries, config, true, &out)) {
        return {};
    }
    return out;
}

bool build_interaction_broadphase_experiment_batch_cuda_device_resident(
    const std::vector<gpu::InteractionEntityPacked>& entities,
    const std::vector<gpu::InteractionQueryPacked>& queries,
    const gpu::InteractionBroadphaseConfig& config
) {
    return run_interaction_broadphase_cuda_impl(entities, queries, config, false, nullptr);
}

}  // namespace gpu::detail
