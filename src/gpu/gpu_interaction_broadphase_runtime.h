#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

namespace gpu {

struct InteractionEntityPacked {
    int world_index = 0;
    int local_index = 0;
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    double bounding_radius_m = 0.0;
};

struct InteractionQueryPacked {
    int world_index = 0;
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    double range_m = 0.0;
};

struct InteractionBroadphaseConfig {
    double cell_size_m = 5000.0;
    double max_entity_radius_m = 250.0;
    int entities_per_world = 1024;
    int hash_bucket_count = 1 << 15;
    int bucket_capacity = 64;
};

struct InteractionBroadphaseExperimentStats {
    bool used_cuda = false;
    double host_to_device_ms = 0.0;
    double kernel_ms = 0.0;
    double device_to_host_ms = 0.0;
    double total_ms = 0.0;
    int overflow_bucket_count = 0;
    int overflow_query_count = 0;
};

std::size_t interaction_broadphase_word_count(int entities_per_world);

InteractionBroadphaseExperimentStats last_interaction_broadphase_stats();
const void* last_interaction_broadphase_output_device_ptr();
std::size_t last_interaction_broadphase_output_word_count();

std::vector<std::uint32_t> build_interaction_broadphase_reference_cpu_batch(
    const std::vector<InteractionEntityPacked>& entities,
    const std::vector<InteractionQueryPacked>& queries,
    const InteractionBroadphaseConfig& config
);

std::vector<std::uint32_t> build_interaction_broadphase_experiment_batch(
    const std::vector<InteractionEntityPacked>& entities,
    const std::vector<InteractionQueryPacked>& queries,
    const InteractionBroadphaseConfig& config
);

bool build_interaction_broadphase_experiment_batch_device_resident(
    const std::vector<InteractionEntityPacked>& entities,
    const std::vector<InteractionQueryPacked>& queries,
    const InteractionBroadphaseConfig& config
);

}  // namespace gpu
