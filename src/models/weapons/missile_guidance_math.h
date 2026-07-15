#pragma once

#include <algorithm>
#include <cmath>

#include "components/basic/common.h"

namespace missile_guidance {

using Vec3 = Math::Vector3;

inline Vec3 operator+(const Vec3& a, const Vec3& b) {
    return {a.x + b.x, a.y + b.y, a.z + b.z};
}

inline Vec3 operator-(const Vec3& a, const Vec3& b) {
    return {a.x - b.x, a.y - b.y, a.z - b.z};
}

inline Vec3 operator*(const Vec3& v, double s) {
    return {v.x * s, v.y * s, v.z * s};
}

inline Vec3 operator/(const Vec3& v, double s) {
    return s == 0.0 ? Vec3{0.0, 0.0, 0.0} : Vec3{v.x / s, v.y / s, v.z / s};
}

inline double dot(const Vec3& a, const Vec3& b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

inline Vec3 cross(const Vec3& a, const Vec3& b) {
    return {
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x,
    };
}

inline double norm(const Vec3& v) {
    return std::sqrt(dot(v, v));
}

inline Vec3 normalize(const Vec3& v) {
    const double n = norm(v);
    if (n <= 1.0e-9) {
        return {0.0, 0.0, 0.0};
    }
    return v / n;
}

inline double clamp01(double v) {
    return std::clamp(v, 0.0, 1.0);
}

inline double lerp(double a, double b, double t) {
    return a + (b - a) * clamp01(t);
}

inline double normalize_angle_deg(double angle) {
    while (angle > 180.0) angle -= 360.0;
    while (angle < -180.0) angle += 360.0;
    return angle;
}

inline double shortest_angle_delta_deg(double from_deg, double to_deg) {
    return normalize_angle_deg(to_deg - from_deg);
}

inline double exp_smooth(double previous, double measurement, double tau_s, double dt) {
    if (tau_s <= 1.0e-6 || dt <= 0.0) {
        return measurement;
    }
    const double alpha = std::clamp(dt / (tau_s + dt), 0.0, 1.0);
    return previous + alpha * (measurement - previous);
}

inline double exp_smooth_angle_deg(double previous_deg, double measurement_deg, double tau_s, double dt) {
    if (tau_s <= 1.0e-6 || dt <= 0.0) {
        return measurement_deg;
    }
    const double alpha = std::clamp(dt / (tau_s + dt), 0.0, 1.0);
    return normalize_angle_deg(previous_deg + alpha * shortest_angle_delta_deg(previous_deg, measurement_deg));
}

inline Vec3 velocity_to_vec3(const Velocity& velocity) {
    return {velocity.vx, velocity.vy, velocity.vz};
}

inline void write_velocity(Velocity& velocity, const Vec3& v) {
    velocity.vx = v.x;
    velocity.vy = v.y;
    velocity.vz = v.z;
}

inline Vec3 forward_from_heading_deg(double heading_deg) {
    const double heading_rad = Math::to_radians(heading_deg);
    return {
        std::sin(heading_rad),
        std::cos(heading_rad),
        0.0,
    };
}

inline Vec3 right_from_heading_deg(double heading_deg) {
    const double heading_rad = Math::to_radians(heading_deg);
    return {
        std::cos(heading_rad),
        -std::sin(heading_rad),
        0.0,
    };
}

inline Vec3 world_los_from_relative_angles(
    double bearing_deg,
    double elevation_deg,
    const Transform& transform
) {
    const double az = Math::to_radians(bearing_deg);
    const double el = Math::to_radians(elevation_deg);
    const double cos_el = std::cos(el);
    const Vec3 forward = forward_from_heading_deg(transform.heading);
    const Vec3 right = right_from_heading_deg(transform.heading);
    const Vec3 up = {0.0, 0.0, 1.0};
    return normalize(
        (forward * (cos_el * std::cos(az))) +
        (right * (cos_el * std::sin(az))) +
        (up * std::sin(el)));
}

inline Vec3 project_lateral(const Vec3& acceleration, const Vec3& velocity_dir) {
    return acceleration - velocity_dir * dot(acceleration, velocity_dir);
}

inline Vec3 world_los_angular_rate(const Vec3& previous_los, const Vec3& current_los,
                                   double elapsed_s) {
    const Vec3 previous = normalize(previous_los);
    const Vec3 current = normalize(current_los);
    if (elapsed_s <= 1.0e-6 || norm(previous) <= 1.0e-6 || norm(current) <= 1.0e-6) {
        return {0.0, 0.0, 0.0};
    }

    const Vec3 rotation_axis = cross(previous, current);
    const double sin_angle = norm(rotation_axis);
    const double cos_angle = std::clamp(dot(previous, current), -1.0, 1.0);
    if (sin_angle <= 1.0e-12) {
        return {0.0, 0.0, 0.0};
    }

    const double angle_rad = std::atan2(sin_angle, cos_angle);
    return rotation_axis * (angle_rad / (sin_angle * elapsed_s));
}

inline Vec3 transverse_pn_acceleration(const Vec3& los_angular_rate,
                                       const Vec3& velocity_dir, double closing_speed_mps,
                                       double nav_gain, double gain_scale) {
    if (closing_speed_mps <= 0.0 || nav_gain <= 0.0 || gain_scale <= 0.0) {
        return {0.0, 0.0, 0.0};
    }
    const Vec3 velocity_axis = normalize(velocity_dir);
    if (norm(velocity_axis) <= 1.0e-6) {
        return {0.0, 0.0, 0.0};
    }
    return project_lateral(cross(los_angular_rate, velocity_axis), velocity_axis) *
           (gain_scale * nav_gain * closing_speed_mps);
}

inline double capture_base_range_factor(double speed_mps, double range_m,
                                        double reference_range_m, int mode) {
    const double safe_range_m = std::max(1.0, range_m);
    const double safe_reference_range_m = std::max(1.0, reference_range_m);
    const double denominator_m = mode == 1 ? safe_reference_range_m : safe_range_m;
    return speed_mps * speed_mps / denominator_m;
}

inline double capture_terminal_weight(double range_m, double reference_range_m,
                                      double minimum_weight, double maximum_weight, int mode) {
    if (mode == 1) {
        return 1.0;
    }
    const double reciprocal = std::max(1.0, reference_range_m) / std::max(1.0, range_m);
    if (mode == 2) {
        return reciprocal;
    }
    return std::clamp(reciprocal, minimum_weight, maximum_weight);
}

inline double lead_blend_range_fraction(double range_m, double reference_range_m,
                                        double minimum_fraction, int mode) {
    if (mode == 1) {
        return 1.0;
    }
    if (mode == 2) {
        return 0.0;
    }
    return std::clamp(std::max(1.0, reference_range_m) / std::max(1.0, range_m),
                      minimum_fraction, 1.0);
}

}  // namespace missile_guidance
