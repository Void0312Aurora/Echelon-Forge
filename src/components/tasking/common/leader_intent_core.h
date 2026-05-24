#pragma once

#include <cstdint>

#include "components/tasking/common/core_tasking_enums.h"

struct LeaderIntentCore {
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
    double cmd_heading_deg = 0.0;
    double cmd_altitude_m = 0.0;
    double cmd_speed_mps = 0.0;
    int roe_state = 0;
    std::uint64_t engagement_authority_holder_id = 0;
    std::uint64_t engagement_authority_grantor_id = 0;
    std::uint64_t assigned_target_id = 0;
    int threat_state = 0;
    std::uint64_t assigned_target_track_id = 0;
    std::uint64_t assigned_target_source_id = 0;
    double assigned_target_snapshot_time_s = 0.0;
    bool authorization_to_fire = false;
    bool active = false;
};
