#pragma once
#include <vector>
#include <cstdint>

struct TrackData {
    uint64_t id;      // Track ID (Might not match entity ID in real radar, but here checks out)
    double range;     // Meters
    double azimuth;   // Degrees relative to own nose (-180 to 180)
    double elevation; // Degrees relative to horizon
    double time_since_update; // Seconds
};

struct AgentObservation {
    double sim_time;
    uint64_t id;
    
    // Own State (Kinematics)
    double x, y, z;
    double vx, vy, vz;
    double heading, pitch, roll;
    double speed;
    double health;
    
    // Sensor Picture
    std::vector<TrackData> contacts;
    
    // Weapons status
    int missiles_remaining; // Placeholder
    bool can_fire;          // Cooldown/Geometry check?
    
    double total_reward;    // Accumulated score
};
