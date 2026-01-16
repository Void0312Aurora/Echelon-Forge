#pragma once

#include <cstdint>

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
    Facility
};

struct KeyEntity {
    UnitType type;
};
