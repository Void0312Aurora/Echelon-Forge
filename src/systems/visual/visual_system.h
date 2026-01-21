#pragma once

#include <flecs.h>
#include <cmath>
#include <algorithm>
#include <vector>
#include "components/visual/visual_sensor.h"
#include "components/basic/common.h"
#include "components/physics/action.h"
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
                const auto& c = cells[v][u];
                int base = (v * ARB_WIDTH + u) * ARB_CHANNELS;
                out[base + CH_DEPTH_LOG] = c.depth_log;
                out[base + CH_INV_DEPTH] = c.inv_depth;
                out[base + CH_COVERAGE] = c.coverage;
                out[base + CH_ANG_SIZE] = c.ang_size;
                // One-hot class
                out[base + CH_CLASS_AIR] = (c.cls == 0) ? 1.0f : 0.0f;
                out[base + CH_CLASS_GROUND] = (c.cls == 1) ? 1.0f : 0.0f;
                out[base + CH_CLASS_SEA] = (c.cls == 2) ? 1.0f : 0.0f;
                out[base + CH_CLASS_TERRAIN] = (c.cls == 3) ? 1.0f : 0.0f;
                out[base + CH_TEAM] = static_cast<float>(c.team);
                out[base + CH_VEL_RADIAL] = c.vr;
            }
        }
    }
};

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
    
    // === PASS 1: Terrain (optional, sample grid) ===
    // For now, skip terrain pass - focus on entities
    
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

} // namespace arb
