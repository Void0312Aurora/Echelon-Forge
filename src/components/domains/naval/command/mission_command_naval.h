#pragma once

#include <cstdint>

inline constexpr int kMissionCommandCodeNavalLaunchHelo = 31;
inline constexpr int kMissionCommandCodeNavalRecoverHelo = 32;
inline constexpr int kMissionCommandCodeNavalRelayOthTargeting = 33;
inline constexpr int kMissionCommandCodeNavalAutoCloseInDefense = 34;
inline constexpr int kMissionCommandCodeNavalSurfaceEngage = 35;

struct MissionCommandNaval {
    struct StationingDirective {
        std::uint64_t reference_entity_id = 0;
        double station_radius_m = 0.0;
        double station_bearing_deg = 0.0;

        bool operator==(const StationingDirective &) const = default;
    };

    struct EmbarkedHeloDirective {
        std::uint64_t embarked_helo_entity_id = 0;
        bool launch_helo = false;
        bool recover_helo = false;
        bool relay_oth_targeting = false;

        bool operator==(const EmbarkedHeloDirective &) const = default;
    };

    std::uint64_t reference_entity_id = 0;
    double station_radius_m = 0.0;
    double station_bearing_deg = 0.0;
    std::uint64_t embarked_helo_entity_id = 0;
    bool launch_helo = false;
    bool recover_helo = false;
    bool relay_oth_targeting = false;
};

// Maintained naval-domain owner slice projected through MissionCommand compatibility shells.
using MissionCommandNavalOwnerSlice = MissionCommandNaval;
inline constexpr bool kMissionCommandNavalOwnedDomainSlice = true;

[[nodiscard]] inline MissionCommandNaval::StationingDirective
mission_command_naval_stationing_directive(const MissionCommandNavalOwnerSlice &naval) noexcept {
    return {
        .reference_entity_id = naval.reference_entity_id,
        .station_radius_m = naval.station_radius_m,
        .station_bearing_deg = naval.station_bearing_deg,
    };
}

[[nodiscard]] inline MissionCommandNaval::EmbarkedHeloDirective
mission_command_naval_embarked_helo_directive(const MissionCommandNavalOwnerSlice &naval) noexcept {
    return {
        .embarked_helo_entity_id = naval.embarked_helo_entity_id,
        .launch_helo = naval.launch_helo,
        .recover_helo = naval.recover_helo,
        .relay_oth_targeting = naval.relay_oth_targeting,
    };
}
