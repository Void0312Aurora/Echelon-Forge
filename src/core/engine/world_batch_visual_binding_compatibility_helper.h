#pragma once

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <vector>

#include "core/engine/simulation_kernel.h"
#include "gpu/gpu_visual_runtime.h"
#include "models/environment/default_environment_snapshot.h"

struct WorldBatchVisualBindingCompatibilityScene;
struct WorldBatchVisualObservationCompatibilityExport {
    std::size_t batch_size = 0;
    int out_h = 0;
    int out_w = 0;
    std::size_t frame_size = 0;
    std::vector<float> flat;
    const void *device_ptr = nullptr;
    std::size_t device_float_count = 0;
};

namespace world_batch_visual_binding_compatibility {

inline bool collect_scene_from_candidate_ids(const SimulationKernel &kernel,
                                             std::uint64_t entity_id, int downsample,
                                             WorldBatchVisualBindingCompatibilityScene *out_scene,
                                             const std::vector<std::uint64_t> *candidate_ids) {
    if (out_scene == nullptr) {
        return false;
    }

    auto world_lease = kernel.acquire_world_lease();
    const auto &world = world_lease.world();
    auto entity = world.entity(entity_id);
    if (!entity.is_valid()) {
        return false;
    }
    const Transform *camera_transform = entity.get<Transform>();
    const Alliance *camera_alliance = entity.get<Alliance>();
    if (camera_transform == nullptr) {
        return false;
    }

    const auto *env_ref = world.get<EnvironmentModelRef>();
    out_scene->environment = env_ref != nullptr ? env_ref->model : nullptr;

    const int factor = std::max(1, downsample);
    gpu::VisualRenderRequest request{};
    request.cam_pos = {camera_transform->x, camera_transform->y, camera_transform->z};
    request.cam_heading_deg = camera_transform->heading;
    request.cam_pitch_deg = camera_transform->pitch;
    request.fov_h_deg = 180.0;
    request.fov_v_deg = 90.0;
    request.out_height = arb::ARB_HEIGHT / factor;
    request.out_width = arb::ARB_WIDTH / factor;
    request.include_terrain = true;
    request.allow_gpu_terrain = true;
    out_scene->request = request;

    const int viewer_side =
        camera_alliance != nullptr ? static_cast<int>(camera_alliance->side) : 0;
    out_scene->objects.clear();
    world.each([&](flecs::entity other_entity, const Transform &transform,
                   const Velocity &velocity, const Alliance &alliance,
                   const KeyEntity &key) {
        if (other_entity.id() == entity_id) {
            return;
        }
        if (candidate_ids != nullptr &&
            !std::binary_search(candidate_ids->begin(), candidate_ids->end(), other_entity.id())) {
            return;
        }

        gpu::VisibleObjectPacked object{};
        object.x = transform.x;
        object.y = transform.y;
        object.z = transform.z;
        object.vx = velocity.vx;
        object.vy = velocity.vy;
        object.vz = velocity.vz;

        switch (key.type) {
        case UnitType::Aircraft:
            object.bounding_radius = 10.0;
            object.cls = 0;
            break;
        case UnitType::Ship:
            object.bounding_radius = 50.0;
            object.cls = 2;
            break;
        case UnitType::Submarine:
            object.bounding_radius = 40.0;
            object.cls = 2;
            break;
        case UnitType::Missile:
            object.bounding_radius = 2.0;
            object.cls = 0;
            break;
        case UnitType::Facility:
            object.bounding_radius = 20.0;
            object.cls = 1;
            break;
        default:
            object.bounding_radius = 5.0;
            object.cls = 1;
            break;
        }

        const int other_side = static_cast<int>(alliance.side);
        if (other_side == viewer_side) {
            object.team = 1;
        } else if (other_side == 0) {
            object.team = 0;
        } else {
            object.team = -1;
        }
        out_scene->objects.push_back(object);
    });

    out_scene->environment_snapshot = {};
    if (out_scene->environment != nullptr) {
        (void)extract_default_environment_snapshot(out_scene->environment,
                                                   &out_scene->environment_snapshot);
    }
    return true;
}

inline bool collect_scene(const SimulationKernel &kernel, std::uint64_t entity_id, int downsample,
                          WorldBatchVisualBindingCompatibilityScene *out_scene,
                          const std::vector<std::uint64_t> *candidate_ids) {
    return collect_scene_from_candidate_ids(kernel, entity_id, downsample, out_scene,
                                            candidate_ids);
}

inline bool default_environment_snapshots_equal(const DefaultEnvironmentSnapshot &lhs,
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

inline WorldBatchVisualObservationCompatibilityExport
render_scenes_batch(const std::vector<WorldBatchVisualBindingCompatibilityScene> &scenes,
                    bool use_gpu) {
    std::vector<gpu::VisualRenderRequest> requests;
    std::vector<std::vector<gpu::VisibleObjectPacked>> objects_batch;
    requests.reserve(scenes.size());
    objects_batch.reserve(scenes.size());

    std::vector<IEnvironmentModel *> envs;
    envs.reserve(scenes.size());
    std::vector<DefaultEnvironmentSnapshot> snapshots;
    snapshots.reserve(scenes.size());

    for (const auto &scene : scenes) {
        requests.push_back(scene.request);
        objects_batch.push_back(scene.objects);
        envs.push_back(scene.environment);
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
        if (!default_environment_snapshots_equal(snapshots[0], snapshots[idx])) {
            can_batch = false;
            break;
        }
    }

    if (can_batch && !requests.empty()) {
        if (use_gpu) {
            auto rendered =
                gpu::render_visual_experiment_batch_export(requests, objects_batch, envs.front());
            out.flat = std::move(rendered.flat);
            out.device_ptr = rendered.device_ptr;
            out.device_float_count = rendered.device_float_count;
        } else {
            out.flat =
                gpu::render_visual_reference_cpu_batch(requests, objects_batch, envs.front());
        }
        return out;
    }

    for (std::size_t idx = 0; idx < requests.size(); ++idx) {
        auto rendered =
            use_gpu
                ? gpu::render_visual_experiment(requests[idx], objects_batch[idx], envs[idx])
                : gpu::render_visual_reference_cpu(requests[idx], objects_batch[idx], envs[idx]);
        std::copy(rendered.begin(), rendered.end(),
                  out.flat.begin() + static_cast<std::ptrdiff_t>(idx * out.frame_size));
    }
    return out;
}

} // namespace world_batch_visual_binding_compatibility
