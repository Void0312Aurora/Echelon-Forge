#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>

namespace missile_seeker {

// ── 9-state EKF: [x, y, z, vx, vy, vz, ax, ay, az] in world Cartesian ──

struct SeekerEkfState {
    double x[9] = {};
    double P[81] = {};  // 9x9 covariance, row-major: P[row*9 + col]
    bool initialized = false;
    double last_predict_time_s = -1.0;
};

struct SeekerEkfParams {
    double process_noise_sigma_a = 5.0;       // m/s² — Singer σ_max
    double maneuver_tau_s = 15.0;              // Singer τ_m (target maneuver time constant)
    double meas_noise_angle_rad = 0.003;       // rad (~0.17° ≈ 3 mrad)
    double meas_noise_range_m = 10.0;          // m
    double track_memory_timeout_s = 0.75;
};

// ── small-matrix helpers ──

inline double dot3(const double a[3], const double b[3]) {
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

inline double norm3(const double v[3]) {
    return std::sqrt(dot3(v, v));
}

inline void mat9vec(const double M[81], const double v[9], double out[9]) {
    for (int r = 0; r < 9; ++r) {
        double s = 0.0;
        for (int c = 0; c < 9; ++c) s += M[r * 9 + c] * v[c];
        out[r] = s;
    }
}

inline void mat9tvec(const double M[81], const double v[9], double out[9]) {
    for (int r = 0; r < 9; ++r) {
        double s = 0.0;
        for (int c = 0; c < 9; ++c) s += M[c * 9 + r] * v[c];
        out[r] = s;
    }
}

inline void mat3vec(const double M[9], const double v[3], double out[3]) {
    out[0] = M[0]*v[0] + M[1]*v[1] + M[2]*v[2];
    out[1] = M[3]*v[0] + M[4]*v[1] + M[5]*v[2];
    out[2] = M[6]*v[0] + M[7]*v[1] + M[8]*v[2];
}

// 3x3 matrix inverse (Gauss-Jordan)
inline bool mat3inv(const double A[9], double Ainv[9]) {
    double M[9] = {A[0],A[1],A[2], A[3],A[4],A[5], A[6],A[7],A[8]};
    double I[9] = {1,0,0, 0,1,0, 0,0,1};

    for (int col = 0; col < 3; ++col) {
        int pivot = col;
        double pv = std::abs(M[col * 3 + col]);
        for (int r = col + 1; r < 3; ++r) {
            if (std::abs(M[r * 3 + col]) > pv) { pv = std::abs(M[r * 3 + col]); pivot = r; }
        }
        if (pv < 1.0e-14) return false;
        if (pivot != col) {
            for (int c = 0; c < 3; ++c) {
                std::swap(M[col * 3 + c], M[pivot * 3 + c]);
                std::swap(I[col * 3 + c], I[pivot * 3 + c]);
            }
        }
        double inv_pivot = 1.0 / M[col * 3 + col];
        for (int c = 0; c < 3; ++c) { M[col * 3 + c] *= inv_pivot; I[col * 3 + c] *= inv_pivot; }
        for (int r = 0; r < 3; ++r) {
            if (r == col) continue;
            double f = M[r * 3 + col];
            for (int c = 0; c < 3; ++c) {
                M[r * 3 + c] -= f * M[col * 3 + c];
                I[r * 3 + c] -= f * I[col * 3 + c];
            }
        }
    }
    for (int i = 0; i < 9; ++i) Ainv[i] = I[i];
    return true;
}

// ── process noise: Singer model, discrete-time Q(Δt) ──

inline void singer_Q(double dt, double tau_m, double sigma_a, double Q[81]) {
    const double a = 1.0 / std::max(0.01, tau_m);
    const double T = std::max(1.0e-6, dt);
    const double aT = a * T;
    const double eaT = std::exp(-aT);
    const double eaT2 = eaT * eaT;

    // q11 = position variance scaling
    const double q11 = (2.0 * aT - 3.0 + 4.0 * eaT - eaT2) / (2.0 * a * a * a * a * a);
    const double q12 = (1.0 - 2.0 * eaT + eaT2) / (2.0 * a * a * a * a);
    const double q13 = (1.0 - eaT2) / (2.0 * a * a * a);
    const double q22 = (2.0 * aT + 1.0 - eaT2 * (2.0 * aT + 1.0)) / (2.0 * a * a * a);
    const double q23 = (1.0 - 2.0 * eaT + eaT2) / (2.0 * a * a);
    const double q33 = (1.0 - eaT2) / (2.0 * a);

    const double s2 = sigma_a * sigma_a;

    for (int i = 0; i < 81; ++i) Q[i] = 0.0;
    for (int axis = 0; axis < 3; ++axis) {
        const int p = axis;       // position index
        const int v = 3 + axis;   // velocity index
        const int a_ = 6 + axis;  // acceleration index
        Q[p * 9 + p] = s2 * q11;
        Q[p * 9 + v] = s2 * q12;  Q[v * 9 + p] = s2 * q12;
        Q[p * 9 + a_] = s2 * q13; Q[a_ * 9 + p] = s2 * q13;
        Q[v * 9 + v] = s2 * q22;
        Q[v * 9 + a_] = s2 * q23; Q[a_ * 9 + v] = s2 * q23;
        Q[a_ * 9 + a_] = s2 * q33;
    }
}

// ── state transition: constant-acceleration model, F(Δt) ──

inline void state_transition_F(double dt, double F[81]) {
    const double T = std::max(1.0e-6, dt);
    for (int i = 0; i < 81; ++i) F[i] = 0.0;
    for (int r = 0; r < 9; ++r) F[r * 9 + r] = 1.0;
    F[0 * 9 + 3] = T; F[1 * 9 + 4] = T; F[2 * 9 + 5] = T;   // pos += vel * dt
    F[0 * 9 + 6] = 0.5 * T * T; F[1 * 9 + 7] = 0.5 * T * T; F[2 * 9 + 8] = 0.5 * T * T; // pos += 0.5*acc*dt²
    F[3 * 9 + 6] = T; F[4 * 9 + 7] = T; F[5 * 9 + 8] = T;   // vel += acc * dt
}

// ── measurement Jacobian H: [bearing, elevation, range] w.r.t. [x,y,z, ...] ──
// bearing = atan2(dy, dx), elevation = atan2(dz, sqrt(dx²+dy²)), range = sqrt(dx²+dy²+dz²)
// dx = target_x - missile_x, etc.

inline void measurement_jacobian_H(const double rel[3], double H[27]) {
    // H is 3x9, row-major: H[row*9 + col]
    for (int i = 0; i < 27; ++i) H[i] = 0.0;

    const double dx = rel[0], dy = rel[1], dz = rel[2];
    const double r2 = dx*dx + dy*dy + dz*dz;
    const double r = std::sqrt(std::max(1.0e-6, r2));
    const double xy2 = dx*dx + dy*dy;
    const double xy = std::sqrt(std::max(1.0e-6, xy2));

    // d(bearing)/dx = -dy/xy², d(bearing)/dy = dx/xy², d(bearing)/dz = 0
    // d(elev)/dx = -dx*dz/(r²*xy), d(elev)/dy = -dy*dz/(r²*xy), d(elev)/dz = xy/r²
    // d(range)/dx = dx/r, d(range)/dy = dy/r, d(range)/dz = dz/r

    const double inv_xy2 = 1.0 / std::max(1.0e-6, xy2);
    const double inv_r2 = 1.0 / std::max(1.0e-6, r2);
    const double inv_r = 1.0 / std::max(1.0e-6, r);

    // bearing row (row 0)
    H[0] = -dy * inv_xy2;
    H[1] =  dx * inv_xy2;
    // H[2] = 0 (dz)

    // elevation row (row 1)
    const double elev_factor = 1.0 / std::max(1.0e-6, r2 * xy);
    H[9 + 0] = -dx * dz * elev_factor;
    H[9 + 1] = -dy * dz * elev_factor;
    H[9 + 2] = xy * inv_r2;

    // range row (row 2)
    H[18 + 0] = dx * inv_r;
    H[18 + 1] = dy * inv_r;
    H[18 + 2] = dz * inv_r;
}

// ── core EKF step ──

inline void ekf_predict(SeekerEkfState &s, const SeekerEkfParams &p, double dt) {
    if (!s.initialized || dt <= 1.0e-9) return;

    double F[81];
    state_transition_F(dt, F);

    // x_pred = F * x
    double x_pred[9];
    mat9vec(F, s.x, x_pred);

    // P_pred = F * P * F' + Q
    double FP[81] = {};
    for (int r = 0; r < 9; ++r)
        for (int c = 0; c < 9; ++c) {
            double sum = 0.0;
            for (int k = 0; k < 9; ++k) sum += F[r * 9 + k] * s.P[k * 9 + c];
            FP[r * 9 + c] = sum;
        }

    double FPFt[81] = {};
    for (int r = 0; r < 9; ++r)
        for (int c = 0; c < 9; ++c) {
            double sum = 0.0;
            for (int k = 0; k < 9; ++k) sum += FP[r * 9 + k] * F[c * 9 + k];
            FPFt[r * 9 + c] = sum;
        }

    double Q[81];
    singer_Q(dt, p.maneuver_tau_s, p.process_noise_sigma_a, Q);

    for (int i = 0; i < 81; ++i) s.P[i] = FPFt[i] + Q[i];
    for (int i = 0; i < 9; ++i) s.x[i] = x_pred[i];
    s.last_predict_time_s += dt;
}

inline void ekf_update(SeekerEkfState &s, const SeekerEkfParams &p,
                       double bearing_rad, double elevation_rad, double range_m,
                       const double missile_world[3]) {
    // Compute relative position from state
    double rel[3] = {s.x[0] - missile_world[0], s.x[1] - missile_world[1], s.x[2] - missile_world[2]};

    // Predicted measurement
    double r_pred = norm3(rel);
    if (r_pred < 1.0) r_pred = 1.0;
    double bearing_pred = std::atan2(rel[1], rel[0]);
    double elev_pred = std::atan2(rel[2], std::sqrt(rel[0]*rel[0] + rel[1]*rel[1]));

    // Innovation
    double dz_bearing = bearing_rad - bearing_pred;
    while (dz_bearing > M_PI) dz_bearing -= 2.0 * M_PI;
    while (dz_bearing < -M_PI) dz_bearing += 2.0 * M_PI;
    double dz_elev = elevation_rad - elev_pred;
    double dz_range = range_m - r_pred;
    double innov[3] = {dz_bearing, dz_elev, dz_range};

    // H Jacobian
    double H[27];
    measurement_jacobian_H(rel, H);

    // S = H * P * H' + R
    double PHt[27] = {};  // 9x3
    for (int r = 0; r < 9; ++r)
        for (int c = 0; c < 3; ++c) {
            double sum = 0.0;
            for (int k = 0; k < 9; ++k) sum += s.P[r * 9 + k] * H[c * 9 + k];
            PHt[r * 3 + c] = sum;
        }

    double S[9] = {};
    for (int r = 0; r < 3; ++r)
        for (int c = 0; c < 3; ++c) {
            double sum = 0.0;
            for (int k = 0; k < 9; ++k) sum += H[r * 9 + k] * PHt[k * 3 + c];
            S[r * 3 + c] = sum;
        }

    double Rmeas[9] = {
        p.meas_noise_angle_rad * p.meas_noise_angle_rad, 0, 0,
        0, p.meas_noise_angle_rad * p.meas_noise_angle_rad, 0,
        0, 0, p.meas_noise_range_m * p.meas_noise_range_m
    };
    for (int i = 0; i < 9; ++i) S[i] += Rmeas[i];

    // K = P * H' * inv(S)
    double Sinv[9];
    if (!mat3inv(S, Sinv)) return;

    double K[27] = {};  // 9x3
    for (int r = 0; r < 9; ++r)
        for (int c = 0; c < 3; ++c) {
            double sum = 0.0;
            for (int k = 0; k < 3; ++k) sum += PHt[r * 3 + k] * Sinv[k * 3 + c];
            K[r * 3 + c] = sum;
        }

    // x = x + K * innov
    double Kinnov[9];
    mat3vec(K, innov, Kinnov);
    for (int i = 0; i < 9; ++i) s.x[i] += Kinnov[i];

    // P = (I - K*H) * P
    double KH[81] = {};
    for (int r = 0; r < 9; ++r)
        for (int c = 0; c < 9; ++c) {
            double sum = 0.0;
            for (int k = 0; k < 3; ++k) sum += K[r * 3 + k] * H[k * 9 + c];
            KH[r * 9 + c] = sum;
        }

    double IKHP[81] = {};
    for (int r = 0; r < 9; ++r)
        for (int c = 0; c < 9; ++c) {
            double sum = 0.0;
            for (int k = 0; k < 9; ++k) {
                double ikh = (r == k) ? (1.0 - KH[r * 9 + k]) : -KH[r * 9 + k];
                sum += ikh * s.P[k * 9 + c];
            }
            IKHP[r * 9 + c] = sum;
        }

    for (int i = 0; i < 81; ++i) s.P[i] = IKHP[i];
}

inline void ekf_init(SeekerEkfState &s, const SeekerEkfParams &p,
                     double bearing_rad, double elevation_rad, double range_m,
                     const double missile_world[3], double current_time_s) {
    // Initialize state from first measurement
    double dx = range_m * std::cos(elevation_rad) * std::cos(bearing_rad);
    double dy = range_m * std::cos(elevation_rad) * std::sin(bearing_rad);
    double dz = range_m * std::sin(elevation_rad);

    s.x[0] = missile_world[0] + dx;
    s.x[1] = missile_world[1] + dy;
    s.x[2] = missile_world[2] + dz;
    s.x[3] = 0.0; s.x[4] = 0.0; s.x[5] = 0.0;
    s.x[6] = 0.0; s.x[7] = 0.0; s.x[8] = 0.0;

    // Initial covariance: diagonal with position uncertainty from measurement noise
    for (int i = 0; i < 81; ++i) s.P[i] = 0.0;
    double pos_var = p.meas_noise_range_m * p.meas_noise_range_m;
    double vel_var = 50.0 * 50.0;    // 50 m/s velocity uncertainty
    double acc_var = 10.0 * 10.0;    // 10 m/s² acceleration uncertainty (1g)
    s.P[0] = s.P[10] = s.P[20] = pos_var;
    s.P[30] = s.P[40] = s.P[50] = vel_var;
    s.P[60] = s.P[70] = s.P[80] = acc_var;

    s.initialized = true;
    s.last_predict_time_s = current_time_s;
}

// ── extract filtered spherical state (for PN guidance compatibility) ──

inline double ekf_filtered_bearing_deg(const SeekerEkfState &s, const double missile_world[3]) {
    double dx = s.x[0] - missile_world[0];
    double dy = s.x[1] - missile_world[1];
    return std::atan2(dy, dx) * 180.0 / M_PI;
}

inline double ekf_filtered_elevation_deg(const SeekerEkfState &s, const double missile_world[3]) {
    double dx = s.x[0] - missile_world[0];
    double dy = s.x[1] - missile_world[1];
    double dz = s.x[2] - missile_world[2];
    double xy = std::sqrt(dx*dx + dy*dy);
    return std::atan2(dz, std::max(1.0e-6, xy)) * 180.0 / M_PI;
}

inline double ekf_filtered_range_m(const SeekerEkfState &s, const double missile_world[3]) {
    double dx = s.x[0] - missile_world[0];
    double dy = s.x[1] - missile_world[1];
    double dz = s.x[2] - missile_world[2];
    return std::sqrt(dx*dx + dy*dy + dz*dz);
}

inline double ekf_closing_speed_mps(const SeekerEkfState &s, const double missile_world[3],
                                     const double missile_vel[3]) {
    double dx = s.x[0] - missile_world[0];
    double dy = s.x[1] - missile_world[1];
    double dz = s.x[2] - missile_world[2];
    double r = std::sqrt(dx*dx + dy*dy + dz*dz);
    if (r < 1.0) return 0.0;
    double rel_vx = s.x[3] - missile_vel[0];
    double rel_vy = s.x[4] - missile_vel[1];
    double rel_vz = s.x[5] - missile_vel[2];
    return -(dx * rel_vx + dy * rel_vy + dz * rel_vz) / r;
}

inline double ekf_covariance_trace(const SeekerEkfState &s) {
    double tr = 0.0;
    for (int i = 0; i < 9; ++i) tr += s.P[i * 9 + i];
    return tr;
}

inline bool ekf_has_valid_track(const SeekerEkfState &s, double current_time_s,
                                 double memory_timeout_s) {
    return s.initialized && (current_time_s - s.last_predict_time_s) < memory_timeout_s;
}

}  // namespace missile_seeker
