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

inline constexpr std::array<std::string_view, 3> kLethalityChainPositiveDetonationOutcomes = {
    "damage_applied",
    "detonated_no_effect",
    "hit",
};

inline bool is_lethality_chain_positive_detonation_outcome(std::string_view outcome_state) {
    for (const std::string_view positive_outcome : kLethalityChainPositiveDetonationOutcomes) {
        if (outcome_state == positive_outcome) {
            return true;
        }
    }
    return false;
}

inline constexpr std::string_view kLethalityObservationModeSampledRuntime = "sampled_runtime";
inline constexpr std::string_view kLethalityObservationModeExpectedProjection =
    "expected_projection";
inline constexpr std::string_view kLethalityConsumerVisibilityDiagnosticsAndTraining =
    "diagnostics_and_training";
inline constexpr std::string_view kLethalityConsumerVisibilityDiagnosticsOnly = "diagnostics_only";

// Vocabulary note (I33, unified architecture program T1): the `stage` /
// `owner_stage` string fields below (LethalityChainHeader and the
// KillChain*/EffectsEvent-adjacent facts) are this family's stage-tagging
// anchor. Per SCAL baseline amendment (b), engagement/command schema groups
// are meant to eventually carry stage-contract and event-driven sub-graph
// metadata instead of a forced linear P0-P10 stage sequence. This iteration
// is vocabulary single-sourcing only: the strings keep their current
// free-form values and no stage-contract type or enforcement mechanism is
// introduced here.

struct EngagementEntityRef {
#define EF_ENGAGEMENT_ENTITY_REF_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/engagement_entity_ref.inc"
};

struct LethalityChainHeader {
#define EF_LETHALITY_CHAIN_HEADER_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/lethality_chain_header.inc"
};

struct NearestApproachEvent {
#define EF_NEAREST_APPROACH_EVENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/nearest_approach_event.inc"
};

struct FuzeEvaluationEvent {
#define EF_FUZE_EVALUATION_EVENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/fuze_evaluation_event.inc"
};

struct WarheadMechanismEvent {
#define EF_WARHEAD_MECHANISM_EVENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/warhead_mechanism_event.inc"
};

struct SpatialCoverageEvent {
#define EF_SPATIAL_COVERAGE_EVENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/spatial_coverage_event.inc"
};

struct ComponentLoadEvent {
#define EF_COMPONENT_LOAD_EVENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/component_load_event.inc"
};

struct ComponentDamageEvent {
#define EF_COMPONENT_DAMAGE_EVENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/component_damage_event.inc"
};

struct PlatformConsequenceEvent {
#define EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/platform_consequence_event.inc"
};

struct StructuralBreakupEvent {
#define EF_STRUCTURAL_BREAKUP_EVENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/structural_breakup_event.inc"
};

struct LifecycleTransitionEvent {
#define EF_LIFECYCLE_TRANSITION_EVENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/lifecycle_transition_event.inc"
};

struct TrainingProjectionEvent {
#define EF_TRAINING_PROJECTION_EVENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/training_projection_event.inc"
};

struct ComponentMechanismLoadRow {
#define EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/component_mechanism_load_row.inc"
};

struct ComponentResponseRow {
#define EF_COMPONENT_RESPONSE_ROW_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/component_response_row.inc"
};

struct TrackPacket {
#define EF_TRACK_PACKET_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/track_packet.inc"
};

struct LaunchRequest {
#define EF_LAUNCH_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/launch_request.inc"
};

struct LaunchEvent {
#define EF_LAUNCH_EVENT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/launch_event.inc"
};

struct MunitionLifecyclePacket {
#define EF_MUNITION_LIFECYCLE_PACKET_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/munition_lifecycle_packet.inc"
};

struct EffectsEvent {
    // Field surface owned by the X-macro list; see the .inc for order and
    // EffectsResult-overlap semantics.
#define EF_EFFECTS_EVENT_FIELD(type, name, default_value) type name = default_value;
#define EF_EFFECTS_EVENT_RESULT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/effects_event_fields.inc"
#undef EF_EFFECTS_EVENT_RESULT_FIELD
#undef EF_EFFECTS_EVENT_FIELD
};

struct KillChainApproachFact {
#define EF_KILL_CHAIN_APPROACH_FACT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/kill_chain_approach_fact.inc"
};

struct KillChainFuzeDecision {
#define EF_KILL_CHAIN_FUZE_DECISION_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/kill_chain_fuze_decision.inc"
};

struct KillChainComponentLoadFact {
#define EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(type, name, default_value)                         \
    type name = default_value;
#include "runtime/contracts/detail/kill_chain_component_load_fact.inc"
};

struct KillChainWarheadLoadField {
#define EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/kill_chain_warhead_load_field.inc"
};

struct KillChainTargetSusceptibility {
#define EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD(type, name, default_value)                       \
    type name = default_value;
#include "runtime/contracts/detail/kill_chain_target_susceptibility.inc"
};

struct KillChainComponentResponseFact {
#define EF_KILL_CHAIN_COMPONENT_RESPONSE_FACT_FIELD(type, name, default_value)                     \
    type name = default_value;
#include "runtime/contracts/detail/kill_chain_component_response_fact.inc"
};

struct KillChainConsequenceProjection {
#define EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD(type, name, default_value)                      \
    type name = default_value;
#include "runtime/contracts/detail/kill_chain_consequence_projection.inc"
};

struct KillChainRuntimeFacade {
#define EF_KILL_CHAIN_RUNTIME_FACADE_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/kill_chain_runtime_facade.inc"
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
    facade.fuze_decision.detonated =
        is_lethality_chain_positive_detonation_outcome(effects.outcome_state);
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
    facade.warhead_load_field.orientation_pattern_scale = effects.warhead_orientation_pattern_scale;
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
    facade.target_susceptibility.miss_distance_scale = effects.vulnerability_miss_distance_scale;
    facade.target_susceptibility.effect_scale = effects.vulnerability_effect_scale;

    facade.warhead_load_field.component_loads.reserve(effects.component_mechanism_load_rows.size());
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
        response.failure_probability_evidence_component_name =
            row.failure_probability_evidence_component_name;
        response.failure_probability_evidence_component_system =
            row.failure_probability_evidence_component_system;
        response.failure_probability_evidence_component_redundancy_group_id =
            row.failure_probability_evidence_component_redundancy_group_id;
        response.failure_mode = row.failure_mode;
        response.failure_severity = row.failure_severity;
        response.failure_mode_names = row.failure_mode_names;
        response.failure_mode_severities = row.failure_mode_severities;
        response.failure_mode_source = row.failure_mode_source;
        response.failure_mode_authority = row.failure_mode_authority;
        response.integrity_before = row.integrity_before;
        response.integrity_after = row.integrity_after;
        response.redundancy_group_availability_before = row.redundancy_group_availability_before;
        response.redundancy_group_availability_after = row.redundancy_group_availability_after;
        facade.component_responses.push_back(response);
    }

    facade.consequence_projection.outcome_state = effects.outcome_state;
    facade.consequence_projection.component_hit_count = effects.component_hit_count;
    facade.consequence_projection.component_failure_count = effects.component_failure_count;
    facade.consequence_projection.primary_component_name = effects.component_primary_name;
    facade.consequence_projection.primary_component_system = effects.component_primary_system;
    facade.consequence_projection.primary_component_integrity = effects.component_primary_integrity;
    facade.consequence_projection.redundancy_group_availability =
        effects.component_redundancy_group_availability;
    facade.consequence_projection.air_system_hit_flags = effects.air_system_hit_flags;
    facade.consequence_projection.air_system_spatial_scales = effects.air_system_spatial_scales;
    facade.consequence_projection.vulnerability_scale_trace = effects.vulnerability_scale_trace;

    return facade;
}

struct DamageReport {
#define EF_DAMAGE_REPORT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/damage_report.inc"
};

struct DiagnosticsTrace {
#define EF_DIAGNOSTICS_TRACE_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/diagnostics_trace.inc"
};
