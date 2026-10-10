#pragma once

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <vector>

#include "core/engine/simulation_kernel.h"
#include "core/engine/world_batch_visual_binding_compatibility_types.h"

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
    out_scene->environment = nullptr;

    const int factor = std::max(1, downsample);
    WorldBatchVisualRenderRequest request{};
    request.cam_x = camera_transform->x;
    request.cam_y = camera_transform->y;
    request.cam_z = camera_transform->z;
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
    world.each([&](flecs::entity other_entity, const Transform &transform, const Velocity &velocity,
                   const Alliance &alliance, const KeyEntity &key) {
        if (other_entity.id() == entity_id) {
            return;
        }
        if (candidate_ids != nullptr &&
            !std::binary_search(candidate_ids->begin(), candidate_ids->end(), other_entity.id())) {
            return;
        }

        WorldBatchVisibleObject object{};
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
    if (env_ref != nullptr && env_ref->model != nullptr &&
        !extract_default_environment_snapshot(env_ref->model, &out_scene->environment_snapshot)) {
        return false;
    }
    return true;
}

inline bool collect_scene(const SimulationKernel &kernel, std::uint64_t entity_id, int downsample,
                          WorldBatchVisualBindingCompatibilityScene *out_scene,
                          const std::vector<std::uint64_t> *candidate_ids) {
    return collect_scene_from_candidate_ids(kernel, entity_id, downsample, out_scene,
                                            candidate_ids);
}

} // namespace world_batch_visual_binding_compatibility
