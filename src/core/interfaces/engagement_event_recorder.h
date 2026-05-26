#pragma once

#include <cstdint>
#include <string>

struct EngagementDamageStateSnapshot {
    bool entity_active = false;
    bool has_health = false;
    double hp = 0.0;
    double max_hp = 0.0;
    bool mission_kill = false;
    bool mobility_kill = false;
    bool sensor_kill = false;
    bool has_platform_damage = false;
    double mission_capability = 1.0;
    double mobility_capability = 1.0;
    double sensor_capability = 1.0;
    double survivability_margin = 1.0;
    std::string loss_state = "unknown";
};

class IEngagementEventRecorder {
public:
    virtual ~IEngagementEventRecorder() = default;

    virtual EngagementDamageStateSnapshot capture_engagement_damage_state(
        std::uint64_t target_id
    ) const = 0;

    virtual std::uint64_t record_effects_damage_event(
        std::uint64_t munition_entity_id,
        std::uint64_t target_id,
        const EngagementDamageStateSnapshot& before,
        const EngagementDamageStateSnapshot& after,
        const std::string& trigger_type,
        const std::string& outcome_state,
        double event_time_s,
        double nearest_approach_time_s,
        double miss_distance_m,
        double detonation_local_forward_m,
        double detonation_local_right_m,
        double detonation_local_up_m,
        double closure_mps,
        double missile_axis_forward,
        double missile_axis_right,
        double missile_axis_up,
        double quality,
        double confidence,
        const std::string& effect_family,
        double warhead_mass_kg = 0.0,
        double warhead_lethal_radius_m = 0.0,
        bool warhead_profile_synthetic = true,
        bool damage_scalar_synthetic = true,
        const std::string& fuze_type = "unknown",
        double fuze_trigger_radius_m = 0.0,
        double fuze_delay_s = 0.0,
        double fuze_reliability = 1.0,
        bool fuze_profile_synthetic = true,
        bool direct_hitbox_intersection = false,
        std::uint32_t projected_hitbox_count = 0,
        double spatial_effect_scale = 0.0,
        double mechanism_armor_scale = 1.0,
        double mechanism_exposure_scale = 1.0,
        double mechanism_effect_scale = 1.0,
        double component_threshold_scale = 1.0,
        double component_failure_probability = 0.0,
        double component_failure_sample = 1.0,
        std::uint32_t component_failure_count = 0,
        std::uint32_t component_hit_count = 0,
        const std::string& component_primary_name = "",
        const std::string& component_primary_system = "",
        double component_primary_redundancy_group = 0.0,
        bool component_primary_critical = false
    ) = 0;
};

struct EngagementEventRecorderRef {
    IEngagementEventRecorder* recorder = nullptr;
};
