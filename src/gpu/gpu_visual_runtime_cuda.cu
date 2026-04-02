#include "gpu/gpu_visual_runtime.h"

#include <cuda_runtime_api.h>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <vector>

namespace {

constexpr float kDefaultZ = 1.0e10f;
constexpr std::uint32_t kTerrainKeyObjectIndex = 0xffffffffu;
gpu::VisualExperimentStats g_last_stats{};
const void* g_last_output_device_ptr = nullptr;
std::size_t g_last_output_float_count = 0;

struct TerrainSnapshotHeader {
    int flat_terrain = 0;
    double raster_origin_x = 0.0;
    double raster_origin_y = 0.0;
    double raster_resolution_m = 1.0;
    int raster_width = 0;
    int raster_height = 0;
    int zone_count = 0;
};

struct TerrainZonePacked {
    double center_x = 0.0;
    double center_y = 0.0;
    double width = 0.0;
    double length = 0.0;
    double heading_deg = 0.0;
    int type = 0;
    std::uint8_t surface_code = 0;
};

struct DeviceVisualCache {
    gpu::VisualRenderRequest* d_requests = nullptr;
    gpu::VisibleObjectPacked* d_objects = nullptr;
    int* d_object_request_indices = nullptr;
    std::uint64_t* d_keys = nullptr;
    std::uint8_t* d_terrain_cls = nullptr;
    std::uint8_t* d_raster_surface_codes = nullptr;
    TerrainZonePacked* d_zones = nullptr;
    float* d_output = nullptr;
    std::size_t request_capacity = 0;
    std::size_t object_capacity = 0;
    std::size_t pixel_capacity = 0;
    std::size_t raster_surface_capacity = 0;
    std::size_t zone_capacity = 0;
};

DeviceVisualCache g_cache{};

__host__ __device__ inline double deg_to_rad(double deg) {
    return deg * 3.14159265358979323846 / 180.0;
}

__host__ __device__ inline void write_default_pixel(float* out) {
    out[arb::CH_DEPTH_LOG] = 0.0f;
    out[arb::CH_INV_DEPTH] = 0.0f;
    out[arb::CH_COVERAGE] = 0.0f;
    out[arb::CH_ANG_SIZE] = 0.0f;
    out[arb::CH_CLASS_AIR] = 0.0f;
    out[arb::CH_CLASS_GROUND] = 0.0f;
    out[arb::CH_CLASS_SEA] = 0.0f;
    out[arb::CH_CLASS_TERRAIN] = 1.0f;
    out[arb::CH_TEAM] = 0.0f;
    out[arb::CH_VEL_RADIAL] = 0.0f;
}

__host__ __device__ inline void write_object_pixel(
    float* out,
    float z_obj,
    float alpha,
    int cls,
    int team,
    float vr
) {
    out[arb::CH_DEPTH_LOG] = log1pf(z_obj);
    out[arb::CH_INV_DEPTH] = 1.0f / (z_obj + 1.0e-3f);
    out[arb::CH_COVERAGE] = fminf(1.0f, alpha * 100.0f);
    out[arb::CH_ANG_SIZE] = alpha;
    out[arb::CH_CLASS_AIR] = (cls == 0) ? 1.0f : 0.0f;
    out[arb::CH_CLASS_GROUND] = (cls == 1) ? 1.0f : 0.0f;
    out[arb::CH_CLASS_SEA] = (cls == 2) ? 1.0f : 0.0f;
    out[arb::CH_CLASS_TERRAIN] = (cls == 3) ? 1.0f : 0.0f;
    out[arb::CH_TEAM] = static_cast<float>(team);
    out[arb::CH_VEL_RADIAL] = vr;
}

__host__ __device__ inline int terrain_surface_to_visual_class(std::uint8_t surface_code) {
    if (surface_code == static_cast<std::uint8_t>(IEnvironmentModel::SurfaceType::Concrete) ||
        surface_code == static_cast<std::uint8_t>(IEnvironmentModel::SurfaceType::Asphalt)) {
        return 1;
    }
    if (surface_code == static_cast<std::uint8_t>(IEnvironmentModel::SurfaceType::Water)) {
        return 2;
    }
    return 3;
}

__host__ __device__ inline void write_terrain_pixel(
    float* out,
    float z_obj,
    int cls
) {
    out[arb::CH_DEPTH_LOG] = log1pf(z_obj);
    out[arb::CH_INV_DEPTH] = 1.0f / (z_obj + 1.0e-3f);
    out[arb::CH_COVERAGE] = 1.0f;
    out[arb::CH_ANG_SIZE] = 0.0f;
    out[arb::CH_CLASS_AIR] = 0.0f;
    out[arb::CH_CLASS_GROUND] = (cls == 1) ? 1.0f : 0.0f;
    out[arb::CH_CLASS_SEA] = (cls == 2) ? 1.0f : 0.0f;
    out[arb::CH_CLASS_TERRAIN] = (cls == 3) ? 1.0f : 0.0f;
    out[arb::CH_TEAM] = 0.0f;
    out[arb::CH_VEL_RADIAL] = 0.0f;
}

__device__ inline std::uint64_t encode_depth_object_key(float depth, std::uint32_t object_index) {
    const std::uint32_t depth_bits = __float_as_uint(depth);
    return (static_cast<std::uint64_t>(depth_bits) << 32) | static_cast<std::uint64_t>(object_index);
}

__device__ inline float decode_depth_from_key(std::uint64_t key) {
    return __uint_as_float(static_cast<std::uint32_t>(key >> 32));
}

__device__ inline std::uint32_t decode_object_index_from_key(std::uint64_t key) {
    return static_cast<std::uint32_t>(key & 0xffffffffu);
}

__host__ __device__ inline double terrain_elevation_m(
    const TerrainSnapshotHeader& snapshot,
    double x,
    double y
) {
    if (snapshot.flat_terrain != 0) {
        return 0.0;
    }
    constexpr double kPeakX = 25000.0;
    constexpr double kPeakY = 25000.0;
    constexpr double kPeakH = 2000.0;
    constexpr double kSigmaSq = 25000000.0;
    const double d2 = (x - kPeakX) * (x - kPeakX) + (y - kPeakY) * (y - kPeakY);
    return kPeakH * exp(-d2 / (2.0 * kSigmaSq));
}

__device__ inline bool zone_contains_point(
    const TerrainZonePacked& zone,
    double x,
    double y
) {
    const double dx = x - zone.center_x;
    const double dy = y - zone.center_y;
    if (zone.type == 0) {
        const double yaw = fmod(90.0 - zone.heading_deg, 360.0) * 3.14159265358979323846 / 180.0;
        const double c = cos(yaw);
        const double s = sin(yaw);
        const double local_len = dx * c + dy * s;
        const double local_wid = dx * (-s) + dy * c;
        return fabs(local_wid) <= zone.width / 2.0 && fabs(local_len) <= zone.length / 2.0;
    }
    return dx * dx + dy * dy <= zone.width * zone.width;
}

__device__ inline std::uint8_t terrain_surface_code_at(
    const TerrainSnapshotHeader& snapshot,
    const std::uint8_t* raster_surface_codes,
    const TerrainZonePacked* zones,
    double x,
    double y
) {
    for (int idx = 0; idx < snapshot.zone_count; ++idx) {
        if (zone_contains_point(zones[idx], x, y)) {
            return zones[idx].surface_code;
        }
    }

    const double lx = x - snapshot.raster_origin_x;
    const double ly = y - snapshot.raster_origin_y;
    if (lx >= 0.0 && ly >= 0.0 && snapshot.raster_resolution_m > 1.0e-9) {
        const int col = static_cast<int>(lx / snapshot.raster_resolution_m);
        const int row = static_cast<int>(ly / snapshot.raster_resolution_m);
        if (col >= 0 && col < snapshot.raster_width && row >= 0 && row < snapshot.raster_height) {
            return raster_surface_codes[row * snapshot.raster_width + col];
        }
    }

    return static_cast<std::uint8_t>(IEnvironmentModel::SurfaceType::SoftDirt);
}

__global__ void clear_depth_keys_kernel(std::uint64_t* keys, int pixel_count) {
    const int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= pixel_count) {
        return;
    }
    keys[idx] = 0xffffffffffffffffULL;
}

__global__ void raster_terrain_to_depth_batch_kernel(
    const gpu::VisualRenderRequest* requests,
    int request_count,
    int pixels_per_request,
    TerrainSnapshotHeader snapshot,
    const std::uint8_t* raster_surface_codes,
    const TerrainZonePacked* zones,
    std::uint8_t* terrain_cls,
    std::uint64_t* depth_keys
) {
    const int global_pixel_index = blockIdx.x * blockDim.x + threadIdx.x;
    const int total_pixels = request_count * pixels_per_request;
    if (global_pixel_index >= total_pixels) {
        return;
    }
    terrain_cls[global_pixel_index] = 0;
    const int request_index = global_pixel_index / pixels_per_request;
    const int local_pixel_index = global_pixel_index % pixels_per_request;
    const auto request = requests[request_index];
    const int u = local_pixel_index % request.out_width;
    const int v = local_pixel_index / request.out_width;

    const double yaw_rad = deg_to_rad(90.0 - request.cam_heading_deg);
    const double pitch_rad = deg_to_rad(request.cam_pitch_deg);

    const double fwd_x = cos(yaw_rad) * cos(pitch_rad);
    const double fwd_y = sin(yaw_rad) * cos(pitch_rad);
    const double fwd_z = sin(pitch_rad);

    const double right_x = sin(yaw_rad);
    const double right_y = -cos(yaw_rad);
    const double right_z = 0.0;

    const double up_x = -cos(yaw_rad) * sin(pitch_rad);
    const double up_y = -sin(yaw_rad) * sin(pitch_rad);
    const double up_z = cos(pitch_rad);

    const double half_fov_h = deg_to_rad(request.fov_h_deg / 2.0);
    const double half_fov_v = deg_to_rad(request.fov_v_deg / 2.0);
    const double theta = (static_cast<double>(u) / max(1, request.out_width - 1)) * (2.0 * half_fov_h) - half_fov_h;
    const double phi = (static_cast<double>(v) / max(1, request.out_height - 1)) * (2.0 * half_fov_v) - half_fov_v;

    double x_cam = tan(theta);
    double y_cam = tan(phi);
    double z_cam = 1.0;
    const double inv_norm = 1.0 / sqrt(x_cam * x_cam + y_cam * y_cam + z_cam * z_cam);
    x_cam *= inv_norm;
    y_cam *= inv_norm;
    z_cam *= inv_norm;

    const double dir_x = right_x * x_cam + up_x * y_cam + fwd_x * z_cam;
    const double dir_y = right_y * x_cam + up_y * y_cam + fwd_y * z_cam;
    const double dir_z = right_z * x_cam + up_z * y_cam + fwd_z * z_cam;
    if (dir_z >= -1e-6) {
        return;
    }

    double ground_z = terrain_elevation_m(snapshot, request.cam_pos.x, request.cam_pos.y);
    double t = 0.0;
    for (int iter = 0; iter < 2; ++iter) {
        t = (ground_z - request.cam_pos.z) / dir_z;
        if (t <= 0.0) {
            break;
        }
        const double ix = request.cam_pos.x + dir_x * t;
        const double iy = request.cam_pos.y + dir_y * t;
        ground_z = terrain_elevation_m(snapshot, ix, iy);
    }
    if (t <= 0.0) {
        return;
    }

    const double ix = request.cam_pos.x + dir_x * t;
    const double iy = request.cam_pos.y + dir_y * t;
    const std::uint8_t surface_code = terrain_surface_code_at(snapshot, raster_surface_codes, zones, ix, iy);
    terrain_cls[global_pixel_index] = static_cast<std::uint8_t>(terrain_surface_to_visual_class(surface_code));
    depth_keys[global_pixel_index] = encode_depth_object_key(static_cast<float>(t), kTerrainKeyObjectIndex);
}

__global__ void raster_objects_to_depth_batch_kernel(
    const gpu::VisualRenderRequest* requests,
    const gpu::VisibleObjectPacked* objects,
    const int* object_request_indices,
    int total_object_count,
    int pixels_per_request,
    std::uint64_t* depth_keys
) {
    const int object_index = blockIdx.x * blockDim.x + threadIdx.x;
    if (object_index >= total_object_count) {
        return;
    }
    const int request_index = object_request_indices[object_index];
    const auto request = requests[request_index];
    const auto& obj = objects[object_index];

    const double yaw_rad = deg_to_rad(90.0 - request.cam_heading_deg);
    const double pitch_rad = deg_to_rad(request.cam_pitch_deg);

    const double fwd_x = cos(yaw_rad) * cos(pitch_rad);
    const double fwd_y = sin(yaw_rad) * cos(pitch_rad);
    const double fwd_z = sin(pitch_rad);

    const double right_x = sin(yaw_rad);
    const double right_y = -cos(yaw_rad);
    const double right_z = 0.0;

    const double up_x = -cos(yaw_rad) * sin(pitch_rad);
    const double up_y = -sin(yaw_rad) * sin(pitch_rad);
    const double up_z = cos(pitch_rad);

    const double half_fov_h = deg_to_rad(request.fov_h_deg / 2.0);
    const double half_fov_v = deg_to_rad(request.fov_v_deg / 2.0);

    const double dx = obj.x - request.cam_pos.x;
    const double dy = obj.y - request.cam_pos.y;
    const double dz = obj.z - request.cam_pos.z;

    const double cam_z = dx * fwd_x + dy * fwd_y + dz * fwd_z;
    const double cam_x = dx * right_x + dy * right_y + dz * right_z;
    const double cam_y = dx * up_x + dy * up_y + dz * up_z;
    if (cam_z <= 0.1) {
        return;
    }

    const double d = sqrt(dx * dx + dy * dy + dz * dz);
    const double theta = atan2(cam_x, cam_z);
    const double phi = atan2(cam_y, cam_z);
    const double alpha = atan(obj.bounding_radius / d);

    if (fabs(theta) > half_fov_h + alpha || fabs(phi) > half_fov_v + alpha) {
        return;
    }

    const double u_center = (theta + half_fov_h) / (2.0 * half_fov_h) * (request.out_width - 1);
    const double v_center = (phi + half_fov_v) / (2.0 * half_fov_v) * (request.out_height - 1);
    const double u_radius = alpha / (2.0 * half_fov_h) * (request.out_width - 1);
    const double v_radius = alpha / (2.0 * half_fov_v) * (request.out_height - 1);

    const int u0 = max(0, static_cast<int>(u_center - u_radius - 0.5));
    const int u1 = min(request.out_width - 1, static_cast<int>(u_center + u_radius + 0.5));
    const int v0 = max(0, static_cast<int>(v_center - v_radius - 0.5));
    const int v1 = min(request.out_height - 1, static_cast<int>(v_center + v_radius + 0.5));

    const float z_obj = static_cast<float>(d);
    const std::uint64_t key = encode_depth_object_key(z_obj, static_cast<std::uint32_t>(object_index));
    const int pixel_base = request_index * pixels_per_request;
    for (int v = v0; v <= v1; ++v) {
        for (int u = u0; u <= u1; ++u) {
            const double du = (static_cast<double>(u) - u_center) / fmax(u_radius, 0.5);
            const double dv = (static_cast<double>(v) - v_center) / fmax(v_radius, 0.5);
            if (du * du + dv * dv > 1.0) {
                continue;
            }
            const int pixel_index = pixel_base + v * request.out_width + u;
            atomicMin(reinterpret_cast<unsigned long long*>(&depth_keys[pixel_index]), static_cast<unsigned long long>(key));
        }
    }
}

__global__ void raster_objects_to_depth_kernel(
    gpu::VisualRenderRequest request,
    const gpu::VisibleObjectPacked* objects,
    int object_count,
    std::uint64_t* depth_keys
) {
    const int object_index = blockIdx.x * blockDim.x + threadIdx.x;
    if (object_index >= object_count) {
        return;
    }
    const auto& obj = objects[object_index];

    const double yaw_rad = deg_to_rad(90.0 - request.cam_heading_deg);
    const double pitch_rad = deg_to_rad(request.cam_pitch_deg);

    const double fwd_x = cos(yaw_rad) * cos(pitch_rad);
    const double fwd_y = sin(yaw_rad) * cos(pitch_rad);
    const double fwd_z = sin(pitch_rad);

    const double right_x = sin(yaw_rad);
    const double right_y = -cos(yaw_rad);
    const double right_z = 0.0;

    const double up_x = -cos(yaw_rad) * sin(pitch_rad);
    const double up_y = -sin(yaw_rad) * sin(pitch_rad);
    const double up_z = cos(pitch_rad);

    const double half_fov_h = deg_to_rad(request.fov_h_deg / 2.0);
    const double half_fov_v = deg_to_rad(request.fov_v_deg / 2.0);

    const double dx = obj.x - request.cam_pos.x;
    const double dy = obj.y - request.cam_pos.y;
    const double dz = obj.z - request.cam_pos.z;

    const double cam_z = dx * fwd_x + dy * fwd_y + dz * fwd_z;
    const double cam_x = dx * right_x + dy * right_y + dz * right_z;
    const double cam_y = dx * up_x + dy * up_y + dz * up_z;
    if (cam_z <= 0.1) {
        return;
    }

    const double d = sqrt(dx * dx + dy * dy + dz * dz);
    const double theta = atan2(cam_x, cam_z);
    const double phi = atan2(cam_y, cam_z);
    const double alpha = atan(obj.bounding_radius / d);

    if (fabs(theta) > half_fov_h + alpha || fabs(phi) > half_fov_v + alpha) {
        return;
    }

    const double u_center = (theta + half_fov_h) / (2.0 * half_fov_h) * (request.out_width - 1);
    const double v_center = (phi + half_fov_v) / (2.0 * half_fov_v) * (request.out_height - 1);
    const double u_radius = alpha / (2.0 * half_fov_h) * (request.out_width - 1);
    const double v_radius = alpha / (2.0 * half_fov_v) * (request.out_height - 1);

    const int u0 = max(0, static_cast<int>(u_center - u_radius - 0.5));
    const int u1 = min(request.out_width - 1, static_cast<int>(u_center + u_radius + 0.5));
    const int v0 = max(0, static_cast<int>(v_center - v_radius - 0.5));
    const int v1 = min(request.out_height - 1, static_cast<int>(v_center + v_radius + 0.5));

    const float z_obj = static_cast<float>(d);
    const std::uint64_t key = encode_depth_object_key(z_obj, static_cast<std::uint32_t>(object_index));
    for (int v = v0; v <= v1; ++v) {
        for (int u = u0; u <= u1; ++u) {
            const double du = (static_cast<double>(u) - u_center) / fmax(u_radius, 0.5);
            const double dv = (static_cast<double>(v) - v_center) / fmax(v_radius, 0.5);
            if (du * du + dv * dv > 1.0) {
                continue;
            }
            const int pixel_index = v * request.out_width + u;
            atomicMin(reinterpret_cast<unsigned long long*>(&depth_keys[pixel_index]), static_cast<unsigned long long>(key));
        }
    }
}

__global__ void resolve_depth_keys_batch_kernel(
    const gpu::VisualRenderRequest* requests,
    const gpu::VisibleObjectPacked* objects,
    const std::uint64_t* depth_keys,
    const std::uint8_t* terrain_cls,
    int request_count,
    int pixels_per_request,
    float* output
) {
    const int global_pixel_index = blockIdx.x * blockDim.x + threadIdx.x;
    const int total_pixels = request_count * pixels_per_request;
    if (global_pixel_index >= total_pixels) {
        return;
    }
    const int request_index = global_pixel_index / pixels_per_request;
    const int local_pixel_index = global_pixel_index % pixels_per_request;
    const auto request = requests[request_index];

    float* out = output + static_cast<std::size_t>(global_pixel_index) * static_cast<std::size_t>(arb::ARB_CHANNELS);
    write_default_pixel(out);

    const std::uint64_t key = depth_keys[global_pixel_index];
    if (key == 0xffffffffffffffffULL) {
        return;
    }

    const auto object_index = decode_object_index_from_key(key);
    if (object_index == kTerrainKeyObjectIndex) {
        write_terrain_pixel(out, decode_depth_from_key(key), static_cast<int>(terrain_cls[global_pixel_index]));
        return;
    }

    const auto& obj = objects[object_index];
    const float z_obj = decode_depth_from_key(key);
    const double dx = obj.x - request.cam_pos.x;
    const double dy = obj.y - request.cam_pos.y;
    const double dz = obj.z - request.cam_pos.z;
    const double d = sqrt(dx * dx + dy * dy + dz * dz);
    const float alpha = static_cast<float>(atan(obj.bounding_radius / d));
    const double dot = dx * obj.vx + dy * obj.vy + dz * obj.vz;
    const float vr = static_cast<float>(dot / (d + 1.0e-6));
    (void)local_pixel_index;
    write_object_pixel(out, z_obj, alpha, obj.cls, obj.team, vr);
}

__global__ void resolve_depth_keys_kernel(
    gpu::VisualRenderRequest request,
    const gpu::VisibleObjectPacked* objects,
    const std::uint64_t* depth_keys,
    float* output
) {
    const int u = blockIdx.x * blockDim.x + threadIdx.x;
    const int v = blockIdx.y * blockDim.y + threadIdx.y;
    if (u >= request.out_width || v >= request.out_height) {
        return;
    }

    const int pixel_index = v * request.out_width + u;
    float* out = output + static_cast<std::size_t>(pixel_index) * static_cast<std::size_t>(arb::ARB_CHANNELS);
    write_default_pixel(out);

    const std::uint64_t key = depth_keys[pixel_index];
    if (key == 0xffffffffffffffffULL) {
        return;
    }

    const auto& obj = objects[decode_object_index_from_key(key)];
    const float z_obj = decode_depth_from_key(key);
    const double dx = obj.x - request.cam_pos.x;
    const double dy = obj.y - request.cam_pos.y;
    const double dz = obj.z - request.cam_pos.z;
    const double d = sqrt(dx * dx + dy * dy + dz * dz);
    const float alpha = static_cast<float>(atan(obj.bounding_radius / d));
    const double dot = dx * obj.vx + dy * obj.vy + dz * obj.vz;
    const float vr = static_cast<float>(dot / (d + 1.0e-6));
    write_object_pixel(out, z_obj, alpha, obj.cls, obj.team, vr);
}

bool ensure_cache_capacity(
    std::size_t request_count,
    std::size_t object_count,
    std::size_t pixel_count,
    std::size_t raster_surface_count,
    std::size_t zone_count
) {
    if (request_count > g_cache.request_capacity) {
        if (g_cache.d_requests != nullptr) {
            cudaFree(g_cache.d_requests);
            g_cache.d_requests = nullptr;
        }
        if (cudaMalloc(&g_cache.d_requests, request_count * sizeof(gpu::VisualRenderRequest)) != cudaSuccess) {
            return false;
        }
        g_cache.request_capacity = request_count;
    }
    if (object_count > g_cache.object_capacity) {
        if (g_cache.d_objects != nullptr) {
            cudaFree(g_cache.d_objects);
            g_cache.d_objects = nullptr;
        }
        if (g_cache.d_object_request_indices != nullptr) {
            cudaFree(g_cache.d_object_request_indices);
            g_cache.d_object_request_indices = nullptr;
        }
        if (cudaMalloc(&g_cache.d_objects, object_count * sizeof(gpu::VisibleObjectPacked)) != cudaSuccess) {
            return false;
        }
        if (cudaMalloc(&g_cache.d_object_request_indices, object_count * sizeof(int)) != cudaSuccess) {
            return false;
        }
        g_cache.object_capacity = object_count;
    }
    if (pixel_count > g_cache.pixel_capacity) {
        if (g_cache.d_keys != nullptr) {
            cudaFree(g_cache.d_keys);
            g_cache.d_keys = nullptr;
        }
        if (g_cache.d_terrain_cls != nullptr) {
            cudaFree(g_cache.d_terrain_cls);
            g_cache.d_terrain_cls = nullptr;
        }
        if (g_cache.d_output != nullptr) {
            cudaFree(g_cache.d_output);
            g_cache.d_output = nullptr;
        }
        if (cudaMalloc(&g_cache.d_keys, pixel_count * sizeof(std::uint64_t)) != cudaSuccess) {
            return false;
        }
        if (cudaMalloc(&g_cache.d_terrain_cls, pixel_count * sizeof(std::uint8_t)) != cudaSuccess) {
            return false;
        }
        if (cudaMalloc(&g_cache.d_output, pixel_count * static_cast<std::size_t>(arb::ARB_CHANNELS) * sizeof(float)) != cudaSuccess) {
            return false;
        }
        g_cache.pixel_capacity = pixel_count;
    }
    if (raster_surface_count > g_cache.raster_surface_capacity) {
        if (g_cache.d_raster_surface_codes != nullptr) {
            cudaFree(g_cache.d_raster_surface_codes);
            g_cache.d_raster_surface_codes = nullptr;
        }
        if (cudaMalloc(&g_cache.d_raster_surface_codes, raster_surface_count * sizeof(std::uint8_t)) != cudaSuccess) {
            return false;
        }
        g_cache.raster_surface_capacity = raster_surface_count;
    }
    if (zone_count > g_cache.zone_capacity) {
        if (g_cache.d_zones != nullptr) {
            cudaFree(g_cache.d_zones);
            g_cache.d_zones = nullptr;
        }
        if (cudaMalloc(&g_cache.d_zones, zone_count * sizeof(TerrainZonePacked)) != cudaSuccess) {
            return false;
        }
        g_cache.zone_capacity = zone_count;
    }
    return true;
}

std::vector<float> render_object_only_cpu(
    const gpu::VisualRenderRequest& request,
    const std::vector<gpu::VisibleObjectPacked>& objects
) {
    std::vector<float> out(
        static_cast<std::size_t>(request.out_height) *
        static_cast<std::size_t>(request.out_width) *
        static_cast<std::size_t>(arb::ARB_CHANNELS),
        0.0f
    );

    for (int v = 0; v < request.out_height; ++v) {
        for (int u = 0; u < request.out_width; ++u) {
            float* pixel = out.data() + (static_cast<std::size_t>(v) * static_cast<std::size_t>(request.out_width) + static_cast<std::size_t>(u)) * static_cast<std::size_t>(arb::ARB_CHANNELS);
            write_default_pixel(pixel);
        }
    }

    const double yaw_rad = deg_to_rad(90.0 - request.cam_heading_deg);
    const double pitch_rad = deg_to_rad(request.cam_pitch_deg);

    const double fwd_x = std::cos(yaw_rad) * std::cos(pitch_rad);
    const double fwd_y = std::sin(yaw_rad) * std::cos(pitch_rad);
    const double fwd_z = std::sin(pitch_rad);

    const double right_x = std::sin(yaw_rad);
    const double right_y = -std::cos(yaw_rad);
    const double right_z = 0.0;

    const double up_x = -std::cos(yaw_rad) * std::sin(pitch_rad);
    const double up_y = -std::sin(yaw_rad) * std::sin(pitch_rad);
    const double up_z = std::cos(pitch_rad);

    const double half_fov_h = deg_to_rad(request.fov_h_deg / 2.0);
    const double half_fov_v = deg_to_rad(request.fov_v_deg / 2.0);

    for (int v = 0; v < request.out_height; ++v) {
        for (int u = 0; u < request.out_width; ++u) {
            float best_z = kDefaultZ;
            float best_alpha = 0.0f;
            float best_vr = 0.0f;
            int best_cls = 3;
            int best_team = 0;

            for (const auto& obj : objects) {
                const double dx = obj.x - request.cam_pos.x;
                const double dy = obj.y - request.cam_pos.y;
                const double dz = obj.z - request.cam_pos.z;

                const double cam_z = dx * fwd_x + dy * fwd_y + dz * fwd_z;
                const double cam_x = dx * right_x + dy * right_y + dz * right_z;
                const double cam_y = dx * up_x + dy * up_y + dz * up_z;
                if (cam_z <= 0.1) {
                    continue;
                }

                const double d = std::sqrt(dx * dx + dy * dy + dz * dz);
                const double theta = std::atan2(cam_x, cam_z);
                const double phi = std::atan2(cam_y, cam_z);
                const double alpha = std::atan(obj.bounding_radius / d);
                if (std::fabs(theta) > half_fov_h + alpha || std::fabs(phi) > half_fov_v + alpha) {
                    continue;
                }

                const double u_center = (theta + half_fov_h) / (2.0 * half_fov_h) * (request.out_width - 1);
                const double v_center = (phi + half_fov_v) / (2.0 * half_fov_v) * (request.out_height - 1);
                const double u_radius = alpha / (2.0 * half_fov_h) * (request.out_width - 1);
                const double v_radius = alpha / (2.0 * half_fov_v) * (request.out_height - 1);

                const double du = (static_cast<double>(u) - u_center) / std::max(u_radius, 0.5);
                const double dv = (static_cast<double>(v) - v_center) / std::max(v_radius, 0.5);
                if (du * du + dv * dv > 1.0) {
                    continue;
                }

                const float z_obj = static_cast<float>(d);
                if (z_obj < best_z) {
                    best_z = z_obj;
                    best_alpha = static_cast<float>(alpha);
                    best_cls = obj.cls;
                    best_team = obj.team;
                    const double dot = dx * obj.vx + dy * obj.vy + dz * obj.vz;
                    best_vr = static_cast<float>(dot / (d + 1.0e-6));
                }
            }

            if (best_z < kDefaultZ) {
                float* pixel = out.data() + (static_cast<std::size_t>(v) * static_cast<std::size_t>(request.out_width) + static_cast<std::size_t>(u)) * static_cast<std::size_t>(arb::ARB_CHANNELS);
                write_object_pixel(pixel, best_z, best_alpha, best_cls, best_team, best_vr);
            }
        }
    }
    return out;
}

bool run_visual_experiment_batch_cuda_impl(
    const std::vector<gpu::VisualRenderRequest>& requests,
    const std::vector<std::vector<gpu::VisibleObjectPacked>>& objects_batch,
    const DefaultEnvironmentSnapshot* terrain_snapshot,
    bool copy_output_to_host,
    std::vector<float>* host_output
) {
    g_last_stats = gpu::VisualExperimentStats{};
    g_last_output_device_ptr = nullptr;
    g_last_output_float_count = 0;
    if (host_output != nullptr) {
        host_output->clear();
    }
    if (requests.empty() || requests.size() != objects_batch.size()) {
        return false;
    }

    const int out_height = requests.front().out_height;
    const int out_width = requests.front().out_width;
    for (const auto& request : requests) {
        if (request.out_height != out_height || request.out_width != out_width) {
            return false;
        }
        if (terrain_snapshot == nullptr && request.include_terrain) {
            return false;
        }
        if (terrain_snapshot != nullptr && !request.include_terrain) {
            return false;
        }
    }

    int device_count = 0;
    if (cudaGetDeviceCount(&device_count) != cudaSuccess || device_count <= 0) {
        return false;
    }
    g_last_stats.used_cuda = true;

    const std::size_t request_count = requests.size();
    const std::size_t pixels_per_request =
        static_cast<std::size_t>(out_height) * static_cast<std::size_t>(out_width);
    const std::size_t total_pixels = request_count * pixels_per_request;
    const std::size_t output_size = total_pixels * static_cast<std::size_t>(arb::ARB_CHANNELS);

    std::size_t total_object_count = 0;
    for (const auto& objects : objects_batch) {
        total_object_count += objects.size();
    }

    std::vector<gpu::VisibleObjectPacked> flat_objects;
    flat_objects.reserve(total_object_count);
    std::vector<int> object_request_indices;
    object_request_indices.reserve(total_object_count);
    for (std::size_t request_index = 0; request_index < request_count; ++request_index) {
        for (const auto& object : objects_batch[request_index]) {
            flat_objects.push_back(object);
            object_request_indices.push_back(static_cast<int>(request_index));
        }
    }

    const std::size_t request_bytes = request_count * sizeof(gpu::VisualRenderRequest);
    const std::size_t object_bytes = total_object_count * sizeof(gpu::VisibleObjectPacked);
    const std::size_t object_request_bytes = total_object_count * sizeof(int);
    const std::size_t output_bytes = output_size * sizeof(float);
    const std::size_t raster_surface_count = terrain_snapshot != nullptr
        ? terrain_snapshot->raster.surface_codes.size()
        : 0u;
    const std::size_t zone_count = terrain_snapshot != nullptr
        ? terrain_snapshot->zones.size()
        : 0u;
    std::vector<TerrainZonePacked> packed_zones;
    if (terrain_snapshot != nullptr) {
        packed_zones.reserve(zone_count);
        for (const auto& zone : terrain_snapshot->zones) {
            TerrainZonePacked packed{};
            packed.center_x = zone.center_x;
            packed.center_y = zone.center_y;
            packed.width = zone.width;
            packed.length = zone.length;
            packed.heading_deg = zone.heading_deg;
            packed.type = zone.type;
            packed.surface_code = zone.surface_code;
            packed_zones.push_back(packed);
        }
    }

    cudaError_t status = cudaSuccess;
    cudaEvent_t ev_h2d_start = nullptr;
    cudaEvent_t ev_h2d_end = nullptr;
    cudaEvent_t ev_kernel_end = nullptr;
    cudaEvent_t ev_d2h_end = nullptr;
    cudaEventCreate(&ev_h2d_start);
    cudaEventCreate(&ev_h2d_end);
    cudaEventCreate(&ev_kernel_end);
    cudaEventCreate(&ev_d2h_end);
    cudaEventRecord(ev_h2d_start);

    if (!ensure_cache_capacity(
            request_count,
            total_object_count,
            total_pixels,
            raster_surface_count,
            zone_count)) {
        cudaEventDestroy(ev_h2d_start);
        cudaEventDestroy(ev_h2d_end);
        cudaEventDestroy(ev_kernel_end);
        cudaEventDestroy(ev_d2h_end);
        return false;
    }

    status = cudaMemcpy(g_cache.d_requests, requests.data(), request_bytes, cudaMemcpyHostToDevice);
    if (status == cudaSuccess && object_bytes > 0) {
        status = cudaMemcpy(g_cache.d_objects, flat_objects.data(), object_bytes, cudaMemcpyHostToDevice);
    }
    if (status == cudaSuccess && object_request_bytes > 0) {
        status = cudaMemcpy(
            g_cache.d_object_request_indices,
            object_request_indices.data(),
            object_request_bytes,
            cudaMemcpyHostToDevice
        );
    }
    TerrainSnapshotHeader terrain_header{};
    if (status == cudaSuccess && terrain_snapshot != nullptr) {
        terrain_header.flat_terrain = terrain_snapshot->flat_terrain ? 1 : 0;
        terrain_header.raster_origin_x = terrain_snapshot->raster.origin_x;
        terrain_header.raster_origin_y = terrain_snapshot->raster.origin_y;
        terrain_header.raster_resolution_m = terrain_snapshot->raster.resolution_m;
        terrain_header.raster_width = terrain_snapshot->raster.width;
        terrain_header.raster_height = terrain_snapshot->raster.height;
        terrain_header.zone_count = static_cast<int>(terrain_snapshot->zones.size());
        if (raster_surface_count > 0) {
            status = cudaMemcpy(
                g_cache.d_raster_surface_codes,
                terrain_snapshot->raster.surface_codes.data(),
                raster_surface_count * sizeof(std::uint8_t),
                cudaMemcpyHostToDevice
            );
        }
        if (status == cudaSuccess && zone_count > 0) {
            status = cudaMemcpy(
                g_cache.d_zones,
                packed_zones.data(),
                zone_count * sizeof(TerrainZonePacked),
                cudaMemcpyHostToDevice
            );
        }
    }
    if (status != cudaSuccess) {
        cudaEventDestroy(ev_h2d_start);
        cudaEventDestroy(ev_h2d_end);
        cudaEventDestroy(ev_kernel_end);
        cudaEventDestroy(ev_d2h_end);
        return false;
    }
    cudaEventRecord(ev_h2d_end);

    const int clear_threads = 256;
    const int clear_blocks = static_cast<int>(
        (total_pixels + static_cast<std::size_t>(clear_threads) - 1) /
        static_cast<std::size_t>(clear_threads)
    );
    clear_depth_keys_kernel<<<clear_blocks, clear_threads>>>(
        g_cache.d_keys,
        static_cast<int>(total_pixels)
    );
    if (terrain_snapshot != nullptr) {
        raster_terrain_to_depth_batch_kernel<<<clear_blocks, clear_threads>>>(
            g_cache.d_requests,
            static_cast<int>(request_count),
            static_cast<int>(pixels_per_request),
            terrain_header,
            g_cache.d_raster_surface_codes,
            g_cache.d_zones,
            g_cache.d_terrain_cls,
            g_cache.d_keys
        );
    }

    const int object_threads = 128;
    const int object_blocks = static_cast<int>(
        (total_object_count + static_cast<std::size_t>(object_threads) - 1) /
        static_cast<std::size_t>(object_threads)
    );
    if (object_blocks > 0) {
        raster_objects_to_depth_batch_kernel<<<object_blocks, object_threads>>>(
            g_cache.d_requests,
            g_cache.d_objects,
            g_cache.d_object_request_indices,
            static_cast<int>(total_object_count),
            static_cast<int>(pixels_per_request),
            g_cache.d_keys
        );
    }

    const int resolve_threads = 256;
    const int resolve_blocks = static_cast<int>(
        (total_pixels + static_cast<std::size_t>(resolve_threads) - 1) /
        static_cast<std::size_t>(resolve_threads)
    );
    resolve_depth_keys_batch_kernel<<<resolve_blocks, resolve_threads>>>(
        g_cache.d_requests,
        g_cache.d_objects,
        g_cache.d_keys,
        g_cache.d_terrain_cls,
        static_cast<int>(request_count),
        static_cast<int>(pixels_per_request),
        g_cache.d_output
    );
    cudaEventRecord(ev_kernel_end);

    status = cudaGetLastError();
    if (status == cudaSuccess) {
        status = cudaDeviceSynchronize();
    }
    double d2h_wall_ms = 0.0;

    if (status == cudaSuccess && copy_output_to_host && host_output != nullptr) {
        host_output->assign(output_size, 0.0f);
        const auto d2h_start = std::chrono::steady_clock::now();
        status = cudaMemcpy(host_output->data(), g_cache.d_output, output_bytes, cudaMemcpyDeviceToHost);
        const auto d2h_end = std::chrono::steady_clock::now();
        d2h_wall_ms = std::chrono::duration<double, std::milli>(d2h_end - d2h_start).count();
        if (status == cudaSuccess) {
            cudaEventRecord(ev_d2h_end);
        }
    } else {
        cudaEventRecord(ev_d2h_end);
    }

    if (status != cudaSuccess) {
        cudaEventDestroy(ev_h2d_start);
        cudaEventDestroy(ev_h2d_end);
        cudaEventDestroy(ev_kernel_end);
        cudaEventDestroy(ev_d2h_end);
        g_last_output_device_ptr = nullptr;
        g_last_output_float_count = 0;
        return false;
    }

    float h2d_ms = 0.0f;
    float kernel_ms = 0.0f;
    cudaEventElapsedTime(&h2d_ms, ev_h2d_start, ev_h2d_end);
    cudaEventElapsedTime(&kernel_ms, ev_h2d_end, ev_kernel_end);
    g_last_stats.host_to_device_ms = static_cast<double>(h2d_ms);
    g_last_stats.kernel_ms = static_cast<double>(kernel_ms);
    g_last_stats.device_to_host_ms = copy_output_to_host ? d2h_wall_ms : 0.0;
    g_last_stats.total_ms =
        g_last_stats.host_to_device_ms +
        g_last_stats.kernel_ms +
        g_last_stats.device_to_host_ms;
    g_last_output_device_ptr = g_cache.d_output;
    g_last_output_float_count = output_size;

    cudaEventDestroy(ev_h2d_start);
    cudaEventDestroy(ev_h2d_end);
    cudaEventDestroy(ev_kernel_end);
    cudaEventDestroy(ev_d2h_end);
    return true;
}

}  // namespace

namespace gpu::detail {

VisualExperimentStats last_visual_experiment_cuda_stats() {
    return g_last_stats;
}

const void* last_visual_output_device_ptr_cuda() {
    return g_last_output_device_ptr;
}

std::size_t last_visual_output_float_count_cuda() {
    return g_last_output_float_count;
}

DeviceInfo probe_cuda_device() {
    DeviceInfo info{};
    info.cuda_runtime_built = true;

    const cudaError_t init_status = cudaFree(nullptr);
    if (init_status != cudaSuccess && init_status != cudaErrorCudartUnloading) {
        info.error_message = cudaGetErrorString(init_status);
        return info;
    }

    int runtime_version = 0;
    if (cudaRuntimeGetVersion(&runtime_version) == cudaSuccess) {
        info.runtime_version = runtime_version;
    }

    int device_count = 0;
    const cudaError_t count_status = cudaGetDeviceCount(&device_count);
    if (count_status != cudaSuccess) {
        info.error_message = cudaGetErrorString(count_status);
        return info;
    }

    info.cuda_runtime_available = device_count > 0;
    info.device_count = device_count;
    if (device_count <= 0) {
        return info;
    }

    int active_device = 0;
    if (cudaGetDevice(&active_device) != cudaSuccess) {
        active_device = 0;
    }
    info.active_device = active_device;

    cudaDeviceProp prop{};
    const cudaError_t prop_status = cudaGetDeviceProperties(&prop, active_device);
    if (prop_status != cudaSuccess) {
        info.error_message = cudaGetErrorString(prop_status);
        return info;
    }

    info.device_name = prop.name;
    info.compute_major = prop.major;
    info.compute_minor = prop.minor;
    info.total_global_mem_bytes = static_cast<std::size_t>(prop.totalGlobalMem);

    std::size_t free_bytes = 0;
    std::size_t total_bytes = 0;
    if (cudaMemGetInfo(&free_bytes, &total_bytes) == cudaSuccess) {
        info.free_global_mem_bytes = free_bytes;
        if (total_bytes > 0) {
            info.total_global_mem_bytes = total_bytes;
        }
    }

    return info;
}

std::vector<float> render_visual_experiment_cuda(
    const gpu::VisualRenderRequest& request,
    const std::vector<gpu::VisibleObjectPacked>& objects
) {
    g_last_stats = gpu::VisualExperimentStats{};
    g_last_output_device_ptr = nullptr;
    g_last_output_float_count = 0;
    const std::size_t output_size =
        static_cast<std::size_t>(request.out_height) *
        static_cast<std::size_t>(request.out_width) *
        static_cast<std::size_t>(arb::ARB_CHANNELS);

    if (request.include_terrain) {
        return render_object_only_cpu(request, objects);
    }

    int device_count = 0;
    if (cudaGetDeviceCount(&device_count) != cudaSuccess || device_count <= 0) {
        return render_object_only_cpu(request, objects);
    }
    g_last_stats.used_cuda = true;

    gpu::VisibleObjectPacked* d_objects = nullptr;
    float* d_output = nullptr;
    std::vector<float> out(output_size, 0.0f);

    const std::size_t object_bytes = objects.size() * sizeof(gpu::VisibleObjectPacked);
    const std::size_t output_bytes = output_size * sizeof(float);
    const std::size_t pixel_count = static_cast<std::size_t>(request.out_height) * static_cast<std::size_t>(request.out_width);

    cudaError_t status = cudaSuccess;
    cudaEvent_t ev_h2d_start = nullptr;
    cudaEvent_t ev_h2d_end = nullptr;
    cudaEvent_t ev_kernel_end = nullptr;
    cudaEvent_t ev_d2h_end = nullptr;
    cudaEventCreate(&ev_h2d_start);
    cudaEventCreate(&ev_h2d_end);
    cudaEventCreate(&ev_kernel_end);
    cudaEventCreate(&ev_d2h_end);
    cudaEventRecord(ev_h2d_start);
    if (!ensure_cache_capacity(1, objects.size(), pixel_count, 0, 0)) {
        cudaEventDestroy(ev_h2d_start);
        cudaEventDestroy(ev_h2d_end);
        cudaEventDestroy(ev_kernel_end);
        cudaEventDestroy(ev_d2h_end);
        return render_object_only_cpu(request, objects);
    }
    if (object_bytes > 0) {
        d_objects = g_cache.d_objects;
        status = cudaMemcpy(d_objects, objects.data(), object_bytes, cudaMemcpyHostToDevice);
        if (status != cudaSuccess) {
            cudaEventDestroy(ev_h2d_start);
            cudaEventDestroy(ev_h2d_end);
            cudaEventDestroy(ev_kernel_end);
            cudaEventDestroy(ev_d2h_end);
            return render_object_only_cpu(request, objects);
        }
    }

    d_output = g_cache.d_output;
    auto* d_keys = g_cache.d_keys;
    cudaEventRecord(ev_h2d_end);

    const int key_threads = 256;
    const int key_blocks = static_cast<int>((pixel_count + static_cast<std::size_t>(key_threads) - 1) / static_cast<std::size_t>(key_threads));
    clear_depth_keys_kernel<<<key_blocks, key_threads>>>(d_keys, static_cast<int>(pixel_count));

    const int object_threads = 128;
    const int object_blocks = (static_cast<int>(objects.size()) + object_threads - 1) / object_threads;
    if (object_blocks > 0) {
        raster_objects_to_depth_kernel<<<object_blocks, object_threads>>>(
            request,
            d_objects,
            static_cast<int>(objects.size()),
            d_keys
        );
    }

    const dim3 block(16, 16);
    const dim3 grid(
        static_cast<unsigned int>((request.out_width + block.x - 1) / block.x),
        static_cast<unsigned int>((request.out_height + block.y - 1) / block.y)
    );
    resolve_depth_keys_kernel<<<grid, block>>>(
        request,
        d_objects,
        d_keys,
        d_output
    );
    cudaEventRecord(ev_kernel_end);
    status = cudaGetLastError();
    if (status == cudaSuccess) {
        status = cudaDeviceSynchronize();
    }
    double d2h_wall_ms = 0.0;
    if (status == cudaSuccess) {
        const auto d2h_start = std::chrono::steady_clock::now();
        status = cudaMemcpy(out.data(), d_output, output_bytes, cudaMemcpyDeviceToHost);
        const auto d2h_end = std::chrono::steady_clock::now();
        d2h_wall_ms = std::chrono::duration<double, std::milli>(d2h_end - d2h_start).count();
        cudaEventRecord(ev_d2h_end);
    }

    if (status != cudaSuccess) {
        cudaEventDestroy(ev_h2d_start);
        cudaEventDestroy(ev_h2d_end);
        cudaEventDestroy(ev_kernel_end);
        cudaEventDestroy(ev_d2h_end);
        return render_object_only_cpu(request, objects);
    }

    float h2d_ms = 0.0f;
    float kernel_ms = 0.0f;
    cudaEventElapsedTime(&h2d_ms, ev_h2d_start, ev_h2d_end);
    cudaEventElapsedTime(&kernel_ms, ev_h2d_end, ev_kernel_end);
    g_last_stats.host_to_device_ms = static_cast<double>(h2d_ms);
    g_last_stats.kernel_ms = static_cast<double>(kernel_ms);
    g_last_stats.device_to_host_ms = d2h_wall_ms;
    g_last_stats.total_ms = g_last_stats.host_to_device_ms + g_last_stats.kernel_ms + g_last_stats.device_to_host_ms;
    g_last_output_device_ptr = g_cache.d_output;
    g_last_output_float_count = output_size;

    cudaEventDestroy(ev_h2d_start);
    cudaEventDestroy(ev_h2d_end);
    cudaEventDestroy(ev_kernel_end);
    cudaEventDestroy(ev_d2h_end);
    return out;
}

std::vector<float> render_visual_experiment_batch_cuda(
    const std::vector<gpu::VisualRenderRequest>& requests,
    const std::vector<std::vector<gpu::VisibleObjectPacked>>& objects_batch
) {
    std::vector<float> out;
    if (!run_visual_experiment_batch_cuda_impl(requests, objects_batch, nullptr, true, &out)) {
        return {};
    }
    return out;
}

std::vector<float> render_visual_experiment_batch_cuda_with_terrain(
    const std::vector<gpu::VisualRenderRequest>& requests,
    const std::vector<std::vector<gpu::VisibleObjectPacked>>& objects_batch,
    const DefaultEnvironmentSnapshot& snapshot
) {
    std::vector<float> out;
    if (!run_visual_experiment_batch_cuda_impl(requests, objects_batch, &snapshot, true, &out)) {
        return {};
    }
    return out;
}

bool render_visual_experiment_batch_cuda_device_resident(
    const std::vector<gpu::VisualRenderRequest>& requests,
    const std::vector<std::vector<gpu::VisibleObjectPacked>>& objects_batch
) {
    return run_visual_experiment_batch_cuda_impl(requests, objects_batch, nullptr, false, nullptr);
}

bool render_visual_experiment_batch_cuda_with_terrain_device_resident(
    const std::vector<gpu::VisualRenderRequest>& requests,
    const std::vector<std::vector<gpu::VisibleObjectPacked>>& objects_batch,
    const DefaultEnvironmentSnapshot& snapshot
) {
    return run_visual_experiment_batch_cuda_impl(requests, objects_batch, &snapshot, false, nullptr);
}

}  // namespace gpu::detail
