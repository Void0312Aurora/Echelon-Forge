#include "runtime/compatibility/runtime_facade_visual_observation.h"

#include <algorithm>
#include <cstddef>
#include <utility>

#include "gpu/gpu_visual_runtime.h"

namespace {

bool default_environment_snapshots_equal(const DefaultEnvironmentSnapshot &lhs,
                                         const DefaultEnvironmentSnapshot &rhs) {
    if (lhs.valid != rhs.valid || lhs.flat_terrain != rhs.flat_terrain) {
        return false;
    }
    if (lhs.raster.origin_x != rhs.raster.origin_x || lhs.raster.origin_y != rhs.raster.origin_y ||
        lhs.raster.resolution_m != rhs.raster.resolution_m ||
        lhs.raster.width != rhs.raster.width || lhs.raster.height != rhs.raster.height ||
        lhs.raster.surface_codes != rhs.raster.surface_codes) {
        return false;
    }
    if (lhs.zones.size() != rhs.zones.size()) {
        return false;
    }
    for (std::size_t idx = 0; idx < lhs.zones.size(); ++idx) {
        const auto &a = lhs.zones[idx];
        const auto &b = rhs.zones[idx];
        if (a.center_x != b.center_x || a.center_y != b.center_y || a.width != b.width ||
            a.length != b.length || a.heading_deg != b.heading_deg || a.type != b.type ||
            a.surface_code != b.surface_code) {
            return false;
        }
    }
    return true;
}

}  // namespace

RuntimeFacadeVisualObservationExport render_runtime_facade_visual_observation_batch(
    const RuntimeFacade &facade, const std::vector<WorldEntityRef> &refs, int downsample,
    bool use_gpu) {
    const int factor = std::max(1, downsample);
    const auto scenes =
        facade.collect_visual_binding_compatibility_scenes_batch(refs, factor, use_gpu);

    std::vector<gpu::VisualRenderRequest> requests;
    std::vector<std::vector<gpu::VisibleObjectPacked>> objects_batch;
    std::vector<DefaultEnvironmentSnapshot> snapshots;
    requests.reserve(scenes.size());
    objects_batch.reserve(scenes.size());
    snapshots.reserve(scenes.size());
    for (const auto &scene : scenes) {
        requests.push_back(scene.request);
        objects_batch.push_back(scene.objects);
        snapshots.push_back(scene.environment_snapshot);
    }

    RuntimeFacadeVisualObservationExport out{};
    out.batch_size = scenes.size();
    out.out_h = requests.empty() ? arb::ARB_HEIGHT : requests.front().out_height;
    out.out_w = requests.empty() ? arb::ARB_WIDTH : requests.front().out_width;
    out.frame_size = static_cast<std::size_t>(out.out_h) * static_cast<std::size_t>(out.out_w) *
                     static_cast<std::size_t>(arb::ARB_CHANNELS);
    out.flat.assign(out.frame_size * scenes.size(), 0.0f);

    bool can_batch = !requests.empty();
    for (std::size_t idx = 1; idx < snapshots.size(); ++idx) {
        if (!default_environment_snapshots_equal(snapshots.front(), snapshots[idx])) {
            can_batch = false;
            break;
        }
    }

    if (can_batch && !requests.empty()) {
        if (use_gpu) {
            out.flat = gpu::render_visual_experiment_batch_export_from_snapshot(
                           requests, objects_batch,
                           snapshots.front().valid ? &snapshots.front() : nullptr)
                           .flat;
        } else {
            out.flat = gpu::render_visual_reference_cpu_batch_from_snapshot(
                requests, objects_batch, snapshots.front().valid ? &snapshots.front() : nullptr);
        }
        return out;
    }

    for (std::size_t idx = 0; idx < requests.size(); ++idx) {
        auto rendered = use_gpu
                            ? gpu::render_visual_experiment_from_snapshot(
                                  requests[idx], objects_batch[idx],
                                  snapshots[idx].valid ? &snapshots[idx] : nullptr)
                            : gpu::render_visual_reference_cpu_from_snapshot(
                                  requests[idx], objects_batch[idx],
                                  snapshots[idx].valid ? &snapshots[idx] : nullptr);
        std::copy(rendered.begin(), rendered.end(),
                  out.flat.begin() + static_cast<std::ptrdiff_t>(idx * out.frame_size));
    }
    return out;
}
