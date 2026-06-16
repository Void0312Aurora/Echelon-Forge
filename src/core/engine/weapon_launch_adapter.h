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
    double miss_distance_m = 0.0;
    double detonation_local_forward_m = 0.0;
    double detonation_local_right_m = 0.0;
    double detonation_local_up_m = 0.0;
    double detonation_heading_deg = 0.0;
    double detonation_pitch_deg = 0.0;
    double detonation_roll_deg = 0.0;
    double closure_mps = 0.0;
    double missile_axis_forward = 0.0;
    double missile_axis_right = 0.0;
    double missile_axis_up = 0.0;
    double quality = 0.0;
    double confidence = 0.0;
    std::string effect_family = "unknown";
    double warhead_mass_kg = 0.0;
    double warhead_lethal_radius_m = 0.0;
    bool warhead_profile_synthetic = true;
    bool damage_scalar_synthetic = true;
    std::string fuze_type = "unknown";
    double fuze_trigger_radius_m = 0.0;
    double fuze_delay_s = 0.0;
    double fuze_reliability = 1.0;
    bool fuze_profile_synthetic = true;
    std::string fuze_signature_source = "none";
    double fuze_target_signature = 0.0;
    double fuze_signature_scale = 1.0;
    double fuze_effective_reliability = 1.0;
    double fuze_contact_surface_distance_m = 0.0;
    double fuze_contact_penetration_depth_m = 0.0;
    double fuze_contact_surface_tolerance_m = 0.0;
    bool fuze_contact_inside_hitbox = false;
    std::string fuze_sensor_opportunity_source = "none";
    double fuze_sensor_opportunity_score = 0.0;
    bool fuze_terminal_track_valid = false;
    bool fuze_target_detected = false;
    std::string fuze_target_detection_source = "none";
    double fuze_target_detection_confidence = 0.0;
    double fuze_target_detection_threshold = 0.0;
    std::string detonation_point_source = "unknown";
    double fuze_mechanism_coverage_score = 0.0;
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
    std::string air_system_hit_flags;
    std::string air_system_spatial_scales;
    std::string vulnerability_scale_trace;
    std::string producer_node_id;
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
    bool forced_landing = false;
    bool flight_control_kill = false;
    bool propulsion_kill = false;
    bool crew_kill = false;
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

inline EngagementEntityRef make_entity_ref(std::uint64_t world_index, std::uint64_t entity_id) {
    return EngagementEntityRef{
        .world_index = world_index,
        .entity_id = entity_id,
    };
}

inline LaunchRequest make_launch_request(const LaunchRequestSnapshot &snapshot) {
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

inline LaunchEvent make_launch_event(const LegacyLaunchOutcomeSnapshot &snapshot) {
    return LaunchEvent{
        .event_id = snapshot.event_id,
        .request_id = snapshot.request_id,
        .accepted = snapshot.accepted,
        .rejection_reason = snapshot.rejection_reason,
        .selected_launcher = snapshot.selected_launcher,
        .selected_munition = snapshot.selected_munition,
        .ammo_delta = snapshot.ammo_delta,
        .cooldown_delta_s = snapshot.cooldown_delta_s,
        .spawned_munition =
            make_entity_ref(snapshot.world_index, snapshot.spawned_munition_entity_id),
        .has_spawned_munition = snapshot.spawned_munition_entity_id != 0,
        .event_time_s = snapshot.event_time_s,
    };
}

inline MunitionLifecyclePacket
make_munition_lifecycle_packet(const MunitionLifecycleSnapshot &snapshot) {
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

inline EffectsEvent make_effects_event(const EffectsEventSnapshot &snapshot) {
    return EffectsEvent{
        .event_id = snapshot.event_id,
        .munition = make_entity_ref(snapshot.world_index, snapshot.munition_entity_id),
        .target = make_entity_ref(snapshot.world_index, snapshot.target_entity_id),
        .trigger_type = snapshot.trigger_type,
        .outcome_state = snapshot.outcome_state,
        .detonation_time_s = snapshot.detonation_time_s,
        .nearest_approach_time_s = snapshot.nearest_approach_time_s,
        .miss_distance_m = snapshot.miss_distance_m,
        .detonation_local_forward_m = snapshot.detonation_local_forward_m,
        .detonation_local_right_m = snapshot.detonation_local_right_m,
        .detonation_local_up_m = snapshot.detonation_local_up_m,
        .detonation_heading_deg = snapshot.detonation_heading_deg,
        .detonation_pitch_deg = snapshot.detonation_pitch_deg,
        .detonation_roll_deg = snapshot.detonation_roll_deg,
        .closure_mps = snapshot.closure_mps,
        .missile_axis_forward = snapshot.missile_axis_forward,
        .missile_axis_right = snapshot.missile_axis_right,
        .missile_axis_up = snapshot.missile_axis_up,
        .quality = snapshot.quality,
        .confidence = snapshot.confidence,
        .effect_family = snapshot.effect_family,
        .warhead_mass_kg = snapshot.warhead_mass_kg,
        .warhead_lethal_radius_m = snapshot.warhead_lethal_radius_m,
        .warhead_profile_synthetic = snapshot.warhead_profile_synthetic,
        .damage_scalar_synthetic = snapshot.damage_scalar_synthetic,
        .fuze_type = snapshot.fuze_type,
        .fuze_trigger_radius_m = snapshot.fuze_trigger_radius_m,
        .fuze_delay_s = snapshot.fuze_delay_s,
        .fuze_reliability = snapshot.fuze_reliability,
        .fuze_profile_synthetic = snapshot.fuze_profile_synthetic,
        .fuze_signature_source = snapshot.fuze_signature_source,
        .fuze_target_signature = snapshot.fuze_target_signature,
        .fuze_signature_scale = snapshot.fuze_signature_scale,
        .fuze_effective_reliability = snapshot.fuze_effective_reliability,
        .fuze_contact_surface_distance_m = snapshot.fuze_contact_surface_distance_m,
        .fuze_contact_penetration_depth_m = snapshot.fuze_contact_penetration_depth_m,
        .fuze_contact_surface_tolerance_m = snapshot.fuze_contact_surface_tolerance_m,
        .fuze_contact_inside_hitbox = snapshot.fuze_contact_inside_hitbox,
        .fuze_sensor_opportunity_source = snapshot.fuze_sensor_opportunity_source,
        .fuze_sensor_opportunity_score = snapshot.fuze_sensor_opportunity_score,
        .fuze_terminal_track_valid = snapshot.fuze_terminal_track_valid,
        .fuze_target_detected = snapshot.fuze_target_detected,
        .fuze_target_detection_source = snapshot.fuze_target_detection_source,
        .fuze_target_detection_confidence = snapshot.fuze_target_detection_confidence,
        .fuze_target_detection_threshold = snapshot.fuze_target_detection_threshold,
        .detonation_point_source = snapshot.detonation_point_source,
        .fuze_mechanism_coverage_score = snapshot.fuze_mechanism_coverage_score,
        .direct_hitbox_intersection = snapshot.direct_hitbox_intersection,
        .projected_hitbox_count = snapshot.projected_hitbox_count,
        .spatial_effect_scale = snapshot.spatial_effect_scale,
        .mechanism_armor_scale = snapshot.mechanism_armor_scale,
        .mechanism_exposure_scale = snapshot.mechanism_exposure_scale,
        .mechanism_effect_scale = snapshot.mechanism_effect_scale,
        .mechanism_fragment_energy_j = snapshot.mechanism_fragment_energy_j,
        .mechanism_fragment_areal_density_per_m2 = snapshot.mechanism_fragment_areal_density_per_m2,
        .mechanism_penetration_margin = snapshot.mechanism_penetration_margin,
        .mechanism_blast_overpressure_kpa = snapshot.mechanism_blast_overpressure_kpa,
        .mechanism_blast_impulse_kpa_ms = snapshot.mechanism_blast_impulse_kpa_ms,
        .mechanism_blast_scaled_distance_m_kg13 = snapshot.mechanism_blast_scaled_distance_m_kg13,
        .mechanism_rod_cut_margin = snapshot.mechanism_rod_cut_margin,
        .mechanism_surface_incidence_cos = snapshot.mechanism_surface_incidence_cos,
        .warhead_spatial_sample_count = snapshot.warhead_spatial_sample_count,
        .warhead_spatial_hit_estimate = snapshot.warhead_spatial_hit_estimate,
        .warhead_spatial_hit_fraction = snapshot.warhead_spatial_hit_fraction,
        .warhead_spatial_energy_scale = snapshot.warhead_spatial_energy_scale,
        .warhead_spatial_pattern_scale = snapshot.warhead_spatial_pattern_scale,
        .warhead_orientation_axis_forward = snapshot.warhead_orientation_axis_forward,
        .warhead_orientation_axis_right = snapshot.warhead_orientation_axis_right,
        .warhead_orientation_axis_up = snapshot.warhead_orientation_axis_up,
        .warhead_orientation_pattern_scale = snapshot.warhead_orientation_pattern_scale,
        .component_threshold_scale = snapshot.component_threshold_scale,
        .component_failure_probability = snapshot.component_failure_probability,
        .component_failure_probability_source = snapshot.component_failure_probability_source,
        .component_failure_probability_calibrated =
            snapshot.component_failure_probability_calibrated,
        .component_failure_probability_evidence_dataset_ref =
            snapshot.component_failure_probability_evidence_dataset_ref,
        .component_failure_probability_evidence_row_id =
            snapshot.component_failure_probability_evidence_row_id,
        .component_failure_probability_evidence_source_ref =
            snapshot.component_failure_probability_evidence_source_ref,
        .component_failure_probability_evidence_provenance =
            snapshot.component_failure_probability_evidence_provenance,
        .component_failure_sample = snapshot.component_failure_sample,
        .component_failure_count = snapshot.component_failure_count,
        .component_hit_count = snapshot.component_hit_count,
        .component_mechanism_load_rows = snapshot.component_mechanism_load_rows,
        .component_primary_name = snapshot.component_primary_name,
        .component_primary_system = snapshot.component_primary_system,
        .component_primary_redundancy_group = snapshot.component_primary_redundancy_group,
        .component_primary_critical = snapshot.component_primary_critical,
        .component_primary_redundancy_group_id = snapshot.component_primary_redundancy_group_id,
        .component_primary_integrity = snapshot.component_primary_integrity,
        .component_primary_mechanism_fragment_energy_j =
            snapshot.component_primary_mechanism_fragment_energy_j,
        .component_primary_mechanism_fragment_areal_density_per_m2 =
            snapshot.component_primary_mechanism_fragment_areal_density_per_m2,
        .component_primary_mechanism_penetration_margin =
            snapshot.component_primary_mechanism_penetration_margin,
        .component_primary_mechanism_blast_overpressure_kpa =
            snapshot.component_primary_mechanism_blast_overpressure_kpa,
        .component_primary_mechanism_blast_impulse_kpa_ms =
            snapshot.component_primary_mechanism_blast_impulse_kpa_ms,
        .component_primary_mechanism_blast_scaled_distance_m_kg13 =
            snapshot.component_primary_mechanism_blast_scaled_distance_m_kg13,
        .component_primary_mechanism_rod_cut_margin =
            snapshot.component_primary_mechanism_rod_cut_margin,
        .component_primary_mechanism_surface_incidence_cos =
            snapshot.component_primary_mechanism_surface_incidence_cos,
        .component_redundancy_group_availability = snapshot.component_redundancy_group_availability,
        .component_redundancy_group_member_count = snapshot.component_redundancy_group_member_count,
        .component_redundancy_group_failed_count = snapshot.component_redundancy_group_failed_count,
        .vulnerability_profile_present = snapshot.vulnerability_profile_present,
        .vulnerability_profile_synthetic = snapshot.vulnerability_profile_synthetic,
        .vulnerability_calibrated_evidence = snapshot.vulnerability_calibrated_evidence,
        .vulnerability_pk_authority = snapshot.vulnerability_pk_authority,
        .vulnerability_deterministic_fuze_authority =
            snapshot.vulnerability_deterministic_fuze_authority,
        .vulnerability_evidence_dataset_valid = snapshot.vulnerability_evidence_dataset_valid,
        .vulnerability_evidence_dataset_ref = snapshot.vulnerability_evidence_dataset_ref,
        .vulnerability_calibration_status = snapshot.vulnerability_calibration_status,
        .vulnerability_provenance = snapshot.vulnerability_provenance,
        .vulnerability_evidence_schema_version = snapshot.vulnerability_evidence_schema_version,
        .vulnerability_evidence_source_kind = snapshot.vulnerability_evidence_source_kind,
        .vulnerability_evidence_source_ref = snapshot.vulnerability_evidence_source_ref,
        .vulnerability_evidence_validation_artifact_ref =
            snapshot.vulnerability_evidence_validation_artifact_ref,
        .vulnerability_evidence_validation_manifest_schema_version =
            snapshot.vulnerability_evidence_validation_manifest_schema_version,
        .vulnerability_evidence_validation_status =
            snapshot.vulnerability_evidence_validation_status,
        .vulnerability_evidence_validation_artifact_sha256 =
            snapshot.vulnerability_evidence_validation_artifact_sha256,
        .vulnerability_evidence_validated_surrogate_model_ref =
            snapshot.vulnerability_evidence_validated_surrogate_model_ref,
        .vulnerability_evidence_validation_benchmark_ref =
            snapshot.vulnerability_evidence_validation_benchmark_ref,
        .vulnerability_evidence_validation_metrics_ref =
            snapshot.vulnerability_evidence_validation_metrics_ref,
        .vulnerability_evidence_validation_acceptance_criteria_ref =
            snapshot.vulnerability_evidence_validation_acceptance_criteria_ref,
        .vulnerability_aspect_bucket = snapshot.vulnerability_aspect_bucket,
        .vulnerability_family_scale = snapshot.vulnerability_family_scale,
        .vulnerability_aspect_scale = snapshot.vulnerability_aspect_scale,
        .vulnerability_closure_mps = snapshot.vulnerability_closure_mps,
        .vulnerability_closure_scale = snapshot.vulnerability_closure_scale,
        .vulnerability_miss_distance_scale = snapshot.vulnerability_miss_distance_scale,
        .vulnerability_effect_scale = snapshot.vulnerability_effect_scale,
        .vulnerability_effect_scale_source = snapshot.vulnerability_effect_scale_source,
        .vulnerability_effect_scale_evidence_row_id =
            snapshot.vulnerability_effect_scale_evidence_row_id,
        .vulnerability_effect_scale_evidence_source_ref =
            snapshot.vulnerability_effect_scale_evidence_source_ref,
        .vulnerability_effect_scale_evidence_provenance =
            snapshot.vulnerability_effect_scale_evidence_provenance,
        .air_system_hit_flags = snapshot.air_system_hit_flags,
        .air_system_spatial_scales = snapshot.air_system_spatial_scales,
        .vulnerability_scale_trace = snapshot.vulnerability_scale_trace,
        .producer_node_id = snapshot.producer_node_id,
    };
}

inline DamageReport make_damage_report(const DamageReportSnapshot &snapshot) {
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
        .forced_landing = snapshot.forced_landing,
        .flight_control_kill = snapshot.flight_control_kill,
        .propulsion_kill = snapshot.propulsion_kill,
        .crew_kill = snapshot.crew_kill,
        .loss_state_from = snapshot.loss_state_from,
        .loss_state_to = snapshot.loss_state_to,
        .destroyed = snapshot.destroyed,
        .report_time_s = snapshot.report_time_s,
    };
}

inline DiagnosticsTrace make_diagnostics_trace(const DiagnosticsTraceSnapshot &snapshot) {
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

} // namespace engagement_adapter
