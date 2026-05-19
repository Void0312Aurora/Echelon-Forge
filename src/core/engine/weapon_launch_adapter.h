#pragma once

#include <cstdint>
#include <string>

#include "runtime/contracts/engagement_contracts.h"

namespace engagement_adapter {

struct LaunchRequestSnapshot {
    std::uint64_t world_index = 0;
    std::uint64_t request_id = 0;
    std::uint64_t shooter_entity_id = 0;
    std::uint64_t target_entity_id = 0;
    bool has_target_entity = false;
    std::uint64_t target_track_id = 0;
    bool has_target_track = false;
    std::string station_id;
    std::string mount_id;
    std::string requested_munition_family;
    std::string authority = "unspecified";
    double requested_time_s = 0.0;
    std::string merge_policy = "reject_on_conflict";
};

struct LegacyLaunchOutcomeSnapshot {
    std::uint64_t world_index = 0;
    std::uint64_t event_id = 0;
    std::uint64_t request_id = 0;
    bool accepted = false;
    std::string rejection_reason;
    std::string selected_launcher;
    std::string selected_munition;
    int ammo_delta = 0;
    double cooldown_delta_s = 0.0;
    std::uint64_t spawned_munition_entity_id = 0;
    double event_time_s = 0.0;
};

inline EngagementEntityRef make_entity_ref(
    std::uint64_t world_index,
    std::uint64_t entity_id
) {
    return EngagementEntityRef{
        .world_index = world_index,
        .entity_id = entity_id,
    };
}

inline LaunchRequest make_launch_request(const LaunchRequestSnapshot& snapshot) {
    return LaunchRequest{
        .request_id = snapshot.request_id,
        .shooter = make_entity_ref(snapshot.world_index, snapshot.shooter_entity_id),
        .target_entity = make_entity_ref(snapshot.world_index, snapshot.target_entity_id),
        .has_target_entity = snapshot.has_target_entity,
        .target_track_id = snapshot.target_track_id,
        .has_target_track = snapshot.has_target_track,
        .station_id = snapshot.station_id,
        .mount_id = snapshot.mount_id,
        .requested_munition_family = snapshot.requested_munition_family,
        .authority = snapshot.authority,
        .requested_time_s = snapshot.requested_time_s,
        .merge_policy = snapshot.merge_policy,
    };
}

inline LaunchEvent make_launch_event(const LegacyLaunchOutcomeSnapshot& snapshot) {
    return LaunchEvent{
        .event_id = snapshot.event_id,
        .request_id = snapshot.request_id,
        .accepted = snapshot.accepted,
        .rejection_reason = snapshot.rejection_reason,
        .selected_launcher = snapshot.selected_launcher,
        .selected_munition = snapshot.selected_munition,
        .ammo_delta = snapshot.ammo_delta,
        .cooldown_delta_s = snapshot.cooldown_delta_s,
        .spawned_munition = make_entity_ref(snapshot.world_index, snapshot.spawned_munition_entity_id),
        .has_spawned_munition = snapshot.spawned_munition_entity_id != 0,
        .event_time_s = snapshot.event_time_s,
    };
}

}  // namespace engagement_adapter
