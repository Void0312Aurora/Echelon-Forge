#pragma once
#include <vector>
#include <cstdint>

struct TrackData {
    uint64_t id;      // Track ID (Might not match entity ID in real radar, but here checks out)
    double range;     // Meters
    double azimuth;   // Degrees relative to own nose (-180 to 180)
    double elevation; // Degrees relative to horizon
    double closing_speed; // m/s (Positive = Approaching)
    double time_since_update; // Seconds
    int source; // 0=None, 1=Radar, 2=RWR, 3=DL, 4=Fused
    int classification; // 0=Unknown, 1=Friend, 2=Hostile, 3=Neutral
};

struct RWREvent {
    uint64_t source_id; // ID of the radar source (if identified)
    double bearing;     // Degrees (relative)
    double signal_strength;
    bool is_lock;       // Is this a tracking radar lock?
    bool is_launch;     // Is this a missile guidance signal?
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
    std::vector<RWREvent> rwr_warnings;
    
    
    // Weapons status
    int missiles_remaining; // Placeholder
    bool can_fire;          // Cooldown/Geometry check?
    
    // Systems status
    double gear_state; // 0.0=Up, 1.0=Down
    double throttle;   // 0.0 to 1.0 (or >1.0 for AB)
    
    double total_reward;    // Accumulated score
};
