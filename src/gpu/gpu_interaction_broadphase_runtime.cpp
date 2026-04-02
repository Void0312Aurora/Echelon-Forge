#include "gpu/gpu_interaction_broadphase_runtime.h"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace gpu::detail {

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
std::vector<std::uint32_t> build_interaction_broadphase_experiment_batch_cuda(
    const std::vector<InteractionEntityPacked>& entities,
    const std::vector<InteractionQueryPacked>& queries,
    const InteractionBroadphaseConfig& config
);
bool build_interaction_broadphase_experiment_batch_cuda_device_resident(
    const std::vector<InteractionEntityPacked>& entities,
    const std::vector<InteractionQueryPacked>& queries,
    const InteractionBroadphaseConfig& config
);
InteractionBroadphaseExperimentStats last_interaction_broadphase_cuda_stats();
const void* last_interaction_broadphase_output_device_ptr_cuda();
std::size_t last_interaction_broadphase_output_word_count_cuda();
#endif

}  // namespace gpu::detail

namespace gpu {

namespace {

std::uint32_t bit_mask_for_local_index(int local_index) {
    return static_cast<std::uint32_t>(1u << (local_index & 31));
}

void validate_config(const InteractionBroadphaseConfig& config) {
    if (config.cell_size_m <= 0.0) {
        throw std::invalid_argument("interaction broadphase requires cell_size_m > 0");
    }
    if (config.max_entity_radius_m < 0.0) {
        throw std::invalid_argument("interaction broadphase requires max_entity_radius_m >= 0");
    }
    if (config.entities_per_world <= 0) {
        throw std::invalid_argument("interaction broadphase requires entities_per_world > 0");
    }
    if (config.hash_bucket_count <= 0) {
        throw std::invalid_argument("interaction broadphase requires hash_bucket_count > 0");
    }
    if (config.bucket_capacity <= 0) {
        throw std::invalid_argument("interaction broadphase requires bucket_capacity > 0");
    }
}

}  // namespace

std::size_t interaction_broadphase_word_count(int entities_per_world) {
    return static_cast<std::size_t>(std::max(0, entities_per_world) + 31) / 32u;
}

InteractionBroadphaseExperimentStats last_interaction_broadphase_stats() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::last_interaction_broadphase_cuda_stats();
#else
    return InteractionBroadphaseExperimentStats{};
#endif
}

const void* last_interaction_broadphase_output_device_ptr() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::last_interaction_broadphase_output_device_ptr_cuda();
#else
    return nullptr;
#endif
}

std::size_t last_interaction_broadphase_output_word_count() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::last_interaction_broadphase_output_word_count_cuda();
#else
    return 0;
#endif
}

std::vector<std::uint32_t> build_interaction_broadphase_reference_cpu_batch(
    const std::vector<InteractionEntityPacked>& entities,
    const std::vector<InteractionQueryPacked>& queries,
    const InteractionBroadphaseConfig& config
) {
    validate_config(config);
    const std::size_t words_per_query = interaction_broadphase_word_count(config.entities_per_world);
    std::vector<std::uint32_t> out(queries.size() * words_per_query, 0u);
    if (queries.empty() || entities.empty()) {
        return out;
    }

    for (std::size_t q_idx = 0; q_idx < queries.size(); ++q_idx) {
        const auto& query = queries[q_idx];
        auto* dst = out.data() + q_idx * words_per_query;
        for (const auto& entity : entities) {
            if (entity.world_index != query.world_index) {
                continue;
            }
            if (entity.local_index < 0 || entity.local_index >= config.entities_per_world) {
                throw std::invalid_argument("entity local_index out of range for entities_per_world");
            }
            const double dx = entity.x - query.x;
            const double dy = entity.y - query.y;
            const double dz = entity.z - query.z;
            const double limit = std::max(0.0, query.range_m) + std::max(0.0, entity.bounding_radius_m);
            if ((dx * dx + dy * dy + dz * dz) <= (limit * limit)) {
                const std::size_t word_index = static_cast<std::size_t>(entity.local_index) / 32u;
                dst[word_index] |= bit_mask_for_local_index(entity.local_index);
            }
        }
    }
    return out;
}

std::vector<std::uint32_t> build_interaction_broadphase_experiment_batch(
    const std::vector<InteractionEntityPacked>& entities,
    const std::vector<InteractionQueryPacked>& queries,
    const InteractionBroadphaseConfig& config
) {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    auto out = detail::build_interaction_broadphase_experiment_batch_cuda(entities, queries, config);
    if (!out.empty() || queries.empty()) {
        return out;
    }
#endif
    return build_interaction_broadphase_reference_cpu_batch(entities, queries, config);
}

bool build_interaction_broadphase_experiment_batch_device_resident(
    const std::vector<InteractionEntityPacked>& entities,
    const std::vector<InteractionQueryPacked>& queries,
    const InteractionBroadphaseConfig& config
) {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::build_interaction_broadphase_experiment_batch_cuda_device_resident(entities, queries, config);
#else
    (void)entities;
    (void)queries;
    (void)config;
    return false;
#endif
}

}  // namespace gpu
