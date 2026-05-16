#pragma once

#include <cstdint>
#include <string>

struct EmbarkedAirOps {
    std::string helo_unit_name{};
    std::uint64_t active_helo_entity_id = 0;
    double launch_altitude_m = 180.0;
    double launch_offset_forward_m = 120.0;
    double launch_offset_starboard_m = 0.0;
    double recover_range_m = 250.0;
    double relay_refresh_s = 3.0;
    bool enabled = false;
    bool relay_oth_targeting = true;
    bool helo_airborne = false;
};
