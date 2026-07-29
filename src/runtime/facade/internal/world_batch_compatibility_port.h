#pragma once

#include <cstdint>
#include <vector>

#include "runtime/contracts/world_batch_contracts.h"

struct WorldBatchVisualBindingCompatibilityScene;

// Explicitly quarantined legacy query port. The maintained semantic backend
// SPI never carries use_gpu or old visual-helper scene types; only the CPU
// reference adapter exposes this optional compatibility surface.
class IWorldBatchCompatibilityPort {
  public:
    virtual ~IWorldBatchCompatibilityPort() = default;

    virtual std::vector<std::vector<std::uint64_t>>
    get_sensor_candidate_ids_batch(const std::vector<WorldEntityRef> &refs, bool use_gpu) const = 0;
    virtual std::vector<std::vector<std::uint64_t>>
    get_visual_candidate_ids_batch(const std::vector<WorldEntityRef> &refs, double range_m,
                                   bool use_gpu) const = 0;
    virtual std::vector<std::vector<std::uint64_t>>
    get_comm_candidate_ids_batch(const std::vector<WorldEntityRef> &refs, bool use_gpu) const = 0;
    virtual std::vector<WorldBatchVisualBindingCompatibilityScene>
    collect_visual_binding_compatibility_scenes_from_candidate_ids_batch(
        const std::vector<WorldEntityRef> &refs, int downsample,
        const std::vector<std::vector<std::uint64_t>> &candidate_ids_batch) const = 0;
};
