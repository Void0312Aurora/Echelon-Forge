#pragma once

#include <cstddef>
#include <vector>

#include "core/engine/world_batch_visual_binding_compatibility_types.h"
#include "runtime/facade/runtime_facade.h"

struct RuntimeFacadeVisualObservationExport {
    std::size_t batch_size = 0;
    int out_h = 0;
    int out_w = 0;
    std::size_t frame_size = 0;
    std::vector<float> flat;
};

RuntimeFacadeVisualObservationExport
render_runtime_facade_visual_observation_batch(const RuntimeFacade &facade,
                                               const std::vector<WorldEntityRef> &refs,
                                               int downsample, bool use_gpu);
