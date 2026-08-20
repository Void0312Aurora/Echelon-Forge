#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include "components/basic/common.h"
#include "core/interfaces/environment_model.h"
#include "components/visual/visual_sensor.h"
#include "models/environment/default_environment_snapshot.h"

namespace gpu {

struct DeviceInfo {
    bool cuda_runtime_built = false;
    bool cuda_runtime_available = false;
    int device_count = 0;
    int active_device = -1;
    int compute_major = 0;
    int compute_minor = 0;
    int runtime_version = 0;
    std::size_t total_global_mem_bytes = 0;
    std::size_t free_global_mem_bytes = 0;
    std::string device_name;
    std::string error_message;
};

struct VisualTensorFootprint {
    int height = 0;
    int width = 0;
    int channels = arb::ARB_CHANNELS;
    int env_count = 1;
    int history_steps = 1;
    std::size_t frame_bytes = 0;
    std::size_t batch_bytes = 0;
    std::size_t history_bytes = 0;
    std::size_t double_buffer_bytes = 0;
};

struct VisualExperimentStats {
    bool used_cuda = false;
    double host_to_device_ms = 0.0;
    double kernel_ms = 0.0;
    double device_to_host_ms = 0.0;
    double total_ms = 0.0;
};

struct VisualBatchRenderExport {
    std::vector<float> flat;
    const void *device_ptr = nullptr;
    std::size_t device_float_count = 0;
    bool used_cuda = false;
};

struct VisibleObjectPacked {
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

struct VisualRenderRequest {
    Math::Vector3 cam_pos{};
    double cam_heading_deg = 0.0;
    double cam_pitch_deg = 0.0;
    double fov_h_deg = 180.0;
    double fov_v_deg = 90.0;
    int out_height = arb::ARB_HEIGHT;
    int out_width = arb::ARB_WIDTH;
    bool include_terrain = true;
    bool allow_gpu_terrain = true;
};

DeviceInfo probe_device();
VisualTensorFootprint estimate_visual_tensor_footprint(int height, int width, int env_count = 1,
                                                       int history_steps = 1);
std::string format_bytes(std::size_t bytes);
VisualExperimentStats last_visual_experiment_stats();

std::vector<float> render_visual_reference_cpu_batch(
    const std::vector<VisualRenderRequest> &requests,
    const std::vector<std::vector<VisibleObjectPacked>> &objects_batch, IEnvironmentModel *env);

std::vector<float> render_visual_reference_cpu(const VisualRenderRequest &request,
                                               const std::vector<VisibleObjectPacked> &objects,
                                               IEnvironmentModel *env);

std::vector<float> render_visual_reference_cpu_from_snapshot(
    const VisualRenderRequest &request, const std::vector<VisibleObjectPacked> &objects,
    const DefaultEnvironmentSnapshot *snapshot);

std::vector<float> render_visual_reference_cpu_batch_from_snapshot(
    const std::vector<VisualRenderRequest> &requests,
    const std::vector<std::vector<VisibleObjectPacked>> &objects_batch,
    const DefaultEnvironmentSnapshot *snapshot);

std::vector<float>
render_visual_experiment_batch(const std::vector<VisualRenderRequest> &requests,
                               const std::vector<std::vector<VisibleObjectPacked>> &objects_batch,
                               IEnvironmentModel *env);

VisualBatchRenderExport render_visual_experiment_batch_export(
    const std::vector<VisualRenderRequest> &requests,
    const std::vector<std::vector<VisibleObjectPacked>> &objects_batch, IEnvironmentModel *env);

VisualBatchRenderExport render_visual_experiment_batch_export_from_snapshot(
    const std::vector<VisualRenderRequest> &requests,
    const std::vector<std::vector<VisibleObjectPacked>> &objects_batch,
    const DefaultEnvironmentSnapshot *snapshot);

bool render_visual_experiment_batch_device_resident(
    const std::vector<VisualRenderRequest> &requests,
    const std::vector<std::vector<VisibleObjectPacked>> &objects_batch, IEnvironmentModel *env);

const void *last_visual_output_device_ptr();
std::size_t last_visual_output_float_count();

std::vector<float> render_visual_experiment(const VisualRenderRequest &request,
                                            const std::vector<VisibleObjectPacked> &objects,
                                            IEnvironmentModel *env);

std::vector<float> render_visual_experiment_from_snapshot(
    const VisualRenderRequest &request, const std::vector<VisibleObjectPacked> &objects,
    const DefaultEnvironmentSnapshot *snapshot);

} // namespace gpu
