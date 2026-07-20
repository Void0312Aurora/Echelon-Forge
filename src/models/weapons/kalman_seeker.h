#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>

#include "components/combat/common/missile_seeker_state.h"

namespace missile_seeker {

// SeekerEkfState/SeekerEkfParams are defined in
// components/combat/common/missile_seeker_state.h (a components-visible
// leaf); the two value types are declared there so the Missile component
// can embed them by value without depending on this models/ header.

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
        for (int c = 0; c < 9; ++c)
            s += M[r * 9 + c] * v[c];
        out[r] = s;
    }
}

inline void mat9tvec(const double M[81], const double v[9], double out[9]) {
    for (int r = 0; r < 9; ++r) {
        double s = 0.0;
        for (int c = 0; c < 9; ++c)
            s += M[c * 9 + r] * v[c];
        out[r] = s;
    }
}

inline void mat3vec(const double M[9], const double v[3], double out[3]) {
    out[0] = M[0] * v[0] + M[1] * v[1] + M[2] * v[2];
    out[1] = M[3] * v[0] + M[4] * v[1] + M[5] * v[2];
    out[2] = M[6] * v[0] + M[7] * v[1] + M[8] * v[2];
}

// K is 9x3 row-major, innov is 3-vector → 9-vector output
inline void mat9x3vec(const double K[27], const double v[3], double out[9]) {
    for (int r = 0; r < 9; ++r) {
        out[r] = K[r * 3 + 0] * v[0] + K[r * 3 + 1] * v[1] + K[r * 3 + 2] * v[2];
    }
}

// 3x3 matrix inverse (Gauss-Jordan)
inline bool mat3inv(const double A[9], double Ainv[9]) {
    double M[9] = {A[0], A[1], A[2], A[3], A[4], A[5], A[6], A[7], A[8]};
    double I[9] = {1, 0, 0, 0, 1, 0, 0, 0, 1};

    for (int col = 0; col < 3; ++col) {
        int pivot = col;
        double pv = std::abs(M[col * 3 + col]);
        for (int r = col + 1; r < 3; ++r) {
            if (std::abs(M[r * 3 + col]) > pv) {
                pv = std::abs(M[r * 3 + col]);
                pivot = r;
            }
        }
        if (pv < 1.0e-14) return false;
        if (pivot != col) {
            for (int c = 0; c < 3; ++c) {
                std::swap(M[col * 3 + c], M[pivot * 3 + c]);
                std::swap(I[col * 3 + c], I[pivot * 3 + c]);
            }
        }
        double inv_pivot = 1.0 / M[col * 3 + col];
        for (int c = 0; c < 3; ++c) {
            M[col * 3 + c] *= inv_pivot;
            I[col * 3 + c] *= inv_pivot;
        }
        for (int r = 0; r < 3; ++r) {
            if (r == col) continue;
            double f = M[r * 3 + col];
            for (int c = 0; c < 3; ++c) {
                M[r * 3 + c] -= f * M[col * 3 + c];
                I[r * 3 + c] -= f * I[col * 3 + c];
            }
        }
    }
    for (int i = 0; i < 9; ++i)
        Ainv[i] = I[i];
    return true;
}

// ── process noise: white-jerk model, discrete-time Q(dt) ──

inline void singer_Q(double dt, double tau_m, double sigma_a, double Q[81]) {
    (void)tau_m; // Reserved for a future full Singer transition model.
    const double T = std::max(1.0e-6, dt);
    const double T2 = T * T;
    const double T3 = T2 * T;
    const double T4 = T3 * T;
    const double T5 = T4 * T;
    const double q = std::max(0.0, sigma_a) * std::max(0.0, sigma_a);

    const double q11 = q * T5 / 20.0;
    const double q12 = q * T4 / 8.0;
    const double q13 = q * T3 / 6.0;
    const double q22 = q * T3 / 3.0;
    const double q23 = q * T2 / 2.0;
    const double q33 = q * T;

    for (int i = 0; i < 81; ++i)
        Q[i] = 0.0;
    for (int axis = 0; axis < 3; ++axis) {
        const int p = axis;      // position index
        const int v = 3 + axis;  // velocity index
        const int a_ = 6 + axis; // acceleration index
        Q[p * 9 + p] = q11;
        Q[p * 9 + v] = q12;
        Q[v * 9 + p] = q12;
        Q[p * 9 + a_] = q13;
        Q[a_ * 9 + p] = q13;
        Q[v * 9 + v] = q22;
        Q[v * 9 + a_] = q23;
        Q[a_ * 9 + v] = q23;
        Q[a_ * 9 + a_] = q33;
    }
}

// ── state transition: constant-acceleration model, F(Δt) ──

inline void state_transition_F(double dt, double F[81]) {
    const double T = std::max(1.0e-6, dt);
    for (int i = 0; i < 81; ++i)
        F[i] = 0.0;
    for (int r = 0; r < 9; ++r)
        F[r * 9 + r] = 1.0;
    F[0 * 9 + 3] = T;
    F[1 * 9 + 4] = T;
    F[2 * 9 + 5] = T; // pos += vel * dt
    F[0 * 9 + 6] = 0.5 * T * T;
    F[1 * 9 + 7] = 0.5 * T * T;
    F[2 * 9 + 8] = 0.5 * T * T; // pos += 0.5*acc*dt²
    F[3 * 9 + 6] = T;
    F[4 * 9 + 7] = T;
    F[5 * 9 + 8] = T; // vel += acc * dt
}

// ── measurement Jacobian H: [bearing, elevation, range] w.r.t. [x,y,z, ...] ──
// bearing = atan2(dy, dx), elevation = atan2(dz, sqrt(dx²+dy²)), range = sqrt(dx²+dy²+dz²)
// dx = target_x - missile_x, etc.

inline void measurement_jacobian_H(const double rel[3], double H[27]) {
    // H is 3x9, row-major: H[row*9 + col]
    for (int i = 0; i < 27; ++i)
        H[i] = 0.0;

    const double dx = rel[0], dy = rel[1], dz = rel[2];
    const double r2 = dx * dx + dy * dy + dz * dz;
    const double r = std::sqrt(std::max(1.0e-6, r2));
    const double xy2 = dx * dx + dy * dy;
    const double xy = std::sqrt(std::max(1.0e-6, xy2));

    // d(bearing)/dx = -dy/xy², d(bearing)/dy = dx/xy², d(bearing)/dz = 0
    // d(elev)/dx = -dx*dz/(r²*xy), d(elev)/dy = -dy*dz/(r²*xy), d(elev)/dz = xy/r²
    // d(range)/dx = dx/r, d(range)/dy = dy/r, d(range)/dz = dz/r

    const double inv_xy2 = 1.0 / std::max(1.0e-6, xy2);
    const double inv_r2 = 1.0 / std::max(1.0e-6, r2);
    const double inv_r = 1.0 / std::max(1.0e-6, r);

    // bearing row (row 0)
    H[0] = -dy * inv_xy2;
    H[1] = dx * inv_xy2;
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
            for (int k = 0; k < 9; ++k)
                sum += F[r * 9 + k] * s.P[k * 9 + c];
            FP[r * 9 + c] = sum;
        }

    double FPFt[81] = {};
    for (int r = 0; r < 9; ++r)
        for (int c = 0; c < 9; ++c) {
            double sum = 0.0;
            for (int k = 0; k < 9; ++k)
                sum += FP[r * 9 + k] * F[c * 9 + k];
            FPFt[r * 9 + c] = sum;
        }

    double Q[81];
    singer_Q(dt, p.maneuver_tau_s, p.process_noise_sigma_a, Q);

    for (int i = 0; i < 81; ++i)
        s.P[i] = FPFt[i] + Q[i];
    for (int i = 0; i < 9; ++i)
        s.x[i] = x_pred[i];
    s.last_predict_time_s += dt;
}

// Convert body-relative bearing/elevation/range to world-frame position.
// bearing/elevation are relative to missile body (+X forward, +Y right, +Z up).
// heading_rad rotates body → world around Z axis.
inline void body_rel_to_world(double bearing_rad, double elevation_rad, double range_m,
                              double heading_rad, const double missile_world[3],
                              double world_pos[3]) {
    double ce = std::cos(elevation_rad);
    double dx_body = range_m * ce * std::cos(bearing_rad);
    double dy_body = range_m * ce * std::sin(bearing_rad);
    double dz_body = range_m * std::sin(elevation_rad);
    double ch = std::cos(heading_rad);
    double sh = std::sin(heading_rad);
    world_pos[0] = missile_world[0] + dx_body * ch - dy_body * sh;
    world_pos[1] = missile_world[1] + dx_body * sh + dy_body * ch;
    world_pos[2] = missile_world[2] + dz_body;
}

// Convert world-frame relative position to body-relative bearing/elevation/range.
inline void world_to_body_rel(const double world_pos[3], const double missile_world[3],
                              double heading_rad, double &bearing_rad, double &elevation_rad,
                              double &range_m) {
    double dx = world_pos[0] - missile_world[0];
    double dy = world_pos[1] - missile_world[1];
    double dz = world_pos[2] - missile_world[2];
    double ch = std::cos(heading_rad);
    double sh = std::sin(heading_rad);
    double dx_body = dx * ch + dy * sh;
    double dy_body = -dx * sh + dy * ch;
    bearing_rad = std::atan2(dy_body, dx_body);
    double xy = std::sqrt(dx_body * dx_body + dy_body * dy_body);
    elevation_rad = std::atan2(dz, std::max(1.0e-6, xy));
    range_m = std::sqrt(dx_body * dx_body + dy_body * dy_body + dz * dz);
}

inline void ekf_update(SeekerEkfState &s, const SeekerEkfParams &p, double bearing_rad,
                       double elevation_rad, double range_m, const double missile_world[3],
                       double heading_rad) {
    // Compute predicted body-relative measurement from world state
    double bearing_pred, elev_pred, r_pred;
    world_to_body_rel(s.x, missile_world, heading_rad, bearing_pred, elev_pred, r_pred);
    if (r_pred < 1.0) r_pred = 1.0;

    // Innovation
    double dz_bearing = bearing_rad - bearing_pred;
    while (dz_bearing > M_PI)
        dz_bearing -= 2.0 * M_PI;
    while (dz_bearing < -M_PI)
        dz_bearing += 2.0 * M_PI;
    double dz_elev = elevation_rad - elev_pred;
    double dz_range = range_m - r_pred;
    double innov[3] = {dz_bearing, dz_elev, dz_range};

    double rel[3] = {s.x[0] - missile_world[0], s.x[1] - missile_world[1],
                     s.x[2] - missile_world[2]};

    // H Jacobian (world-frame)
    double H[27];
    measurement_jacobian_H(rel, H);

    // S = H * P * H' + R
    double PHt[27] = {}; // 9x3
    for (int r = 0; r < 9; ++r)
        for (int c = 0; c < 3; ++c) {
            double sum = 0.0;
            for (int k = 0; k < 9; ++k)
                sum += s.P[r * 9 + k] * H[c * 9 + k];
            PHt[r * 3 + c] = sum;
        }

    double S[9] = {};
    for (int r = 0; r < 3; ++r)
        for (int c = 0; c < 3; ++c) {
            double sum = 0.0;
            for (int k = 0; k < 9; ++k)
                sum += H[r * 9 + k] * PHt[k * 3 + c];
            S[r * 3 + c] = sum;
        }

    double Rmeas[9] = {p.meas_noise_angle_rad * p.meas_noise_angle_rad, 0, 0, 0,
                       p.meas_noise_angle_rad * p.meas_noise_angle_rad, 0, 0, 0,
                       p.meas_noise_range_m * p.meas_noise_range_m};
    for (int i = 0; i < 9; ++i)
        S[i] += Rmeas[i];

    // K = P * H' * inv(S)
    double Sinv[9];
    if (!mat3inv(S, Sinv)) return;

    double K[27] = {}; // 9x3
    for (int r = 0; r < 9; ++r)
        for (int c = 0; c < 3; ++c) {
            double sum = 0.0;
            for (int k = 0; k < 3; ++k)
                sum += PHt[r * 3 + k] * Sinv[k * 3 + c];
            K[r * 3 + c] = sum;
        }

    // x = x + K * innov
    double Kinnov[9];
    mat9x3vec(K, innov, Kinnov);
    for (int i = 0; i < 9; ++i)
        s.x[i] += Kinnov[i];

    // P = (I - K*H) * P * (I - K*H)' + K * R * K'
    double KH[81] = {};
    for (int r = 0; r < 9; ++r)
        for (int c = 0; c < 9; ++c) {
            double sum = 0.0;
            for (int k = 0; k < 3; ++k)
                sum += K[r * 3 + k] * H[k * 9 + c];
            KH[r * 9 + c] = sum;
        }

    double IKH[81] = {};
    for (int r = 0; r < 9; ++r)
        for (int c = 0; c < 9; ++c)
            IKH[r * 9 + c] = (r == c ? 1.0 : 0.0) - KH[r * 9 + c];

    double IKHP[81] = {};
    for (int r = 0; r < 9; ++r)
        for (int c = 0; c < 9; ++c) {
            double sum = 0.0;
            for (int k = 0; k < 9; ++k)
                sum += IKH[r * 9 + k] * s.P[k * 9 + c];
            IKHP[r * 9 + c] = sum;
        }

    double joseph[81] = {};
    for (int r = 0; r < 9; ++r)
        for (int c = 0; c < 9; ++c) {
            double sum = 0.0;
            for (int k = 0; k < 9; ++k)
                sum += IKHP[r * 9 + k] * IKH[c * 9 + k];
            joseph[r * 9 + c] = sum;
        }

    double KR[27] = {};
    for (int r = 0; r < 9; ++r)
        for (int c = 0; c < 3; ++c) {
            double sum = 0.0;
            for (int k = 0; k < 3; ++k)
                sum += K[r * 3 + k] * Rmeas[k * 3 + c];
            KR[r * 3 + c] = sum;
        }
    for (int r = 0; r < 9; ++r)
        for (int c = 0; c < 9; ++c) {
            double sum = 0.0;
            for (int k = 0; k < 3; ++k)
                sum += KR[r * 3 + k] * K[c * 3 + k];
            joseph[r * 9 + c] += sum;
        }

    for (int r = 0; r < 9; ++r)
        for (int c = r; c < 9; ++c) {
            double v = 0.5 * (joseph[r * 9 + c] + joseph[c * 9 + r]);
            s.P[r * 9 + c] = v;
            s.P[c * 9 + r] = v;
        }
}

inline void ekf_init(SeekerEkfState &s, const SeekerEkfParams &p, double bearing_rad,
                     double elevation_rad, double range_m, const double missile_world[3],
                     double heading_rad, double current_time_s) {
    // Initialize state from body-relative measurement converted to world frame
    double world_pos[3];
    body_rel_to_world(bearing_rad, elevation_rad, range_m, heading_rad, missile_world, world_pos);
    s.x[0] = world_pos[0];
    s.x[1] = world_pos[1];
    s.x[2] = world_pos[2];
    s.x[3] = 0.0;
    s.x[4] = 0.0;
    s.x[5] = 0.0;
    s.x[6] = 0.0;
    s.x[7] = 0.0;
    s.x[8] = 0.0;

    // Initial covariance: diagonal with position uncertainty from measurement noise
    for (int i = 0; i < 81; ++i)
        s.P[i] = 0.0;
    double pos_var = p.meas_noise_range_m * p.meas_noise_range_m;
    double vel_var = 50.0 * 50.0; // 50 m/s velocity uncertainty
    double acc_var = 10.0 * 10.0; // 10 m/s² acceleration uncertainty (1g)
    s.P[0] = s.P[10] = s.P[20] = pos_var;
    s.P[30] = s.P[40] = s.P[50] = vel_var;
    s.P[60] = s.P[70] = s.P[80] = acc_var;

    s.initialized = true;
    s.last_predict_time_s = current_time_s;
}

// ── extract filtered body-relative spherical state (for PN guidance compatibility) ──

inline double ekf_filtered_bearing_deg(const SeekerEkfState &s, const double missile_world[3],
                                       double heading_rad) {
    double bearing_rad, elev_rad, range_m;
    world_to_body_rel(s.x, missile_world, heading_rad, bearing_rad, elev_rad, range_m);
    return bearing_rad * 180.0 / M_PI;
}

inline double ekf_filtered_elevation_deg(const SeekerEkfState &s, const double missile_world[3],
                                         double heading_rad) {
    double bearing_rad, elev_rad, range_m;
    world_to_body_rel(s.x, missile_world, heading_rad, bearing_rad, elev_rad, range_m);
    return elev_rad * 180.0 / M_PI;
}

inline double ekf_filtered_range_m(const SeekerEkfState &s, const double missile_world[3],
                                   double heading_rad) {
    double bearing_rad, elev_rad, range_m;
    world_to_body_rel(s.x, missile_world, heading_rad, bearing_rad, elev_rad, range_m);
    return range_m;
}

inline double ekf_closing_speed_mps(const SeekerEkfState &s, const double missile_world[3],
                                    const double missile_vel[3]) {
    double dx = s.x[0] - missile_world[0];
    double dy = s.x[1] - missile_world[1];
    double dz = s.x[2] - missile_world[2];
    double r = std::sqrt(dx * dx + dy * dy + dz * dz);
    if (r < 1.0) return 0.0;
    double rel_vx = s.x[3] - missile_vel[0];
    double rel_vy = s.x[4] - missile_vel[1];
    double rel_vz = s.x[5] - missile_vel[2];
    return -(dx * rel_vx + dy * rel_vy + dz * rel_vz) / r;
}

inline double ekf_covariance_trace(const SeekerEkfState &s) {
    double tr = 0.0;
    for (int i = 0; i < 9; ++i)
        tr += s.P[i * 9 + i];
    return tr;
}

inline bool ekf_has_valid_track(const SeekerEkfState &s, double current_time_s,
                                double memory_timeout_s) {
    return s.initialized && (current_time_s - s.last_predict_time_s) < memory_timeout_s;
}

} // namespace missile_seeker
