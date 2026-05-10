#pragma once

#include <flecs.h>
#include <cmath>
#include <algorithm>
#include <vector>
#include <stdexcept>
#include "components/visual/visual_sensor.h"
#include "components/basic/common.h"
#include "core/interfaces/environment_model.h"

namespace arb {

/**
 * RetinaCell
 * Single cell in the Angular Retina Buffer
 */
struct RetinaCell {
    float z = 1e10f;           // Nearest depth (meters)
    float depth_log = 0.0f;    // log(1+d)
    float inv_depth = 0.0f;    // 1/(d+eps)
    float coverage = 0.0f;     // Area fraction [0,1]
    float ang_size = 0.0f;     // Angular radius
    int cls = 3;               // Class: 0=Air, 1=Ground, 2=Sea, 3=Terrain
    int team = 0;              // -1=Enemy, 0=Neutral, +1=Friendly
    float vr = 0.0f;           // Radial velocity
    float conf = 0.0f;         // Confidence
};

inline void write_retina_cell_to_tensor(const RetinaCell& c, float* out);

/**
 * RetinaBuffer
 * The full ARB output buffer
 */
struct RetinaBuffer {
    RetinaCell cells[ARB_HEIGHT][ARB_WIDTH];
    
    void clear() {
        for (int v = 0; v < ARB_HEIGHT; ++v) {
            for (int u = 0; u < ARB_WIDTH; ++u) {
                cells[v][u] = RetinaCell{};
            }
        }
    }
    
    // Convert to flat tensor [H, W, C]
    void to_tensor(float* out) const {
        for (int v = 0; v < ARB_HEIGHT; ++v) {
            for (int u = 0; u < ARB_WIDTH; ++u) {
                write_retina_cell_to_tensor(cells[v][u], out + (v * ARB_WIDTH + u) * ARB_CHANNELS);
            }
        }
    }
};

inline void write_retina_cell_to_tensor(const RetinaCell& c, float* out) {
    out[CH_DEPTH_LOG] = c.depth_log;
    out[CH_INV_DEPTH] = c.inv_depth;
    out[CH_COVERAGE] = c.coverage;
    out[CH_ANG_SIZE] = c.ang_size;
    out[CH_CLASS_AIR] = (c.cls == 0) ? 1.0f : 0.0f;
    out[CH_CLASS_GROUND] = (c.cls == 1) ? 1.0f : 0.0f;
    out[CH_CLASS_SEA] = (c.cls == 2) ? 1.0f : 0.0f;
    out[CH_CLASS_TERRAIN] = (c.cls == 3) ? 1.0f : 0.0f;
    out[CH_TEAM] = static_cast<float>(c.team);
    out[CH_VEL_RADIAL] = c.vr;
}

/**
 * VisibleObject
 * Temporary structure for objects to be rendered
 */
struct VisibleObject {
    double x, y, z;           // World position
    double vx, vy, vz;        // World velocity
    double bounding_radius;
    int cls;
    int team;
};

/**
 * Render the Angular Retina Buffer
 * 
 * @param cam_pos Camera position (world)
 * @param cam_heading Camera heading (degrees, 0=North)
 * @param cam_pitch Camera pitch (degrees)
 * @param fov_h Horizontal FOV (degrees)
 * @param fov_v Vertical FOV (degrees)
 * @param objects Visible objects to render
 * @param env Environment model for terrain
 * @param out Output buffer
 */
inline void render_retina(
    const Math::Vector3& cam_pos,
    double cam_heading,
    double cam_pitch,
    double fov_h,
    double fov_v,
    const std::vector<VisibleObject>& objects,
    IEnvironmentModel* env,
    RetinaBuffer& out
) {
    out.clear();
    
    // Convert heading to radians (0=North -> math convention)
    double yaw_rad = Math::to_radians(90.0 - cam_heading);
    double pitch_rad = Math::to_radians(cam_pitch);
    
    // Camera forward vector
    double fwd_x = std::cos(yaw_rad) * std::cos(pitch_rad);
    double fwd_y = std::sin(yaw_rad) * std::cos(pitch_rad);
    double fwd_z = std::sin(pitch_rad);
    
    // Camera right vector (simplified: ignore roll)
    double right_x = std::sin(yaw_rad);
    double right_y = -std::cos(yaw_rad);
    double right_z = 0.0;
    
    // Camera up vector
    double up_x = -std::cos(yaw_rad) * std::sin(pitch_rad);
    double up_y = -std::sin(yaw_rad) * std::sin(pitch_rad);
    double up_z = std::cos(pitch_rad);
    
    // FOV in radians
    double half_fov_h = Math::to_radians(fov_h / 2.0);
    double half_fov_v = Math::to_radians(fov_v / 2.0);
    
    // === PASS 1: Terrain / Runway Surface ===
    // Ray-cast each ARB cell to the terrain to provide a visual cue for ground/runway alignment.
    // This is intentionally low-res (ARB 48x96) and is only computed when the caller requests
    // ARB output.
    if (env) {
        // Precompute tan(theta/phi) per pixel for speed.
        double tan_theta[ARB_WIDTH];
        double tan_phi[ARB_HEIGHT];

        for (int u = 0; u < ARB_WIDTH; ++u) {
            double theta = (static_cast<double>(u) / std::max(1, ARB_WIDTH - 1)) * (2.0 * half_fov_h) - half_fov_h;
            tan_theta[u] = std::tan(theta);
        }
        for (int v = 0; v < ARB_HEIGHT; ++v) {
            double phi = (static_cast<double>(v) / std::max(1, ARB_HEIGHT - 1)) * (2.0 * half_fov_v) - half_fov_v;
            tan_phi[v] = std::tan(phi);
        }

        // Seed ground elevation near the camera and refine per-pixel with a tiny fixed-point iteration.
        double ground_z_seed = env->get_terrain_elevation(cam_pos.x, cam_pos.y);

        for (int v = 0; v < ARB_HEIGHT; ++v) {
            for (int u = 0; u < ARB_WIDTH; ++u) {
                // Build a unit direction in camera space: (tan(theta), tan(phi), 1).
                double x_cam = tan_theta[u];
                double y_cam = tan_phi[v];
                double z_cam = 1.0;

                double inv_norm = 1.0 / std::sqrt(x_cam * x_cam + y_cam * y_cam + z_cam * z_cam);
                x_cam *= inv_norm;
                y_cam *= inv_norm;
                z_cam *= inv_norm;

                // Transform to world space using camera basis vectors.
                double dir_x = right_x * x_cam + up_x * y_cam + fwd_x * z_cam;
                double dir_y = right_y * x_cam + up_y * y_cam + fwd_y * z_cam;
                double dir_z = right_z * x_cam + up_z * y_cam + fwd_z * z_cam;

                // Only rays pointing downward can intersect the terrain.
                if (dir_z >= -1e-6) continue;

                double ground_z = ground_z_seed;
                double t = 0.0;

                // 2-step fixed-point refinement: z depends on (x,y), which depends on t.
                for (int iter = 0; iter < 2; ++iter) {
                    t = (ground_z - cam_pos.z) / dir_z;  // dir_z < 0
                    if (t <= 0.0) break;
                    double ix = cam_pos.x + dir_x * t;
                    double iy = cam_pos.y + dir_y * t;
                    ground_z = env->get_terrain_elevation(ix, iy);
                }

                if (t <= 0.0) continue;

                double ix = cam_pos.x + dir_x * t;
                double iy = cam_pos.y + dir_y * t;

                const auto cell = env->get_terrain_at(ix, iy);

                int cls = 3; // Terrain by default
                switch (cell.type) {
                    case IEnvironmentModel::SurfaceType::Concrete:
                    case IEnvironmentModel::SurfaceType::Asphalt:
                        cls = 1; // Ground (paved) => runway/taxiway cue
                        break;
                    case IEnvironmentModel::SurfaceType::Water:
                        cls = 2;
                        break;
                    default:
                        cls = 3;
                        break;
                }

                auto& out_cell = out.cells[v][u];
                out_cell.z = static_cast<float>(t);
                out_cell.depth_log = std::log1p(out_cell.z);
                out_cell.inv_depth = 1.0f / (out_cell.z + 1e-3f);
                out_cell.coverage = 1.0f;
                out_cell.ang_size = 0.0f;
                out_cell.cls = cls;
                out_cell.team = 0;
                out_cell.vr = 0.0f;
                out_cell.conf = 1.0f;
            }
        }
    }
    
    // === PASS 2: Render each object ===
    for (const auto& obj : objects) {
        // 1. Transform to camera space
        double dx = obj.x - cam_pos.x;
        double dy = obj.y - cam_pos.y;
        double dz = obj.z - cam_pos.z;
        
        // Project onto camera axes
        double cam_z = dx * fwd_x + dy * fwd_y + dz * fwd_z;  // Forward (depth)
        double cam_x = dx * right_x + dy * right_y + dz * right_z;  // Right
        double cam_y = dx * up_x + dy * up_y + dz * up_z;  // Up
        
        // 2. Frustum cull (behind camera)
        if (cam_z <= 0.1) continue;
        
        double d = std::sqrt(dx*dx + dy*dy + dz*dz);
        double r = obj.bounding_radius;
        
        // 3. Angular position and size
        double theta = std::atan2(cam_x, cam_z);  // Azimuth
        double phi = std::atan2(cam_y, cam_z);    // Elevation
        double alpha = std::atan(r / d);          // Angular radius
        
        // 4. Frustum cull (outside FOV)
        if (std::abs(theta) > half_fov_h + alpha) continue;
        if (std::abs(phi) > half_fov_v + alpha) continue;
        
        // 5. Map to grid coordinates
        // u: 0 = left edge (-fov_h/2), W-1 = right edge (+fov_h/2)
        // v: 0 = bottom edge (-fov_v/2), H-1 = top edge (+fov_v/2)
        double u_center = (theta + half_fov_h) / (2.0 * half_fov_h) * (ARB_WIDTH - 1);
        double v_center = (phi + half_fov_v) / (2.0 * half_fov_v) * (ARB_HEIGHT - 1);
        
        // Angular radius in grid units
        double u_radius = alpha / (2.0 * half_fov_h) * (ARB_WIDTH - 1);
        double v_radius = alpha / (2.0 * half_fov_v) * (ARB_HEIGHT - 1);
        
        int u0 = std::max(0, static_cast<int>(u_center - u_radius - 0.5));
        int u1 = std::min(ARB_WIDTH - 1, static_cast<int>(u_center + u_radius + 0.5));
        int v0 = std::max(0, static_cast<int>(v_center - v_radius - 0.5));
        int v1 = std::min(ARB_HEIGHT - 1, static_cast<int>(v_center + v_radius + 0.5));
        
        // 6. Fill cells with Z-buffer test
        float z_obj = static_cast<float>(d);
        
        for (int v = v0; v <= v1; ++v) {
            for (int u = u0; u <= u1; ++u) {
                // Optional: exact circle test
                double du = (u - u_center) / std::max(u_radius, 0.5);
                double dv = (v - v_center) / std::max(v_radius, 0.5);
                if (du*du + dv*dv > 1.0) continue;
                
                // Z-buffer test
                if (z_obj < out.cells[v][u].z) {
                    auto& cell = out.cells[v][u];
                    cell.z = z_obj;
                    cell.depth_log = std::log1p(z_obj);
                    cell.inv_depth = 1.0f / (z_obj + 1e-3f);
                    cell.coverage = std::min(1.0f, static_cast<float>(alpha * 100.0));  // Simplified
                    cell.ang_size = static_cast<float>(alpha);
                    cell.cls = obj.cls;
                    cell.team = obj.team;
                    
                    // Radial velocity
                    double dvx = obj.vx;
                    double dvy = obj.vy;
                    double dvz = obj.vz;
                    double dot = (dx * dvx + dy * dvy + dz * dvz);
                    cell.vr = static_cast<float>(dot / (d + 1e-6));
                    cell.conf = 1.0f;
                }
            }
        }
    }
}

inline std::vector<float> render_retina_tensor(
    const Math::Vector3& cam_pos,
    double cam_heading,
    double cam_pitch,
    double fov_h,
    double fov_v,
    const std::vector<VisibleObject>& objects,
    IEnvironmentModel* env,
    int out_height,
    int out_width
) {
    if (out_height <= 0 || out_width <= 0) {
        throw std::invalid_argument("render_retina_tensor requires positive output dimensions");
    }

    std::vector<RetinaCell> cells(static_cast<size_t>(out_height) * static_cast<size_t>(out_width), RetinaCell{});
    std::vector<float> output(
        static_cast<size_t>(out_height) * static_cast<size_t>(out_width) * static_cast<size_t>(ARB_CHANNELS),
        0.0f
    );

    const double yaw_rad = Math::to_radians(90.0 - cam_heading);
    const double pitch_rad = Math::to_radians(cam_pitch);

    const double fwd_x = std::cos(yaw_rad) * std::cos(pitch_rad);
    const double fwd_y = std::sin(yaw_rad) * std::cos(pitch_rad);
    const double fwd_z = std::sin(pitch_rad);

    const double right_x = std::sin(yaw_rad);
    const double right_y = -std::cos(yaw_rad);
    const double right_z = 0.0;

    const double up_x = -std::cos(yaw_rad) * std::sin(pitch_rad);
    const double up_y = -std::sin(yaw_rad) * std::sin(pitch_rad);
    const double up_z = std::cos(pitch_rad);

    const double half_fov_h = Math::to_radians(fov_h / 2.0);
    const double half_fov_v = Math::to_radians(fov_v / 2.0);

    if (env) {
        std::vector<double> tan_theta(static_cast<size_t>(out_width), 0.0);
        std::vector<double> tan_phi(static_cast<size_t>(out_height), 0.0);

        for (int u = 0; u < out_width; ++u) {
            const double theta = (static_cast<double>(u) / std::max(1, out_width - 1)) * (2.0 * half_fov_h) - half_fov_h;
            tan_theta[static_cast<size_t>(u)] = std::tan(theta);
        }
        for (int v = 0; v < out_height; ++v) {
            const double phi = (static_cast<double>(v) / std::max(1, out_height - 1)) * (2.0 * half_fov_v) - half_fov_v;
            tan_phi[static_cast<size_t>(v)] = std::tan(phi);
        }

        const double ground_z_seed = env->get_terrain_elevation(cam_pos.x, cam_pos.y);

        for (int v = 0; v < out_height; ++v) {
            for (int u = 0; u < out_width; ++u) {
                double x_cam = tan_theta[static_cast<size_t>(u)];
                double y_cam = tan_phi[static_cast<size_t>(v)];
                double z_cam = 1.0;

                const double inv_norm = 1.0 / std::sqrt(x_cam * x_cam + y_cam * y_cam + z_cam * z_cam);
                x_cam *= inv_norm;
                y_cam *= inv_norm;
                z_cam *= inv_norm;

                const double dir_x = right_x * x_cam + up_x * y_cam + fwd_x * z_cam;
                const double dir_y = right_y * x_cam + up_y * y_cam + fwd_y * z_cam;
                const double dir_z = right_z * x_cam + up_z * y_cam + fwd_z * z_cam;

                if (dir_z >= -1e-6) {
                    continue;
                }

                double ground_z = ground_z_seed;
                double t = 0.0;

                for (int iter = 0; iter < 2; ++iter) {
                    t = (ground_z - cam_pos.z) / dir_z;
                    if (t <= 0.0) {
                        break;
                    }
                    const double ix = cam_pos.x + dir_x * t;
                    const double iy = cam_pos.y + dir_y * t;
                    ground_z = env->get_terrain_elevation(ix, iy);
                }

                if (t <= 0.0) {
                    continue;
                }

                const double ix = cam_pos.x + dir_x * t;
                const double iy = cam_pos.y + dir_y * t;
                const auto cell = env->get_terrain_at(ix, iy);

                int cls = 3;
                switch (cell.type) {
                    case IEnvironmentModel::SurfaceType::Concrete:
                    case IEnvironmentModel::SurfaceType::Asphalt:
                        cls = 1;
                        break;
                    case IEnvironmentModel::SurfaceType::Water:
                        cls = 2;
                        break;
                    default:
                        cls = 3;
                        break;
                }

                auto& out_cell = cells[static_cast<size_t>(v) * static_cast<size_t>(out_width) + static_cast<size_t>(u)];
                out_cell.z = static_cast<float>(t);
                out_cell.depth_log = std::log1p(out_cell.z);
                out_cell.inv_depth = 1.0f / (out_cell.z + 1e-3f);
                out_cell.coverage = 1.0f;
                out_cell.ang_size = 0.0f;
                out_cell.cls = cls;
                out_cell.team = 0;
                out_cell.vr = 0.0f;
                out_cell.conf = 1.0f;
            }
        }
    }

    for (const auto& obj : objects) {
        const double dx = obj.x - cam_pos.x;
        const double dy = obj.y - cam_pos.y;
        const double dz = obj.z - cam_pos.z;

        const double cam_z = dx * fwd_x + dy * fwd_y + dz * fwd_z;
        const double cam_x = dx * right_x + dy * right_y + dz * right_z;
        const double cam_y = dx * up_x + dy * up_y + dz * up_z;

        if (cam_z <= 0.1) {
            continue;
        }

        const double d = std::sqrt(dx * dx + dy * dy + dz * dz);
        const double r = obj.bounding_radius;
        const double theta = std::atan2(cam_x, cam_z);
        const double phi = std::atan2(cam_y, cam_z);
        const double alpha = std::atan(r / d);

        if (std::abs(theta) > half_fov_h + alpha) {
            continue;
        }
        if (std::abs(phi) > half_fov_v + alpha) {
            continue;
        }

        const double u_center = (theta + half_fov_h) / (2.0 * half_fov_h) * (out_width - 1);
        const double v_center = (phi + half_fov_v) / (2.0 * half_fov_v) * (out_height - 1);
        const double u_radius = alpha / (2.0 * half_fov_h) * (out_width - 1);
        const double v_radius = alpha / (2.0 * half_fov_v) * (out_height - 1);

        const int u0 = std::max(0, static_cast<int>(u_center - u_radius - 0.5));
        const int u1 = std::min(out_width - 1, static_cast<int>(u_center + u_radius + 0.5));
        const int v0 = std::max(0, static_cast<int>(v_center - v_radius - 0.5));
        const int v1 = std::min(out_height - 1, static_cast<int>(v_center + v_radius + 0.5));
        const float z_obj = static_cast<float>(d);

        for (int v = v0; v <= v1; ++v) {
            for (int u = u0; u <= u1; ++u) {
                const double du = (u - u_center) / std::max(u_radius, 0.5);
                const double dv = (v - v_center) / std::max(v_radius, 0.5);
                if (du * du + dv * dv > 1.0) {
                    continue;
                }

                auto& cell = cells[static_cast<size_t>(v) * static_cast<size_t>(out_width) + static_cast<size_t>(u)];
                if (z_obj < cell.z) {
                    cell.z = z_obj;
                    cell.depth_log = std::log1p(z_obj);
                    cell.inv_depth = 1.0f / (z_obj + 1e-3f);
                    cell.coverage = std::min(1.0f, static_cast<float>(alpha * 100.0));
                    cell.ang_size = static_cast<float>(alpha);
                    cell.cls = obj.cls;
                    cell.team = obj.team;
                    const double dot = (dx * obj.vx + dy * obj.vy + dz * obj.vz);
                    cell.vr = static_cast<float>(dot / (d + 1e-6));
                    cell.conf = 1.0f;
                }
            }
        }
    }

    for (int v = 0; v < out_height; ++v) {
        for (int u = 0; u < out_width; ++u) {
            write_retina_cell_to_tensor(
                cells[static_cast<size_t>(v) * static_cast<size_t>(out_width) + static_cast<size_t>(u)],
                output.data() + (static_cast<size_t>(v) * static_cast<size_t>(out_width) + static_cast<size_t>(u)) * static_cast<size_t>(ARB_CHANNELS)
            );
        }
    }

    return output;
}

} // namespace arb
