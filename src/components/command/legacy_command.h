#pragma once

#include <cstdint>

// Legacy command surface retained for compatibility with the existing systems.
struct MovementCommand {
    double target_heading; // Degrees, 0 = North, Clockwise
    double target_speed;   // m/s
    double target_altitude;// m

    // Direct Stick Inputs (Overlay) - moved to PilotAction for the maintained surface.
    bool use_stick_control;
    double stick_roll;
    double stick_pitch;
    double throttle_cmd;
    bool gear_handle;

    bool active;
};

struct ActionCommand {
    double turn_rate_cmd;  // Normalized [-1, 1]
    double accel_cmd;      // Normalized [-1, 1]
    double climb_rate_cmd; // Normalized [-1, 1]

    double fire_cmd;       // [0, 1], optional
    bool release_chaff;    // Instantaneous trigger
    bool release_flare;    // Instantaneous trigger
    bool jettison_tanks;   // Instantaneous trigger
    bool send_msg;         // C2: Send a message
    int msg_type;          // C2: CommMsgType cast to int
    std::uint64_t msg_recipient;// C2: Target ID (0=Broadcast)
    std::uint64_t msg_arg;      // C2: Reference ID (e.g. Target)
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
