#pragma once

#include <cstdint>

struct SubmarinePlatform {
    double submerged_displacement_kg = 0.0;
    double length_m = 0.0;
    double beam_m = 0.0;
    double draft_m = 0.0;
    double max_speed_submerged_mps = 0.0;
    double quiet_speed_mps = 0.0;
    double max_accel_mps2 = 0.05;
    double max_decel_mps2 = 0.08;
    double max_turn_rate_deg_s = 1.5;
    double max_depth_rate_mps = 3.0;
    double nominal_patrol_depth_m = 60.0;
    double max_operating_depth_m = 300.0;
    double acoustic_stealth_bias_db = 0.0;
    double self_noise_per_speed_db = 1.2;
    int crew = 0;
};

enum class SubmarineDepthConstraintStatus : std::uint8_t {
    Disabled = 0,
    Allowed = 1,
    LimitedBySeabed = 2,
    UnknownBathymetry = 3,
};

// Opt-in policy for scenarios that have an admitted shared bathymetry
// provider.  The Transform reference point is treated as the hull reference
// point; draft_m is measured downward from it.  Unknown, dry, out-of-coverage,
// and invalid-datum observations hold the current depth until the caller
// supplies a valid segment observation.  Runtime status fields make a limited
// or rejected command observable without adding a second environment service.
struct SubmarineBathymetryPolicy {
    bool enabled = false;
    double min_keel_clearance_m = 5.0;
    SubmarineDepthConstraintStatus last_status = SubmarineDepthConstraintStatus::Disabled;
    double last_requested_depth_m = 0.0;
    double last_allowed_depth_m = 0.0;
};
