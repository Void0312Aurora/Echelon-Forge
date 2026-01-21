#pragma once
#include <vector>
#include <cstdint>

enum class SensorType {
    Visual = 0,
    Infrared = 1,
    Radar = 2,
    RWR = 3,
    MIDS = 4
};

struct Sensor { 
    double max_range;         // Meters
    double fov_deg;           // Degrees (Total)
    double scan_period;       // Seconds between scans
    double last_scan_time;    // Simulation time of last scan
    double detection_prob;    // Base detection probability [0,1]
    double range_power;       // Range attenuation exponent (4.0 for Radar)
    double bearing_noise_std; // Bearing noise std-dev (deg)
    double range_noise_std;   // Range noise std-dev (m)
    double track_memory_s;    // Track memory retention (s)
    double aspect_influence;  // [0,1] influence of target aspect on detection
    double doppler_notch_width; // m/s relative velocity notch (0=disable)
    int type;                 // See SensorType
};

struct Detection { 
    uint64_t target_id; 
    double range;           // Meters
    double bearing;         // Degrees (relative azimuth, NAV: -180..180)
    double elevation;       // Degrees (relative elevation, -90..90)
    double closing_speed;   // m/s (Positive = Approaching)
    double signal_strength; // Signal intensity (RCS/R^4 or similar linear scale)
    double timestamp;       // Simulation time
};

struct ContactList { 
    std::vector<Detection> contacts; 
};
