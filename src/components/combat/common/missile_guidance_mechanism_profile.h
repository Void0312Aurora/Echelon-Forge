#pragma once

// Diagnostics-only per-missile mechanism profile. Production missiles do not carry this
// component, so the unprofiled guidance path remains the runtime baseline.
struct MissileGuidanceMechanismProfile {
    static constexpr int kCaptureOff = 0;
    static constexpr int kCaptureOn = 1;

    static constexpr int kCaptureBaseInverseRange = 0;
    static constexpr int kCaptureBaseReferenceRange = 1;

    static constexpr int kCaptureTerminalCurrentClamped = 0;
    static constexpr int kCaptureTerminalUnity = 1;
    static constexpr int kCaptureTerminalReciprocalUnclamped = 2;

    static constexpr int kCaptureLeadCurrentSchedule = 0;
    static constexpr int kCaptureLeadConstantMax = 1;
    static constexpr int kCaptureLeadOff = 2;

    static constexpr int kPnLegacyBodyRates = 0;
    static constexpr int kPnOff = 1;
    static constexpr int kPnWorldLosHistory = 2;
    static constexpr int kPnWorldTrackAnalytic = 3;

    static constexpr int kLeadOff = 0;
    static constexpr int kLeadVelocityOnly = 1;
    static constexpr int kLeadQuadratic = 2;

    static constexpr int kKinematicsTrack = 0;
    static constexpr int kKinematicsTruthConstantVelocity = 1;

    static constexpr int kApnOff = 0;
    static constexpr int kApnOn = 1;

    bool active = false;
    int capture_mode = kCaptureOn;
    int capture_base_range_mode = kCaptureBaseInverseRange;
    int capture_terminal_weight_mode = kCaptureTerminalCurrentClamped;
    int capture_lead_blend_mode = kCaptureLeadCurrentSchedule;
    int pn_mode = kPnLegacyBodyRates;
    int lead_mode = kLeadQuadratic;
    int kinematics_source = kKinematicsTrack;
    int apn_mode = kApnOn;

    // Internal state for the world-LOS-history PN matched comparison.
    bool previous_world_los_valid = false;
    double previous_world_los_x = 0.0;
    double previous_world_los_y = 0.0;
    double previous_world_los_z = 0.0;
    double previous_world_los_time_s = -1.0;

    // Component-resolved diagnostics exported through debug_get_missile_runtime_state().
    int target_kinematics_source_used = 0; // 0=none, 1=track estimate, 2=truth CV oracle
    int pn_source_used = 0;                // 0=off, 1=legacy, 2=LOS history, 3=analytic
    double capture_accel_x_mps2 = 0.0;
    double capture_accel_y_mps2 = 0.0;
    double capture_accel_z_mps2 = 0.0;
    double capture_accel_mps2 = 0.0;
    double capture_lateral_error = 0.0;
    double capture_base_range_factor = 0.0;
    double capture_terminal_weight = 0.0;
    double capture_raw_accel_mps2 = 0.0;
    double pn_accel_x_mps2 = 0.0;
    double pn_accel_y_mps2 = 0.0;
    double pn_accel_z_mps2 = 0.0;
    double pn_accel_mps2 = 0.0;
    double apn_accel_x_mps2 = 0.0;
    double apn_accel_y_mps2 = 0.0;
    double apn_accel_z_mps2 = 0.0;
    double preclamp_accel_x_mps2 = 0.0;
    double preclamp_accel_y_mps2 = 0.0;
    double preclamp_accel_z_mps2 = 0.0;
    double preclamp_accel_mps2 = 0.0;
    double postclamp_accel_x_mps2 = 0.0;
    double postclamp_accel_y_mps2 = 0.0;
    double postclamp_accel_z_mps2 = 0.0;
    double postclamp_accel_mps2 = 0.0;
    double los_rate_x_rad_s = 0.0;
    double los_rate_y_rad_s = 0.0;
    double los_rate_z_rad_s = 0.0;
    double los_rate_rad_s = 0.0;
    double closing_speed_used_mps = 0.0;
    double achieved_accel_x_mps2 = 0.0;
    double achieved_accel_y_mps2 = 0.0;
    double achieved_accel_z_mps2 = 0.0;
};
