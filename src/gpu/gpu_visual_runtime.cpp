#include "gpu/gpu_visual_runtime.h"

#include <algorithm>
#include <array>
#include <cmath>
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

// Snapshot-backed read-only environment used by compatibility rendering after
// collection has released the SimulationKernel WorldLease. It deliberately
// implements the terrain subset consumed by the visual renderer while keeping
// the DTO independent from provider lifetime.
class SnapshotEnvironmentModel final : public IEnvironmentModel {
  public:
    explicit SnapshotEnvironmentModel(const DefaultEnvironmentSnapshot &snapshot)
        : snapshot_(snapshot) {}

    AtmosphericData get_atmosphere_at(double, double, double z) override {
        AtmosphericData data{};
        constexpr double kG = 9.80665;
        constexpr double kR = 287.0;
        constexpr double kL = 0.0065;
        constexpr double kT0 = 288.15;
        constexpr double kP0 = 101325.0;
        const double h = std::max(0.0, z);
        if (h < 11000.0) {
            data.temperature = kT0 - kL * h;
            data.pressure = kP0 * std::pow(1.0 - kL * h / kT0, kG / (kR * kL));
        } else {
            constexpr double kT11 = 216.65;
            constexpr double kP11 = 22632.1;
            data.temperature = kT11;
            data.pressure = kP11 * std::exp(-kG * (h - 11000.0) / (kR * kT11));
        }
        data.air_density = data.pressure / (kR * data.temperature);
        data.speed_of_sound = std::sqrt(1.4 * kR * data.temperature);
        data.wind_velocity = {0.0, 0.0, 0.0};
        return data;
    }

    double get_terrain_elevation(double x, double y) override {
        if (snapshot_.flat_terrain) {
            return 0.0;
        }
        constexpr double kPeakX = 25000.0;
        constexpr double kPeakY = 25000.0;
        constexpr double kPeakH = 2000.0;
        constexpr double kSigmaSq = 25000000.0;
        const double dx = x - kPeakX;
        const double dy = y - kPeakY;
        return kPeakH * std::exp(-(dx * dx + dy * dy) / (2.0 * kSigmaSq));
    }

    bool check_line_of_sight(double x1, double y1, double z1, double x2, double y2,
                             double z2) override {
        return z1 + 0.5 >= get_terrain_elevation(x1, y1) &&
               z2 + 0.5 >= get_terrain_elevation(x2, y2);
    }

    double get_weather_attenuation(double, double, double, double, double, double,
                                   int) override {
        return 0.0;
    }

    Vec3 get_sun_direction() override { return {0.0, 0.7071067811865476, 0.7071067811865476}; }

    TerrainCell get_terrain_at(double x, double y) override {
        TerrainCell cell{};
        cell.elevation = get_terrain_elevation(x, y);
        cell.type = SurfaceType::SoftDirt;
        cell.friction_mult = 0.1;
        cell.roughness = 0.5;
        cell.vegetation_density = 0.5;
        cell.runway_heading = 0.0;

        for (const auto &zone : snapshot_.zones) {
            const double dx = x - zone.center_x;
            const double dy = y - zone.center_y;
            bool inside = false;
            if (zone.type == 0) {
                const double yaw = (90.0 - zone.heading_deg) * M_PI / 180.0;
                const double c = std::cos(yaw);
                const double s = std::sin(yaw);
                const double local_len = dx * c + dy * s;
                const double local_wid = dx * (-s) + dy * c;
                inside = std::abs(local_wid) <= zone.width / 2.0 &&
                         std::abs(local_len) <= zone.length / 2.0;
            } else if (zone.type == 1) {
                inside = dx * dx + dy * dy <= zone.width * zone.width;
            }
            if (inside) {
                return cell_for_surface(static_cast<SurfaceType>(zone.surface_code),
                                        zone.heading_deg, cell.elevation);
            }
        }

        const auto &raster = snapshot_.raster;
        if (raster.resolution_m > 0.0 && raster.width > 0 && raster.height > 0 && x >= raster.origin_x &&
            y >= raster.origin_y) {
            const int col = static_cast<int>((x - raster.origin_x) / raster.resolution_m);
            const int row = static_cast<int>((y - raster.origin_y) / raster.resolution_m);
            if (col >= 0 && col < raster.width && row >= 0 && row < raster.height) {
                const std::size_t index = static_cast<std::size_t>(row) *
                                              static_cast<std::size_t>(raster.width) +
                                          static_cast<std::size_t>(col);
                if (index < raster.surface_codes.size()) {
                    return cell_for_surface(static_cast<SurfaceType>(raster.surface_codes[index]),
                                            0.0, cell.elevation);
                }
            }
        }
        return cell;
    }

    void clear_zones() override {}
    void add_zone(const std::string &, double, double, double, double, double,
                  SurfaceType) override {}
    void set_wind(double, double, double) override {}
    void set_sun_direction(double, double) override {}
    void set_terrain_type(const std::string &) override {}
    void set_maritime_state(double, double, double) override {}
    void clear_maritime_state() override {}

    MaritimeState get_maritime_state() const override {
        return MaritimeState{snapshot_.maritime_state_configured,
                              snapshot_.sea_state,
                              snapshot_.wave_heading_deg,
                              snapshot_.wave_period_s};
    }

  private:
    static TerrainCell cell_for_surface(SurfaceType surface, double runway_heading,
                                        double elevation) {
        TerrainCell cell{};
        cell.elevation = elevation;
        cell.type = surface;
        cell.runway_heading = runway_heading;
        switch (surface) {
        case SurfaceType::Concrete:
        case SurfaceType::Asphalt:
            cell.friction_mult = 0.02;
            cell.roughness = 0.0;
            cell.vegetation_density = 0.0;
            break;
        case SurfaceType::HardPacked:
            cell.friction_mult = 0.04;
            cell.roughness = 0.2;
            cell.vegetation_density = 0.1;
            break;
        case SurfaceType::Water:
            cell.friction_mult = 0.1;
            cell.roughness = 0.0;
            cell.vegetation_density = 0.0;
            break;
        case SurfaceType::SoftDirt:
        default:
            cell.friction_mult = 0.1;
            cell.roughness = 0.5;
            cell.vegetation_density = 0.5;
            break;
        }
        return cell;
    }

    const DefaultEnvironmentSnapshot &snapshot_;
};

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

std::vector<float> render_visual_reference_cpu_from_snapshot(
    const VisualRenderRequest &request, const std::vector<VisibleObjectPacked> &objects,
    const DefaultEnvironmentSnapshot *snapshot) {
    if (snapshot == nullptr || !snapshot->valid) {
        return render_visual_reference_cpu(request, objects, nullptr);
    }
    SnapshotEnvironmentModel environment(*snapshot);
    return render_visual_reference_cpu(request, objects, &environment);
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

std::vector<float> render_visual_reference_cpu_batch_from_snapshot(
    const std::vector<VisualRenderRequest> &requests,
    const std::vector<std::vector<VisibleObjectPacked>> &objects_batch,
    const DefaultEnvironmentSnapshot *snapshot) {
    if (requests.size() != objects_batch.size()) {
        throw std::invalid_argument(
            "render_visual_reference_cpu_batch_from_snapshot expects requests and objects_batch "
            "to have equal size");
    }
    if (snapshot == nullptr || !snapshot->valid) {
        return render_visual_reference_cpu_batch(requests, objects_batch, nullptr);
    }
    SnapshotEnvironmentModel environment(*snapshot);
    return render_visual_reference_cpu_batch(requests, objects_batch, &environment);
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

std::vector<float> render_visual_experiment_from_snapshot(
    const VisualRenderRequest &request, const std::vector<VisibleObjectPacked> &objects,
    const DefaultEnvironmentSnapshot *snapshot) {
    return render_visual_experiment_batch_export_from_snapshot({request}, {objects}, snapshot).flat;
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

VisualBatchRenderExport render_visual_experiment_batch_export_from_snapshot(
    const std::vector<VisualRenderRequest> &requests,
    const std::vector<std::vector<VisibleObjectPacked>> &objects_batch,
    const DefaultEnvironmentSnapshot *snapshot) {
    if (requests.size() != objects_batch.size()) {
        throw std::invalid_argument(
            "render_visual_experiment_batch_export_from_snapshot expects requests and "
            "objects_batch to have equal size");
    }
    if (requests.empty()) {
        return VisualBatchRenderExport{};
    }
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    bool all_object_only = true;
    bool all_terrain_gpu_eligible = snapshot != nullptr && snapshot->valid;
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
            const bool valid_device_output = device_ptr != nullptr && device_float_count == flat.size();
            return VisualBatchRenderExport{
                .flat = std::move(flat),
                .device_ptr = valid_device_output ? device_ptr : nullptr,
                .device_float_count = valid_device_output ? device_float_count : 0,
                .used_cuda = valid_device_output,
            };
        }
    }
    if (all_terrain_gpu_eligible) {
        auto flat = detail::render_visual_experiment_batch_cuda_with_terrain(
            requests, objects_batch, *snapshot);
        if (!flat.empty()) {
            const void *device_ptr = detail::last_visual_output_device_ptr_cuda();
            const std::size_t device_float_count = detail::last_visual_output_float_count_cuda();
            const bool valid_device_output = device_ptr != nullptr && device_float_count == flat.size();
            return VisualBatchRenderExport{
                .flat = std::move(flat),
                .device_ptr = valid_device_output ? device_ptr : nullptr,
                .device_float_count = valid_device_output ? device_float_count : 0,
                .used_cuda = valid_device_output,
            };
        }
    }
#endif
    return VisualBatchRenderExport{
        .flat = render_visual_reference_cpu_batch_from_snapshot(requests, objects_batch, snapshot),
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
