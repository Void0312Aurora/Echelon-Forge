// Private fragment for default_effects_model.cpp.
// Included inside that file's anonymous namespace; not a standalone API.

void populate_default_effects_result(
    EffectsResult& result,
    const DefaultEffectsScratch& scratch,
    const Vec3& warhead_orientation_axis_body
) {
    result.direct_hitbox_intersection = scratch.direct_hitbox_intersection;
    result.projected_hitbox_count = scratch.projected_hitbox_count;
    result.spatial_effect_scale = scratch.spatial_effect_scale;
    result.mechanism_armor_scale = scratch.sampled_armor_scale;
    result.mechanism_exposure_scale = scratch.sampled_exposure_scale;
    result.mechanism_effect_scale = scratch.sampled_mechanism_scale;
    result.mechanism_fragment_energy_j = scratch.sampled_mechanism_fragment_energy_j;
    result.mechanism_fragment_areal_density_per_m2 =
        scratch.sampled_mechanism_fragment_areal_density_per_m2;
    result.mechanism_penetration_margin = scratch.sampled_mechanism_penetration_margin;
    result.mechanism_blast_overpressure_kpa =
        scratch.sampled_mechanism_blast_overpressure_kpa;
    result.mechanism_blast_impulse_kpa_ms =
        scratch.sampled_mechanism_blast_impulse_kpa_ms;
    result.mechanism_blast_scaled_distance_m_kg13 =
        scratch.sampled_mechanism_blast_scaled_distance_m_kg13;
    result.mechanism_rod_cut_margin = scratch.sampled_mechanism_rod_cut_margin;
    result.mechanism_surface_incidence_cos =
        scratch.sampled_mechanism_surface_incidence_cos;
    result.warhead_spatial_sample_count = scratch.sampled_warhead_spatial_sample_count;
    result.warhead_spatial_hit_estimate = scratch.sampled_warhead_spatial_hit_estimate;
    result.warhead_spatial_hit_fraction = scratch.sampled_warhead_spatial_hit_fraction;
    result.warhead_spatial_energy_scale = scratch.sampled_warhead_spatial_energy_scale;
    result.warhead_spatial_pattern_scale =
        scratch.sampled_warhead_spatial_sample_count > 0
            ? scratch.sampled_warhead_spatial_pattern_scale
            : 1.0;
    result.warhead_orientation_axis_forward = warhead_orientation_axis_body.x;
    result.warhead_orientation_axis_right = warhead_orientation_axis_body.y;
    result.warhead_orientation_axis_up = warhead_orientation_axis_body.z;
    result.warhead_orientation_pattern_scale =
        scratch.sampled_warhead_spatial_sample_count > 0
            ? scratch.sampled_warhead_orientation_pattern_scale
            : 1.0;
    result.component_threshold_scale = scratch.sampled_component_threshold_scale;
    result.component_failure_probability =
        scratch.sampled_component_failure_probability;
    result.component_failure_probability_source =
        scratch.sampled_component_failure_probability_source;
    result.component_failure_probability_calibrated =
        scratch.sampled_component_failure_probability_calibrated;
    result.component_failure_probability_evidence_dataset_ref =
        scratch.sampled_component_failure_probability_evidence_dataset_ref;
    result.component_failure_probability_evidence_row_id =
        scratch.sampled_component_failure_probability_evidence_row_id;
    result.component_failure_probability_evidence_source_ref =
        scratch.sampled_component_failure_probability_evidence_source_ref;
    result.component_failure_probability_evidence_provenance =
        scratch.sampled_component_failure_probability_evidence_provenance;
    result.component_failure_sample = scratch.sampled_component_failure_sample;
    result.component_failure_count = scratch.component_failure_count;
    result.component_hit_count = scratch.component_hit_count;
    result.component_mechanism_load_rows = scratch.component_mechanism_load_rows;
    result.component_primary_name = scratch.component_primary_name;
    result.component_primary_system = scratch.component_primary_system;
    result.component_primary_redundancy_group =
        scratch.component_primary_redundancy_group;
    result.component_primary_critical = scratch.component_primary_critical;
    result.component_primary_redundancy_group_id =
        scratch.component_primary_redundancy_group_id;
    result.component_primary_integrity = scratch.component_primary_integrity;
    result.component_primary_mechanism_fragment_energy_j =
        scratch.component_primary_mechanism_load.fragment_energy_j;
    result.component_primary_mechanism_fragment_areal_density_per_m2 =
        scratch.component_primary_mechanism_load.fragment_areal_density_per_m2;
    result.component_primary_mechanism_penetration_margin =
        scratch.component_primary_mechanism_load.penetration_margin;
    result.component_primary_mechanism_blast_overpressure_kpa =
        scratch.component_primary_mechanism_load.blast_overpressure_kpa;
    result.component_primary_mechanism_blast_impulse_kpa_ms =
        scratch.component_primary_mechanism_load.blast_impulse_kpa_ms;
    result.component_primary_mechanism_blast_scaled_distance_m_kg13 =
        scratch.component_primary_mechanism_load.blast_scaled_distance_m_kg13;
    result.component_primary_mechanism_rod_cut_margin =
        scratch.component_primary_mechanism_load.rod_cut_margin;
    result.component_primary_mechanism_surface_incidence_cos =
        scratch.component_primary_mechanism_load.surface_incidence_cos;
    result.component_redundancy_group_availability =
        scratch.component_redundancy_group_availability;
    result.component_redundancy_group_member_count =
        scratch.component_redundancy_group_member_count;
    result.component_redundancy_group_failed_count =
        scratch.component_redundancy_group_failed_count;
    result.vulnerability_profile_present =
        scratch.sampled_vulnerability_adjustment.profile_present;
    result.vulnerability_profile_synthetic =
        scratch.sampled_vulnerability_adjustment.synthetic;
    result.vulnerability_calibrated_evidence =
        scratch.sampled_vulnerability_adjustment.calibrated_evidence;
    result.vulnerability_pk_authority =
        scratch.sampled_vulnerability_adjustment.pk_authority;
    result.vulnerability_deterministic_fuze_authority =
        scratch.sampled_vulnerability_adjustment.deterministic_fuze_authority;
    result.vulnerability_evidence_dataset_valid =
        scratch.sampled_vulnerability_adjustment.evidence_dataset_valid;
    result.vulnerability_evidence_dataset_ref =
        scratch.sampled_vulnerability_adjustment.evidence_dataset_ref;
    result.vulnerability_calibration_status =
        scratch.sampled_vulnerability_adjustment.calibration_status;
    result.vulnerability_provenance =
        scratch.sampled_vulnerability_adjustment.provenance;
    result.vulnerability_evidence_schema_version =
        scratch.sampled_vulnerability_adjustment.evidence_schema_version;
    result.vulnerability_evidence_source_kind =
        scratch.sampled_vulnerability_adjustment.evidence_source_kind;
    result.vulnerability_evidence_source_ref =
        scratch.sampled_vulnerability_adjustment.evidence_source_ref;
    result.vulnerability_evidence_validation_artifact_ref =
        scratch.sampled_vulnerability_adjustment.evidence_validation_artifact_ref;
    result.vulnerability_evidence_validation_manifest_schema_version =
        scratch.sampled_vulnerability_adjustment.evidence_validation_manifest_schema_version;
    result.vulnerability_evidence_validation_status =
        scratch.sampled_vulnerability_adjustment.evidence_validation_status;
    result.vulnerability_evidence_validation_artifact_sha256 =
        scratch.sampled_vulnerability_adjustment.evidence_validation_artifact_sha256;
    result.vulnerability_evidence_validated_surrogate_model_ref =
        scratch.sampled_vulnerability_adjustment.evidence_validated_surrogate_model_ref;
    result.vulnerability_evidence_validation_benchmark_ref =
        scratch.sampled_vulnerability_adjustment.evidence_validation_benchmark_ref;
    result.vulnerability_evidence_validation_metrics_ref =
        scratch.sampled_vulnerability_adjustment.evidence_validation_metrics_ref;
    result.vulnerability_evidence_validation_acceptance_criteria_ref =
        scratch.sampled_vulnerability_adjustment.evidence_validation_acceptance_criteria_ref;
    result.vulnerability_aspect_bucket =
        scratch.sampled_vulnerability_adjustment.aspect_bucket;
    result.vulnerability_family_scale =
        scratch.sampled_vulnerability_adjustment.family_scale;
    result.vulnerability_aspect_scale =
        scratch.sampled_vulnerability_adjustment.aspect_scale;
    result.vulnerability_closure_mps =
        scratch.sampled_vulnerability_adjustment.closure_mps;
    result.vulnerability_closure_scale =
        scratch.sampled_vulnerability_adjustment.closure_scale;
    result.vulnerability_miss_distance_scale =
        scratch.sampled_vulnerability_adjustment.miss_distance_scale;
    result.vulnerability_effect_scale =
        scratch.sampled_vulnerability_adjustment.scale;
    result.vulnerability_effect_scale_source =
        scratch.sampled_vulnerability_adjustment.effect_scale_source;
    result.vulnerability_effect_scale_evidence_row_id =
        scratch.sampled_vulnerability_adjustment.effect_scale_evidence_row_id;
    result.vulnerability_effect_scale_evidence_source_ref =
        scratch.sampled_vulnerability_adjustment.effect_scale_evidence_source_ref;
    result.vulnerability_effect_scale_evidence_provenance =
        scratch.sampled_vulnerability_adjustment.effect_scale_evidence_provenance;
}
