#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

// Neutral interaction packets shared by the engine and an optional GPU
// adapter. These are semantic broadphase inputs; they are not device layouts.
struct WorldBatchInteractionEntity {
    int world_index = 0;
    int local_index = 0;
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    double bounding_radius_m = 0.0;
};

struct WorldBatchInteractionQuery {
    int world_index = 0;
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    double range_m = 0.0;
};

struct WorldBatchInteractionConfig {
    double cell_size_m = 5000.0;
    double max_entity_radius_m = 250.0;
    int entities_per_world = 1024;
    int hash_bucket_count = 1 << 15;
    int bucket_capacity = 64;
};

using WorldBatchInteractionBroadphaseFn = std::vector<std::uint32_t> (*)(
    const std::vector<WorldBatchInteractionEntity> &,
    const std::vector<WorldBatchInteractionQuery> &, const WorldBatchInteractionConfig &);

struct WorldBatchGpuCompatibilityProvider {
    WorldBatchInteractionBroadphaseFn experiment_broadphase = nullptr;
};

void register_world_batch_gpu_compatibility_provider(
    const WorldBatchGpuCompatibilityProvider *provider) noexcept;

std::size_t world_batch_interaction_broadphase_word_count(int entities_per_world);

std::vector<std::uint32_t> world_batch_interaction_broadphase_reference_cpu_batch(
    const std::vector<WorldBatchInteractionEntity> &entities,
    const std::vector<WorldBatchInteractionQuery> &queries,
    const WorldBatchInteractionConfig &config);

std::vector<std::uint32_t> world_batch_interaction_broadphase_experiment_batch(
    const std::vector<WorldBatchInteractionEntity> &entities,
    const std::vector<WorldBatchInteractionQuery> &queries,
    const WorldBatchInteractionConfig &config);
