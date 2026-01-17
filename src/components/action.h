#pragma once

#include <flecs.h>

struct MovementCommand {
    double target_heading; // Degrees, 0 = North, Clockwise
    double target_speed;   // m/s
    double target_altitude;// m (New)
    bool active;           // Whether this command should be processed
};

struct ActionCommand {
    double turn_rate_cmd;  // Normalized [-1, 1]
    double accel_cmd;      // Normalized [-1, 1]
    double climb_rate_cmd; // Normalized [-1, 1]
    double fire_cmd;       // [0, 1], optional
    bool active;
};

struct ActionSpaceConfig {
    double max_turn_rate_deg_s;
    double max_accel_mps2;
    double max_climb_rate_mps;
    double min_speed_mps;
    double max_speed_mps;
    double min_alt_m;
    double max_alt_m;
};

struct CommandLag {
    double heading_tau_s;
    double speed_tau_s;
    double altitude_tau_s;
};

struct LaggedCommand {
    double target_heading;
    double target_speed;
    double target_altitude;
    bool active;
};

struct CommandLink {
    double latency_s;   // One-way command latency
    double drop_prob;   // [0,1] command drop probability
};

struct PendingMovementCommand {
    MovementCommand command;
    double deliver_time;
    bool active;
};

struct PendingActionCommand {
    ActionCommand command;
    double deliver_time;
    bool active;
};
