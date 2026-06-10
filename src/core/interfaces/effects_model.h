#pragma once

#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include <flecs.h>

#include "components/combat/common/weapon_common.h"
#include "runtime/contracts/engagement_contracts.h"

struct EffectsResult {
    bool destroy_missile = true;
    bool direct_hitbox_intersection = false;
    std::uint32_t projected_hitbox_count = 0;
    double spatial_effect_scale = 0.0;
    double mechanism_armor_scale = 1.0;
    double mechanism_exposure_scale = 1.0;
    double mechanism_effect_scale = 1.0;
    double mechanism_fragment_energy_j = 0.0;
    double mechanism_fragment_areal_density_per_m2 = 0.0;
    double mechanism_penetration_margin = 0.0;
    double mechanism_blast_overpressure_kpa = 0.0;
    double mechanism_blast_impulse_kpa_ms = 0.0;
    double mechanism_blast_scaled_distance_m_kg13 = 0.0;
    double mechanism_rod_cut_margin = 0.0;
    double mechanism_surface_incidence_cos = 0.0;
    std::uint32_t warhead_spatial_sample_count = 0;
    double warhead_spatial_hit_estimate = 0.0;
    double warhead_spatial_hit_fraction = 0.0;
    double warhead_spatial_energy_scale = 1.0;
    double warhead_spatial_pattern_scale = 1.0;
    double warhead_orientation_axis_forward = 0.0;
    double warhead_orientation_axis_right = 0.0;
    double warhead_orientation_axis_up = 0.0;
    double warhead_orientation_pattern_scale = 1.0;
    double component_threshold_scale = 1.0;
    double component_failure_probability = 0.0;
    std::string component_failure_probability_source = "none";
    bool component_failure_probability_calibrated = false;
    std::string component_failure_probability_evidence_dataset_ref;
    std::string component_failure_probability_evidence_row_id;
    std::string component_failure_probability_evidence_source_ref;
    std::string component_failure_probability_evidence_provenance;
    double component_failure_sample = 1.0;
    std::uint32_t component_failure_count = 0;
    std::uint32_t component_hit_count = 0;
    std::vector<ComponentMechanismLoadRow> component_mechanism_load_rows;
    std::string component_primary_name;
    std::string component_primary_system;
    double component_primary_redundancy_group = 0.0;
    bool component_primary_critical = false;
    std::string component_primary_redundancy_group_id;
    double component_primary_integrity = 1.0;
    double component_primary_mechanism_fragment_energy_j = 0.0;
    double component_primary_mechanism_fragment_areal_density_per_m2 = 0.0;
    double component_primary_mechanism_penetration_margin = 0.0;
    double component_primary_mechanism_blast_overpressure_kpa = 0.0;
    double component_primary_mechanism_blast_impulse_kpa_ms = 0.0;
    double component_primary_mechanism_blast_scaled_distance_m_kg13 = 0.0;
    double component_primary_mechanism_rod_cut_margin = 0.0;
    double component_primary_mechanism_surface_incidence_cos = 0.0;
    double component_redundancy_group_availability = 1.0;
    std::uint32_t component_redundancy_group_member_count = 0;
    std::uint32_t component_redundancy_group_failed_count = 0;
    bool vulnerability_profile_present = false;
    bool vulnerability_profile_synthetic = true;
    bool vulnerability_calibrated_evidence = false;
    bool vulnerability_pk_authority = false;
    bool vulnerability_deterministic_fuze_authority = false;
    bool vulnerability_evidence_dataset_valid = false;
    std::string vulnerability_evidence_dataset_ref;
    std::string vulnerability_calibration_status = "none";
    std::string vulnerability_provenance;
    std::string vulnerability_evidence_schema_version;
    std::string vulnerability_evidence_source_kind;
    std::string vulnerability_evidence_source_ref;
    std::string vulnerability_evidence_validation_artifact_ref;
    std::string vulnerability_evidence_validation_manifest_schema_version;
    std::string vulnerability_evidence_validation_status;
    std::string vulnerability_evidence_validation_artifact_sha256;
    std::string vulnerability_evidence_validated_surrogate_model_ref;
    std::string vulnerability_evidence_validation_benchmark_ref;
    std::string vulnerability_evidence_validation_metrics_ref;
    std::string vulnerability_evidence_validation_acceptance_criteria_ref;
    std::string vulnerability_aspect_bucket = "unknown";
    double vulnerability_family_scale = 1.0;
    double vulnerability_aspect_scale = 1.0;
    double vulnerability_closure_mps = 0.0;
    double vulnerability_closure_scale = 1.0;
    double vulnerability_miss_distance_scale = 1.0;
    double vulnerability_effect_scale = 1.0;
    std::string vulnerability_effect_scale_source = "profile_scale";
    std::string vulnerability_effect_scale_evidence_row_id;
    std::string vulnerability_effect_scale_evidence_source_ref;
    std::string vulnerability_effect_scale_evidence_provenance;
};

class IEffectsModel {
  public:
    virtual ~IEffectsModel() = default;

    virtual EffectsResult on_proximity_hit(flecs::world world, flecs::entity missile_entity,
                                           const Missile &missile, flecs::entity target_entity) = 0;
};

struct EffectsModelRef {
    IEffectsModel *model;
};

std::unique_ptr<IEffectsModel> make_default_effects_model();
