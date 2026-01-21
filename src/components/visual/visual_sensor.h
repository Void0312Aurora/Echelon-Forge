#pragma once

#include <cstdint>

namespace arb {
    // ARB Grid dimensions
    constexpr int ARB_HEIGHT = 48;  // Elevation: ±45° @ ~2°/cell
    constexpr int ARB_WIDTH = 96;   // Azimuth: ±90° @ ~2°/cell
    constexpr int ARB_CHANNELS = 10;
    
    // Channel indices
    constexpr int CH_DEPTH_LOG = 0;
    constexpr int CH_INV_DEPTH = 1;
    constexpr int CH_COVERAGE = 2;
    constexpr int CH_ANG_SIZE = 3;
    constexpr int CH_CLASS_AIR = 4;
    constexpr int CH_CLASS_GROUND = 5;
    constexpr int CH_CLASS_SEA = 6;
    constexpr int CH_CLASS_TERRAIN = 7;
    constexpr int CH_TEAM = 8;
    constexpr int CH_VEL_RADIAL = 9;
}

/**
 * VisualSensor
 * Defines optical sensor parameters for ARB rendering.
 */
struct VisualSensor {
    double fov_h_deg = 180.0;      // Horizontal FOV (±90°)
    double fov_v_deg = 90.0;       // Vertical FOV (±45°)
    double resolution_mrad = 1.0;  // Angular resolution
    double last_scan_time = 0.0;
    bool active = true;
};

/**
 * VisualSignature
 * Defines how visible/detectable an entity is.
 */
struct VisualSignature {
    double bounding_radius = 10.0;  // Bounding sphere radius (m)
    double contrast = 1.0;          // Visibility factor [0,1]
    int visual_class = 0;           // 0=Air, 1=Ground, 2=Sea, 3=Terrain
};
