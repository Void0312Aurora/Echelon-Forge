#pragma once
#include <vector>
#include <cstdint>
#include <string>

enum class SensorType {
    Visual = 0,
    Infrared = 1,
    Radar = 2,
    RWR = 3,
    MIDS = 4,
    ESM = 5,
    Sonar = 6
};

enum class SensorEnvironmentDomain {
    Air = 0,
    SurfaceMaritime = 1,
    Littoral = 2
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
    double reference_snr_db;  // SNR at reference_range_m/reference_rcs_m2
    double reference_range_m; // SNR calibration range
    double reference_rcs_m2;  // SNR calibration RCS
    double pfa;               // Reference false-alarm probability
    int confirm_hits_m;       // M in M-of-N confirm
    int confirm_window_n;     // N in M-of-N confirm
    double velocity_noise_std; // Radial velocity measurement noise std-dev
    double alpha_beta_alpha;  // Position gain for alpha-beta filter
    double alpha_beta_beta;   // Velocity gain for alpha-beta filter
    double antenna_height_m;  // Sensor reference height for horizon checks
    double target_height_bias_m; // Conservative target-height prior for horizon work
    double sea_clutter_sensitivity; // community-derived approximation [0,1]
    double sea_state_loss_per_level; // engineering calibration loss per sea-state level
    double ducting_gain_factor; // optional ducting extension multiplier
    double ducting_max_bonus_m; // engineering calibration cap for ducting bonus
    double bearing_only_min_range_m; // For passive/ESM style detections
    int environment_domain;    // See SensorEnvironmentDomain
    bool enforce_radar_horizon; // Apply curvature/horizon proxy for surface maritime radars
    bool enable_ducting;       // Apply conservative maritime ducting approximation
    bool sea_clutter_enabled;  // Apply sea-clutter loss proxy
    bool bearing_only;         // Passive-only contact; range omitted in output
    int type;                 // See SensorType
};

struct SensorMount {
    Sensor sensor{};
    std::string label{};
};

struct MountedSensors {
    std::vector<SensorMount> mounts{};
};

struct Detection { 
    uint64_t target_id; 
    double range;           // Meters
    double bearing;         // Degrees (relative azimuth, NAV: -180..180)
    double elevation;       // Degrees (relative elevation, -90..90)
    double closing_speed;   // m/s (Positive = Approaching)
    double signal_strength; // Signal intensity (RCS/R^4 or similar linear scale)
    double snr_db;          // Detection SNR proxy in dB
    double detection_prob_used; // Final single-scan Pd used for this hit
    double measured_vr;     // Measured radial velocity
    int sensor_type;        // Originating sensor type
    bool local_sensor_hit;  // True when produced by local sensor model
    double timestamp;       // Simulation time
};

struct ContactList { 
    std::vector<Detection> contacts; 
};
