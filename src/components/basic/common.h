#pragma once

#include <cstdint>
#include <cmath>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace Math {
    inline double to_radians(double deg) { return deg * M_PI / 180.0; }
    inline double to_degrees(double rad) { return rad * 180.0 / M_PI; }

    inline double normalize_heading_deg(double heading_deg) {
        if (!std::isfinite(heading_deg)) return 0.0;
        double out = std::fmod(heading_deg, 360.0);
        if (out < 0.0) out += 360.0;
        return out;
    }

    inline double ground_track_deg_from_velocity(double vx, double vy, double fallback_heading_deg) {
        const double horiz_speed = std::hypot(vx, vy);
        if (horiz_speed <= 1.0) {
            return normalize_heading_deg(fallback_heading_deg);
        }
        return normalize_heading_deg(to_degrees(std::atan2(vx, vy)));
    }
    
    struct Vector3 { double x, y, z; };
    
    inline double vec_mag(const Vector3& v) {
        return std::sqrt(v.x*v.x + v.y*v.y + v.z*v.z);
    }
    
    inline Vector3 vec_norm(const Vector3& v) {
        double m = vec_mag(v);
        if (m < 1e-6) return {0,0,0};
        return {v.x/m, v.y/m, v.z/m};
    }

    struct EulerRotationCoefficients {
        double c_psi;
        double s_psi;
        double c_theta;
        double s_theta;
        double c_phi;
        double s_phi;
    };

    inline EulerRotationCoefficients euler_rotation_coefficients(
        double heading_deg,
        double pitch_deg,
        double roll_deg
    ) {
        const double psi = to_radians(90.0 - heading_deg);
        // Across the flight-control and propulsion systems, positive pitch is
        // defined as nose-up (forward axis gains +world Z). Use the same sign
        // convention in the shared body/world transforms so aerodynamic state,
        // lift direction, and thrust all agree on attitude semantics.
        const double theta = to_radians(-pitch_deg);
        const double phi = to_radians(roll_deg);
        return {
            std::cos(psi),
            std::sin(psi),
            std::cos(theta),
            std::sin(theta),
            std::cos(phi),
            std::sin(phi),
        };
    }

    inline Vector3 world_to_body(
        const Vector3& v_world,
        double heading_deg,
        double pitch_deg,
        double roll_deg
    ) {
        const EulerRotationCoefficients rot =
            euler_rotation_coefficients(heading_deg, pitch_deg, roll_deg);
        return {
            rot.c_psi * rot.c_theta * v_world.x +
                rot.s_psi * rot.c_theta * v_world.y -
                rot.s_theta * v_world.z,
            (rot.c_psi * rot.s_theta * rot.s_phi - rot.s_psi * rot.c_phi) * v_world.x +
                (rot.s_psi * rot.s_theta * rot.s_phi + rot.c_psi * rot.c_phi) * v_world.y +
                rot.c_theta * rot.s_phi * v_world.z,
            (rot.c_psi * rot.s_theta * rot.c_phi + rot.s_psi * rot.s_phi) * v_world.x +
                (rot.s_psi * rot.s_theta * rot.c_phi - rot.c_psi * rot.s_phi) * v_world.y +
                rot.c_theta * rot.c_phi * v_world.z,
        };
    }

    inline Vector3 body_to_world(
        const Vector3& v_body,
        double heading_deg,
        double pitch_deg,
        double roll_deg
    ) {
        const EulerRotationCoefficients rot =
            euler_rotation_coefficients(heading_deg, pitch_deg, roll_deg);
        return {
            rot.c_psi * rot.c_theta * v_body.x +
                (rot.c_psi * rot.s_theta * rot.s_phi - rot.s_psi * rot.c_phi) * v_body.y +
                (rot.c_psi * rot.s_theta * rot.c_phi + rot.s_psi * rot.s_phi) * v_body.z,
            rot.s_psi * rot.c_theta * v_body.x +
                (rot.s_psi * rot.s_theta * rot.s_phi + rot.c_psi * rot.c_phi) * v_body.y +
                (rot.s_psi * rot.s_theta * rot.c_phi - rot.c_psi * rot.s_phi) * v_body.z,
            -rot.s_theta * v_body.x +
                rot.c_theta * rot.s_phi * v_body.y +
                rot.c_theta * rot.c_phi * v_body.z,
        };
    }
}

// Components

struct Transform {
    // Local ENU (East-North-Up) coordinates relative to scenario origin
    double x, y, z; 
    // Euler angles in degrees (Heading in NAV: 0=North, Clockwise)
    double heading, pitch, roll;
};

struct Velocity {
    // Linear velocity vector in m/s
    double vx, vy, vz;
};

namespace Math {
    inline Vector3 world_to_body(const Vector3& v_world, const Transform& transform) {
        return world_to_body(v_world, transform.heading, transform.pitch, transform.roll);
    }

    inline Vector3 body_to_world(const Vector3& v_body, const Transform& transform) {
        return body_to_world(v_body, transform.heading, transform.pitch, transform.roll);
    }
}

enum class Side : uint8_t {
    Unknown = 0,
    Blue,
    Red,
    Neutral
};

struct Alliance {
    Side side;
};

enum class UnitType : uint8_t {
    Unknown = 0,
    Aircraft,
    Ship,
    Missile,
    Facility,
    C2Node,
    Sensor,
    Engine,
    EWSuite,
    RCSProfile,
    Submarine,
    Ground
};

struct KeyEntity {
    UnitType type;
};
