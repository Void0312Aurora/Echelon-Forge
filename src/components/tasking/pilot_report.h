#pragma once

#include <cstdint>

#include "components/tasking/tasking_enums.h"

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
    RequestSupport,

    // 7. Two-ship / formation status extensions
    REP_JOINED,      // Joined assigned formation slot
    REP_REJOINING,   // Rejoin maneuver in progress
    REP_FORM_LOST,   // Lost formation reference
    REP_UNABLE_FORM, // Unable to establish/maintain formation
    REP_SUPPORTING,  // Supporting lead / assigned element
    WARN_SEPARATION  // Unsafe closure / separation alert
};

struct PilotReport {
    CommMsgType report_type = CommMsgType::None;
    std::uint64_t sender_id = 0;
    std::uint64_t task_id = 0;
    ServiceProfile service_profile = ServiceProfile::Unspecified;
    TaskFamily task_family = TaskFamily::Unspecified;
    TacticalUnitType tactical_unit_type = TacticalUnitType::Unspecified;
    std::uint64_t tactical_unit_id = 0;
    std::uint64_t task_group_id = 0;
    int role_code = 0;
    CoordinationMode coordination_mode = CoordinationMode::Unspecified;
    std::uint64_t element_id = 0;
    int phase_id = 0;
    int formation_role_id = 0;
    double timestamp_s = 0.0;
    double status_value = 0.0;
    std::uint64_t entity_ref = 0;
    double location_x_m = 0.0;
    double location_y_m = 0.0;
    double location_z_m = 0.0;
    double formation_error_m = 0.0;
    double bearing_error_deg = 0.0;
    double closure_mps = 0.0;
    double separation_m = 0.0;
    bool active = false;
};
