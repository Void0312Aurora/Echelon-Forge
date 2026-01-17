#pragma once

struct FlightModel {
    double max_speed;       // m/s
    double min_speed;       // m/s (Stall speed)
    double max_turn_rate;   // deg/s
    double max_accel;       // m/s^2
    double max_climb_rate;  // m/s
    double max_g;           // Max Load Factor (9.0)
};
