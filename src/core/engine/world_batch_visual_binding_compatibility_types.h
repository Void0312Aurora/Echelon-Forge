#pragma once

#include <vector>

#include "gpu/gpu_visual_runtime.h"
#include "models/environment/default_environment_snapshot.h"

// Legacy visual-binding DTO kept outside the semantic backend SPI. It remains
// source/ABI compatible for existing CPU/runtime bindings and is reachable
// from RuntimeFacade only through the quarantined compatibility port.
struct WorldBatchVisualBindingCompatibilityScene {
    gpu::VisualRenderRequest request{};
    std::vector<gpu::VisibleObjectPacked> objects;
    // ABI/source-compatibility tombstone. Collection always stores nullptr and
    // rendering ignores this field; provider pointers must not escape the
    // WorldLease acquired during collection.
    [[deprecated("use environment_snapshot; provider pointers do not escape collection")]]
    IEnvironmentModel *environment = nullptr;
    DefaultEnvironmentSnapshot environment_snapshot{};
};
