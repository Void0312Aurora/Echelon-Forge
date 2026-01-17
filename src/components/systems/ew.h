#pragma once
#include <vector>
#include <cstdint>

// Electronic Warfare Components

enum class JammingType {
    NoiseBarrage,   // Broad coverage, lower density
    NoiseSpot,      // Narrow coverage, high density
    DeceptionDRFM   // False targets
};

struct Jammer {
    bool is_active;          // Is transmitting
    double power_watts;      // Effective Radiated Power (ERP)
    double bandwidth_mhz;    // Bandwidth coverage
    JammingType type;        // Technique
    double effective_angle;  // Beam width (deg)
};

struct Countermeasures {
    int chaff_count;         // Remaining Chaff
    int flare_count;         // Remaining Flares
    double release_interval; // Minimum time between releases
    double last_release_time;// Time of last release
    bool auto_mode;          // Auto-dispense on threat
};

struct RWR {
    double sensitivity_dbm;             // Min detectable signal
    std::vector<uint64_t> detected_radar_ids; // IDs of painting radars
    bool is_locked;                     // STT (Single Target Track) warning
    bool is_missile_launch;             // MAWS (Missile Approach) warning
};

// RCS Profile for Geometric RCS (Optional but recommended)
struct RCSProfile {
    double frontal_rcs;
    double side_rcs;
    double rear_rcs;
    // Simple interpolation will happen in SensorModel
};

struct Lifetime {
    double max_age;
    double current_age;
};
