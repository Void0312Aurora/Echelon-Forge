#pragma once

#include <cstdint>

#include "components/tasking/tasking_enums.h"

/**
 * LeaderIntent
 * Internal Leader-layer output before mapping into MissionCommand.
 */
struct LeaderIntent {
    LeaderPhase phase_id = LeaderPhase::Idle;
    int element_phase_id = 0;
    ServiceProfile service_profile = ServiceProfile::Unspecified;
    TaskFamily task_family = TaskFamily::Unspecified;
    TacticalUnitType tactical_unit_type = TacticalUnitType::Unspecified;
    std::uint64_t tactical_unit_id = 0;
    std::uint64_t task_group_id = 0;
    int role_code = 0;
    CoordinationMode coordination_mode = CoordinationMode::Unspecified;
    int relative_slot_code = 0;
    std::uint64_t recovery_site_id = 0;
    int command_code = 0;
    std::uint64_t route_ref_id = 0;
    std::uint64_t recovery_base_id = 0;
    std::uint64_t recovery_runway_id = 0;
    RecoveryApproachType recovery_approach_type = RecoveryApproachType::None;
    double cmd_heading_deg = 0.0;
    double cmd_altitude_m = 0.0;
    double cmd_speed_mps = 0.0;
    int formation_id = 0;
    double form_offset_x = 0.0;
    double form_offset_y = 0.0;
    double form_offset_z = 0.0;
    std::uint64_t assigned_target_id = 0;
    bool authorization_to_fire = false;
    FormationMode formation_mode_id = FormationMode::Unspecified;
    bool join_required_flag = false;
    bool rejoin_required_flag = false;
    bool split_flag = false;
    double support_anchor_x_m = 0.0;
    double support_anchor_y_m = 0.0;
    double support_slot_offset_x_m = 0.0;
    double support_slot_offset_y_m = 0.0;
    WingmanCommandMode wingman_command_mode = WingmanCommandMode::None;
    bool approach_armed = false;
    bool commit_to_land = false;
    bool abort_flag = false;
    bool active = false;
};
