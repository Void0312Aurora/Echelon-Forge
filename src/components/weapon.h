#pragma once

#include <flecs.h>

struct Missile {
    uint64_t target_id;    // Entity ID of the target
    double max_speed;      // Maximum speed (m/s)
    double turn_rate;      // Maximum turn rate (deg/s)
    double fuse_distance;  // Lethal radius (m)
    bool active;           // If false, missile is dead/inert
};
