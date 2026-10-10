#pragma once

#include <vector>

#include "core/engine/world_batch_visual_binding_compatibility_types.h"

namespace gpu {

// GPU-owned adapter for the legacy visual compatibility route. The engine
// supplies neutral scene packets; this adapter performs GPU packet conversion
// and owns device/render implementation details.
WorldBatchVisualObservationCompatibilityExport
render_world_batch_visual_binding_compatibility(
    const std::vector<WorldBatchVisualBindingCompatibilityScene> &scenes, bool use_gpu);

} // namespace gpu
