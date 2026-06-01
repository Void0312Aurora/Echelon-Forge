#pragma once

#include <cstddef>
#include <cstdint>
#include <string>

#include <flecs.h>

#include "core/engine/engagement_event_types.h"
#include "core/interfaces/engagement_event_recorder.h"
#include "core/interfaces/engagement_launch_recorder.h"

class SimulationKernelEngagementEventStore final
    : public IEngagementEventRecorder,
      public IEngagementLaunchRecorder {
public:
    explicit SimulationKernelEngagementEventStore(flecs::world& ecs);

    EngagementDamageStateSnapshot capture_engagement_damage_state(
        std::uint64_t target_id
    ) const override;

    std::uint64_t record_effects_damage_event(
        EngagementEffectsDamageEventRecord record
    ) override;

    std::uint64_t record_legacy_launch_event(
        std::uint64_t shooter_id,
        std::uint64_t target_id,
        std::uint64_t spawned_munition_id,
        const std::string& selected_launcher,
        const std::string& selected_munition,
        int ammo_delta,
        double cooldown_delta_s,
        double event_time_s
    ) override;

    std::uint64_t record_effects_damage_event(
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
        double detonation_heading_deg,
        double detonation_pitch_deg,
        double detonation_roll_deg,
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
        const std::string& fuze_signature_source = "none",
        double fuze_target_signature = 0.0,
        double fuze_signature_scale = 1.0,
        double fuze_effective_reliability = 1.0,
        double fuze_contact_surface_distance_m = 0.0,
        double fuze_contact_penetration_depth_m = 0.0,
        double fuze_contact_surface_tolerance_m = 0.0,
        bool fuze_contact_inside_hitbox = false,
        bool direct_hitbox_intersection = false,
        std::uint32_t projected_hitbox_count = 0,
        double spatial_effect_scale = 0.0,
        double mechanism_armor_scale = 1.0,
        double mechanism_exposure_scale = 1.0,
        double mechanism_effect_scale = 1.0,
        double mechanism_fragment_energy_j = 0.0,
        double mechanism_fragment_areal_density_per_m2 = 0.0,
        double mechanism_penetration_margin = 0.0,
        double mechanism_blast_overpressure_kpa = 0.0,
        double mechanism_blast_impulse_kpa_ms = 0.0,
        double mechanism_blast_scaled_distance_m_kg13 = 0.0,
        double mechanism_rod_cut_margin = 0.0,
        std::uint32_t warhead_spatial_sample_count = 0,
        double warhead_spatial_hit_estimate = 0.0,
        double warhead_spatial_hit_fraction = 0.0,
        double warhead_spatial_energy_scale = 1.0,
        double warhead_spatial_pattern_scale = 1.0,
        double warhead_orientation_axis_forward = 0.0,
        double warhead_orientation_axis_right = 0.0,
        double warhead_orientation_axis_up = 0.0,
        double warhead_orientation_pattern_scale = 1.0,
        double component_threshold_scale = 1.0,
        double component_failure_probability = 0.0,
        const std::string& component_failure_probability_source = "none",
        bool component_failure_probability_calibrated = false,
        const std::string& component_failure_probability_evidence_dataset_ref = "",
        const std::string& component_failure_probability_evidence_row_id = "",
        const std::string& component_failure_probability_evidence_source_ref = "",
        const std::string& component_failure_probability_evidence_provenance = "",
        double component_failure_sample = 1.0,
        std::uint32_t component_failure_count = 0,
        std::uint32_t component_hit_count = 0,
        std::vector<ComponentMechanismLoadRow> component_mechanism_load_rows = {},
        const std::string& component_primary_name = "",
        const std::string& component_primary_system = "",
        double component_primary_redundancy_group = 0.0,
        bool component_primary_critical = false,
        const std::string& component_primary_redundancy_group_id = "",
        double component_primary_integrity = 1.0,
        double component_primary_mechanism_fragment_energy_j = 0.0,
        double component_primary_mechanism_fragment_areal_density_per_m2 = 0.0,
        double component_primary_mechanism_penetration_margin = 0.0,
        double component_primary_mechanism_blast_overpressure_kpa = 0.0,
        double component_primary_mechanism_blast_impulse_kpa_ms = 0.0,
        double component_primary_mechanism_blast_scaled_distance_m_kg13 = 0.0,
        double component_primary_mechanism_rod_cut_margin = 0.0,
        double component_redundancy_group_availability = 1.0,
        std::uint32_t component_redundancy_group_member_count = 0,
        std::uint32_t component_redundancy_group_failed_count = 0,
        bool vulnerability_profile_present = false,
        bool vulnerability_profile_synthetic = true,
        bool vulnerability_calibrated_evidence = false,
        bool vulnerability_pk_authority = false,
        bool vulnerability_deterministic_fuze_authority = false,
        bool vulnerability_evidence_dataset_valid = false,
        const std::string& vulnerability_evidence_dataset_ref = "",
        const std::string& vulnerability_calibration_status = "none",
        const std::string& vulnerability_provenance = "",
        const std::string& vulnerability_evidence_schema_version = "",
        const std::string& vulnerability_evidence_source_kind = "",
        const std::string& vulnerability_evidence_source_ref = "",
        const std::string& vulnerability_evidence_validation_artifact_ref = "",
        const std::string& vulnerability_evidence_validation_manifest_schema_version = "",
        const std::string& vulnerability_evidence_validation_status = "",
        const std::string& vulnerability_evidence_validation_artifact_sha256 = "",
        const std::string& vulnerability_evidence_validated_surrogate_model_ref = "",
        const std::string& vulnerability_evidence_validation_benchmark_ref = "",
        const std::string& vulnerability_evidence_validation_metrics_ref = "",
        const std::string& vulnerability_evidence_validation_acceptance_criteria_ref = "",
        const std::string& vulnerability_aspect_bucket = "unknown",
        double vulnerability_family_scale = 1.0,
        double vulnerability_aspect_scale = 1.0,
        double vulnerability_closure_mps = 0.0,
        double vulnerability_closure_scale = 1.0,
        double vulnerability_miss_distance_scale = 1.0,
        double vulnerability_effect_scale = 1.0,
        const std::string& vulnerability_effect_scale_source = "profile_scale",
        const std::string& vulnerability_effect_scale_evidence_row_id = "",
        const std::string& vulnerability_effect_scale_evidence_source_ref = "",
        const std::string& vulnerability_effect_scale_evidence_provenance = "",
        double mechanism_surface_incidence_cos = 0.0,
        double component_primary_mechanism_surface_incidence_cos = 0.0
    ) override;

    void set_pending_effects_launch_event_id(std::uint64_t launch_event_id) override;
    RecentEngagementEvents export_recent_events_sorted() const;
    void clear();

private:
    void reset_if_event_clock_rewound(double event_time_s);

    flecs::world& ecs_;
    RecentEngagementEvents recent_engagement_events_;
    std::uint64_t next_engagement_event_id_ = 1;
    std::uint64_t pending_effects_launch_event_id_ = 0;
    double recent_engagement_event_epoch_time_s_ = 0.0;
    std::int64_t recent_engagement_event_epoch_frame_ = 0;
    static constexpr std::size_t kMaxRecentEngagementEvents = 64;
};
