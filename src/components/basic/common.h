#pragma once

#include <cstdint>
#include <cmath>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace Math {
    inline double to_radians(double deg) { return deg * M_PI / 180.0; }
    inline double to_degrees(double rad) { return rad * 180.0 / M_PI; }
    
    struct Vector3 { double x, y, z; };
    
    inline double vec_mag(const Vector3& v) {
        return std::sqrt(v.x*v.x + v.y*v.y + v.z*v.z);
    }
    
    inline Vector3 vec_norm(const Vector3& v) {
        double m = vec_mag(v);
        if (m < 1e-6) return {0,0,0};
        return {v.x/m, v.y/m, v.z/m};
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
    RCSProfile
};

struct KeyEntity {
    UnitType type;
};
