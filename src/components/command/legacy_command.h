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

inline MovementCommand make_legacy_autopilot_movement_command(
    double heading_deg,
    double speed_mps,
    double altitude_m,
    bool active = true
) {
    return {
        heading_deg,
        speed_mps,
        altitude_m,
        false,
        0.0,
        0.0,
        0.0,
        true,
        active,
    };
}

inline MovementCommand make_legacy_stick_movement_command(
    double stick_roll,
    double stick_pitch,
    double throttle_cmd,
    bool gear_down,
    bool active = true
) {
    return {
        0.0,
        0.0,
        0.0,
        true,
        stick_roll,
        stick_pitch,
        throttle_cmd,
        gear_down,
        active,
    };
}

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

inline ActionCommand make_action_command(
    double turn_rate_cmd = 0.0,
    double accel_cmd = 0.0,
    double climb_rate_cmd = 0.0,
    double fire_cmd = 0.0,
    bool release_chaff = false,
    bool release_flare = false,
    bool jettison_tanks = false,
    bool send_msg = false,
    int msg_type = 0,
    std::uint64_t msg_recipient = 0,
    std::uint64_t msg_arg = 0,
    bool active = false
) {
    return {
        turn_rate_cmd,
        accel_cmd,
        climb_rate_cmd,
        fire_cmd,
        release_chaff,
        release_flare,
        jettison_tanks,
        send_msg,
        msg_type,
        msg_recipient,
        msg_arg,
        active,
    };
}

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

inline LaggedCommand make_lagged_command(
    double heading_deg,
    double speed_mps,
    double altitude_m,
    bool active = true
) {
    return {heading_deg, speed_mps, altitude_m, active};
}
