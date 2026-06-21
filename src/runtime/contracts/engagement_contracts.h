#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

inline constexpr std::uint32_t kLethalityChainContractSchemaVersion = 1;

inline constexpr std::string_view kLethalityChainStageNearestApproach = "nearest_approach";
inline constexpr std::string_view kLethalityChainStageFuze = "fuze";
inline constexpr std::string_view kLethalityChainStageWarheadMechanism = "warhead_mechanism";
inline constexpr std::string_view kLethalityChainStageSpatialCoverage = "spatial_coverage";
inline constexpr std::string_view kLethalityChainStageComponentLoad = "component_load";
inline constexpr std::string_view kLethalityChainStageComponentDamage = "component_damage";
inline constexpr std::string_view kLethalityChainStageStructuralBreakup = "structural_breakup";
inline constexpr std::string_view kLethalityChainStagePlatformConsequence = "platform_consequence";
inline constexpr std::string_view kLethalityChainStageLifecycle = "lifecycle";
inline constexpr std::string_view kLethalityChainStageTrainingProjection = "training_projection";

inline constexpr std::array<std::string_view, 10> kLethalityChainCanonicalStages = {
    kLethalityChainStageNearestApproach,   kLethalityChainStageFuze,
    kLethalityChainStageWarheadMechanism,  kLethalityChainStageSpatialCoverage,
    kLethalityChainStageComponentLoad,     kLethalityChainStageComponentDamage,
    kLethalityChainStageStructuralBreakup, kLethalityChainStagePlatformConsequence,
    kLethalityChainStageLifecycle,         kLethalityChainStageTrainingProjection,
};

inline constexpr std::string_view kLethalityReasonFuzeArmed = "fuze_armed";
inline constexpr std::string_view kLethalityReasonFuzeNoDetonation = "fuze_no_detonation";
inline constexpr std::string_view kLethalityReasonFuzeNoTerminalTrack = "fuze_no_terminal_track";
inline constexpr std::string_view kLethalityReasonMissOutsideTriggerRadius =
    "miss_outside_trigger_radius";
inline constexpr std::string_view kLethalityReasonOutsideSensorWindow = "outside_sensor_window";
inline constexpr std::string_view kLethalityReasonTargetNotDetected = "target_not_detected";
inline constexpr std::string_view kLethalityReasonMissileTimeout = "missile_timeout";
inline constexpr std::string_view kLethalityReasonPlatformConsequenceProjection =
    "generic_research_platform_consequence_projection";
inline constexpr std::string_view kLethalityReasonLifecycleProjection =
    "transitional_damage_report_projection";

inline constexpr std::array<std::string_view, 6> kLethalityChainTerminalNegativeReasons = {
    kLethalityReasonFuzeNoDetonation,         kLethalityReasonFuzeNoTerminalTrack,
    kLethalityReasonMissOutsideTriggerRadius, kLethalityReasonOutsideSensorWindow,
    kLethalityReasonTargetNotDetected,        kLethalityReasonMissileTimeout,
};

inline constexpr std::string_view kLethalityObservationModeSampledRuntime = "sampled_runtime";
inline constexpr std::string_view kLethalityObservationModeExpectedProjection =
    "expected_projection";
inline constexpr std::string_view kLethalityConsumerVisibilityDiagnosticsAndTraining =
    "diagnostics_and_training";
inline constexpr std::string_view kLethalityConsumerVisibilityDiagnosticsOnly = "diagnostics_only";

struct EngagementEntityRef {
    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
};

struct LethalityChainHeader {
    std::uint32_t schema_version = kLethalityChainContractSchemaVersion;
    std::uint64_t chain_id = 0;
    std::uint64_t event_id = 0;
    std::uint64_t parent_event_id = 0;
    std::string stage = "unknown";
    std::string status = "not_evaluated";
    std::string reason;
    double source_time_s = 0.0;
    std::uint64_t source_frame = 0;
    EngagementEntityRef munition{};
    EngagementEntityRef shooter{};
    EngagementEntityRef target{};
    std::string producer_node_id;
    std::string fidelity_mode = "unspecified";
    std::string evidence_level = "uncalibrated";
    std::string observation_mode = std::string(kLethalityObservationModeSampledRuntime);
    std::string consumer_visibility =
        std::string(kLethalityConsumerVisibilityDiagnosticsAndTraining);
    double confidence = 0.0;
};

struct NearestApproachEvent {
    LethalityChainHeader header{};
    double nearest_approach_time_s = 0.0;
    double miss_distance_m = 0.0;
    double local_forward_m = 0.0;
    double local_right_m = 0.0;
    double local_up_m = 0.0;
    double closure_mps = 0.0;
    std::string aspect_bucket = "unknown";
};

struct FuzeEvaluationEvent {
    LethalityChainHeader header{};
    std::string fuze_type = "unknown";
    bool armed = false;
    bool triggered = false;
    std::string failure_reason;
    double delay_s = 0.0;
    double reliability = 1.0;
    double sample = 1.0;
    double expected_detonation_probability = 0.0;
    bool sampled_outcome = true;
    double trigger_radius_m = 0.0;
    double contact_surface_distance_m = 0.0;
    double contact_penetration_depth_m = 0.0;
    double contact_surface_tolerance_m = 0.0;
    bool contact_inside_hitbox = false;
    std::string sensor_opportunity_source = "none";
    double sensor_opportunity_score = 0.0;
    bool terminal_track_valid = false;
    bool target_detected = false;
    std::string target_detection_source = "none";
    double target_detection_confidence = 0.0;
    double target_detection_threshold = 0.0;
    std::string detonation_point_source = "unknown";
    double mechanism_coverage_score = 0.0;
    bool direct_hitbox_intersection = false;
};

struct WarheadMechanismEvent {
    LethalityChainHeader header{};
    std::string mechanism_family = "unknown";
    double warhead_mass_kg = 0.0;
    double lethal_radius_m = 0.0;
    double fragment_energy_j = 0.0;
    double fragment_density_per_m2 = 0.0;
    double blast_overpressure_kpa = 0.0;
    double blast_impulse_kpa_ms = 0.0;
    double blast_scaled_distance_m_kg13 = 0.0;
    double rod_cut_margin = 0.0;
    double penetration_margin = 0.0;
    double surface_incidence_cos = 0.0;
};

struct SpatialCoverageEvent {
    LethalityChainHeader header{};
    std::uint32_t projected_hitbox_count = 0;
    std::uint32_t sample_count = 0;
    double hit_estimate = 0.0;
    double hit_fraction = 0.0;
    double energy_scale = 1.0;
    double pattern_scale = 1.0;
    double orientation_axis_forward = 0.0;
    double orientation_axis_right = 0.0;
    double orientation_axis_up = 0.0;
};

struct ComponentLoadEvent {
    LethalityChainHeader header{};
    std::string component_name;
    std::string component_system;
    std::string component_redundancy_group_id;
    bool direct_hit = false;
    double distance_m = 0.0;
    double effect_scale = 0.0;
    double spatial_intersection_fraction = 0.0;
    double pattern_weight = 1.0;
    double orientation_weight = 1.0;
    double receiver_exposure_fraction = 1.0;
    double armor_transmission = 1.0;
    double sampling_confidence = 1.0;
    double load_intensity_scale = 1.0;
    double fragment_energy_j = 0.0;
    double fragment_density_per_m2 = 0.0;
    double penetration_margin = 0.0;
    double blast_overpressure_kpa = 0.0;
    double blast_impulse_kpa_ms = 0.0;
    double blast_scaled_distance_m_kg13 = 0.0;
    double rod_cut_margin = 0.0;
    double surface_incidence_cos = 0.0;
    std::string load_source = "unprojected";
};

struct ComponentDamageEvent {
    LethalityChainHeader header{};
    std::string component_name;
    std::string component_system;
    std::string component_redundancy_group_id;
    double integrity_before = 1.0;
    double integrity_after = 1.0;
    std::string failure_mode = "none";
    double failure_severity = 0.0;
    double failure_probability = 0.0;
    double failure_sample = 1.0;
};

struct PlatformConsequenceEvent {
    LethalityChainHeader header{};
    double mission_capability_before = 1.0;
    double mission_capability_after = 1.0;
    double mobility_capability_before = 1.0;
    double mobility_capability_after = 1.0;
    double sensor_capability_before = 1.0;
    double sensor_capability_after = 1.0;
    double survivability_capability_before = 1.0;
    double survivability_capability_after = 1.0;
    bool mission_kill = false;
    bool mobility_kill = false;
    bool sensor_kill = false;
    bool survivability_kill = false;
    bool flight_control_kill = false;
    bool propulsion_kill = false;
    bool forced_landing = false;
    bool crew_kill = false;
    double control_delta = 0.0;
    double engine_delta = 0.0;
    double fuel_leak_delta = 0.0;
    std::string fire_state = "unknown";
    std::string aircraft_damage_state_before;
    std::string aircraft_damage_state_after;
    std::string aircraft_damage_state_delta;
    std::string air_system_hit_flags;
    std::string air_system_spatial_scales;
    std::string vulnerability_scale_trace;
    std::string loss_state_from = "unknown";
    std::string loss_state_to = "unknown";
};

struct StructuralBreakupEvent {
    LethalityChainHeader header{};
    std::string breakup_state = "none";
    std::string break_mode = "none";
    std::string detached_part_ref;
    std::uint32_t detached_part_count = 0;
    bool airframe_breakup = false;
    std::uint64_t cause_event_id = 0;
};

struct LifecycleTransitionEvent {
    LethalityChainHeader header{};
    std::string lifecycle_from = "unknown";
    std::string lifecycle_to = "unknown";
    std::string ground_lifecycle = "unknown";
    EngagementEntityRef wreck_entity{};
    std::uint32_t debris_count = 0;
    bool terminal = false;
    std::uint64_t terminal_projection_id = 0;
};

struct TrainingProjectionEvent {
    LethalityChainHeader header{};
    std::vector<std::uint64_t> consumed_event_ids;
    std::string consumer_node_id;
    std::string consumer_version;
    std::string projection_kind = "training_consumer";
    std::string reward_term;
    double reward_delta = 0.0;
    std::string terminal_reason;
    bool fact_source = false;
};

struct ComponentMechanismLoadRow {
    std::string component_name;
    std::string component_system;
    std::string component_redundancy_group_id;
    bool direct_hit = false;
    double distance_m = 0.0;
    double effect_scale = 0.0;
    std::uint32_t component_dependency_propagation_count = 0;
    std::string component_dependency_target_system;
    std::string component_dependency_edge_type = "none";
    double component_dependency_threshold = 1.0;
    double component_dependency_delay_s = 0.0;
    std::string component_dependency_direction = "one_way";
    std::string component_dependency_provenance;
    double component_dependency_source_availability = 1.0;
    double component_dependency_effective_scale = 0.0;
    bool component_dependency_propagated = false;
    double mechanism_fragment_energy_j = 0.0;
    double mechanism_fragment_areal_density_per_m2 = 0.0;
    double mechanism_penetration_margin = 0.0;
    double mechanism_blast_overpressure_kpa = 0.0;
    double mechanism_blast_impulse_kpa_ms = 0.0;
    double mechanism_blast_scaled_distance_m_kg13 = 0.0;
    double mechanism_rod_cut_margin = 0.0;
    double mechanism_surface_incidence_cos = 0.0;
};

struct ComponentResponseRow {
    std::string owner_stage = "component_response";
    std::string source_current_owner_stage = "component_response_row";
    std::uint32_t source_row_index = 0;
    std::string component_name;
    std::string component_system;
    std::string component_redundancy_group_id;
    double threshold_scale = 1.0;
    double failure_probability = 0.0;
    double failure_sample = 1.0;
    std::string failure_probability_source = "none";
    bool failure_probability_calibrated = false;
    std::string failure_probability_evidence_dataset_ref;
    std::string failure_probability_evidence_row_id;
    std::string failure_probability_evidence_source_ref;
    std::string failure_probability_evidence_provenance;
    bool failure_probability_authority = false;
    bool failure_probability_component_specific = false;
    std::string failure_probability_weapon_family = "unknown";
    std::string failure_probability_aspect_bucket = "unknown";
    std::string failure_probability_closure_bucket = "unknown";
    std::string failure_probability_miss_distance_bucket = "unknown";
    std::string failure_probability_evidence_component_name;
    std::string failure_probability_evidence_component_system;
    std::string failure_probability_evidence_component_redundancy_group_id;
    std::string failure_mode = "none";
    double failure_severity = 0.0;
    std::vector<std::string> failure_mode_names;
    std::vector<double> failure_mode_severities;
    std::string failure_mode_source = "none";
    bool failure_mode_authority = false;
    double integrity_before = 1.0;
    double integrity_after = 1.0;
    double redundancy_group_availability_before = 1.0;
    double redundancy_group_availability_after = 1.0;
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
    std::string producer_node_id;
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
    std::vector<ComponentResponseRow> component_response_rows;
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

struct KillChainApproachFact {
    std::string owner_stage = "approach";
    double closest_distance_m = 0.0;
    double closest_point_local_forward_m = 0.0;
    double closest_point_local_right_m = 0.0;
    double closest_point_local_up_m = 0.0;
    double closure_mps = 0.0;
    double nearest_approach_time_s = 0.0;
};

struct KillChainFuzeDecision {
    std::string owner_stage = "fuze_decision";
    std::string fuze_type = "unknown";
    bool detonated = false;
    std::string outcome_state = "unknown";
    double detonation_time_s = 0.0;
    double detonation_probability = 0.0;
    double fuze_quality = 0.0;
    double sensor_opportunity_score = 0.0;
    bool terminal_track_valid = false;
    bool target_detected = false;
    double target_detection_confidence = 0.0;
    double target_detection_threshold = 0.0;
    std::string detonation_point_source = "unknown";
};

struct KillChainComponentLoadFact {
    std::string owner_stage = "warhead_load_field";
    std::string component_name;
    std::string component_system;
    std::string component_redundancy_group_id;
    bool direct_hit = false;
    double distance_m = 0.0;
    double effect_scale = 0.0;
    double spatial_intersection_fraction = 0.0;
    double pattern_weight = 1.0;
    double orientation_weight = 1.0;
    double receiver_exposure_fraction = 1.0;
    double armor_transmission = 1.0;
    double sampling_confidence = 1.0;
    double load_intensity_scale = 1.0;
    double fragment_energy_j = 0.0;
    double fragment_areal_density_per_m2 = 0.0;
    double penetration_margin = 0.0;
    double blast_overpressure_kpa = 0.0;
    double blast_impulse_kpa_ms = 0.0;
    double blast_scaled_distance_m_kg13 = 0.0;
    double rod_cut_margin = 0.0;
    double surface_incidence_cos = 0.0;
};

struct KillChainWarheadLoadField {
    std::string owner_stage = "warhead_load_field";
    std::string effect_family = "unknown";
    double warhead_mass_kg = 0.0;
    double lethal_radius_m = 0.0;
    double spatial_effect_scale = 0.0;
    double armor_transmission = 1.0;
    double receiver_exposure_fraction = 1.0;
    double mechanism_effect_scale = 1.0;
    std::uint32_t projected_hitbox_count = 0;
    std::uint32_t spatial_sample_count = 0;
    double spatial_hit_estimate = 0.0;
    double spatial_hit_fraction = 0.0;
    double spatial_energy_scale = 1.0;
    double spatial_pattern_scale = 1.0;
    double orientation_pattern_scale = 1.0;
    double fragment_energy_j = 0.0;
    double fragment_areal_density_per_m2 = 0.0;
    double penetration_margin = 0.0;
    double blast_overpressure_kpa = 0.0;
    double blast_impulse_kpa_ms = 0.0;
    double blast_scaled_distance_m_kg13 = 0.0;
    double rod_cut_margin = 0.0;
    double surface_incidence_cos = 0.0;
    std::vector<KillChainComponentLoadFact> component_loads;
};

struct KillChainTargetSusceptibility {
    std::string owner_stage = "target_susceptibility";
    bool vulnerability_profile_present = false;
    bool vulnerability_profile_synthetic = true;
    bool calibrated_evidence = false;
    bool pk_authority = false;
    bool deterministic_fuze_authority = false;
    std::string calibration_status = "none";
    std::string aspect_bucket = "unknown";
    double family_scale = 1.0;
    double aspect_scale = 1.0;
    double closure_scale = 1.0;
    double miss_distance_scale = 1.0;
    double effect_scale = 1.0;
};

struct KillChainComponentResponseFact {
    std::string owner_stage = "component_response";
    std::string source_current_owner_stage = "component_response_row";
    std::uint32_t source_row_index = 0;
    std::string component_name;
    std::string component_system;
    std::string component_redundancy_group_id;
    double threshold_scale = 1.0;
    double failure_probability = 0.0;
    double failure_sample = 1.0;
    std::string failure_probability_source = "none";
    bool failure_probability_calibrated = false;
    std::string failure_probability_evidence_dataset_ref;
    std::string failure_probability_evidence_row_id;
    std::string failure_probability_evidence_source_ref;
    std::string failure_probability_evidence_provenance;
    bool failure_probability_authority = false;
    bool failure_probability_component_specific = false;
    std::string failure_probability_weapon_family = "unknown";
    std::string failure_probability_aspect_bucket = "unknown";
    std::string failure_probability_closure_bucket = "unknown";
    std::string failure_probability_miss_distance_bucket = "unknown";
    std::string failure_mode = "none";
    double failure_severity = 0.0;
    std::vector<std::string> failure_mode_names;
    std::vector<double> failure_mode_severities;
    std::string failure_mode_source = "none";
    bool failure_mode_authority = false;
    double integrity_before = 1.0;
    double integrity_after = 1.0;
    double redundancy_group_availability_before = 1.0;
    double redundancy_group_availability_after = 1.0;
};

struct KillChainConsequenceProjection {
    std::string owner_stage = "consequence_projection";
    std::string outcome_state = "unknown";
    std::uint32_t component_hit_count = 0;
    std::uint32_t component_failure_count = 0;
    std::string primary_component_name;
    std::string primary_component_system;
    double primary_component_integrity = 1.0;
    double redundancy_group_availability = 1.0;
    std::string air_system_hit_flags;
    std::string air_system_spatial_scales;
    std::string vulnerability_scale_trace;
};

struct KillChainRuntimeFacade {
    std::uint32_t schema_version = 1;
    std::string schema_name = "a2.kill_chain_runtime_facade.v1";
    bool runtime_dto_authority = true;
    bool runtime_parameter_retuning = false;
    bool calibration_authority = false;
    bool real_world_pk = false;
    KillChainApproachFact approach_fact{};
    KillChainFuzeDecision fuze_decision{};
    KillChainWarheadLoadField warhead_load_field{};
    KillChainTargetSusceptibility target_susceptibility{};
    std::vector<KillChainComponentResponseFact> component_responses;
    KillChainConsequenceProjection consequence_projection{};
};

inline KillChainRuntimeFacade make_kill_chain_runtime_facade(const EffectsEvent &effects) {
    KillChainRuntimeFacade facade{};

    facade.approach_fact.closest_distance_m = effects.miss_distance_m;
    facade.approach_fact.closest_point_local_forward_m = effects.detonation_local_forward_m;
    facade.approach_fact.closest_point_local_right_m = effects.detonation_local_right_m;
    facade.approach_fact.closest_point_local_up_m = effects.detonation_local_up_m;
    facade.approach_fact.closure_mps = effects.closure_mps;
    facade.approach_fact.nearest_approach_time_s = effects.nearest_approach_time_s;

    facade.fuze_decision.fuze_type = effects.fuze_type;
    facade.fuze_decision.detonated = effects.outcome_state != "fuze_no_detonation";
    facade.fuze_decision.outcome_state = effects.outcome_state;
    facade.fuze_decision.detonation_time_s = effects.detonation_time_s;
    facade.fuze_decision.detonation_probability = effects.confidence;
    facade.fuze_decision.fuze_quality = effects.quality;
    facade.fuze_decision.sensor_opportunity_score = effects.fuze_sensor_opportunity_score;
    facade.fuze_decision.terminal_track_valid = effects.fuze_terminal_track_valid;
    facade.fuze_decision.target_detected = effects.fuze_target_detected;
    facade.fuze_decision.target_detection_confidence = effects.fuze_target_detection_confidence;
    facade.fuze_decision.target_detection_threshold = effects.fuze_target_detection_threshold;
    facade.fuze_decision.detonation_point_source = effects.detonation_point_source;

    facade.warhead_load_field.effect_family = effects.effect_family;
    facade.warhead_load_field.warhead_mass_kg = effects.warhead_mass_kg;
    facade.warhead_load_field.lethal_radius_m = effects.warhead_lethal_radius_m;
    facade.warhead_load_field.spatial_effect_scale = effects.spatial_effect_scale;
    facade.warhead_load_field.armor_transmission = effects.mechanism_armor_scale;
    facade.warhead_load_field.receiver_exposure_fraction = effects.mechanism_exposure_scale;
    facade.warhead_load_field.mechanism_effect_scale = effects.mechanism_effect_scale;
    facade.warhead_load_field.projected_hitbox_count = effects.projected_hitbox_count;
    facade.warhead_load_field.spatial_sample_count = effects.warhead_spatial_sample_count;
    facade.warhead_load_field.spatial_hit_estimate = effects.warhead_spatial_hit_estimate;
    facade.warhead_load_field.spatial_hit_fraction = effects.warhead_spatial_hit_fraction;
    facade.warhead_load_field.spatial_energy_scale = effects.warhead_spatial_energy_scale;
    facade.warhead_load_field.spatial_pattern_scale = effects.warhead_spatial_pattern_scale;
    facade.warhead_load_field.orientation_pattern_scale =
        effects.warhead_orientation_pattern_scale;
    facade.warhead_load_field.fragment_energy_j = effects.mechanism_fragment_energy_j;
    facade.warhead_load_field.fragment_areal_density_per_m2 =
        effects.mechanism_fragment_areal_density_per_m2;
    facade.warhead_load_field.penetration_margin = effects.mechanism_penetration_margin;
    facade.warhead_load_field.blast_overpressure_kpa = effects.mechanism_blast_overpressure_kpa;
    facade.warhead_load_field.blast_impulse_kpa_ms = effects.mechanism_blast_impulse_kpa_ms;
    facade.warhead_load_field.blast_scaled_distance_m_kg13 =
        effects.mechanism_blast_scaled_distance_m_kg13;
    facade.warhead_load_field.rod_cut_margin = effects.mechanism_rod_cut_margin;
    facade.warhead_load_field.surface_incidence_cos = effects.mechanism_surface_incidence_cos;

    facade.target_susceptibility.vulnerability_profile_present =
        effects.vulnerability_profile_present;
    facade.target_susceptibility.vulnerability_profile_synthetic =
        effects.vulnerability_profile_synthetic;
    facade.target_susceptibility.calibrated_evidence = effects.vulnerability_calibrated_evidence;
    facade.target_susceptibility.pk_authority = effects.vulnerability_pk_authority;
    facade.target_susceptibility.deterministic_fuze_authority =
        effects.vulnerability_deterministic_fuze_authority;
    facade.target_susceptibility.calibration_status = effects.vulnerability_calibration_status;
    facade.target_susceptibility.aspect_bucket = effects.vulnerability_aspect_bucket;
    facade.target_susceptibility.family_scale = effects.vulnerability_family_scale;
    facade.target_susceptibility.aspect_scale = effects.vulnerability_aspect_scale;
    facade.target_susceptibility.closure_scale = effects.vulnerability_closure_scale;
    facade.target_susceptibility.miss_distance_scale =
        effects.vulnerability_miss_distance_scale;
    facade.target_susceptibility.effect_scale = effects.vulnerability_effect_scale;

    facade.warhead_load_field.component_loads.reserve(
        effects.component_mechanism_load_rows.size());
    facade.component_responses.reserve(effects.component_response_rows.size());
    for (const ComponentMechanismLoadRow &row : effects.component_mechanism_load_rows) {
        KillChainComponentLoadFact load{};
        load.component_name = row.component_name;
        load.component_system = row.component_system;
        load.component_redundancy_group_id = row.component_redundancy_group_id;
        load.direct_hit = row.direct_hit;
        load.distance_m = row.distance_m;
        load.effect_scale = row.effect_scale;
        load.spatial_intersection_fraction = effects.warhead_spatial_hit_fraction;
        load.pattern_weight = effects.warhead_spatial_pattern_scale;
        load.orientation_weight = effects.warhead_orientation_pattern_scale;
        load.receiver_exposure_fraction = effects.mechanism_exposure_scale;
        load.armor_transmission = effects.mechanism_armor_scale;
        load.sampling_confidence = effects.confidence;
        load.load_intensity_scale = effects.mechanism_effect_scale;
        load.fragment_energy_j = row.mechanism_fragment_energy_j;
        load.fragment_areal_density_per_m2 = row.mechanism_fragment_areal_density_per_m2;
        load.penetration_margin = row.mechanism_penetration_margin;
        load.blast_overpressure_kpa = row.mechanism_blast_overpressure_kpa;
        load.blast_impulse_kpa_ms = row.mechanism_blast_impulse_kpa_ms;
        load.blast_scaled_distance_m_kg13 = row.mechanism_blast_scaled_distance_m_kg13;
        load.rod_cut_margin = row.mechanism_rod_cut_margin;
        load.surface_incidence_cos = row.mechanism_surface_incidence_cos;
        facade.warhead_load_field.component_loads.push_back(load);

    }

    for (const ComponentResponseRow &row : effects.component_response_rows) {
        KillChainComponentResponseFact response{};
        response.source_current_owner_stage = row.source_current_owner_stage;
        response.source_row_index = row.source_row_index;
        response.component_name = row.component_name;
        response.component_system = row.component_system;
        response.component_redundancy_group_id = row.component_redundancy_group_id;
        response.threshold_scale = row.threshold_scale;
        response.failure_probability = row.failure_probability;
        response.failure_sample = row.failure_sample;
        response.failure_probability_source = row.failure_probability_source;
        response.failure_probability_calibrated = row.failure_probability_calibrated;
        response.failure_probability_evidence_dataset_ref =
            row.failure_probability_evidence_dataset_ref;
        response.failure_probability_evidence_row_id = row.failure_probability_evidence_row_id;
        response.failure_probability_evidence_source_ref =
            row.failure_probability_evidence_source_ref;
        response.failure_probability_evidence_provenance =
            row.failure_probability_evidence_provenance;
        response.failure_probability_authority = row.failure_probability_authority;
        response.failure_probability_component_specific =
            row.failure_probability_component_specific;
        response.failure_probability_weapon_family = row.failure_probability_weapon_family;
        response.failure_probability_aspect_bucket = row.failure_probability_aspect_bucket;
        response.failure_probability_closure_bucket = row.failure_probability_closure_bucket;
        response.failure_probability_miss_distance_bucket =
            row.failure_probability_miss_distance_bucket;
        response.failure_mode = row.failure_mode;
        response.failure_severity = row.failure_severity;
        response.failure_mode_names = row.failure_mode_names;
        response.failure_mode_severities = row.failure_mode_severities;
        response.failure_mode_source = row.failure_mode_source;
        response.failure_mode_authority = row.failure_mode_authority;
        response.integrity_before = row.integrity_before;
        response.integrity_after = row.integrity_after;
        response.redundancy_group_availability_before =
            row.redundancy_group_availability_before;
        response.redundancy_group_availability_after = row.redundancy_group_availability_after;
        facade.component_responses.push_back(response);
    }

    facade.consequence_projection.outcome_state = effects.outcome_state;
    facade.consequence_projection.component_hit_count = effects.component_hit_count;
    facade.consequence_projection.component_failure_count = effects.component_failure_count;
    facade.consequence_projection.primary_component_name = effects.component_primary_name;
    facade.consequence_projection.primary_component_system = effects.component_primary_system;
    facade.consequence_projection.primary_component_integrity =
        effects.component_primary_integrity;
    facade.consequence_projection.redundancy_group_availability =
        effects.component_redundancy_group_availability;
    facade.consequence_projection.air_system_hit_flags = effects.air_system_hit_flags;
    facade.consequence_projection.air_system_spatial_scales = effects.air_system_spatial_scales;
    facade.consequence_projection.vulnerability_scale_trace =
        effects.vulnerability_scale_trace;

    return facade;
}

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
    bool forced_landing = false;
    bool flight_control_kill = false;
    bool propulsion_kill = false;
    bool crew_kill = false;
    std::string loss_state_from = "unknown";
    std::string loss_state_to = "unknown";
    bool destroyed = false;
    double report_time_s = 0.0;
    std::string producer_node_id;
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
    std::uint64_t source_snapshot_version = 0;
    std::string barrier_id = "export";
    std::string barrier_detail = "maintained_facade_export";
    double source_time_s = 0.0;
    std::string source_node_id;
    std::string export_node_id;
};
