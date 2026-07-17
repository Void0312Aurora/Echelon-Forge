#include "gpu/gpu_visual_runtime.h"

#include <algorithm>
#include <array>
#include <iomanip>
#include <stdexcept>
#include <sstream>
#include <utility>

#include "systems/visual/visual_system.h"

namespace gpu::detail {

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
DeviceInfo probe_cuda_device();
std::vector<float> render_visual_experiment_cuda(const VisualRenderRequest &request,
                                                 const std::vector<VisibleObjectPacked> &objects);
std::vector<float> render_visual_experiment_batch_cuda(
    const std::vector<VisualRenderRequest> &requests,
    const std::vector<std::vector<VisibleObjectPacked>> &objects_batch);
std::vector<float> render_visual_experiment_batch_cuda_with_terrain(
    const std::vector<VisualRenderRequest> &requests,
    const std::vector<std::vector<VisibleObjectPacked>> &objects_batch,
    const DefaultEnvironmentSnapshot &snapshot);
bool render_visual_experiment_batch_cuda_device_resident(
    const std::vector<VisualRenderRequest> &requests,
    const std::vector<std::vector<VisibleObjectPacked>> &objects_batch);
bool render_visual_experiment_batch_cuda_with_terrain_device_resident(
    const std::vector<VisualRenderRequest> &requests,
    const std::vector<std::vector<VisibleObjectPacked>> &objects_batch,
    const DefaultEnvironmentSnapshot &snapshot);
VisualExperimentStats last_visual_experiment_cuda_stats();
const void *last_visual_output_device_ptr_cuda();
std::size_t last_visual_output_float_count_cuda();
#endif

} // namespace gpu::detail

namespace {

std::vector<arb::VisibleObject>
to_arb_objects(const std::vector<gpu::VisibleObjectPacked> &objects) {
    std::vector<arb::VisibleObject> out;
    out.reserve(objects.size());
    for (const auto &item : objects) {
        arb::VisibleObject obj{};
        obj.x = item.x;
        obj.y = item.y;
        obj.z = item.z;
        obj.vx = item.vx;
        obj.vy = item.vy;
        obj.vz = item.vz;
        obj.bounding_radius = item.bounding_radius;
        obj.cls = item.cls;
        obj.team = item.team;
        out.push_back(obj);
    }
    return out;
}

} // namespace

namespace gpu {

DeviceInfo probe_device() {
    DeviceInfo info{};
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    info = detail::probe_cuda_device();
#endif
    return info;
}

VisualTensorFootprint estimate_visual_tensor_footprint(int height, int width, int env_count,
                                                       int history_steps) {
    VisualTensorFootprint out{};
    out.height = std::max(1, height);
    out.width = std::max(1, width);
    out.channels = arb::ARB_CHANNELS;
    out.env_count = std::max(1, env_count);
    out.history_steps = std::max(1, history_steps);

    const std::size_t frame_elems = static_cast<std::size_t>(out.height) *
                                    static_cast<std::size_t>(out.width) *
                                    static_cast<std::size_t>(out.channels);
    out.frame_bytes = frame_elems * sizeof(float);
    out.batch_bytes = out.frame_bytes * static_cast<std::size_t>(out.env_count);
    out.history_bytes = out.batch_bytes * static_cast<std::size_t>(out.history_steps);
    out.double_buffer_bytes = out.batch_bytes * 2u;
    return out;
}

std::string format_bytes(std::size_t bytes) {
    static constexpr std::array<const char *, 5> kUnits = {"B", "KiB", "MiB", "GiB", "TiB"};
    double value = static_cast<double>(bytes);
    std::size_t unit_index = 0;
    while (value >= 1024.0 && unit_index + 1 < kUnits.size()) {
        value /= 1024.0;
        ++unit_index;
    }
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(unit_index == 0 ? 0 : 2) << value << ' '
        << kUnits[unit_index];
    return oss.str();
}

VisualExperimentStats last_visual_experiment_stats() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::last_visual_experiment_cuda_stats();
#else
    return VisualExperimentStats{};
#endif
}

const void *last_visual_output_device_ptr() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::last_visual_output_device_ptr_cuda();
#else
    return nullptr;
#endif
}

std::size_t last_visual_output_float_count() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::last_visual_output_float_count_cuda();
#else
    return 0;
#endif
}

std::vector<float> render_visual_reference_cpu(const VisualRenderRequest &request,
                                               const std::vector<VisibleObjectPacked> &objects,
                                               IEnvironmentModel *env) {
    return arb::render_retina_tensor(
        request.cam_pos, request.cam_heading_deg, request.cam_pitch_deg, request.fov_h_deg,
        request.fov_v_deg, to_arb_objects(objects), request.include_terrain ? env : nullptr,
        request.out_height, request.out_width);
}

std::vector<float> render_visual_reference_cpu_batch(
    const std::vector<VisualRenderRequest> &requests,
    const std::vector<std::vector<VisibleObjectPacked>> &objects_batch, IEnvironmentModel *env) {
    if (requests.size() != objects_batch.size()) {
        throw std::invalid_argument("render_visual_reference_cpu_batch expects requests and "
                                    "objects_batch to have equal size");
    }
    if (requests.empty()) {
        return {};
    }
    const auto first_height = requests.front().out_height;
    const auto first_width = requests.front().out_width;
    const std::size_t frame_size = static_cast<std::size_t>(first_height) *
                                   static_cast<std::size_t>(first_width) *
                                   static_cast<std::size_t>(arb::ARB_CHANNELS);
    std::vector<float> out(frame_size * requests.size(), 0.0f);
    for (std::size_t idx = 0; idx < requests.size(); ++idx) {
        if (requests[idx].out_height != first_height || requests[idx].out_width != first_width) {
            throw std::invalid_argument(
                "render_visual_reference_cpu_batch requires uniform output shape across requests");
        }
        auto rendered = render_visual_reference_cpu(requests[idx], objects_batch[idx], env);
        std::copy(rendered.begin(), rendered.end(),
                  out.begin() + static_cast<std::ptrdiff_t>(idx * frame_size));
    }
    return out;
}

std::vector<float> render_visual_experiment(const VisualRenderRequest &request,
                                            const std::vector<VisibleObjectPacked> &objects,
                                            IEnvironmentModel *env) {
    (void)env;
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    if (!request.include_terrain) {
        return detail::render_visual_experiment_cuda(request, objects);
    }
    if (request.allow_gpu_terrain && env != nullptr) {
        DefaultEnvironmentSnapshot snapshot{};
        if (extract_default_environment_snapshot(env, &snapshot) && snapshot.valid) {
            return detail::render_visual_experiment_batch_cuda_with_terrain({request}, {objects},
                                                                            snapshot);
        }
    }
#endif
    return render_visual_reference_cpu(request, objects, env);
}

VisualBatchRenderExport render_visual_experiment_batch_export(
    const std::vector<VisualRenderRequest> &requests,
    const std::vector<std::vector<VisibleObjectPacked>> &objects_batch, IEnvironmentModel *env) {
    if (requests.size() != objects_batch.size()) {
        throw std::invalid_argument(
            "render_visual_experiment_batch expects requests and objects_batch to have equal size");
    }
    if (requests.empty()) {
        return VisualBatchRenderExport{};
    }
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    bool all_object_only = true;
    bool all_terrain_gpu_eligible = true;
    for (const auto &request : requests) {
        if (request.include_terrain) {
            all_object_only = false;
        } else {
            all_terrain_gpu_eligible = false;
        }
        if (!(request.include_terrain && request.allow_gpu_terrain)) {
            all_terrain_gpu_eligible = false;
        }
    }
    if (all_object_only) {
        auto flat = detail::render_visual_experiment_batch_cuda(requests, objects_batch);
        if (!flat.empty()) {
            const void *device_ptr = detail::last_visual_output_device_ptr_cuda();
            const std::size_t device_float_count = detail::last_visual_output_float_count_cuda();
            const bool valid_device_output =
                device_ptr != nullptr && device_float_count == flat.size();
            return VisualBatchRenderExport{
                .flat = std::move(flat),
                .device_ptr = valid_device_output ? device_ptr : nullptr,
                .device_float_count = valid_device_output ? device_float_count : 0,
                .used_cuda = valid_device_output,
            };
        }
    }
    if (all_terrain_gpu_eligible && env != nullptr) {
        DefaultEnvironmentSnapshot snapshot{};
        if (extract_default_environment_snapshot(env, &snapshot) && snapshot.valid) {
            auto flat = detail::render_visual_experiment_batch_cuda_with_terrain(
                requests, objects_batch, snapshot);
            if (!flat.empty()) {
                const void *device_ptr = detail::last_visual_output_device_ptr_cuda();
                const std::size_t device_float_count =
                    detail::last_visual_output_float_count_cuda();
                const bool valid_device_output =
                    device_ptr != nullptr && device_float_count == flat.size();
                return VisualBatchRenderExport{
                    .flat = std::move(flat),
                    .device_ptr = valid_device_output ? device_ptr : nullptr,
                    .device_float_count = valid_device_output ? device_float_count : 0,
                    .used_cuda = valid_device_output,
                };
            }
        }
    }
#endif
    return VisualBatchRenderExport{
        .flat = render_visual_reference_cpu_batch(requests, objects_batch, env),
    };
}

std::vector<float>
render_visual_experiment_batch(const std::vector<VisualRenderRequest> &requests,
                               const std::vector<std::vector<VisibleObjectPacked>> &objects_batch,
                               IEnvironmentModel *env) {
    return render_visual_experiment_batch_export(requests, objects_batch, env).flat;
}

bool render_visual_experiment_batch_device_resident(
    const std::vector<VisualRenderRequest> &requests,
    const std::vector<std::vector<VisibleObjectPacked>> &objects_batch, IEnvironmentModel *env) {
    (void)env;
    if (requests.size() != objects_batch.size() || requests.empty()) {
        return false;
    }
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    bool all_object_only = true;
    bool all_terrain_gpu_eligible = true;
    for (const auto &request : requests) {
        if (request.include_terrain) {
            all_object_only = false;
        } else {
            all_terrain_gpu_eligible = false;
        }
        if (!(request.include_terrain && request.allow_gpu_terrain)) {
            all_terrain_gpu_eligible = false;
        }
    }
    if (all_object_only) {
        return detail::render_visual_experiment_batch_cuda_device_resident(requests, objects_batch);
    }
    if (all_terrain_gpu_eligible && env != nullptr) {
        DefaultEnvironmentSnapshot snapshot{};
        if (extract_default_environment_snapshot(env, &snapshot) && snapshot.valid) {
            return detail::render_visual_experiment_batch_cuda_with_terrain_device_resident(
                requests, objects_batch, snapshot);
        }
    }
#endif
    return false;
}

} // namespace gpu
