#pragma once

#include <cstdint>

#include "components/tasking/tasking_enums.h"

/**
 * MissionCommand
 * Implements [aim.md]: The high-level intent from Commander.
 */
struct MissionCommand {
    // 1. Command-bound parameters
    // These fields are not globally free parameters. They must be interpreted
    // according to command_code:
    //   - command_code == 3: route/LNAV target track-altitude-speed reference
    //   - command_code == 4: terminal recovery metadata selects the procedure;
    //                        terminal heading/alt/speed should come from the
    //                        chosen recovery program rather than free leader bias
    double cmd_heading_deg;  // Route/LNAV track bug when command_code == 3
    double cmd_altitude_m;   // Route/stage reference altitude
    double cmd_speed_mps;    // Route/stage reference speed

    // 2. Macro Codes
    // Project-local convention used by the current RL/scenario stack:
    //   0 = Idle / no mission
    //   1 = Takeoff / runway departure
    //   2 = Heading-altitude-speed vectoring / stable flight
    //   3 = Waypoint / LNAV route navigation
    // Tactical task codes (attack/RTB/etc.) are reserved for future mission layers.
    int command_code;

    // 2.1 Route / recovery references
    std::uint64_t route_ref_id;
    std::uint64_t recovery_base_id;
    std::uint64_t recovery_runway_id;
    RecoveryApproachType recovery_approach_type;
    TakeoffProcedureType takeoff_procedure_id = TakeoffProcedureType::Unspecified;
    TakeoffClearanceState takeoff_clearance_id = TakeoffClearanceState::Unspecified;
    double takeoff_interval_s = 0.0;
    RunwaySlotPosition runway_slot_id = RunwaySlotPosition::Unspecified;

    // 3. Formation
    int formation_id;
    double form_offset_x;
    double form_offset_y;
    double form_offset_z;

    // 4. Tactical
    std::uint64_t assigned_target_id;
    bool authorization_to_fire;

    bool active;
};
