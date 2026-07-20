#pragma once

// Kalman-seeker filter state/parameter value types shared by the Missile
// component (weapon_common.h) and models/weapons/kalman_seeker.h's EKF math.
// Owned here (a components-visible leaf) rather than in models/weapons/ so
// Missile does not have to reach upward into a model implementation header
// just to embed these two structs by value; kalman_seeker.h includes this
// header back for its free functions (models -> components is the
// policy-allowed direction, not the reverse).
namespace missile_seeker {

// ── 9-state EKF: [x, y, z, vx, vy, vz, ax, ay, az] in world Cartesian ──

struct SeekerEkfState {
    double x[9] = {};
    double P[81] = {}; // 9x9 covariance, row-major: P[row*9 + col]
    bool initialized = false;
    double last_predict_time_s = -1.0;
};

struct SeekerEkfParams {
    double process_noise_sigma_a = 100.0; // m/s^2 equivalent maneuver scale (~10 g target turn)
    double maneuver_tau_s = 15.0;         // Reserved for future Singer-style maneuver decay
    double meas_noise_angle_rad = 0.003;  // rad (~0.17° ≈ 3 mrad)
    double meas_noise_range_m = 10.0;     // m
    double track_memory_timeout_s = 0.75;
};

} // namespace missile_seeker
