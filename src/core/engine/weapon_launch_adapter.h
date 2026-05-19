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

struct MunitionLifecycleSnapshot {
    std::uint64_t world_index = 0;
    std::uint64_t packet_id = 0;
    std::uint64_t munition_entity_id = 0;
    std::uint64_t attacker_entity_id = 0;
    std::uint64_t target_entity_id = 0;
    bool has_target_entity = false;
    std::uint64_t target_track_id = 0;
    bool has_target_track = false;
    std::uint64_t launch_event_id = 0;
    bool active = false;
    std::string seeker_mode = "unknown";
    double guidance_cadence_s = 0.0;
    std::string track_memory_state = "unknown";
    double fuel_remaining_fraction = 0.0;
    bool burnout = false;
    double max_flight_time_s = 0.0;
    std::string fuze_state = "unknown";
    double source_time_s = 0.0;
};

struct EffectsEventSnapshot {
    std::uint64_t world_index = 0;
    std::uint64_t event_id = 0;
    std::uint64_t munition_entity_id = 0;
    std::uint64_t target_entity_id = 0;
    std::string trigger_type = "unknown";
    std::string outcome_state = "unknown";
    double detonation_time_s = 0.0;
    double nearest_approach_time_s = 0.0;
    double quality = 0.0;
    double confidence = 0.0;
    std::string effect_family = "unknown";
};

struct DamageReportSnapshot {
    std::uint64_t world_index = 0;
    std::uint64_t report_id = 0;
    std::uint64_t target_entity_id = 0;
    std::uint64_t source_event_id = 0;
    double hp_delta = 0.0;
    double system_health_delta = 0.0;
    std::string platform_damage_state_delta;
    bool mission_kill = false;
    bool mobility_kill = false;
    bool sensor_kill = false;
    bool survivability_kill = false;
    std::string loss_state_from = "unknown";
    std::string loss_state_to = "unknown";
    bool destroyed = false;
    double report_time_s = 0.0;
};

struct DiagnosticsTraceSnapshot {
    std::uint64_t world_index = 0;
    std::uint64_t trace_id = 0;
    std::uint64_t parent_trace_id = 0;
    std::uint64_t chain_id = 0;
    std::uint64_t track_id = 0;
    std::uint64_t launch_request_id = 0;
    std::uint64_t launch_event_id = 0;
    std::uint64_t munition_entity_id = 0;
    std::uint64_t effects_event_id = 0;
    std::uint64_t damage_report_id = 0;
    std::uint64_t observation_packet_version = 0;
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

inline MunitionLifecyclePacket make_munition_lifecycle_packet(
    const MunitionLifecycleSnapshot& snapshot
) {
    return MunitionLifecyclePacket{
        .packet_id = snapshot.packet_id,
        .munition = make_entity_ref(snapshot.world_index, snapshot.munition_entity_id),
        .attacker = make_entity_ref(snapshot.world_index, snapshot.attacker_entity_id),
        .target_entity = make_entity_ref(snapshot.world_index, snapshot.target_entity_id),
        .has_target_entity = snapshot.has_target_entity,
        .target_track_id = snapshot.target_track_id,
        .has_target_track = snapshot.has_target_track,
        .launch_event_id = snapshot.launch_event_id,
        .active = snapshot.active,
        .seeker_mode = snapshot.seeker_mode,
        .guidance_cadence_s = snapshot.guidance_cadence_s,
        .track_memory_state = snapshot.track_memory_state,
        .fuel_remaining_fraction = snapshot.fuel_remaining_fraction,
        .burnout = snapshot.burnout,
        .max_flight_time_s = snapshot.max_flight_time_s,
        .fuze_state = snapshot.fuze_state,
        .source_time_s = snapshot.source_time_s,
    };
}

inline EffectsEvent make_effects_event(const EffectsEventSnapshot& snapshot) {
    return EffectsEvent{
        .event_id = snapshot.event_id,
        .munition = make_entity_ref(snapshot.world_index, snapshot.munition_entity_id),
        .target = make_entity_ref(snapshot.world_index, snapshot.target_entity_id),
        .trigger_type = snapshot.trigger_type,
        .outcome_state = snapshot.outcome_state,
        .detonation_time_s = snapshot.detonation_time_s,
        .nearest_approach_time_s = snapshot.nearest_approach_time_s,
        .quality = snapshot.quality,
        .confidence = snapshot.confidence,
        .effect_family = snapshot.effect_family,
    };
}

inline DamageReport make_damage_report(const DamageReportSnapshot& snapshot) {
    return DamageReport{
        .report_id = snapshot.report_id,
        .target = make_entity_ref(snapshot.world_index, snapshot.target_entity_id),
        .source_event_id = snapshot.source_event_id,
        .hp_delta = snapshot.hp_delta,
        .system_health_delta = snapshot.system_health_delta,
        .platform_damage_state_delta = snapshot.platform_damage_state_delta,
        .mission_kill = snapshot.mission_kill,
        .mobility_kill = snapshot.mobility_kill,
        .sensor_kill = snapshot.sensor_kill,
        .survivability_kill = snapshot.survivability_kill,
        .loss_state_from = snapshot.loss_state_from,
        .loss_state_to = snapshot.loss_state_to,
        .destroyed = snapshot.destroyed,
        .report_time_s = snapshot.report_time_s,
    };
}

inline DiagnosticsTrace make_diagnostics_trace(const DiagnosticsTraceSnapshot& snapshot) {
    return DiagnosticsTrace{
        .trace_id = snapshot.trace_id,
        .parent_trace_id = snapshot.parent_trace_id,
        .chain_id = snapshot.chain_id,
        .track_id = snapshot.track_id,
        .launch_request_id = snapshot.launch_request_id,
        .launch_event_id = snapshot.launch_event_id,
        .munition = make_entity_ref(snapshot.world_index, snapshot.munition_entity_id),
        .effects_event_id = snapshot.effects_event_id,
        .damage_report_id = snapshot.damage_report_id,
        .observation_packet_version = snapshot.observation_packet_version,
    };
}

}  // namespace engagement_adapter
