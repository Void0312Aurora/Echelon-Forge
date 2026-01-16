#pragma once
#include <vector>
#include <cstdint>

struct Sensor { 
    double max_range;       // Meters
    double fov_deg;         // Degrees (Half-angle or Total? Usually Total)
    double scan_period;     // Seconds between scans
    double last_scan_time;  // Simulation time of last scan
};

struct Detection { 
    uint64_t target_id; 
    double range;           // Meters
    double bearing;         // Degrees (relative to nose)
    double timestamp;       // Simulation time
};

struct ContactList { 
    std::vector<Detection> contacts; 
};
