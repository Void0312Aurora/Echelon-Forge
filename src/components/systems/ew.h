#pragma once
#include <cmath>
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
    // A commandable pod is installed only when it has positive ERP. The
    // database switch is the initial position; an active PilotAction owns the
    // per-frame transmit state and the transmit-start timestamp.
    double transmit_start_time_s = -1.0;
    // Authored burn-through range against a 5 m^2 target at this pod's ERP.
    // Zero preserves the historical engineering proxy.
    double burn_through_reference_m = 0.0;
    // NoiseSpot power concentration relative to barrage; 1.0 keeps them equal.
    double spot_power_gain = 1.0;
    // DRFM false-target range offset beyond burn-through. Zero is inert.
    double drfm_range_offset_m = 0.0;
    double rf_eirp_watts = 0.0;
    double rf_frequency_mhz = 0.0;
};

inline bool jammer_installed(const Jammer &jammer) {
    return std::isfinite(jammer.power_watts) && jammer.power_watts > 0.0;
}

inline bool jammer_transmitting(const Jammer &jammer) {
    return jammer.is_active && jammer_installed(jammer);
}

inline constexpr double kBurnThroughReferenceRcsM2 = 5.0;
inline constexpr double kLegacyBurnThroughConstant = 283000.0;

inline double jammer_effective_power_watts(const Jammer &jammer) {
    const double p_j = jammer.power_watts > 1.0 ? jammer.power_watts : 1.0;
    if (jammer.type == JammingType::NoiseSpot && std::isfinite(jammer.spot_power_gain) &&
        jammer.spot_power_gain > 0.0) {
        return p_j * jammer.spot_power_gain;
    }
    return p_j;
}

inline double jammer_burn_through_range_m(const Jammer &jammer, double rcs_m2) {
    const double p_j = jammer.power_watts > 1.0 ? jammer.power_watts : 1.0;
    const double k =
        jammer.burn_through_reference_m > 0.0
            ? jammer.burn_through_reference_m * std::sqrt(p_j / kBurnThroughReferenceRcsM2)
            : kLegacyBurnThroughConstant;
    const double safe_rcs = rcs_m2 > 1.0e-6 ? rcs_m2 : 1.0e-6;
    return k * std::sqrt(safe_rcs / jammer_effective_power_watts(jammer));
}

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
    int chaff_count;          // Remaining Chaff
    int flare_count;          // Remaining Flares
    double release_interval;  // Minimum time between releases
    double last_release_time; // Time of last release
    double last_chaff_release_time = -1.0;
    double last_flare_release_time = -1.0;
    bool auto_mode; // Auto-dispense on threat
    // Expendable signatures and lifetimes, from the EW suite data. The content
    // loader resolves an absent or non-positive value to the historical
    // engineering default (see countermeasure_* defaults below), so a spawned
    // expendable never reads zero here.
    double chaff_rcs_m2 = 0.0;       // Chaff cloud radar cross-section (m^2)
    double flare_ir_intensity = 0.0; // Flare IR intensity (sensor-model relative IR units)
    double chaff_lifetime_s = 0.0;
    double flare_lifetime_s = 0.0;
};

// Historical engineering defaults for expendables, used when the EW suite data
// does not author a value. They are uncalibrated proxies carried over from the
// original hard-coded spawn values.
inline constexpr double kDefaultChaffRcsM2 = 50.0;
inline constexpr double kDefaultFlareIrIntensity = 500.0;
inline constexpr double kDefaultChaffLifetimeS = 20.0;
inline constexpr double kDefaultFlareLifetimeS = 10.0;

inline double countermeasure_positive_or(double value, double fallback) {
    return std::isfinite(value) && value > 0.0 ? value : fallback;
}

enum class DecoyKind : int { Chaff = 0, Flare = 1 };

// A released expendable. `signature` is the radar cross-section (m^2) for
// chaff and the IR intensity (the sensor model's relative IR units) for a
// flare. `owner_id` is the releasing platform; a seeker only considers a decoy
// released by its own assigned target.
struct Decoy {
    DecoyKind kind = DecoyKind::Chaff;
    std::uint64_t owner_id = 0;
    double release_time_s = -1.0;
    double signature = 0.0;
};

struct RWR {
    double sensitivity_dbm;                          // Min detectable signal
    std::vector<uint64_t> detected_radar_ids;        // IDs of painting radars
    std::vector<uint64_t> locking_radar_ids;         // IDs of locking (STT) radars
    std::vector<uint64_t> missile_launch_source_ids; // IDs of launch platforms detected by MAWS
    // bool is_locked; // Removed in favor of locking_radar_ids
    bool is_missile_launch; // MAWS (Missile Approach) warning
};

struct EmitterDetection {
    uint64_t source_id = 0;
    double bearing_deg = 0.0;
    double signal_strength = 0.0;
    bool is_radar_lock = false;
    bool is_missile_guidance = false;
    bool is_jammer = false;
    double received_power_dbm = 0.0; // Valid only when has_rf_power is true.
    bool has_rf_power = false;
    double sensitivity_margin_db = 0.0;
    double observed_time_s = -1.0;
    double confidence = 0.0; // Fraction of required distinct scans, not a Pd.
    int confirmation_count = 0;
    bool classification_known = false;
};

struct ESMReceiver {
    double sensitivity_dbm = -85.0;
    double max_detection_range_m = 250000.0;
    bool classify_emitters = true;
    std::vector<EmitterDetection> detections{};
    // Zero bounds accept any band; strict receivers reject legacy emitters.
    double frequency_min_mhz = 0.0;
    double frequency_max_mhz = 0.0;
    double memory_s = 0.0; // Zero preserves the historical per-step reset.
    int confirmation_scans = 1;
    bool require_rf_contract = false;
};

inline void expire_esm_detections(ESMReceiver &esm, double current_time_s) {
    std::erase_if(esm.detections, [&](const EmitterDetection &det) {
        return esm.memory_s <= 0.0 || det.observed_time_s < 0.0 ||
               current_time_s < det.observed_time_s ||
               current_time_s - det.observed_time_s > esm.memory_s;
    });
}

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
