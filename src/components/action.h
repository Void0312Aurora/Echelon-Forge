#pragma once

#include <flecs.h>

struct MovementCommand {
    double target_heading; // Degrees, 0 = North, Clockwise
    double target_speed;   // m/s
    bool active;           // Whether this command should be processed
};
