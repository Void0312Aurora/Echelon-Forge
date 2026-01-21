#pragma once

#include <flecs.h>
#include <cstdint>

// --- New Standards Implementation ---

/**
 * PilotAction
 * Implements [act.md]: The physical interface for the Digital Pilot.
 */
struct PilotAction {
    // 1. Primary Flight Controls (Continuous [-1, 1] or [0, 1])
    double stick_pitch;      // [-1, 1] (Pull back = negative pitch up? wait. Standard: Pull back = +q. Let's use standard: -1=Pitch Down, 1=Pitch Up? No, Stick Aft is usually positive pitch rate command in FBW? 
                             // Let's follow convention: Stick Pull (+q) is usually Positive Pitch Rate. Stick Push (-q).
                             // Let's stick to standard internal defs: positive = nose up.
    double stick_roll;       // [-1, 1] Positive = Right Roll
    double rudder;           // [-1, 1] Positive = Nose Right (Yaw)
    double throttle;         // [0, 1] 0=Idle, 1=Max AB
    
    // 2. Secondary Controls
    float gear_handle;       // 0.0 (Up) to 1.0 (Down)
    float flaps;             // 0.0 (Up) to 1.0 (Full)
    float speedbrake;        // 0.0 (Retracted) to 1.0 (Extended)
    double brake;            // 0.0 (Off) to 1.0 (Full)
    bool brake_left;         // Wheel brake
    bool brake_right;        // Wheel brake
    
    // 3. Sensors / Avionics
    bool radar_active;       // Main Radar Switch
    double radar_scan_az;    // Scan Center Azimuth
    double radar_scan_el;    // Scan Center Elevation
    bool tms_up;             // Target Management Switch Up (Lock)
    
    // 4. Weapons
    bool master_arm;
    bool fire_weapon;        // Pickle/Trigger
    bool fire_gun;           // Gun Trigger
    int weapon_select_id;    // Selected Weapon Station/Type
    bool jettison_emergency; 
    
    // 5. Countermeasures
    bool program_chaff;
    bool program_flare;
    
    bool active;             // Validity flag
};

/**
 * MissionCommand
 * Implements [aim.md]: The high-level intent from Commander.
 */
struct MissionCommand {
    // 1. Core Vectoring
    double cmd_heading_deg;  // Target Heading (0-360)
    double cmd_altitude_m;   // Target Altitude (MSL)
    double cmd_speed_mps;    // Target Speed (TAS/IAS mix? Let's assume TAS for now or specify)
    
    // 2. Macro Codes
    int command_code;        // 0=Idle, 1=Takeoff, 2=Cruise, 3=Attack, 4=RTB, etc.
    
    // 3. Formation
    int formation_id;
    double form_offset_x;
    double form_offset_y;
    double form_offset_z;
    
    // 4. Tactical
    uint64_t assigned_target_id;
    bool authorization_to_fire;
    
    bool active;
};


// --- Legacy Components (To be Deprecated) ---

struct MovementCommand {
    double target_heading; // Degrees, 0 = North, Clockwise
    double target_speed;   // m/s
    double target_altitude;// m (New)
    
    // Direct Stick Inputs (Overlay) - MOVED TO PILOT ACTION
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
    uint64_t msg_recipient;// C2: Target ID (0=Broadcast)
    uint64_t msg_arg;      // C2: Reference ID (e.g. Target)
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
