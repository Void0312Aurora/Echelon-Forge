#pragma once

#include <cstdint>

#include "components/command/common/mission_command_core.h"

inline constexpr int kMissionCommandCodeNavalLaunchHelo = 31;
inline constexpr int kMissionCommandCodeNavalRecoverHelo = 32;
inline constexpr int kMissionCommandCodeNavalRelayOthTargeting = 33;
inline constexpr int kMissionCommandCodeNavalAutoCloseInDefense = 34;
inline constexpr int kMissionCommandCodeNavalSurfaceEngage = 35;

// Maintained Naval runtime command truth. The flat MissionCommand remains a
// compatibility transport, while Naval systems consume this typed component.
struct NavalCommandIntent {
    double cmd_heading_deg = 0.0;
    double cmd_speed_mps = 0.0;
    double cmd_depth_m = 0.0;
    int command_code = 0;
    std::uint64_t route_ref_id = 0;

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

    std::uint64_t reference_entity_id = 0;
    double station_radius_m = 0.0;
    double station_bearing_deg = 0.0;
    std::uint64_t embarked_helo_entity_id = 0;
    bool launch_helo = false;
    bool recover_helo = false;
    bool relay_oth_targeting = false;

    // Naval-owned embarked-air relay bookkeeping. The maintained naval runtime
    // owns this timestamp instead of reusing the air-owned
    // `MissionCommandAir::takeoff_interval_s` field of the flat transport
    // shell, which the pre-projection system wrote as a relay refresh stamp.
    double last_relay_refresh_time_s = 0.0;
};

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

[[nodiscard]] inline MissionCommandNaval::StationingDirective
mission_command_naval_stationing_directive(const NavalCommandIntent &naval) noexcept {
    return {
        .reference_entity_id = naval.reference_entity_id,
        .station_radius_m = naval.station_radius_m,
        .station_bearing_deg = naval.station_bearing_deg,
    };
}

[[nodiscard]] inline MissionCommandNaval::EmbarkedHeloDirective
mission_command_naval_embarked_helo_directive(const NavalCommandIntent &naval) noexcept {
    return {
        .embarked_helo_entity_id = naval.embarked_helo_entity_id,
        .launch_helo = naval.launch_helo,
        .recover_helo = naval.recover_helo,
        .relay_oth_targeting = naval.relay_oth_targeting,
    };
}

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

// Naval-owned command projection. The maintained naval runtime component is
// projected from the shared core directive plus the naval owner slice, so the
// flat MissionCommand transport never becomes naval runtime truth.
[[nodiscard]] inline NavalCommandIntent mission_command_naval_intent(
    const MissionCommandNavalOwnerSlice &naval,
    const MissionCommandCore &core) noexcept {
    NavalCommandIntent intent{};
    intent.reference_entity_id = naval.reference_entity_id;
    intent.station_radius_m = naval.station_radius_m;
    intent.station_bearing_deg = naval.station_bearing_deg;
    intent.embarked_helo_entity_id = naval.embarked_helo_entity_id;
    intent.launch_helo = naval.launch_helo;
    intent.recover_helo = naval.recover_helo;
    intent.relay_oth_targeting = naval.relay_oth_targeting;
    intent.cmd_heading_deg = core.cmd_heading_deg;
    intent.cmd_speed_mps = core.cmd_speed_mps;
    intent.cmd_depth_m = core.cmd_altitude_m;
    intent.command_code = core.command_code;
    intent.route_ref_id = core.route_ref_id;
    intent.roe_state = core.roe_state;
    intent.engagement_authority_holder_id = core.engagement_authority_holder_id;
    intent.engagement_authority_grantor_id = core.engagement_authority_grantor_id;
    intent.assigned_target_id = core.assigned_target_id;
    intent.threat_state = core.threat_state;
    intent.assigned_target_track_id = core.assigned_target_track_id;
    intent.assigned_target_source_id = core.assigned_target_source_id;
    intent.assigned_target_snapshot_time_s = core.assigned_target_snapshot_time_s;
    intent.authorization_to_fire = core.authorization_to_fire;
    intent.active = core.active;
    return intent;
}

// Single maintained write seam for the naval command projection. Every runtime
// path that publishes a command onto an entity routes through one of these
// helpers, so the naval-owned intent can never drift out of sync with the
// shared core and naval owner slices it was projected from.
//
// `set_mission_command_naval_projection` owns the explicit owner-slice form so
// this header stays usable without the flat transport shell. The
// `MissionCommand`-shaped wrapper lives in `components/command/
// mission_command.h`, where the shell and its accessors are declared.
//
// The entity handle is taken by value: it is a trivially copyable id wrapper,
// and callers routinely pass a temporary such as `iteration.entity(index)`.
template <typename EntityT>
inline void set_mission_command_naval_projection(EntityT entity,
                                                 const MissionCommandCore &core,
                                                 const MissionCommandNavalOwnerSlice &naval) {
    entity.template set<NavalCommandIntent>(mission_command_naval_intent(naval, core));
}
