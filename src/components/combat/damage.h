#pragma once

#include <vector>
#include <string>
#include <unordered_map>

// Geometric shape approximation (OBB/Box oriented aligned for now)
struct Hitbox {
    int id;
    // Relative position from unit center (Forward, Right, Up)
    double offset_x, offset_y, offset_z;
    // Dimensions (Length, Width, Height)
    double dim_l, dim_w, dim_h; 
    
    double armor_mm;
    
    // Critical systems protected by this box
    std::vector<std::string> protected_systems;
};

// Static Configuration (Shared Component candidate)
struct HitboxConfig {
    std::vector<Hitbox> hitboxes;
};

// Runtime State
struct SystemHealth {
    // 0.0 = Dead, 1.0 = Fully Operational
    // Key: System Name (e.g., "radar", "engine", "flight_control")
    std::unordered_map<std::string, double> systems;
};

enum class PlatformLossState : int {
    CombatCapable = 0,
    MissionKill = 1,
    MobilityKill = 2,
    SensorKill = 3,
    Lost = 4,
};

struct PlatformDamageState {
    double mission_capability = 1.0;
    double mobility_capability = 1.0;
    double sensor_capability = 1.0;
    double survivability_margin = 1.0;
    double flooding_severity = 0.0;
    double fire_severity = 0.0;
    double ongoing_hull_breach = 0.0;
    bool mission_kill = false;
    bool mobility_kill = false;
    bool sensor_kill = false;
    PlatformLossState loss_state = PlatformLossState::CombatCapable;
};
