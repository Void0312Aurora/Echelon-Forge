#pragma once
#include <vector>
#include <cstdint>

struct Sensor { 
    double max_range;         // Meters
    double fov_deg;           // Degrees (Half-angle or Total? Usually Total)
    double scan_period;       // Seconds between scans
    double last_scan_time;    // Simulation time of last scan
    double detection_prob;    // Base detection probability [0,1]
    double range_power;       // Range attenuation exponent
    double bearing_noise_std; // Bearing noise std-dev (deg)
    double range_noise_std;   // Range noise std-dev (m)
    double track_memory_s;    // Track memory retention (s)
    double aspect_influence;  // [0,1] influence of target aspect on detection
};

struct Detection { 
    uint64_t target_id; 
    double range;           // Meters
    double bearing;         // Degrees (relative azimuth, NAV: -180..180)
    double timestamp;       // Simulation time
};

struct ContactList { 
    std::vector<Detection> contacts; 
};
