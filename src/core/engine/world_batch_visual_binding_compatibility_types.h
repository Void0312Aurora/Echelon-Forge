#pragma once

#include <cstddef>
#include <vector>

#include "models/environment/default_environment_snapshot.h"

// Engine-owned visual packets deliberately contain only semantic values. GPU
// packing and device handles belong to the lower-level adapter in src/gpu.
struct WorldBatchVisualRenderRequest {
    double cam_x = 0.0;
    double cam_y = 0.0;
    double cam_z = 0.0;
    double cam_heading_deg = 0.0;
    double cam_pitch_deg = 0.0;
    double fov_h_deg = 180.0;
    double fov_v_deg = 90.0;
    int out_height = 0;
    int out_width = 0;
    bool include_terrain = true;
    bool allow_gpu_terrain = true;
};

struct WorldBatchVisibleObject {
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    double vx = 0.0;
    double vy = 0.0;
    double vz = 0.0;
    double bounding_radius = 0.0;
    int cls = 1;
    int team = 0;
};

// Legacy visual-binding DTO kept outside the semantic backend SPI. It remains
// source compatible for existing CPU/runtime bindings and is reachable from
// RuntimeFacade only through the quarantined compatibility port.
struct WorldBatchVisualBindingCompatibilityScene {
    WorldBatchVisualRenderRequest request{};
    std::vector<WorldBatchVisibleObject> objects;
    // ABI/source-compatibility tombstone. Collection always stores nullptr and
    // rendering ignores this field; provider pointers must not escape the
    // WorldLease acquired during collection.
    [[deprecated("use environment_snapshot; provider pointers do not escape collection")]]
    IEnvironmentModel *environment = nullptr;
    DefaultEnvironmentSnapshot environment_snapshot{};
};

struct WorldBatchVisualObservationCompatibilityExport {
    std::size_t batch_size = 0;
    int out_h = 0;
    int out_w = 0;
    std::size_t frame_size = 0;
    std::vector<float> flat;
    const void *device_ptr = nullptr;
    std::size_t device_float_count = 0;
};
