#include "simulation_kernel_engagement_event_store.h"

#include "components/combat/damage.h"
#include "components/combat/health.h"

#include <algorithm>
#include <cstdio>
#include <string>
#include <utility>

namespace {

EngagementEntityRef engagement_ref(uint64_t entity_id) {
    return EngagementEntityRef{
        .world_index = 0,
        .entity_id = entity_id,
    };
}

std::string loss_state_to_string(PlatformLossState state) {
    switch (state) {
        case PlatformLossState::CombatCapable:
            return "combat_capable";
        case PlatformLossState::MissionKill:
            return "mission_kill";
        case PlatformLossState::MobilityKill:
            return "mobility_kill";
        case PlatformLossState::SensorKill:
            return "sensor_kill";
        case PlatformLossState::Lost:
            return "lost";
    }
    return "unknown";
}

}  // namespace

SimulationKernelEngagementEventStore::SimulationKernelEngagementEventStore(flecs::world& ecs)
    : ecs_(ecs) {}

void SimulationKernelEngagementEventStore::reset_if_event_clock_rewound(double event_time_s) {
    const ecs_world_info_t* info = ecs_get_world_info(ecs_.c_ptr());
    const std::int64_t frame_count = info ? info->frame_count_total : 0;
    if (event_time_s < recent_engagement_event_epoch_time_s_ ||
        frame_count < recent_engagement_event_epoch_frame_) {
        clear();
    }
    recent_engagement_event_epoch_time_s_ = event_time_s;
    recent_engagement_event_epoch_frame_ = frame_count;
}

EngagementDamageStateSnapshot SimulationKernelEngagementEventStore::capture_engagement_damage_state(
    uint64_t target_id
) const {
    EngagementDamageStateSnapshot snapshot{};
    const auto target = ecs_.entity(target_id);
    snapshot.entity_active = target.is_valid();
    if (!snapshot.entity_active) {
        return snapshot;
    }

    if (const Health* health = target.get<Health>()) {
        snapshot.has_health = true;
        snapshot.hp = health->current_hp;
        snapshot.max_hp = health->max_hp;
        snapshot.mission_kill = health->mission_kill;
        snapshot.mobility_kill = health->mobility_kill;
        snapshot.sensor_kill = health->sensor_kill;
    }

    if (const PlatformDamageState* damage = target.get<PlatformDamageState>()) {
        snapshot.has_platform_damage = true;
        snapshot.mission_capability = damage->mission_capability;
        snapshot.mobility_capability = damage->mobility_capability;
        snapshot.sensor_capability = damage->sensor_capability;
        snapshot.survivability_margin = damage->survivability_margin;
        snapshot.mission_kill = snapshot.mission_kill || damage->mission_kill;
        snapshot.mobility_kill = snapshot.mobility_kill || damage->mobility_kill;
        snapshot.sensor_kill = snapshot.sensor_kill || damage->sensor_kill;
        snapshot.loss_state = loss_state_to_string(damage->loss_state);
    } else if (snapshot.has_health) {
        snapshot.loss_state = snapshot.hp <= 0.0 ? "lost" : "combat_capable";
    }
    if (const AircraftDamageState* aircraft = target.get<AircraftDamageState>()) {
        snapshot.forced_landing = aircraft->forced_landing_required;
        snapshot.flight_control_kill = aircraft->flight_control_kill;
        snapshot.propulsion_kill = aircraft->propulsion_kill;
        snapshot.crew_kill = aircraft->crew_kill;
    }
    return snapshot;
}

std::uint64_t SimulationKernelEngagementEventStore::record_legacy_launch_event(
    uint64_t shooter_id,
    uint64_t,
    uint64_t spawned_munition_id,
    const std::string& selected_launcher,
    const std::string& selected_munition,
    int ammo_delta,
    double cooldown_delta_s,
    double event_time_s
) {
    reset_if_event_clock_rewound(event_time_s);

    const std::uint64_t event_id = next_engagement_event_id_++;
    LaunchEvent event{};
    event.event_id = event_id;
    event.request_id = event_id;
    event.accepted = true;
    event.selected_launcher = selected_launcher;
    event.selected_munition = selected_munition;
    event.ammo_delta = ammo_delta;
    event.cooldown_delta_s = cooldown_delta_s;
    event.spawned_munition = engagement_ref(spawned_munition_id);
    event.has_spawned_munition = spawned_munition_id != 0;
    event.event_time_s = event_time_s;
    recent_engagement_events_.launch_events.push_back(event);
    while (recent_engagement_events_.launch_events.size() > kMaxRecentEngagementEvents) {
        recent_engagement_events_.launch_events.erase(recent_engagement_events_.launch_events.begin());
    }

    DiagnosticsTrace trace{};
    trace.trace_id = next_engagement_event_id_++;
    trace.chain_id = event_id;
    trace.launch_request_id = event.request_id;
    trace.launch_event_id = event_id;
    trace.munition = event.spawned_munition;
    recent_engagement_events_.diagnostics_traces.push_back(trace);
    while (recent_engagement_events_.diagnostics_traces.size() > kMaxRecentEngagementEvents) {
        recent_engagement_events_.diagnostics_traces.erase(recent_engagement_events_.diagnostics_traces.begin());
    }
    (void)shooter_id;
    return event_id;
}

std::uint64_t SimulationKernelEngagementEventStore::record_effects_damage_event(
    EngagementEffectsDamageEventRecord record
) {
    EffectsEvent& effects = record.effects;
    return record_effects_damage_event(
        record.munition_entity_id,
        record.target_id,
        record.before,
        record.after,
        effects.trigger_type,
        effects.outcome_state,
        effects.detonation_time_s,
        effects.nearest_approach_time_s,
        effects.miss_distance_m,
        effects.detonation_local_forward_m,
        effects.detonation_local_right_m,
        effects.detonation_local_up_m,
        effects.detonation_heading_deg,
        effects.detonation_pitch_deg,
        effects.detonation_roll_deg,
        effects.closure_mps,
        effects.missile_axis_forward,
        effects.missile_axis_right,
        effects.missile_axis_up,
        effects.quality,
        effects.confidence,
        effects.effect_family,
        effects.warhead_mass_kg,
        effects.warhead_lethal_radius_m,
        effects.warhead_profile_synthetic,
        effects.damage_scalar_synthetic,
        effects.fuze_type,
        effects.fuze_trigger_radius_m,
        effects.fuze_delay_s,
        effects.fuze_reliability,
        effects.fuze_profile_synthetic,
        effects.fuze_signature_source,
        effects.fuze_target_signature,
        effects.fuze_signature_scale,
        effects.fuze_effective_reliability,
        effects.fuze_contact_surface_distance_m,
        effects.fuze_contact_penetration_depth_m,
        effects.fuze_contact_surface_tolerance_m,
        effects.fuze_contact_inside_hitbox,
        effects.direct_hitbox_intersection,
        effects.projected_hitbox_count,
        effects.spatial_effect_scale,
        effects.mechanism_armor_scale,
        effects.mechanism_exposure_scale,
        effects.mechanism_effect_scale,
        effects.mechanism_fragment_energy_j,
        effects.mechanism_fragment_areal_density_per_m2,
        effects.mechanism_penetration_margin,
        effects.mechanism_blast_overpressure_kpa,
        effects.mechanism_blast_impulse_kpa_ms,
        effects.mechanism_blast_scaled_distance_m_kg13,
        effects.mechanism_rod_cut_margin,
        effects.warhead_spatial_sample_count,
        effects.warhead_spatial_hit_estimate,
        effects.warhead_spatial_hit_fraction,
        effects.warhead_spatial_energy_scale,
        effects.warhead_spatial_pattern_scale,
        effects.warhead_orientation_axis_forward,
        effects.warhead_orientation_axis_right,
        effects.warhead_orientation_axis_up,
        effects.warhead_orientation_pattern_scale,
        effects.component_threshold_scale,
        effects.component_failure_probability,
        effects.component_failure_probability_source,
        effects.component_failure_probability_calibrated,
        effects.component_failure_probability_evidence_dataset_ref,
        effects.component_failure_probability_evidence_row_id,
        effects.component_failure_probability_evidence_source_ref,
        effects.component_failure_probability_evidence_provenance,
        effects.component_failure_sample,
        effects.component_failure_count,
        effects.component_hit_count,
        std::move(effects.component_mechanism_load_rows),
        effects.component_primary_name,
        effects.component_primary_system,
        effects.component_primary_redundancy_group,
        effects.component_primary_critical,
        effects.component_primary_redundancy_group_id,
        effects.component_primary_integrity,
        effects.component_primary_mechanism_fragment_energy_j,
        effects.component_primary_mechanism_fragment_areal_density_per_m2,
        effects.component_primary_mechanism_penetration_margin,
        effects.component_primary_mechanism_blast_overpressure_kpa,
        effects.component_primary_mechanism_blast_impulse_kpa_ms,
        effects.component_primary_mechanism_blast_scaled_distance_m_kg13,
        effects.component_primary_mechanism_rod_cut_margin,
        effects.component_redundancy_group_availability,
        effects.component_redundancy_group_member_count,
        effects.component_redundancy_group_failed_count,
        effects.vulnerability_profile_present,
        effects.vulnerability_profile_synthetic,
        effects.vulnerability_calibrated_evidence,
        effects.vulnerability_pk_authority,
        effects.vulnerability_deterministic_fuze_authority,
        effects.vulnerability_evidence_dataset_valid,
        effects.vulnerability_evidence_dataset_ref,
        effects.vulnerability_calibration_status,
        effects.vulnerability_provenance,
        effects.vulnerability_evidence_schema_version,
        effects.vulnerability_evidence_source_kind,
        effects.vulnerability_evidence_source_ref,
        effects.vulnerability_evidence_validation_artifact_ref,
        effects.vulnerability_evidence_validation_manifest_schema_version,
        effects.vulnerability_evidence_validation_status,
        effects.vulnerability_evidence_validation_artifact_sha256,
        effects.vulnerability_evidence_validated_surrogate_model_ref,
        effects.vulnerability_evidence_validation_benchmark_ref,
        effects.vulnerability_evidence_validation_metrics_ref,
        effects.vulnerability_evidence_validation_acceptance_criteria_ref,
        effects.vulnerability_aspect_bucket,
        effects.vulnerability_family_scale,
        effects.vulnerability_aspect_scale,
        effects.vulnerability_closure_mps,
        effects.vulnerability_closure_scale,
        effects.vulnerability_miss_distance_scale,
        effects.vulnerability_effect_scale,
        effects.vulnerability_effect_scale_source,
        effects.vulnerability_effect_scale_evidence_row_id,
        effects.vulnerability_effect_scale_evidence_source_ref,
        effects.vulnerability_effect_scale_evidence_provenance,
        effects.mechanism_surface_incidence_cos,
        effects.component_primary_mechanism_surface_incidence_cos);
}

std::uint64_t SimulationKernelEngagementEventStore::record_effects_damage_event(
    uint64_t munition_entity_id,
    uint64_t target_id,
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
    double warhead_mass_kg,
    double warhead_lethal_radius_m,
    bool warhead_profile_synthetic,
    bool damage_scalar_synthetic,
    const std::string& fuze_type,
    double fuze_trigger_radius_m,
    double fuze_delay_s,
    double fuze_reliability,
    bool fuze_profile_synthetic,
    const std::string& fuze_signature_source,
    double fuze_target_signature,
    double fuze_signature_scale,
    double fuze_effective_reliability,
    double fuze_contact_surface_distance_m,
    double fuze_contact_penetration_depth_m,
    double fuze_contact_surface_tolerance_m,
    bool fuze_contact_inside_hitbox,
    bool direct_hitbox_intersection,
    std::uint32_t projected_hitbox_count,
    double spatial_effect_scale,
    double mechanism_armor_scale,
    double mechanism_exposure_scale,
    double mechanism_effect_scale,
    double mechanism_fragment_energy_j,
    double mechanism_fragment_areal_density_per_m2,
    double mechanism_penetration_margin,
    double mechanism_blast_overpressure_kpa,
    double mechanism_blast_impulse_kpa_ms,
    double mechanism_blast_scaled_distance_m_kg13,
    double mechanism_rod_cut_margin,
    std::uint32_t warhead_spatial_sample_count,
    double warhead_spatial_hit_estimate,
    double warhead_spatial_hit_fraction,
    double warhead_spatial_energy_scale,
    double warhead_spatial_pattern_scale,
    double warhead_orientation_axis_forward,
    double warhead_orientation_axis_right,
    double warhead_orientation_axis_up,
    double warhead_orientation_pattern_scale,
    double component_threshold_scale,
    double component_failure_probability,
    const std::string& component_failure_probability_source,
    bool component_failure_probability_calibrated,
    const std::string& component_failure_probability_evidence_dataset_ref,
    const std::string& component_failure_probability_evidence_row_id,
    const std::string& component_failure_probability_evidence_source_ref,
    const std::string& component_failure_probability_evidence_provenance,
    double component_failure_sample,
    std::uint32_t component_failure_count,
    std::uint32_t component_hit_count,
    std::vector<ComponentMechanismLoadRow> component_mechanism_load_rows,
    const std::string& component_primary_name,
    const std::string& component_primary_system,
    double component_primary_redundancy_group,
    bool component_primary_critical,
    const std::string& component_primary_redundancy_group_id,
    double component_primary_integrity,
    double component_primary_mechanism_fragment_energy_j,
    double component_primary_mechanism_fragment_areal_density_per_m2,
    double component_primary_mechanism_penetration_margin,
    double component_primary_mechanism_blast_overpressure_kpa,
    double component_primary_mechanism_blast_impulse_kpa_ms,
    double component_primary_mechanism_blast_scaled_distance_m_kg13,
    double component_primary_mechanism_rod_cut_margin,
    double component_redundancy_group_availability,
    std::uint32_t component_redundancy_group_member_count,
    std::uint32_t component_redundancy_group_failed_count,
    bool vulnerability_profile_present,
    bool vulnerability_profile_synthetic,
    bool vulnerability_calibrated_evidence,
    bool vulnerability_pk_authority,
    bool vulnerability_deterministic_fuze_authority,
    bool vulnerability_evidence_dataset_valid,
    const std::string& vulnerability_evidence_dataset_ref,
    const std::string& vulnerability_calibration_status,
    const std::string& vulnerability_provenance,
    const std::string& vulnerability_evidence_schema_version,
    const std::string& vulnerability_evidence_source_kind,
    const std::string& vulnerability_evidence_source_ref,
    const std::string& vulnerability_evidence_validation_artifact_ref,
    const std::string& vulnerability_evidence_validation_manifest_schema_version,
    const std::string& vulnerability_evidence_validation_status,
    const std::string& vulnerability_evidence_validation_artifact_sha256,
    const std::string& vulnerability_evidence_validated_surrogate_model_ref,
    const std::string& vulnerability_evidence_validation_benchmark_ref,
    const std::string& vulnerability_evidence_validation_metrics_ref,
    const std::string& vulnerability_evidence_validation_acceptance_criteria_ref,
    const std::string& vulnerability_aspect_bucket,
    double vulnerability_family_scale,
    double vulnerability_aspect_scale,
    double vulnerability_closure_mps,
    double vulnerability_closure_scale,
    double vulnerability_miss_distance_scale,
    double vulnerability_effect_scale,
    const std::string& vulnerability_effect_scale_source,
    const std::string& vulnerability_effect_scale_evidence_row_id,
    const std::string& vulnerability_effect_scale_evidence_source_ref,
    const std::string& vulnerability_effect_scale_evidence_provenance,
    double mechanism_surface_incidence_cos,
    double component_primary_mechanism_surface_incidence_cos
) {
    reset_if_event_clock_rewound(event_time_s);

    const std::uint64_t effects_event_id = next_engagement_event_id_++;
    const std::uint64_t damage_report_id = next_engagement_event_id_++;
    const std::uint64_t trace_id = next_engagement_event_id_++;
    std::uint64_t launch_event_id = pending_effects_launch_event_id_;
    if (launch_event_id == 0 && munition_entity_id != 0) {
        for (auto it = recent_engagement_events_.launch_events.rbegin();
             it != recent_engagement_events_.launch_events.rend();
             ++it) {
            if (it->has_spawned_munition &&
                it->spawned_munition.entity_id == munition_entity_id) {
                launch_event_id = it->event_id;
                break;
            }
        }
    }
    const std::uint64_t chain_id = launch_event_id != 0 ? launch_event_id : effects_event_id;

    EffectsEvent effects{};
    effects.event_id = effects_event_id;
    effects.munition = engagement_ref(munition_entity_id);
    effects.target = engagement_ref(target_id);
    effects.trigger_type = trigger_type;
    effects.outcome_state = outcome_state;
    effects.detonation_time_s = event_time_s;
    effects.nearest_approach_time_s = nearest_approach_time_s;
    effects.miss_distance_m = miss_distance_m;
    effects.detonation_local_forward_m = detonation_local_forward_m;
    effects.detonation_local_right_m = detonation_local_right_m;
    effects.detonation_local_up_m = detonation_local_up_m;
    effects.detonation_heading_deg = detonation_heading_deg;
    effects.detonation_pitch_deg = detonation_pitch_deg;
    effects.detonation_roll_deg = detonation_roll_deg;
    effects.closure_mps = closure_mps;
    effects.missile_axis_forward = missile_axis_forward;
    effects.missile_axis_right = missile_axis_right;
    effects.missile_axis_up = missile_axis_up;
    effects.quality = quality;
    effects.confidence = confidence;
    effects.effect_family = effect_family;
    effects.warhead_mass_kg = warhead_mass_kg;
    effects.warhead_lethal_radius_m = warhead_lethal_radius_m;
    effects.warhead_profile_synthetic = warhead_profile_synthetic;
    effects.damage_scalar_synthetic = damage_scalar_synthetic;
    effects.fuze_type = fuze_type;
    effects.fuze_trigger_radius_m = fuze_trigger_radius_m;
    effects.fuze_delay_s = fuze_delay_s;
    effects.fuze_reliability = fuze_reliability;
    effects.fuze_profile_synthetic = fuze_profile_synthetic;
    effects.fuze_signature_source = fuze_signature_source;
    effects.fuze_target_signature = fuze_target_signature;
    effects.fuze_signature_scale = fuze_signature_scale;
    effects.fuze_effective_reliability = fuze_effective_reliability;
    effects.fuze_contact_surface_distance_m = fuze_contact_surface_distance_m;
    effects.fuze_contact_penetration_depth_m = fuze_contact_penetration_depth_m;
    effects.fuze_contact_surface_tolerance_m = fuze_contact_surface_tolerance_m;
    effects.fuze_contact_inside_hitbox = fuze_contact_inside_hitbox;
    effects.direct_hitbox_intersection = direct_hitbox_intersection;
    effects.projected_hitbox_count = projected_hitbox_count;
    effects.spatial_effect_scale = spatial_effect_scale;
    effects.mechanism_armor_scale = mechanism_armor_scale;
    effects.mechanism_exposure_scale = mechanism_exposure_scale;
    effects.mechanism_effect_scale = mechanism_effect_scale;
    effects.mechanism_fragment_energy_j = mechanism_fragment_energy_j;
    effects.mechanism_fragment_areal_density_per_m2 =
        mechanism_fragment_areal_density_per_m2;
    effects.mechanism_penetration_margin = mechanism_penetration_margin;
    effects.mechanism_blast_overpressure_kpa = mechanism_blast_overpressure_kpa;
    effects.mechanism_blast_impulse_kpa_ms = mechanism_blast_impulse_kpa_ms;
    effects.mechanism_blast_scaled_distance_m_kg13 =
        mechanism_blast_scaled_distance_m_kg13;
    effects.mechanism_rod_cut_margin = mechanism_rod_cut_margin;
    effects.mechanism_surface_incidence_cos = mechanism_surface_incidence_cos;
    effects.warhead_spatial_sample_count = warhead_spatial_sample_count;
    effects.warhead_spatial_hit_estimate = warhead_spatial_hit_estimate;
    effects.warhead_spatial_hit_fraction = warhead_spatial_hit_fraction;
    effects.warhead_spatial_energy_scale = warhead_spatial_energy_scale;
    effects.warhead_spatial_pattern_scale = warhead_spatial_pattern_scale;
    effects.warhead_orientation_axis_forward = warhead_orientation_axis_forward;
    effects.warhead_orientation_axis_right = warhead_orientation_axis_right;
    effects.warhead_orientation_axis_up = warhead_orientation_axis_up;
    effects.warhead_orientation_pattern_scale = warhead_orientation_pattern_scale;
    effects.component_threshold_scale = component_threshold_scale;
    effects.component_failure_probability = component_failure_probability;
    effects.component_failure_probability_source = component_failure_probability_source;
    effects.component_failure_probability_calibrated =
        component_failure_probability_calibrated;
    effects.component_failure_probability_evidence_dataset_ref =
        component_failure_probability_evidence_dataset_ref;
    effects.component_failure_probability_evidence_row_id =
        component_failure_probability_evidence_row_id;
    effects.component_failure_probability_evidence_source_ref =
        component_failure_probability_evidence_source_ref;
    effects.component_failure_probability_evidence_provenance =
        component_failure_probability_evidence_provenance;
    effects.component_failure_sample = component_failure_sample;
    effects.component_failure_count = component_failure_count;
    effects.component_hit_count = component_hit_count;
    effects.component_mechanism_load_rows = std::move(component_mechanism_load_rows);
    effects.component_primary_name = component_primary_name;
    effects.component_primary_system = component_primary_system;
    effects.component_primary_redundancy_group = component_primary_redundancy_group;
    effects.component_primary_critical = component_primary_critical;
    effects.component_primary_redundancy_group_id = component_primary_redundancy_group_id;
    effects.component_primary_integrity = component_primary_integrity;
    effects.component_primary_mechanism_fragment_energy_j =
        component_primary_mechanism_fragment_energy_j;
    effects.component_primary_mechanism_fragment_areal_density_per_m2 =
        component_primary_mechanism_fragment_areal_density_per_m2;
    effects.component_primary_mechanism_penetration_margin =
        component_primary_mechanism_penetration_margin;
    effects.component_primary_mechanism_blast_overpressure_kpa =
        component_primary_mechanism_blast_overpressure_kpa;
    effects.component_primary_mechanism_blast_impulse_kpa_ms =
        component_primary_mechanism_blast_impulse_kpa_ms;
    effects.component_primary_mechanism_blast_scaled_distance_m_kg13 =
        component_primary_mechanism_blast_scaled_distance_m_kg13;
    effects.component_primary_mechanism_rod_cut_margin =
        component_primary_mechanism_rod_cut_margin;
    effects.component_primary_mechanism_surface_incidence_cos =
        component_primary_mechanism_surface_incidence_cos;
    effects.component_redundancy_group_availability = component_redundancy_group_availability;
    effects.component_redundancy_group_member_count = component_redundancy_group_member_count;
    effects.component_redundancy_group_failed_count = component_redundancy_group_failed_count;
    effects.vulnerability_profile_present = vulnerability_profile_present;
    effects.vulnerability_profile_synthetic = vulnerability_profile_synthetic;
    effects.vulnerability_calibrated_evidence = vulnerability_calibrated_evidence;
    effects.vulnerability_pk_authority = vulnerability_pk_authority;
    effects.vulnerability_deterministic_fuze_authority =
        vulnerability_deterministic_fuze_authority;
    effects.vulnerability_evidence_dataset_valid = vulnerability_evidence_dataset_valid;
    effects.vulnerability_evidence_dataset_ref = vulnerability_evidence_dataset_ref;
    effects.vulnerability_calibration_status = vulnerability_calibration_status;
    effects.vulnerability_provenance = vulnerability_provenance;
    effects.vulnerability_evidence_schema_version =
        vulnerability_evidence_schema_version;
    effects.vulnerability_evidence_source_kind =
        vulnerability_evidence_source_kind;
    effects.vulnerability_evidence_source_ref =
        vulnerability_evidence_source_ref;
    effects.vulnerability_evidence_validation_artifact_ref =
        vulnerability_evidence_validation_artifact_ref;
    effects.vulnerability_evidence_validation_manifest_schema_version =
        vulnerability_evidence_validation_manifest_schema_version;
    effects.vulnerability_evidence_validation_status =
        vulnerability_evidence_validation_status;
    effects.vulnerability_evidence_validation_artifact_sha256 =
        vulnerability_evidence_validation_artifact_sha256;
    effects.vulnerability_evidence_validated_surrogate_model_ref =
        vulnerability_evidence_validated_surrogate_model_ref;
    effects.vulnerability_evidence_validation_benchmark_ref =
        vulnerability_evidence_validation_benchmark_ref;
    effects.vulnerability_evidence_validation_metrics_ref =
        vulnerability_evidence_validation_metrics_ref;
    effects.vulnerability_evidence_validation_acceptance_criteria_ref =
        vulnerability_evidence_validation_acceptance_criteria_ref;
    effects.vulnerability_aspect_bucket = vulnerability_aspect_bucket;
    effects.vulnerability_family_scale = vulnerability_family_scale;
    effects.vulnerability_aspect_scale = vulnerability_aspect_scale;
    effects.vulnerability_closure_mps = vulnerability_closure_mps;
    effects.vulnerability_closure_scale = vulnerability_closure_scale;
    effects.vulnerability_miss_distance_scale = vulnerability_miss_distance_scale;
    effects.vulnerability_effect_scale = vulnerability_effect_scale;
    effects.vulnerability_effect_scale_source = vulnerability_effect_scale_source;
    effects.vulnerability_effect_scale_evidence_row_id =
        vulnerability_effect_scale_evidence_row_id;
    effects.vulnerability_effect_scale_evidence_source_ref =
        vulnerability_effect_scale_evidence_source_ref;
    effects.vulnerability_effect_scale_evidence_provenance =
        vulnerability_effect_scale_evidence_provenance;
    recent_engagement_events_.effects_events.push_back(effects);
    while (recent_engagement_events_.effects_events.size() > kMaxRecentEngagementEvents) {
        recent_engagement_events_.effects_events.erase(recent_engagement_events_.effects_events.begin());
    }

    const auto min_damage_capability = [](const EngagementDamageStateSnapshot& snapshot) {
        return std::min(
            std::min(snapshot.mission_capability, snapshot.mobility_capability),
            std::min(snapshot.sensor_capability, snapshot.survivability_margin));
    };

    char damage_delta[160];
    std::snprintf(
        damage_delta,
        sizeof(damage_delta),
        "mission=%.6f,mobility=%.6f,sensor=%.6f,survivability=%.6f",
        after.mission_capability - before.mission_capability,
        after.mobility_capability - before.mobility_capability,
        after.sensor_capability - before.sensor_capability,
        after.survivability_margin - before.survivability_margin);

    DamageReport report{};
    report.report_id = damage_report_id;
    report.target = engagement_ref(target_id);
    report.source_event_id = effects_event_id;
    report.hp_delta = (before.has_health || after.has_health) ? after.hp - before.hp : 0.0;
    report.system_health_delta = min_damage_capability(after) - min_damage_capability(before);
    report.platform_damage_state_delta = std::string(damage_delta);
    report.mission_kill = after.mission_kill;
    report.mobility_kill = after.mobility_kill;
    report.sensor_kill = after.sensor_kill;
    report.survivability_kill = after.survivability_margin <= 0.0 || !after.entity_active;
    report.forced_landing = after.forced_landing;
    report.flight_control_kill = after.flight_control_kill;
    report.propulsion_kill = after.propulsion_kill;
    report.crew_kill = after.crew_kill;
    report.loss_state_from = before.loss_state;
    report.loss_state_to = after.entity_active ? after.loss_state : "lost";
    report.destroyed = !after.entity_active || report.loss_state_to == "lost";
    report.report_time_s = event_time_s;
    recent_engagement_events_.damage_reports.push_back(report);
    while (recent_engagement_events_.damage_reports.size() > kMaxRecentEngagementEvents) {
        recent_engagement_events_.damage_reports.erase(recent_engagement_events_.damage_reports.begin());
    }

    DiagnosticsTrace trace{};
    trace.trace_id = trace_id;
    trace.chain_id = chain_id;
    trace.launch_event_id = launch_event_id;
    trace.munition = engagement_ref(munition_entity_id);
    trace.effects_event_id = effects_event_id;
    trace.damage_report_id = damage_report_id;
    recent_engagement_events_.diagnostics_traces.push_back(trace);
    while (recent_engagement_events_.diagnostics_traces.size() > kMaxRecentEngagementEvents) {
        recent_engagement_events_.diagnostics_traces.erase(recent_engagement_events_.diagnostics_traces.begin());
    }
    pending_effects_launch_event_id_ = 0;
    return effects_event_id;
}

void SimulationKernelEngagementEventStore::set_pending_effects_launch_event_id(
    std::uint64_t launch_event_id
) {
    pending_effects_launch_event_id_ = launch_event_id;
}

RecentEngagementEvents SimulationKernelEngagementEventStore::export_recent_events_sorted() const {
    RecentEngagementEvents out = recent_engagement_events_;

    std::sort(
        out.launch_events.begin(),
        out.launch_events.end(),
        [](const LaunchEvent& lhs, const LaunchEvent& rhs) {
            return lhs.event_id < rhs.event_id;
        });
    std::sort(
        out.effects_events.begin(),
        out.effects_events.end(),
        [](const EffectsEvent& lhs, const EffectsEvent& rhs) {
            return lhs.event_id < rhs.event_id;
        });
    std::sort(
        out.damage_reports.begin(),
        out.damage_reports.end(),
        [](const DamageReport& lhs, const DamageReport& rhs) {
            return lhs.report_id < rhs.report_id;
        });
    std::sort(
        out.diagnostics_traces.begin(),
        out.diagnostics_traces.end(),
        [](const DiagnosticsTrace& lhs, const DiagnosticsTrace& rhs) {
            return lhs.trace_id < rhs.trace_id;
        });
    return out;
}

void SimulationKernelEngagementEventStore::clear() {
    recent_engagement_events_ = RecentEngagementEvents{};
    next_engagement_event_id_ = 1;
    pending_effects_launch_event_id_ = 0;
    recent_engagement_event_epoch_time_s_ = 0.0;
    recent_engagement_event_epoch_frame_ = 0;
}
