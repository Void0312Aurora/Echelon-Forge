#pragma once

#include <cstdint>
#include <string>
#include <vector>

#include "runtime/contracts/engagement_contracts.h"

struct EngagementDamageStateSnapshot {
    bool entity_active = false;
    bool has_health = false;
    double hp = 0.0;
    double max_hp = 0.0;
    bool mission_kill = false;
    bool mobility_kill = false;
    bool sensor_kill = false;
    bool forced_landing = false;
    bool flight_control_kill = false;
    bool propulsion_kill = false;
    bool crew_kill = false;
    bool has_aircraft_damage = false;
    double flight_control_integrity = 1.0;
    double hydraulic_integrity = 1.0;
    double hydraulic_pressure_availability = 1.0;
    double propulsion_integrity = 1.0;
    double fuel_system_integrity = 1.0;
    double fuel_leak_severity = 0.0;
    double avionics_integrity = 1.0;
    double structural_integrity = 1.0;
    double crew_effectiveness = 1.0;
    double pilot_effectiveness = 1.0;
    double mission_crew_effectiveness = 1.0;
    double command_navigation_integrity = 1.0;
    double fire_severity = 0.0;
    bool has_platform_damage = false;
    double mission_capability = 1.0;
    double mobility_capability = 1.0;
    double sensor_capability = 1.0;
    double survivability_margin = 1.0;
    std::string loss_state = "unknown";
};

struct EngagementEffectsDamageEventRecord {
    std::uint64_t munition_entity_id = 0;
    std::uint64_t target_id = 0;
    EngagementDamageStateSnapshot before{};
    EngagementDamageStateSnapshot after{};
    EffectsEvent effects{};
};

struct EngagementNearestApproachEventRecord {
    std::uint64_t munition_entity_id = 0;
    std::uint64_t shooter_id = 0;
    std::uint64_t target_id = 0;
    NearestApproachEvent event{};
};

struct EngagementFuzeEvaluationEventRecord {
    std::uint64_t munition_entity_id = 0;
    std::uint64_t shooter_id = 0;
    std::uint64_t target_id = 0;
    FuzeEvaluationEvent event{};
};

struct EngagementWarheadMechanismEventRecord {
    std::uint64_t munition_entity_id = 0;
    std::uint64_t shooter_id = 0;
    std::uint64_t target_id = 0;
    std::uint64_t chain_id = 0;
    std::uint64_t parent_event_id = 0;
    WarheadMechanismEvent event{};
};

struct EngagementSpatialCoverageEventRecord {
    std::uint64_t munition_entity_id = 0;
    std::uint64_t shooter_id = 0;
    std::uint64_t target_id = 0;
    std::uint64_t chain_id = 0;
    std::uint64_t parent_event_id = 0;
    SpatialCoverageEvent event{};
};

struct EngagementComponentLoadEventRecord {
    std::uint64_t munition_entity_id = 0;
    std::uint64_t shooter_id = 0;
    std::uint64_t target_id = 0;
    std::uint64_t chain_id = 0;
    std::uint64_t parent_event_id = 0;
    ComponentLoadEvent event{};
};

struct EngagementComponentDamageEventRecord {
    std::uint64_t munition_entity_id = 0;
    std::uint64_t shooter_id = 0;
    std::uint64_t target_id = 0;
    std::uint64_t chain_id = 0;
    std::uint64_t parent_event_id = 0;
    ComponentDamageEvent event{};
};

class IEngagementEventRecorder {
  public:
    virtual ~IEngagementEventRecorder() = default;

    virtual EngagementDamageStateSnapshot
    capture_engagement_damage_state(std::uint64_t target_id) const = 0;

    virtual std::uint64_t
    record_effects_damage_event(EngagementEffectsDamageEventRecord record) = 0;

    virtual std::uint64_t
    record_nearest_approach_event(EngagementNearestApproachEventRecord record) = 0;

    virtual std::uint64_t
    record_fuze_evaluation_event(EngagementFuzeEvaluationEventRecord record) = 0;

    virtual std::uint64_t
    record_warhead_mechanism_event(EngagementWarheadMechanismEventRecord record) = 0;

    virtual std::uint64_t
    record_spatial_coverage_event(EngagementSpatialCoverageEventRecord record) = 0;

    virtual std::uint64_t
    record_component_load_event(EngagementComponentLoadEventRecord record) = 0;

    virtual std::uint64_t
    record_component_damage_event(EngagementComponentDamageEventRecord record) = 0;
};

struct EngagementEventRecorderRef {
    IEngagementEventRecorder *recorder = nullptr;
};
