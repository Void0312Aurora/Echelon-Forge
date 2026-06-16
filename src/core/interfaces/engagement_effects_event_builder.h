#pragma once

#include "core/interfaces/effects_model.h"
#include "runtime/contracts/engagement_contracts.h"

namespace engagement_events {

inline void apply_effects_result_fields(EffectsEvent &effects, const EffectsResult &result) {
    effects.direct_hitbox_intersection = result.direct_hitbox_intersection;
    effects.projected_hitbox_count = result.projected_hitbox_count;
    effects.spatial_effect_scale = result.spatial_effect_scale;
    effects.mechanism_armor_scale = result.mechanism_armor_scale;
    effects.mechanism_exposure_scale = result.mechanism_exposure_scale;
    effects.mechanism_effect_scale = result.mechanism_effect_scale;
    effects.mechanism_fragment_energy_j = result.mechanism_fragment_energy_j;
    effects.mechanism_fragment_areal_density_per_m2 =
        result.mechanism_fragment_areal_density_per_m2;
    effects.mechanism_penetration_margin = result.mechanism_penetration_margin;
    effects.mechanism_blast_overpressure_kpa = result.mechanism_blast_overpressure_kpa;
    effects.mechanism_blast_impulse_kpa_ms = result.mechanism_blast_impulse_kpa_ms;
    effects.mechanism_blast_scaled_distance_m_kg13 = result.mechanism_blast_scaled_distance_m_kg13;
    effects.mechanism_rod_cut_margin = result.mechanism_rod_cut_margin;
    effects.mechanism_surface_incidence_cos = result.mechanism_surface_incidence_cos;
    effects.warhead_spatial_sample_count = result.warhead_spatial_sample_count;
    effects.warhead_spatial_hit_estimate = result.warhead_spatial_hit_estimate;
    effects.warhead_spatial_hit_fraction = result.warhead_spatial_hit_fraction;
    effects.warhead_spatial_energy_scale = result.warhead_spatial_energy_scale;
    effects.warhead_spatial_pattern_scale = result.warhead_spatial_pattern_scale;
    effects.warhead_orientation_axis_forward = result.warhead_orientation_axis_forward;
    effects.warhead_orientation_axis_right = result.warhead_orientation_axis_right;
    effects.warhead_orientation_axis_up = result.warhead_orientation_axis_up;
    effects.warhead_orientation_pattern_scale = result.warhead_orientation_pattern_scale;
    effects.component_threshold_scale = result.component_threshold_scale;
    effects.component_failure_probability = result.component_failure_probability;
    effects.component_failure_probability_source = result.component_failure_probability_source;
    effects.component_failure_probability_calibrated =
        result.component_failure_probability_calibrated;
    effects.component_failure_probability_evidence_dataset_ref =
        result.component_failure_probability_evidence_dataset_ref;
    effects.component_failure_probability_evidence_row_id =
        result.component_failure_probability_evidence_row_id;
    effects.component_failure_probability_evidence_source_ref =
        result.component_failure_probability_evidence_source_ref;
    effects.component_failure_probability_evidence_provenance =
        result.component_failure_probability_evidence_provenance;
    effects.component_failure_sample = result.component_failure_sample;
    effects.component_failure_count = result.component_failure_count;
    effects.component_hit_count = result.component_hit_count;
    effects.component_mechanism_load_rows = result.component_mechanism_load_rows;
    effects.component_primary_name = result.component_primary_name;
    effects.component_primary_system = result.component_primary_system;
    effects.component_primary_redundancy_group = result.component_primary_redundancy_group;
    effects.component_primary_critical = result.component_primary_critical;
    effects.component_primary_redundancy_group_id = result.component_primary_redundancy_group_id;
    effects.component_primary_integrity = result.component_primary_integrity;
    effects.component_primary_mechanism_fragment_energy_j =
        result.component_primary_mechanism_fragment_energy_j;
    effects.component_primary_mechanism_fragment_areal_density_per_m2 =
        result.component_primary_mechanism_fragment_areal_density_per_m2;
    effects.component_primary_mechanism_penetration_margin =
        result.component_primary_mechanism_penetration_margin;
    effects.component_primary_mechanism_blast_overpressure_kpa =
        result.component_primary_mechanism_blast_overpressure_kpa;
    effects.component_primary_mechanism_blast_impulse_kpa_ms =
        result.component_primary_mechanism_blast_impulse_kpa_ms;
    effects.component_primary_mechanism_blast_scaled_distance_m_kg13 =
        result.component_primary_mechanism_blast_scaled_distance_m_kg13;
    effects.component_primary_mechanism_rod_cut_margin =
        result.component_primary_mechanism_rod_cut_margin;
    effects.component_primary_mechanism_surface_incidence_cos =
        result.component_primary_mechanism_surface_incidence_cos;
    effects.component_redundancy_group_availability =
        result.component_redundancy_group_availability;
    effects.component_redundancy_group_member_count =
        result.component_redundancy_group_member_count;
    effects.component_redundancy_group_failed_count =
        result.component_redundancy_group_failed_count;
    effects.vulnerability_profile_present = result.vulnerability_profile_present;
    effects.vulnerability_profile_synthetic = result.vulnerability_profile_synthetic;
    effects.vulnerability_calibrated_evidence = result.vulnerability_calibrated_evidence;
    effects.vulnerability_pk_authority = result.vulnerability_pk_authority;
    effects.vulnerability_deterministic_fuze_authority =
        result.vulnerability_deterministic_fuze_authority;
    effects.vulnerability_evidence_dataset_valid = result.vulnerability_evidence_dataset_valid;
    effects.vulnerability_evidence_dataset_ref = result.vulnerability_evidence_dataset_ref;
    effects.vulnerability_calibration_status = result.vulnerability_calibration_status;
    effects.vulnerability_provenance = result.vulnerability_provenance;
    effects.vulnerability_evidence_schema_version = result.vulnerability_evidence_schema_version;
    effects.vulnerability_evidence_source_kind = result.vulnerability_evidence_source_kind;
    effects.vulnerability_evidence_source_ref = result.vulnerability_evidence_source_ref;
    effects.vulnerability_evidence_validation_artifact_ref =
        result.vulnerability_evidence_validation_artifact_ref;
    effects.vulnerability_evidence_validation_manifest_schema_version =
        result.vulnerability_evidence_validation_manifest_schema_version;
    effects.vulnerability_evidence_validation_status =
        result.vulnerability_evidence_validation_status;
    effects.vulnerability_evidence_validation_artifact_sha256 =
        result.vulnerability_evidence_validation_artifact_sha256;
    effects.vulnerability_evidence_validated_surrogate_model_ref =
        result.vulnerability_evidence_validated_surrogate_model_ref;
    effects.vulnerability_evidence_validation_benchmark_ref =
        result.vulnerability_evidence_validation_benchmark_ref;
    effects.vulnerability_evidence_validation_metrics_ref =
        result.vulnerability_evidence_validation_metrics_ref;
    effects.vulnerability_evidence_validation_acceptance_criteria_ref =
        result.vulnerability_evidence_validation_acceptance_criteria_ref;
    effects.vulnerability_aspect_bucket = result.vulnerability_aspect_bucket;
    effects.vulnerability_family_scale = result.vulnerability_family_scale;
    effects.vulnerability_aspect_scale = result.vulnerability_aspect_scale;
    effects.vulnerability_closure_mps = result.vulnerability_closure_mps;
    effects.vulnerability_closure_scale = result.vulnerability_closure_scale;
    effects.vulnerability_miss_distance_scale = result.vulnerability_miss_distance_scale;
    effects.vulnerability_effect_scale = result.vulnerability_effect_scale;
    effects.vulnerability_effect_scale_source = result.vulnerability_effect_scale_source;
    effects.vulnerability_effect_scale_evidence_row_id =
        result.vulnerability_effect_scale_evidence_row_id;
    effects.vulnerability_effect_scale_evidence_source_ref =
        result.vulnerability_effect_scale_evidence_source_ref;
    effects.vulnerability_effect_scale_evidence_provenance =
        result.vulnerability_effect_scale_evidence_provenance;
    effects.air_system_hit_flags = result.air_system_hit_flags;
    effects.air_system_spatial_scales = result.air_system_spatial_scales;
    effects.vulnerability_scale_trace = result.vulnerability_scale_trace;
}

} // namespace engagement_events
