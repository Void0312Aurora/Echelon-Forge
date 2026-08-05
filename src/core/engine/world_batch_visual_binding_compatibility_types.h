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
    IEnvironmentModel *environment = nullptr;
    DefaultEnvironmentSnapshot environment_snapshot{};
};
