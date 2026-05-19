#pragma once

#include <cstdint>
#include <string>

struct EngagementEntityRef {
    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
};

struct TrackPacket {
    std::uint64_t track_id = 0;
    EngagementEntityRef correlated_entity{};
    bool has_correlated_entity = false;
    std::string correlation_policy = "unresolved";
    std::string source;
    std::string classification = "unknown";
    std::string status = "unknown";
    double quality = 0.0;
    double confidence = 0.0;
    bool usable = false;
    std::string iff = "unknown";
    double source_time_s = 0.0;
    double update_age_s = 0.0;
    std::uint64_t snapshot_version = 0;
};

struct LaunchRequest {
    std::uint64_t request_id = 0;
    EngagementEntityRef shooter{};
    EngagementEntityRef target_entity{};
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

struct LaunchEvent {
    std::uint64_t event_id = 0;
    std::uint64_t request_id = 0;
    bool accepted = false;
    std::string rejection_reason;
    std::string selected_launcher;
    std::string selected_munition;
    int ammo_delta = 0;
    double cooldown_delta_s = 0.0;
    EngagementEntityRef spawned_munition{};
    bool has_spawned_munition = false;
    double event_time_s = 0.0;
};

struct MunitionLifecyclePacket {
    std::uint64_t packet_id = 0;
    EngagementEntityRef munition{};
    EngagementEntityRef attacker{};
    EngagementEntityRef target_entity{};
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

struct EffectsEvent {
    std::uint64_t event_id = 0;
    EngagementEntityRef munition{};
    EngagementEntityRef target{};
    std::string trigger_type = "unknown";
    std::string outcome_state = "unknown";
    double detonation_time_s = 0.0;
    double nearest_approach_time_s = 0.0;
    double quality = 0.0;
    double confidence = 0.0;
    std::string effect_family = "unknown";
};

struct DamageReport {
    std::uint64_t report_id = 0;
    EngagementEntityRef target{};
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

struct DiagnosticsTrace {
    std::uint64_t trace_id = 0;
    std::uint64_t parent_trace_id = 0;
    std::uint64_t chain_id = 0;
    std::uint64_t track_id = 0;
    std::uint64_t launch_request_id = 0;
    std::uint64_t launch_event_id = 0;
    EngagementEntityRef munition{};
    std::uint64_t effects_event_id = 0;
    std::uint64_t damage_report_id = 0;
    std::uint64_t observation_packet_version = 0;
};
