#pragma once

#include <vector>
#include <cstdint>

enum class CommMsgType {
    None = 0,
    // 1. Command Acknowledgment
    REP_WILCO,     // "Will Comply"
    REP_ROGER,     // "Received"
    REP_UNABLE,    // "Cannot Comply" (Reason)
    REP_CANT_DO,   // "Technical Limitation"

    // 2. Status Report
    STATUS_FUEL,   // Arg: Joker/Bingo/State
    STATUS_AMMO,   // Arg: Winchester/Remington/State
    STATUS_DAMAGE, // Arg: 0-100%
    STATUS_POS,    // Arg: (x,y,z)

    // 3. Tactical / Brevity
    REP_TALLY,     // Visual Enemy (Arg: Target ID)
    REP_VISUAL,    // Visual Friendly (Arg: Target ID)
    REP_BLIND,     // Lost Visual/Radar (Arg: Target ID)
    REP_SPIKE,     // RWR Lock (Arg: Azimuth?)
    REP_FAILED_SORT, // Cannot execute sort
    REP_ENGAGED,   // Engaging Target (Arg: Target ID)
    REP_SPLASH,    // Target Destroyed (Arg: Target ID)
    REP_DEFENDING, // Defensive Maneuver (Arg: Threat Type)

    // 4. Mission Progress
    REP_ON_STATION,// Arrived at station
    REP_FENCE_IN,  // Entering Combat Zone
    REP_FENCE_OUT, // Exiting Combat Zone
    REP_RTB,       // Returning to Base

    // 5. Emergency
    WARN_FLAMEOUT, // Engine Failure
    WARN_BINGO,    // Fuel Critical
    WARN_LAUNCH,   // Missile Launch Detected

    // Legacy aliases retained for compatibility with earlier code/docs.
    ACK_WILCO = REP_WILCO,
    ACK_ROGER = REP_ROGER,
    ACK_UNABLE = REP_UNABLE,
    ACK_CANT_DO = REP_CANT_DO,

    // 6. Python Binding Compatibility
    ReportContact,
    AssignTask,
    StatusUpdate,
    RequestSupport
};

struct CommPacket {
    uint64_t sender_id;
    uint64_t target_receiver_id; // 0 = Broadcast to Net
    CommMsgType type;
    
    // Payload
    uint64_t entity_ref; // Related entity (Target ID)
    double location_x;   // Optional coords
    double location_y;
    double location_z;
    double value;        // Generic value (fuel %, heading, etc)
    int status_code;     // Specific codes (Joker/Bingo enum etc)
    
    double timestamp;
};

struct CommQueue {
    std::vector<CommPacket> inbox;
};

struct PilotReport {
    CommMsgType report_type = CommMsgType::None;
    uint64_t sender_id = 0;
    uint64_t task_id = 0;
    int phase_id = 0;
    double timestamp_s = 0.0;
    double status_value = 0.0;
    uint64_t entity_ref = 0;
    double location_x_m = 0.0;
    double location_y_m = 0.0;
    double location_z_m = 0.0;
    bool active = false;
};
