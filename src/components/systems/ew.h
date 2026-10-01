#pragma once
#include <cmath>
#include <cstdint>
#include <vector>

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
    // Command admission. A pod is commandable only when it is installed (it
    // has a positive ERP); `type` is then the technique the pilot selected.
    // A database `is_active` is the initial switch position. It persists only
    // for platforms without an active PilotAction: an active PilotAction is
    // the whole cockpit state and carries the ECM switch every frame. The
    // transmit-start stamp is < 0 while the pod is in standby.
    double transmit_start_time_s = -1.0;
};

inline bool jammer_installed(const Jammer &jammer) {
    return std::isfinite(jammer.power_watts) && jammer.power_watts > 0.0;
}

// Maps a cockpit ECM technique code onto the native technique. Unknown codes
// are rejected so a malformed panel value cannot silently select barrage.
inline bool jamming_type_from_code(int code, JammingType &out) {
    switch (code) {
    case 0:
        out = JammingType::NoiseBarrage;
        return true;
    case 1:
        out = JammingType::NoiseSpot;
        return true;
    case 2:
        out = JammingType::DeceptionDRFM;
        return true;
    default:
        return false;
    }
}

// Admits one cockpit jammer command. Returns true when the native state
// changed. An uninstalled pod or an unknown technique code is a no-op.
inline bool apply_jammer_command(Jammer &jammer, bool transmit, int mode_code,
                                 double current_time_s) {
    if (!jammer_installed(jammer)) {
        return false;
    }
    JammingType requested_type = jammer.type;
    if (transmit && !jamming_type_from_code(mode_code, requested_type)) {
        return false;
    }
    const bool was_active = jammer.is_active;
    const JammingType was_type = jammer.type;
    jammer.is_active = transmit;
    if (transmit) {
        jammer.type = requested_type;
        if (!was_active) {
            jammer.transmit_start_time_s = current_time_s;
        }
    } else {
        jammer.transmit_start_time_s = -1.0;
    }
    return was_active != jammer.is_active || was_type != jammer.type;
}

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
