#pragma once

// Semi-implicit ground-contact solver.
//
// GroundContact is the last force producer before RotationalIntegrate and
// LeapfrogIntegrate, so the force accumulator already holds every other force
// of the step. The downstream integrators advance
//
//     v(t+h) = v + h a,    z(t+h) = z + h v + h^2 a / 2
//     w(t+h) = w + h tau / I
//
// with a and tau taken from the accumulator. Each function below solves for the
// contact force or torque that satisfies the contact law at the END of the step
// under exactly that update, so the contact is unconditionally stable in the
// step size instead of requiring h below the spring-damper period.
//
// * Normal: unilateral spring-damper F = max(0, k p1 - c v1), evaluated on the
//   end-of-step penetration p1 and sink velocity v1 (closed form).
// * Tangential: set-valued (exact) Coulomb friction per wheel. The admissible
//   wheel force set is rolling resistance (a segment along the wheel) plus the
//   braking/lateral friction ellipse. Lateral tyre compliance
//   v_lat = -(|v_long| / C_alpha) f_lat keeps the cornering-stiffness law at speed
//   and degenerates to exact sticking at rest. Solved as a small convex QP per
//   wheel with block Gauss-Seidel over the wheels.
// * Attitude: the pitch and roll gear-constraint laws are evaluated on the
//   end-of-step angle and rate (scalar monotone solve per axis).

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>

namespace ground_contact_solver {

struct Vec2 {
    double x = 0.0;
    double y = 0.0;
};

struct Mat2 {
    // Symmetric 2x2: [[a, b], [b, d]].
    double a = 0.0;
    double b = 0.0;
    double d = 0.0;
};

inline double quad_value(const Mat2 &P, const Vec2 &q, const Vec2 &z) {
    return 0.5 * (P.a * z.x * z.x + 2.0 * P.b * z.x * z.y + P.d * z.y * z.y) + q.x * z.x +
           q.y * z.y;
}

// ---------------------------------------------------------------------------
// Normal direction
// ---------------------------------------------------------------------------

struct NormalContactInput {
    double mass_kg = 0.0;
    double dt_s = 0.0;
    double penetration_m = 0.0; // gear height minus height above terrain, at step start
    double vertical_speed_mps = 0.0;
    double other_vertical_force_n = 0.0; // accumulator fz before contact
    double stiffness_n_per_m = 0.0;
    double damping_n_s_per_m = 0.0;
};

struct NormalContactResult {
    bool active = false;
    double force_n = 0.0;
    double end_penetration_m = 0.0;
};

// Solve F = max(0, k p1 - c v1) with p1 = p0 - h^2 F / (2m), v1 = v0 + h F / m,
// where p0 and v0 are the free (no-contact) end-of-step penetration and vertical
// speed. The contact is active only when the free motion would end in
// penetration. The result is capped so the contact alone cannot carry the body
// above the surface within the step: a unilateral contact pushes, it does not
// launch.
inline NormalContactResult solve_normal_contact(const NormalContactInput &in) {
    NormalContactResult out;
    const double m = in.mass_kg;
    const double h = in.dt_s;
    if (!(m > 0.0) || !(h > 0.0)) {
        return out;
    }
    const double free_accel = in.other_vertical_force_n / m;
    const double p0 = in.penetration_m - h * in.vertical_speed_mps - 0.5 * h * h * free_accel;
    if (!(p0 > 0.0)) {
        return out;
    }
    const double v0 = in.vertical_speed_mps + h * free_accel;
    const double k = in.stiffness_n_per_m;
    const double c = in.damping_n_s_per_m;
    const double beta = (k * h * h) / (2.0 * m) + (c * h) / m;
    double force = std::max(0.0, (k * p0 - c * v0) / (1.0 + beta));
    force = std::min(force, 2.0 * m * p0 / (h * h));
    out.active = true;
    out.force_n = force;
    out.end_penetration_m = p0 - 0.5 * h * h * force / m;
    return out;
}

// ---------------------------------------------------------------------------
// Attitude constraints (pitch, roll)
// ---------------------------------------------------------------------------

// One rotational axis as RotationalIntegrate advances it:
//     w1    = rate + h (other_torque + tau) / I
//     angle1 = angle + h (angle_rate_gain * w1 + angle_rate_bias)
// The gain and bias carry the Euler kinematics (e.g. pitch rate = q cos(roll)
// - r sin(roll)) with the other body rates held at their start-of-step values.
struct ImplicitAxis {
    double inverse_inertia = 0.0; // 1 / I; 0 for an axis that does not rotate
    double dt_s = 0.0;
    double angle_rad = 0.0;
    double rate_rad_s = 0.0;
    double other_torque_nm = 0.0;
    double angle_rate_gain = 1.0;
    double angle_rate_bias = 0.0;
};

// Find the torque tau with tau = law(angle1(tau), w1(tau)). The gear laws are
// restoring and dissipative (non-increasing in angle and rate), so with a
// non-negative angle-rate gain G(tau) = tau - law(...) rises at least as fast as
// tau and has one crossing, bracketed by [0, -G(0)]. Bisection on G also
// resolves the laws' jumps (a switched spring, a damping deadband): the crossing
// then sits on the jump, which is the set-valued (Filippov) solution rather than
// a step that chatters across it. A negative gain (the body rolled past 90 deg,
// where the rate no longer advances this angle) is treated as zero.
template <class Law> double solve_implicit_axis_torque(const ImplicitAxis &axis, Law law) {
    const double h = axis.dt_s;
    const double gain = std::max(0.0, axis.angle_rate_gain);
    auto residual = [&](double tau) {
        const double w1 = axis.rate_rad_s + h * axis.inverse_inertia * (axis.other_torque_nm + tau);
        const double angle1 = axis.angle_rad + h * (gain * w1 + axis.angle_rate_bias);
        return tau - law(angle1, w1);
    };
    const double g0 = residual(0.0);
    if (g0 == 0.0 || !std::isfinite(g0)) {
        return 0.0;
    }
    if (!(h > 0.0) || !(axis.inverse_inertia > 0.0)) {
        // The axis does not move this step: the law is explicit.
        return -g0;
    }
    const double direction = (g0 < 0.0) ? 1.0 : -1.0;
    double near_tau = 0.0;
    double far_tau = direction * std::abs(g0);
    int expansions = 0;
    // The laws' only non-monotone pieces are damping-deadband steps, far smaller
    // than |G(0)| once any spring or damping acts; expansion rarely runs.
    while ((residual(far_tau) < 0.0) == (g0 < 0.0)) {
        near_tau = far_tau;
        far_tau *= 2.0;
        if (++expansions > 64 || !std::isfinite(far_tau)) {
            return near_tau;
        }
    }
    for (int iter = 0; iter < 200; ++iter) {
        const double mid = 0.5 * (near_tau + far_tau);
        if ((residual(mid) < 0.0) == (g0 < 0.0)) {
            near_tau = mid;
        } else {
            far_tau = mid;
        }
        if (std::abs(far_tau - near_tau) <= 1e-12 * std::max(1.0, std::abs(far_tau))) {
            break;
        }
    }
    return 0.5 * (near_tau + far_tau);
}

// ---------------------------------------------------------------------------
// Tangential friction
// ---------------------------------------------------------------------------

// Admissible force set of one wheel, in its own frame (x forward, y left):
//     S = [-rolling, rolling] x {0}  (+)  { (bx, by) : (bx/brake)^2 + (by/lateral)^2 <= 1 }
// Rolling resistance is a segment that does not consume the ellipse budget
// (matching the previous explicit law); braking and lateral grip share the
// friction ellipse. brake == 0 degenerates the ellipse to the lateral segment,
// and S becomes a box.
struct WheelForceSet {
    double rolling_n = 0.0;
    double brake_n = 0.0;
    double lateral_n = 0.0;
};

inline bool in_wheel_force_set(const Vec2 &f, const WheelForceSet &s, double rel_tol = 1e-9) {
    const double slack_x = s.rolling_n + s.brake_n;
    if (std::abs(f.x) > slack_x * (1.0 + rel_tol) + 1e-12) {
        return false;
    }
    if (std::abs(f.y) > s.lateral_n * (1.0 + rel_tol) + 1e-12) {
        return false;
    }
    if (s.brake_n <= 0.0) {
        return std::abs(f.x) <= s.rolling_n * (1.0 + rel_tol) + 1e-12;
    }
    const double ex = std::max(0.0, std::abs(f.x) - s.rolling_n) / s.brake_n;
    const double ey = (s.lateral_n > 0.0) ? f.y / s.lateral_n : 0.0;
    return ex * ex + ey * ey <= 1.0 + 2.0 * rel_tol;
}

namespace detail {

// Minimiser of 0.5 z'Pz + q'z (P symmetric positive definite).
inline Vec2 unconstrained_min(const Mat2 &P, const Vec2 &q) {
    const double det = P.a * P.d - P.b * P.b;
    return {(-P.d * q.x + P.b * q.y) / det, (P.b * q.x - P.a * q.y) / det};
}

// Minimiser of 0.5 z'Pz + q'z over the disk |z - c| <= rho (trust-region
// subproblem, solved on the secular equation by bisection).
inline Vec2 disk_min(const Mat2 &P, const Vec2 &q, const Vec2 &c, double rho) {
    // Shift: z = c + d, objective 0.5 d'Pd + (q + Pc)'d.
    const Vec2 qs{q.x + P.a * c.x + P.b * c.y, q.y + P.b * c.x + P.d * c.y};
    const Vec2 d0 = unconstrained_min(P, qs);
    if (d0.x * d0.x + d0.y * d0.y <= rho * rho) {
        return {c.x + d0.x, c.y + d0.y};
    }
    auto step_for = [&](double mu) {
        const Mat2 Pm{P.a + mu, P.b, P.d + mu};
        return unconstrained_min(Pm, qs);
    };
    double lo = 0.0;
    double hi = std::sqrt(qs.x * qs.x + qs.y * qs.y) / std::max(rho, 1e-300);
    for (int iter = 0; iter < 200; ++iter) {
        const double mid = 0.5 * (lo + hi);
        const Vec2 d = step_for(mid);
        if (d.x * d.x + d.y * d.y > rho * rho) {
            lo = mid;
        } else {
            hi = mid;
        }
        if (hi - lo <= 1e-15 * std::max(1.0, hi)) {
            break;
        }
    }
    const Vec2 d = step_for(hi);
    return {c.x + d.x, c.y + d.y};
}

inline Vec2 box_min(const Mat2 &P, const Vec2 &q, double ax, double ay) {
    // Minimiser of a strictly convex quadratic over |x| <= ax, |y| <= ay:
    // the unconstrained point, or the best point on one of the four edges.
    Vec2 best{};
    double best_value = 0.0;
    bool have = false;
    auto consider = [&](const Vec2 &z) {
        if (std::abs(z.x) > ax * (1.0 + 1e-12) + 1e-300 ||
            std::abs(z.y) > ay * (1.0 + 1e-12) + 1e-300) {
            return;
        }
        const double value = quad_value(P, q, z);
        if (!have || value < best_value) {
            best = z;
            best_value = value;
            have = true;
        }
    };
    consider(unconstrained_min(P, q));
    for (double sx : {-ax, ax}) {
        const double y = (P.d > 0.0) ? std::clamp(-(q.y + P.b * sx) / P.d, -ay, ay) : 0.0;
        consider({sx, y});
    }
    for (double sy : {-ay, ay}) {
        const double x = (P.a > 0.0) ? std::clamp(-(q.x + P.b * sy) / P.a, -ax, ax) : 0.0;
        consider({x, sy});
    }
    return have ? best : Vec2{};
}

} // namespace detail

// Minimiser of 0.5 f'Af + g'f over the wheel force set S (A symmetric positive
// definite). In the scaled variable z = (x * lateral / brake, y) the set is a
// capsule (a segment of half-length rolling * lateral / brake swept by a disk of
// radius lateral), so the minimiser is either the unconstrained point, a point
// on one of the two flat sides, or a point on one of the two end caps.
inline Vec2 minimize_over_wheel_force_set(const Mat2 &A, const Vec2 &g, const WheelForceSet &s) {
    const double a = std::max(0.0, s.rolling_n);
    const double b = std::max(0.0, s.brake_n);
    const double r = std::max(0.0, s.lateral_n);
    if (a <= 0.0 && b <= 0.0 && r <= 0.0) {
        return {};
    }
    if (b <= 1e-12 * std::max(r, 1.0) || r <= 0.0) {
        return detail::box_min(A, g, a + (r <= 0.0 ? b : 0.0), r);
    }
    const double scale = r / b; // z.x = scale * f.x
    const double inv = 1.0 / scale;
    const Mat2 P{A.a * inv * inv, A.b * inv, A.d};
    const Vec2 q{g.x * inv, g.y};
    const double half_length = a * scale;
    auto inside = [&](const Vec2 &z) {
        const double dx = std::max(0.0, std::abs(z.x) - half_length);
        return dx * dx + z.y * z.y <= r * r * (1.0 + 1e-10);
    };

    Vec2 best{};
    double best_value = 0.0;
    bool have = false;
    auto consider = [&](const Vec2 &z) {
        if (!inside(z)) {
            return;
        }
        const double value = quad_value(P, q, z);
        if (!have || value < best_value) {
            best = z;
            best_value = value;
            have = true;
        }
    };
    consider(detail::unconstrained_min(P, q));
    for (double sy : {-r, r}) {
        const double x = std::clamp(-(q.x + P.b * sy) / P.a, -half_length, half_length);
        consider({x, sy});
    }
    for (double side : {-1.0, 1.0}) {
        // End cap on this side: the disk of radius r around the segment end. With no
        // rolling resistance both caps are the whole disk.
        const double cx = side * half_length;
        const Vec2 z = detail::disk_min(P, q, {cx, 0.0}, r);
        const double tol = 1e-12 * std::max(1.0, half_length);
        const bool on_cap = half_length <= 0.0 || (side > 0.0 ? z.x >= cx - tol : z.x <= cx + tol);
        if (on_cap) {
            consider(z);
        }
    }
    if (!have) {
        return {};
    }
    return {best.x * inv, best.y};
}

// Planar rigid body state for the tangential solve, in the body-heading frame:
// u = (v_forward, v_left, yaw_rate). Mass and yaw inertia are diagonal there.
struct PlanarBody {
    double mass_kg = 0.0;
    double inverse_yaw_inertia = 0.0; // 0 when the body carries no rotational state
};

// One wheel at body-forward offset x_m, steered by steer_rad. Its Jacobian maps
// the body twist to the wheel-frame contact velocity:
//     v_wheel = J u,  J = [[c, s, s x], [-s, c, c x]]  (c = cos steer, s = sin steer)
// and J^T maps the wheel-frame force to the body (forward force, left force,
// yaw torque).
struct Wheel {
    double x_m = 0.0;
    double steer_rad = 0.0;
    WheelForceSet force_set{};
    double lateral_compliance_s_per_kg = 0.0; // |v_long| / C_alpha
};

template <std::size_t N> struct TangentialResult {
    std::array<Vec2, N> wheel_force{};
    double force_forward_n = 0.0;
    double force_left_n = 0.0;
    double torque_yaw_nm = 0.0;
    int sweeps = 0;
    bool converged = false;
};

// Solve the implicit tangential step: find wheel forces f_i in S_i such that
// each f_i minimises its share of 0.5 f'(h J M^-1 J' + R) f + (J u_free)'f, i.e.
// the end-of-step contact velocity v_i = J_i u1 + R_i f_i lies in the normal
// cone of S_i at f_i (maximum dissipation). u_free is the end-of-step twist
// without contact. Block Gauss-Seidel over the wheels.
template <std::size_t N>
TangentialResult<N> solve_tangential_contact(const PlanarBody &body, double dt_s,
                                             const std::array<double, 3> &u_free,
                                             const std::array<Wheel, N> &wheels,
                                             int max_sweeps = 64, double tolerance_n = 1e-6) {
    TangentialResult<N> out;
    if (!(body.mass_kg > 0.0) || !(body.inverse_yaw_inertia >= 0.0) || !(dt_s > 0.0)) {
        return out;
    }
    const double h = dt_s;
    const double inv_m = 1.0 / body.mass_kg;
    const double inv_i = body.inverse_yaw_inertia;

    struct Row {
        double c, s, x;
    };
    std::array<Row, N> rows{};
    for (std::size_t i = 0; i < N; ++i) {
        rows[i] = {std::cos(wheels[i].steer_rad), std::sin(wheels[i].steer_rad), wheels[i].x_m};
    }
    auto jt_times = [&](std::size_t i, const Vec2 &f) {
        const Row &w = rows[i];
        return std::array<double, 3>{w.c * f.x - w.s * f.y, w.s * f.x + w.c * f.y,
                                     w.s * w.x * f.x + w.c * w.x * f.y};
    };
    auto j_times = [&](std::size_t i, const std::array<double, 3> &u) {
        const Row &w = rows[i];
        return Vec2{w.c * u[0] + w.s * u[1] + w.s * w.x * u[2],
                    -w.s * u[0] + w.c * u[1] + w.c * w.x * u[2]};
    };

    for (int sweep = 1; sweep <= max_sweeps; ++sweep) {
        double max_change = 0.0;
        for (std::size_t i = 0; i < N; ++i) {
            // Twist with every other wheel's current force applied.
            std::array<double, 3> u = u_free;
            for (std::size_t k = 0; k < N; ++k) {
                if (k == i) {
                    continue;
                }
                const std::array<double, 3> q = jt_times(k, out.wheel_force[k]);
                u[0] += h * inv_m * q[0];
                u[1] += h * inv_m * q[1];
                u[2] += h * inv_i * q[2];
            }
            const Row &w = rows[i];
            // A_i = h J_i M^-1 J_i^T + diag(0, R_i)
            const double j00 = w.c, j01 = w.s, j02 = w.s * w.x;
            const double j10 = -w.s, j11 = w.c, j12 = w.c * w.x;
            Mat2 A;
            A.a = h * (inv_m * (j00 * j00 + j01 * j01) + inv_i * j02 * j02);
            A.b = h * (inv_m * (j00 * j10 + j01 * j11) + inv_i * j02 * j12);
            A.d = h * (inv_m * (j10 * j10 + j11 * j11) + inv_i * j12 * j12) +
                  std::max(0.0, wheels[i].lateral_compliance_s_per_kg);
            const Vec2 g = j_times(i, u);
            const Vec2 f = minimize_over_wheel_force_set(A, g, wheels[i].force_set);
            max_change = std::max(max_change, std::max(std::abs(f.x - out.wheel_force[i].x),
                                                       std::abs(f.y - out.wheel_force[i].y)));
            out.wheel_force[i] = f;
        }
        out.sweeps = sweep;
        if (max_change <= tolerance_n) {
            out.converged = true;
            break;
        }
    }
    for (std::size_t i = 0; i < N; ++i) {
        const std::array<double, 3> q = jt_times(i, out.wheel_force[i]);
        out.force_forward_n += q[0];
        out.force_left_n += q[1];
        out.torque_yaw_nm += q[2];
    }
    return out;
}

} // namespace ground_contact_solver
