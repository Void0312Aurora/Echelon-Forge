#pragma once
#include <vector>
#include <cstdint>

// Electronic Warfare Components

enum class JammingType {
    NoiseBarrage, // Broad coverage, lower density
    NoiseSpot,    // Narrow coverage, high density
    DeceptionDRFM // False targets
};

struct Jammer {
    bool is_active;         // Is transmitting
    double power_watts;     // Effective Radiated Power (ERP)
    double bandwidth_mhz;   // Bandwidth coverage
    JammingType type;       // Technique
    double effective_angle; // Beam width (deg)
};

struct Countermeasures {
    int chaff_count;                 // Remaining Chaff
    int flare_count;                 // Remaining Flares
    double release_interval;         // Minimum time between releases
    double last_release_time = -1.0; // Time of last release (< 0 = never released)
    double last_chaff_release_time = -1.0;
    double last_flare_release_time = -1.0;
    bool auto_mode; // Auto-dispense on threat
};

// A release is admissible when the dispenser has never fired (negative stamp)
// or the native release interval has elapsed since the last release.
inline bool countermeasure_release_ready(double last_release_time_s, double release_interval_s,
                                         double current_time_s) {
    return last_release_time_s < 0.0 || current_time_s - last_release_time_s >= release_interval_s;
}

// One MAWS warning per inbound missile.  The bearing is measured from the
// warned platform to the missile (relative to its nose, NAV convention), which
// is what an approach-warning sensor observes; the launcher id is retained only
// as attribution for the RWR row merge.
struct MissileApproachWarning {
    uint64_t source_id = 0;
    uint64_t missile_id = 0;
    double bearing_deg = 0.0;
};

struct RWR {
    double sensitivity_dbm;                          // Min detectable signal
    std::vector<uint64_t> detected_radar_ids;        // IDs of painting radars
    std::vector<uint64_t> locking_radar_ids;         // IDs of locking (STT) radars
    std::vector<uint64_t> missile_launch_source_ids; // IDs of launch platforms detected by MAWS
    // bool is_locked; // Removed in favor of locking_radar_ids
    bool is_missile_launch; // MAWS (Missile Approach) warning
    std::vector<MissileApproachWarning> missile_approach_warnings{};
};

struct EmitterDetection {
    uint64_t source_id = 0;
    double bearing_deg = 0.0;
    double signal_strength = 0.0;
    bool is_radar_lock = false;
    bool is_missile_guidance = false;
};

struct ESMReceiver {
    double sensitivity_dbm = -85.0;
    double max_detection_range_m = 250000.0;
    bool classify_emitters = true;
    std::vector<EmitterDetection> detections{};
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
