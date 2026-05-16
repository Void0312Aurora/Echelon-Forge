#pragma once

#include <cstdint>

inline constexpr int kMissionCommandCodeNavalLaunchHelo = 31;
inline constexpr int kMissionCommandCodeNavalRecoverHelo = 32;
inline constexpr int kMissionCommandCodeNavalRelayOthTargeting = 33;
inline constexpr int kMissionCommandCodeNavalAutoCloseInDefense = 34;
inline constexpr int kMissionCommandCodeNavalSurfaceEngage = 35;

struct MissionCommandNaval {
    std::uint64_t reference_entity_id = 0;
    double station_radius_m = 0.0;
    double station_bearing_deg = 0.0;
    std::uint64_t embarked_helo_entity_id = 0;
    bool launch_helo = false;
    bool recover_helo = false;
    bool relay_oth_targeting = false;
};
