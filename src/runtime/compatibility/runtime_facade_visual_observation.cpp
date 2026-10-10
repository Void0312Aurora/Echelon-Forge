#include "runtime/compatibility/runtime_facade_visual_observation.h"

#include <algorithm>

#include "gpu/gpu_world_batch_visual_binding_compatibility.h"

RuntimeFacadeVisualObservationExport
render_runtime_facade_visual_observation_batch(const RuntimeFacade &facade,
                                               const std::vector<WorldEntityRef> &refs,
                                               int downsample, bool use_gpu) {
    const int factor = std::max(1, downsample);
    const auto scenes =
        facade.collect_visual_binding_compatibility_scenes_batch(refs, factor, use_gpu);
    const auto rendered = gpu::render_world_batch_visual_binding_compatibility(scenes, use_gpu);

    RuntimeFacadeVisualObservationExport out{};
    out.batch_size = rendered.batch_size;
    out.out_h = rendered.out_h;
    out.out_w = rendered.out_w;
    out.frame_size = rendered.frame_size;
    out.flat = rendered.flat;
    return out;
}
