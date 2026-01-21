#pragma once

#include <vector>
#include <cstdint>
#include "components/basic/common.h"

enum class TrackSource {
    None = 0,
    Radar,
    RWR,
    DataLink,
    Fused // Merged from multiple sources
};

enum class TrackClass {
    Unknown = 0,
    Friendly,
    Hostile,
    Neutral
};

struct SystemTrack {
    uint64_t track_id;
    uint64_t entity_id; // True ID (cheating/lookup) or purely internal logic?
                        // Ideally we correlate by ID if DL, but by position if Radar.
                        // For simplicity in MVP: Store entity_id if known (DL), else 0? 
                        // Actually, sensors often provide a handle. Let's store entity_id for ground truth correlation/debugging, 
                        // but logic should rely on position.
                        
    double x, y, z; // Estimated Position
    double vx, vy, vz; // Estimated Velocity
    
    double range;
    double azimuth;
    double elevation;
    
    TrackSource main_source;
    TrackClass classification;
    
    double confidence; // 0.0 - 1.0
    double time_since_update;
};

// Component attached to the Agent/Aircraft
struct TrackDatabase {
    std::vector<SystemTrack> tracks;
    // Configuration
    double fusion_radius_m = 1000.0; // Correlate within 1km
    int max_tracks = 32;
};
