#pragma once

#include <cstdint>

struct MissionCommandCore {
    // Command-bound reference targets interpreted by command_code.
    double cmd_heading_deg = 0.0;
    double cmd_altitude_m = 0.0;
    double cmd_speed_mps = 0.0;

    int command_code = 0;

    std::uint64_t route_ref_id = 0;

    int roe_state = 0;
    std::uint64_t engagement_authority_holder_id = 0;
    std::uint64_t engagement_authority_grantor_id = 0;
    std::uint64_t assigned_target_id = 0;
    bool authorization_to_fire = false;

    bool active = false;
};
