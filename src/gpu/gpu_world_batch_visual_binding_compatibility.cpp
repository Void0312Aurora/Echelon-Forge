#include "gpu/gpu_world_batch_visual_binding_compatibility.h"

#include <algorithm>
#include <cstddef>
#include <utility>

#include "gpu/gpu_visual_runtime.h"

namespace gpu {
namespace {

bool default_environment_snapshots_equal(const DefaultEnvironmentSnapshot &lhs,
                                         const DefaultEnvironmentSnapshot &rhs) {
    if (lhs.valid != rhs.valid || lhs.flat_terrain != rhs.flat_terrain) {
        return false;
    }
    if (lhs.raster.origin_x != rhs.raster.origin_x || lhs.raster.origin_y != rhs.raster.origin_y ||
        lhs.raster.resolution_m != rhs.raster.resolution_m || lhs.raster.width != rhs.raster.width ||
        lhs.raster.height != rhs.raster.height || lhs.raster.surface_codes != rhs.raster.surface_codes) {
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

VisualRenderRequest to_gpu_request(const WorldBatchVisualRenderRequest &request) {
    VisualRenderRequest out{};
    out.cam_pos = {request.cam_x, request.cam_y, request.cam_z};
    out.cam_heading_deg = request.cam_heading_deg;
    out.cam_pitch_deg = request.cam_pitch_deg;
    out.fov_h_deg = request.fov_h_deg;
    out.fov_v_deg = request.fov_v_deg;
    out.out_height = request.out_height;
    out.out_width = request.out_width;
    out.include_terrain = request.include_terrain;
    out.allow_gpu_terrain = request.allow_gpu_terrain;
    return out;
}

VisibleObjectPacked to_gpu_object(const WorldBatchVisibleObject &object) {
    VisibleObjectPacked out{};
    out.x = object.x;
    out.y = object.y;
    out.z = object.z;
    out.vx = object.vx;
    out.vy = object.vy;
    out.vz = object.vz;
    out.bounding_radius = object.bounding_radius;
    out.cls = object.cls;
    out.team = object.team;
    return out;
}

} // namespace

WorldBatchVisualObservationCompatibilityExport
render_world_batch_visual_binding_compatibility(
    const std::vector<WorldBatchVisualBindingCompatibilityScene> &scenes, bool use_gpu) {
    std::vector<VisualRenderRequest> requests;
    std::vector<std::vector<VisibleObjectPacked>> objects_batch;
    std::vector<DefaultEnvironmentSnapshot> snapshots;
    requests.reserve(scenes.size());
    objects_batch.reserve(scenes.size());
    snapshots.reserve(scenes.size());

    for (const auto &scene : scenes) {
        requests.push_back(to_gpu_request(scene.request));
        auto &objects = objects_batch.emplace_back();
        objects.reserve(scene.objects.size());
        for (const auto &object : scene.objects) {
            objects.push_back(to_gpu_object(object));
        }
        snapshots.push_back(scene.environment_snapshot);
    }

    WorldBatchVisualObservationCompatibilityExport out{};
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
            auto rendered = render_visual_experiment_batch_export_from_snapshot(
                requests, objects_batch, snapshots.front().valid ? &snapshots.front() : nullptr);
            out.flat = std::move(rendered.flat);
            out.device_ptr = rendered.device_ptr;
            out.device_float_count = rendered.device_float_count;
        } else {
            out.flat = render_visual_reference_cpu_batch_from_snapshot(
                requests, objects_batch, snapshots.front().valid ? &snapshots.front() : nullptr);
        }
        return out;
    }

    for (std::size_t idx = 0; idx < requests.size(); ++idx) {
        auto rendered = use_gpu ? render_visual_experiment_from_snapshot(
                                      requests[idx], objects_batch[idx],
                                      snapshots[idx].valid ? &snapshots[idx] : nullptr)
                                : render_visual_reference_cpu_from_snapshot(
                                      requests[idx], objects_batch[idx],
                                      snapshots[idx].valid ? &snapshots[idx] : nullptr);
        std::copy(rendered.begin(), rendered.end(),
                  out.flat.begin() + static_cast<std::ptrdiff_t>(idx * out.frame_size));
    }
    return out;
}

} // namespace gpu
