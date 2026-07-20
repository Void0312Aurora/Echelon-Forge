#include "interfaces/python/binding_utils.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include <spdlog/spdlog.h>

#include "core/engine/world_batch_runtime.h"
#include "runtime/contracts/engagement_contracts.h"
#include "runtime/contracts/fidelity_profile_contracts.h"
#include "runtime/contracts/platform_capability_contracts.h"
#include "runtime/contracts/policy_contracts.h"
#include "runtime/facade/runtime_facade.h"

void bind_runtime(nb::module_ &m) {
    nb::class_<RuntimeCapabilities> runtime_capabilities_class(m, "RuntimeCapabilities");
    runtime_capabilities_class.def(nb::init<>());
#define EF_RUNTIME_CAPABILITIES_FIELD(type, name, default_value) \
    runtime_capabilities_class.def_rw(#name, &RuntimeCapabilities::name);
#include "runtime/facade/detail/runtime_capabilities.inc"

    nb::class_<RuntimeBatchConfig> runtime_batch_config_class(m, "RuntimeBatchConfig");
    runtime_batch_config_class.def(nb::init<>());
#define EF_RUNTIME_BATCH_CONFIG_FIELD(type, name, default_value) \
    runtime_batch_config_class.def_rw(#name, &RuntimeBatchConfig::name);
#include "runtime/facade/detail/runtime_batch_config.inc"

    nb::class_<RuntimeFidelityRequest> runtime_fidelity_request_class(m, "RuntimeFidelityRequest");
    runtime_fidelity_request_class.def(nb::init<>());
#define EF_RUNTIME_FIDELITY_REQUEST_FIELD(type, name, default_value) \
    runtime_fidelity_request_class.def_rw(#name, &RuntimeFidelityRequest::name);
#include "runtime/facade/detail/runtime_fidelity_request.inc"

    nb::class_<RuntimeFidelityAdmission> runtime_fidelity_admission_class(
        m, "RuntimeFidelityAdmission");
    runtime_fidelity_admission_class.def(nb::init<>());
#define EF_RUNTIME_FIDELITY_ADMISSION_FIELD(type, name, default_value) \
    runtime_fidelity_admission_class.def_rw(#name, &RuntimeFidelityAdmission::name);
#include "runtime/facade/detail/runtime_fidelity_admission.inc"

    nb::class_<RuntimeCounterfactualSnapshot> runtime_counterfactual_snapshot_class(
        m, "RuntimeCounterfactualSnapshot");
    runtime_counterfactual_snapshot_class.def(nb::init<>());
#define EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(type, name, default_value) \
    runtime_counterfactual_snapshot_class.def_rw(#name, &RuntimeCounterfactualSnapshot::name);
#include "runtime/facade/detail/runtime_counterfactual_snapshot.inc"

    nb::class_<RuntimeWorldlineComparison> runtime_worldline_comparison_class(
        m, "RuntimeWorldlineComparison");
    runtime_worldline_comparison_class.def(nb::init<>());
#define EF_RUNTIME_WORLDLINE_COMPARISON_FIELD(type, name, default_value) \
    runtime_worldline_comparison_class.def_rw(#name, &RuntimeWorldlineComparison::name);
#include "runtime/facade/detail/runtime_worldline_comparison.inc"

    nb::class_<DeviceResidentOutputDescriptor> device_resident_output_descriptor_class(
        m, "DeviceResidentOutputDescriptor");
    device_resident_output_descriptor_class.def(nb::init<>());
#define EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD(type, name, default_value)          \
    device_resident_output_descriptor_class.def_rw(                                    \
        #name, &DeviceResidentOutputDescriptor::name);
#include "runtime/facade/detail/resident_device_output_descriptor.inc"

    nb::class_<runtime::fidelity::FidelityProfileRequest>(m, "FidelityProfileRequest")
        .def(nb::init<>())
        .def_rw("request_label", &runtime::fidelity::FidelityProfileRequest::request_label)
        .def_rw("backend_profile_id",
                &runtime::fidelity::FidelityProfileRequest::backend_profile_id)
        .def_rw("parity_budget_ref", &runtime::fidelity::FidelityProfileRequest::parity_budget_ref)
        .def_rw("model_family_scope",
                &runtime::fidelity::FidelityProfileRequest::model_family_scope)
        .def_rw("validation_gate", &runtime::fidelity::FidelityProfileRequest::validation_gate)
        .def_rw("facade_evidence_refs",
                &runtime::fidelity::FidelityProfileRequest::facade_evidence_refs)
        .def_rw("requests_adaptive_scheduling",
                &runtime::fidelity::FidelityProfileRequest::requests_adaptive_scheduling)
        .def_rw("requests_learned_model_provider",
                &runtime::fidelity::FidelityProfileRequest::requests_learned_model_provider)
        .def_rw("requests_approximate_execution",
                &runtime::fidelity::FidelityProfileRequest::requests_approximate_execution)
        .def_rw("requests_exact_gpu_backend",
                &runtime::fidelity::FidelityProfileRequest::requests_exact_gpu_backend)
        .def_rw("requests_resident_state",
                &runtime::fidelity::FidelityProfileRequest::requests_resident_state)
        .def_rw("requests_shadow_compare",
                &runtime::fidelity::FidelityProfileRequest::requests_shadow_compare);

    nb::class_<runtime::fidelity::FidelityProfileAdmissionResult>(m,
                                                                  "FidelityProfileAdmissionResult")
        .def(nb::init<>())
        .def_rw("admitted", &runtime::fidelity::FidelityProfileAdmissionResult::admitted)
        .def_rw("baseline_exact_evaluation",
                &runtime::fidelity::FidelityProfileAdmissionResult::baseline_exact_evaluation)
        .def_rw("request_label", &runtime::fidelity::FidelityProfileAdmissionResult::request_label)
        .def_rw("backend_profile_id",
                &runtime::fidelity::FidelityProfileAdmissionResult::backend_profile_id)
        .def_rw("parity_budget_ref",
                &runtime::fidelity::FidelityProfileAdmissionResult::parity_budget_ref)
        .def_rw("rejection_reason",
                &runtime::fidelity::FidelityProfileAdmissionResult::rejection_reason)
        .def_rw("errors", &runtime::fidelity::FidelityProfileAdmissionResult::errors)
        .def_rw("evidence_refs", &runtime::fidelity::FidelityProfileAdmissionResult::evidence_refs);

    nb::class_<runtime::platform_capabilities::Capability> platform_capability_class(
        m, "PlatformCapability");
    platform_capability_class.def(nb::init<>());
#define EF_PLATFORM_CAPABILITY_FIELD(type, name, default_value) \
    platform_capability_class.def_rw(#name, &runtime::platform_capabilities::Capability::name);
#include "runtime/contracts/detail/platform_capability.inc"

    nb::class_<runtime::platform_capabilities::CapabilityBundle> capability_bundle_class(
        m, "CapabilityBundle");
    capability_bundle_class.def(nb::init<>());
#define EF_CAPABILITY_BUNDLE_FIELD(type, name, default_value) \
    capability_bundle_class.def_rw(#name, &runtime::platform_capabilities::CapabilityBundle::name);
#include "runtime/contracts/detail/capability_bundle.inc"

    nb::class_<runtime::platform_capabilities::ResolvedPlatformSpawnPlan>
        resolved_platform_spawn_plan_class(m, "ResolvedPlatformSpawnPlan");
    resolved_platform_spawn_plan_class.def(nb::init<>());
#define EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(type, name, default_value)               \
    resolved_platform_spawn_plan_class.def_rw(                                         \
        #name, &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::name);
#include "runtime/contracts/detail/resolved_platform_spawn_plan.inc"

    nb::class_<TypedPlatformSpawnRequest> typed_platform_spawn_request_class(
        m, "TypedPlatformSpawnRequest");
    typed_platform_spawn_request_class.def(nb::init<>());
#define EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(type, name, default_value) \
    typed_platform_spawn_request_class.def_rw(#name, &TypedPlatformSpawnRequest::name);
#include "runtime/contracts/detail/typed_platform_spawn_request.inc"

    nb::class_<TypedPlatformSpawnValidationResult> typed_platform_spawn_validation_result_class(
        m, "TypedPlatformSpawnValidationResult");
    typed_platform_spawn_validation_result_class.def(nb::init<>());
#define EF_TYPED_PLATFORM_SPAWN_VALIDATION_RESULT_FIELD(type, name, default_value)     \
    typed_platform_spawn_validation_result_class.def_rw(                               \
        #name, &TypedPlatformSpawnValidationResult::name);
#include "runtime/contracts/detail/typed_platform_spawn_validation_result.inc"

    nb::class_<BatchResetRequest> batch_reset_request_class(m, "BatchResetRequest");
    batch_reset_request_class.def(nb::init<>());
#define EF_BATCH_RESET_REQUEST_FIELD(type, name, default_value) \
    batch_reset_request_class.def_rw(#name, &BatchResetRequest::name);
#include "runtime/facade/detail/batch_reset_request.inc"

    nb::class_<EngagementEntityRef>(m, "EngagementEntityRef")
        .def(nb::init<>())
        .def_rw("world_index", &EngagementEntityRef::world_index)
        .def_rw("entity_id", &EngagementEntityRef::entity_id);

    nb::class_<LethalityChainHeader>(m, "LethalityChainHeader")
        .def(nb::init<>())
        .def_rw("schema_version", &LethalityChainHeader::schema_version)
        .def_rw("chain_id", &LethalityChainHeader::chain_id)
        .def_rw("event_id", &LethalityChainHeader::event_id)
        .def_rw("parent_event_id", &LethalityChainHeader::parent_event_id)
        .def_rw("stage", &LethalityChainHeader::stage)
        .def_rw("status", &LethalityChainHeader::status)
        .def_rw("reason", &LethalityChainHeader::reason)
        .def_rw("source_time_s", &LethalityChainHeader::source_time_s)
        .def_rw("source_frame", &LethalityChainHeader::source_frame)
        .def_rw("munition", &LethalityChainHeader::munition)
        .def_rw("shooter", &LethalityChainHeader::shooter)
        .def_rw("target", &LethalityChainHeader::target)
        .def_rw("producer_node_id", &LethalityChainHeader::producer_node_id)
        .def_rw("fidelity_mode", &LethalityChainHeader::fidelity_mode)
        .def_rw("evidence_level", &LethalityChainHeader::evidence_level)
        .def_rw("observation_mode", &LethalityChainHeader::observation_mode)
        .def_rw("consumer_visibility", &LethalityChainHeader::consumer_visibility)
        .def_rw("confidence", &LethalityChainHeader::confidence);

    nb::class_<NearestApproachEvent>(m, "NearestApproachEvent")
        .def(nb::init<>())
        .def_rw("header", &NearestApproachEvent::header)
        .def_rw("nearest_approach_time_s", &NearestApproachEvent::nearest_approach_time_s)
        .def_rw("miss_distance_m", &NearestApproachEvent::miss_distance_m)
        .def_rw("local_forward_m", &NearestApproachEvent::local_forward_m)
        .def_rw("local_right_m", &NearestApproachEvent::local_right_m)
        .def_rw("local_up_m", &NearestApproachEvent::local_up_m)
        .def_rw("closure_mps", &NearestApproachEvent::closure_mps)
        .def_rw("aspect_bucket", &NearestApproachEvent::aspect_bucket);

    nb::class_<FuzeEvaluationEvent>(m, "FuzeEvaluationEvent")
        .def(nb::init<>())
        .def_rw("header", &FuzeEvaluationEvent::header)
        .def_rw("fuze_type", &FuzeEvaluationEvent::fuze_type)
        .def_rw("armed", &FuzeEvaluationEvent::armed)
        .def_rw("triggered", &FuzeEvaluationEvent::triggered)
        .def_rw("failure_reason", &FuzeEvaluationEvent::failure_reason)
        .def_rw("delay_s", &FuzeEvaluationEvent::delay_s)
        .def_rw("reliability", &FuzeEvaluationEvent::reliability)
        .def_rw("sample", &FuzeEvaluationEvent::sample)
        .def_rw("expected_detonation_probability",
                &FuzeEvaluationEvent::expected_detonation_probability)
        .def_rw("sampled_outcome", &FuzeEvaluationEvent::sampled_outcome)
        .def_rw("trigger_radius_m", &FuzeEvaluationEvent::trigger_radius_m)
        .def_rw("contact_surface_distance_m", &FuzeEvaluationEvent::contact_surface_distance_m)
        .def_rw("contact_penetration_depth_m", &FuzeEvaluationEvent::contact_penetration_depth_m)
        .def_rw("contact_surface_tolerance_m", &FuzeEvaluationEvent::contact_surface_tolerance_m)
        .def_rw("contact_inside_hitbox", &FuzeEvaluationEvent::contact_inside_hitbox)
        .def_rw("sensor_opportunity_source", &FuzeEvaluationEvent::sensor_opportunity_source)
        .def_rw("sensor_opportunity_score", &FuzeEvaluationEvent::sensor_opportunity_score)
        .def_rw("terminal_track_valid", &FuzeEvaluationEvent::terminal_track_valid)
        .def_rw("target_detected", &FuzeEvaluationEvent::target_detected)
        .def_rw("target_detection_source", &FuzeEvaluationEvent::target_detection_source)
        .def_rw("target_detection_confidence", &FuzeEvaluationEvent::target_detection_confidence)
        .def_rw("target_detection_threshold", &FuzeEvaluationEvent::target_detection_threshold)
        .def_rw("detonation_point_source", &FuzeEvaluationEvent::detonation_point_source)
        .def_rw("mechanism_coverage_score", &FuzeEvaluationEvent::mechanism_coverage_score)
        .def_rw("direct_hitbox_intersection", &FuzeEvaluationEvent::direct_hitbox_intersection);

    nb::class_<WarheadMechanismEvent>(m, "WarheadMechanismEvent")
        .def(nb::init<>())
        .def_rw("header", &WarheadMechanismEvent::header)
        .def_rw("mechanism_family", &WarheadMechanismEvent::mechanism_family)
        .def_rw("warhead_mass_kg", &WarheadMechanismEvent::warhead_mass_kg)
        .def_rw("lethal_radius_m", &WarheadMechanismEvent::lethal_radius_m)
        .def_rw("fragment_energy_j", &WarheadMechanismEvent::fragment_energy_j)
        .def_rw("fragment_density_per_m2", &WarheadMechanismEvent::fragment_density_per_m2)
        .def_rw("blast_overpressure_kpa", &WarheadMechanismEvent::blast_overpressure_kpa)
        .def_rw("blast_impulse_kpa_ms", &WarheadMechanismEvent::blast_impulse_kpa_ms)
        .def_rw("blast_scaled_distance_m_kg13",
                &WarheadMechanismEvent::blast_scaled_distance_m_kg13)
        .def_rw("rod_cut_margin", &WarheadMechanismEvent::rod_cut_margin)
        .def_rw("penetration_margin", &WarheadMechanismEvent::penetration_margin)
        .def_rw("surface_incidence_cos", &WarheadMechanismEvent::surface_incidence_cos);

    nb::class_<SpatialCoverageEvent>(m, "SpatialCoverageEvent")
        .def(nb::init<>())
        .def_rw("header", &SpatialCoverageEvent::header)
        .def_rw("projected_hitbox_count", &SpatialCoverageEvent::projected_hitbox_count)
        .def_rw("sample_count", &SpatialCoverageEvent::sample_count)
        .def_rw("hit_estimate", &SpatialCoverageEvent::hit_estimate)
        .def_rw("hit_fraction", &SpatialCoverageEvent::hit_fraction)
        .def_rw("energy_scale", &SpatialCoverageEvent::energy_scale)
        .def_rw("pattern_scale", &SpatialCoverageEvent::pattern_scale)
        .def_rw("orientation_axis_forward", &SpatialCoverageEvent::orientation_axis_forward)
        .def_rw("orientation_axis_right", &SpatialCoverageEvent::orientation_axis_right)
        .def_rw("orientation_axis_up", &SpatialCoverageEvent::orientation_axis_up);

    nb::class_<ComponentLoadEvent>(m, "ComponentLoadEvent")
        .def(nb::init<>())
        .def_rw("header", &ComponentLoadEvent::header)
        .def_rw("component_name", &ComponentLoadEvent::component_name)
        .def_rw("component_system", &ComponentLoadEvent::component_system)
        .def_rw("component_redundancy_group_id", &ComponentLoadEvent::component_redundancy_group_id)
        .def_rw("direct_hit", &ComponentLoadEvent::direct_hit)
        .def_rw("distance_m", &ComponentLoadEvent::distance_m)
        .def_rw("effect_scale", &ComponentLoadEvent::effect_scale)
        .def_rw("spatial_intersection_fraction", &ComponentLoadEvent::spatial_intersection_fraction)
        .def_rw("pattern_weight", &ComponentLoadEvent::pattern_weight)
        .def_rw("orientation_weight", &ComponentLoadEvent::orientation_weight)
        .def_rw("receiver_exposure_fraction", &ComponentLoadEvent::receiver_exposure_fraction)
        .def_rw("armor_transmission", &ComponentLoadEvent::armor_transmission)
        .def_rw("sampling_confidence", &ComponentLoadEvent::sampling_confidence)
        .def_rw("load_intensity_scale", &ComponentLoadEvent::load_intensity_scale)
        .def_rw("fragment_energy_j", &ComponentLoadEvent::fragment_energy_j)
        .def_rw("fragment_density_per_m2", &ComponentLoadEvent::fragment_density_per_m2)
        .def_rw("penetration_margin", &ComponentLoadEvent::penetration_margin)
        .def_rw("blast_overpressure_kpa", &ComponentLoadEvent::blast_overpressure_kpa)
        .def_rw("blast_impulse_kpa_ms", &ComponentLoadEvent::blast_impulse_kpa_ms)
        .def_rw("blast_scaled_distance_m_kg13", &ComponentLoadEvent::blast_scaled_distance_m_kg13)
        .def_rw("rod_cut_margin", &ComponentLoadEvent::rod_cut_margin)
        .def_rw("surface_incidence_cos", &ComponentLoadEvent::surface_incidence_cos)
        .def_rw("load_source", &ComponentLoadEvent::load_source);

    nb::class_<ComponentDamageEvent>(m, "ComponentDamageEvent")
        .def(nb::init<>())
        .def_rw("header", &ComponentDamageEvent::header)
        .def_rw("component_name", &ComponentDamageEvent::component_name)
        .def_rw("component_system", &ComponentDamageEvent::component_system)
        .def_rw("component_redundancy_group_id",
                &ComponentDamageEvent::component_redundancy_group_id)
        .def_rw("integrity_before", &ComponentDamageEvent::integrity_before)
        .def_rw("integrity_after", &ComponentDamageEvent::integrity_after)
        .def_rw("failure_mode", &ComponentDamageEvent::failure_mode)
        .def_rw("failure_severity", &ComponentDamageEvent::failure_severity)
        .def_rw("failure_probability", &ComponentDamageEvent::failure_probability)
        .def_rw("failure_sample", &ComponentDamageEvent::failure_sample);

    nb::class_<PlatformConsequenceEvent>(m, "PlatformConsequenceEvent")
        .def(nb::init<>())
        .def_rw("header", &PlatformConsequenceEvent::header)
        .def_rw("mission_capability_before", &PlatformConsequenceEvent::mission_capability_before)
        .def_rw("mission_capability_after", &PlatformConsequenceEvent::mission_capability_after)
        .def_rw("mobility_capability_before", &PlatformConsequenceEvent::mobility_capability_before)
        .def_rw("mobility_capability_after", &PlatformConsequenceEvent::mobility_capability_after)
        .def_rw("sensor_capability_before", &PlatformConsequenceEvent::sensor_capability_before)
        .def_rw("sensor_capability_after", &PlatformConsequenceEvent::sensor_capability_after)
        .def_rw("survivability_capability_before",
                &PlatformConsequenceEvent::survivability_capability_before)
        .def_rw("survivability_capability_after",
                &PlatformConsequenceEvent::survivability_capability_after)
        .def_rw("mission_kill", &PlatformConsequenceEvent::mission_kill)
        .def_rw("mobility_kill", &PlatformConsequenceEvent::mobility_kill)
        .def_rw("sensor_kill", &PlatformConsequenceEvent::sensor_kill)
        .def_rw("survivability_kill", &PlatformConsequenceEvent::survivability_kill)
        .def_rw("flight_control_kill", &PlatformConsequenceEvent::flight_control_kill)
        .def_rw("propulsion_kill", &PlatformConsequenceEvent::propulsion_kill)
        .def_rw("forced_landing", &PlatformConsequenceEvent::forced_landing)
        .def_rw("crew_kill", &PlatformConsequenceEvent::crew_kill)
        .def_rw("control_delta", &PlatformConsequenceEvent::control_delta)
        .def_rw("engine_delta", &PlatformConsequenceEvent::engine_delta)
        .def_rw("fuel_leak_delta", &PlatformConsequenceEvent::fuel_leak_delta)
        .def_rw("fire_state", &PlatformConsequenceEvent::fire_state)
        .def_rw("aircraft_damage_state_before",
                &PlatformConsequenceEvent::aircraft_damage_state_before)
        .def_rw("aircraft_damage_state_after",
                &PlatformConsequenceEvent::aircraft_damage_state_after)
        .def_rw("aircraft_damage_state_delta",
                &PlatformConsequenceEvent::aircraft_damage_state_delta)
        .def_rw("air_system_hit_flags", &PlatformConsequenceEvent::air_system_hit_flags)
        .def_rw("air_system_spatial_scales", &PlatformConsequenceEvent::air_system_spatial_scales)
        .def_rw("vulnerability_scale_trace", &PlatformConsequenceEvent::vulnerability_scale_trace)
        .def_rw("loss_state_from", &PlatformConsequenceEvent::loss_state_from)
        .def_rw("loss_state_to", &PlatformConsequenceEvent::loss_state_to);

    nb::class_<StructuralBreakupEvent>(m, "StructuralBreakupEvent")
        .def(nb::init<>())
        .def_rw("header", &StructuralBreakupEvent::header)
        .def_rw("breakup_state", &StructuralBreakupEvent::breakup_state)
        .def_rw("break_mode", &StructuralBreakupEvent::break_mode)
        .def_rw("detached_part_ref", &StructuralBreakupEvent::detached_part_ref)
        .def_rw("detached_part_count", &StructuralBreakupEvent::detached_part_count)
        .def_rw("airframe_breakup", &StructuralBreakupEvent::airframe_breakup)
        .def_rw("cause_event_id", &StructuralBreakupEvent::cause_event_id);

    nb::class_<LifecycleTransitionEvent>(m, "LifecycleTransitionEvent")
        .def(nb::init<>())
        .def_rw("header", &LifecycleTransitionEvent::header)
        .def_rw("lifecycle_from", &LifecycleTransitionEvent::lifecycle_from)
        .def_rw("lifecycle_to", &LifecycleTransitionEvent::lifecycle_to)
        .def_rw("ground_lifecycle", &LifecycleTransitionEvent::ground_lifecycle)
        .def_rw("wreck_entity", &LifecycleTransitionEvent::wreck_entity)
        .def_rw("debris_count", &LifecycleTransitionEvent::debris_count)
        .def_rw("terminal", &LifecycleTransitionEvent::terminal)
        .def_rw("terminal_projection_id", &LifecycleTransitionEvent::terminal_projection_id);

    nb::class_<TrainingProjectionEvent>(m, "TrainingProjectionEvent")
        .def(nb::init<>())
        .def_rw("header", &TrainingProjectionEvent::header)
        .def_rw("consumed_event_ids", &TrainingProjectionEvent::consumed_event_ids)
        .def_rw("consumer_node_id", &TrainingProjectionEvent::consumer_node_id)
        .def_rw("consumer_version", &TrainingProjectionEvent::consumer_version)
        .def_rw("projection_kind", &TrainingProjectionEvent::projection_kind)
        .def_rw("reward_term", &TrainingProjectionEvent::reward_term)
        .def_rw("reward_delta", &TrainingProjectionEvent::reward_delta)
        .def_rw("terminal_reason", &TrainingProjectionEvent::terminal_reason)
        .def_rw("fact_source", &TrainingProjectionEvent::fact_source);

    nb::class_<TrackPacket>(m, "TrackPacket")
        .def(nb::init<>())
        .def_rw("track_id", &TrackPacket::track_id)
        .def_rw("correlated_entity", &TrackPacket::correlated_entity)
        .def_rw("has_correlated_entity", &TrackPacket::has_correlated_entity)
        .def_rw("correlation_policy", &TrackPacket::correlation_policy)
        .def_rw("source", &TrackPacket::source)
        .def_rw("classification", &TrackPacket::classification)
        .def_rw("status", &TrackPacket::status)
        .def_rw("quality", &TrackPacket::quality)
        .def_rw("confidence", &TrackPacket::confidence)
        .def_rw("usable", &TrackPacket::usable)
        .def_rw("iff", &TrackPacket::iff)
        .def_rw("source_time_s", &TrackPacket::source_time_s)
        .def_rw("update_age_s", &TrackPacket::update_age_s)
        .def_rw("snapshot_version", &TrackPacket::snapshot_version);

    nb::class_<LaunchRequest>(m, "LaunchRequest")
        .def(nb::init<>())
        .def_rw("request_id", &LaunchRequest::request_id)
        .def_rw("shooter", &LaunchRequest::shooter)
        .def_rw("target_entity", &LaunchRequest::target_entity)
        .def_rw("has_target_entity", &LaunchRequest::has_target_entity)
        .def_rw("target_track_id", &LaunchRequest::target_track_id)
        .def_rw("has_target_track", &LaunchRequest::has_target_track)
        .def_rw("station_id", &LaunchRequest::station_id)
        .def_rw("mount_id", &LaunchRequest::mount_id)
        .def_rw("requested_munition_family", &LaunchRequest::requested_munition_family)
        .def_rw("authority", &LaunchRequest::authority)
        .def_rw("requested_time_s", &LaunchRequest::requested_time_s)
        .def_rw("merge_policy", &LaunchRequest::merge_policy);

    nb::class_<LaunchEvent>(m, "LaunchEvent")
        .def(nb::init<>())
        .def_rw("event_id", &LaunchEvent::event_id)
        .def_rw("request_id", &LaunchEvent::request_id)
        .def_rw("accepted", &LaunchEvent::accepted)
        .def_rw("rejection_reason", &LaunchEvent::rejection_reason)
        .def_rw("selected_launcher", &LaunchEvent::selected_launcher)
        .def_rw("selected_munition", &LaunchEvent::selected_munition)
        .def_rw("ammo_delta", &LaunchEvent::ammo_delta)
        .def_rw("cooldown_delta_s", &LaunchEvent::cooldown_delta_s)
        .def_rw("spawned_munition", &LaunchEvent::spawned_munition)
        .def_rw("has_spawned_munition", &LaunchEvent::has_spawned_munition)
        .def_rw("event_time_s", &LaunchEvent::event_time_s)
        .def_rw("producer_node_id", &LaunchEvent::producer_node_id);

    nb::class_<MunitionLifecyclePacket>(m, "MunitionLifecyclePacket")
        .def(nb::init<>())
        .def_rw("packet_id", &MunitionLifecyclePacket::packet_id)
        .def_rw("munition", &MunitionLifecyclePacket::munition)
        .def_rw("attacker", &MunitionLifecyclePacket::attacker)
        .def_rw("target_entity", &MunitionLifecyclePacket::target_entity)
        .def_rw("has_target_entity", &MunitionLifecyclePacket::has_target_entity)
        .def_rw("target_track_id", &MunitionLifecyclePacket::target_track_id)
        .def_rw("has_target_track", &MunitionLifecyclePacket::has_target_track)
        .def_rw("launch_event_id", &MunitionLifecyclePacket::launch_event_id)
        .def_rw("active", &MunitionLifecyclePacket::active)
        .def_rw("seeker_mode", &MunitionLifecyclePacket::seeker_mode)
        .def_rw("guidance_cadence_s", &MunitionLifecyclePacket::guidance_cadence_s)
        .def_rw("track_memory_state", &MunitionLifecyclePacket::track_memory_state)
        .def_rw("fuel_remaining_fraction", &MunitionLifecyclePacket::fuel_remaining_fraction)
        .def_rw("burnout", &MunitionLifecyclePacket::burnout)
        .def_rw("max_flight_time_s", &MunitionLifecyclePacket::max_flight_time_s)
        .def_rw("fuze_state", &MunitionLifecyclePacket::fuze_state)
        .def_rw("source_time_s", &MunitionLifecyclePacket::source_time_s);

    nb::class_<ComponentMechanismLoadRow>(m, "ComponentMechanismLoadRow")
        .def(nb::init<>())
        .def_rw("component_name", &ComponentMechanismLoadRow::component_name)
        .def_rw("component_system", &ComponentMechanismLoadRow::component_system)
        .def_rw("component_redundancy_group_id",
                &ComponentMechanismLoadRow::component_redundancy_group_id)
        .def_rw("direct_hit", &ComponentMechanismLoadRow::direct_hit)
        .def_rw("distance_m", &ComponentMechanismLoadRow::distance_m)
        .def_rw("effect_scale", &ComponentMechanismLoadRow::effect_scale)
        .def_rw("component_dependency_propagation_count",
                &ComponentMechanismLoadRow::component_dependency_propagation_count)
        .def_rw("component_dependency_target_system",
                &ComponentMechanismLoadRow::component_dependency_target_system)
        .def_rw("component_dependency_edge_type",
                &ComponentMechanismLoadRow::component_dependency_edge_type)
        .def_rw("component_dependency_threshold",
                &ComponentMechanismLoadRow::component_dependency_threshold)
        .def_rw("component_dependency_delay_s",
                &ComponentMechanismLoadRow::component_dependency_delay_s)
        .def_rw("component_dependency_direction",
                &ComponentMechanismLoadRow::component_dependency_direction)
        .def_rw("component_dependency_provenance",
                &ComponentMechanismLoadRow::component_dependency_provenance)
        .def_rw("component_dependency_source_availability",
                &ComponentMechanismLoadRow::component_dependency_source_availability)
        .def_rw("component_dependency_effective_scale",
                &ComponentMechanismLoadRow::component_dependency_effective_scale)
        .def_rw("component_dependency_propagated",
                &ComponentMechanismLoadRow::component_dependency_propagated)
        .def_rw("mechanism_fragment_energy_j",
                &ComponentMechanismLoadRow::mechanism_fragment_energy_j)
        .def_rw("mechanism_fragment_areal_density_per_m2",
                &ComponentMechanismLoadRow::mechanism_fragment_areal_density_per_m2)
        .def_rw("mechanism_penetration_margin",
                &ComponentMechanismLoadRow::mechanism_penetration_margin)
        .def_rw("mechanism_blast_overpressure_kpa",
                &ComponentMechanismLoadRow::mechanism_blast_overpressure_kpa)
        .def_rw("mechanism_blast_impulse_kpa_ms",
                &ComponentMechanismLoadRow::mechanism_blast_impulse_kpa_ms)
        .def_rw("mechanism_blast_scaled_distance_m_kg13",
                &ComponentMechanismLoadRow::mechanism_blast_scaled_distance_m_kg13)
        .def_rw("mechanism_rod_cut_margin", &ComponentMechanismLoadRow::mechanism_rod_cut_margin)
        .def_rw("mechanism_surface_incidence_cos",
                &ComponentMechanismLoadRow::mechanism_surface_incidence_cos);

    nb::class_<ComponentResponseRow>(m, "ComponentResponseRow")
        .def(nb::init<>())
        .def_rw("owner_stage", &ComponentResponseRow::owner_stage)
        .def_rw("source_current_owner_stage", &ComponentResponseRow::source_current_owner_stage)
        .def_rw("source_row_index", &ComponentResponseRow::source_row_index)
        .def_rw("component_name", &ComponentResponseRow::component_name)
        .def_rw("component_system", &ComponentResponseRow::component_system)
        .def_rw("component_redundancy_group_id",
                &ComponentResponseRow::component_redundancy_group_id)
        .def_rw("threshold_scale", &ComponentResponseRow::threshold_scale)
        .def_rw("failure_probability", &ComponentResponseRow::failure_probability)
        .def_rw("failure_sample", &ComponentResponseRow::failure_sample)
        .def_rw("failure_probability_source", &ComponentResponseRow::failure_probability_source)
        .def_rw("failure_probability_calibrated",
                &ComponentResponseRow::failure_probability_calibrated)
        .def_rw("failure_probability_evidence_dataset_ref",
                &ComponentResponseRow::failure_probability_evidence_dataset_ref)
        .def_rw("failure_probability_evidence_row_id",
                &ComponentResponseRow::failure_probability_evidence_row_id)
        .def_rw("failure_probability_evidence_source_ref",
                &ComponentResponseRow::failure_probability_evidence_source_ref)
        .def_rw("failure_probability_evidence_provenance",
                &ComponentResponseRow::failure_probability_evidence_provenance)
        .def_rw("failure_probability_authority",
                &ComponentResponseRow::failure_probability_authority)
        .def_rw("failure_probability_component_specific",
                &ComponentResponseRow::failure_probability_component_specific)
        .def_rw("failure_probability_weapon_family",
                &ComponentResponseRow::failure_probability_weapon_family)
        .def_rw("failure_probability_aspect_bucket",
                &ComponentResponseRow::failure_probability_aspect_bucket)
        .def_rw("failure_probability_closure_bucket",
                &ComponentResponseRow::failure_probability_closure_bucket)
        .def_rw("failure_probability_miss_distance_bucket",
                &ComponentResponseRow::failure_probability_miss_distance_bucket)
        .def_rw("failure_probability_evidence_component_name",
                &ComponentResponseRow::failure_probability_evidence_component_name)
        .def_rw("failure_probability_evidence_component_system",
                &ComponentResponseRow::failure_probability_evidence_component_system)
        .def_rw("failure_probability_evidence_component_redundancy_group_id",
                &ComponentResponseRow::failure_probability_evidence_component_redundancy_group_id)
        .def_rw("failure_mode", &ComponentResponseRow::failure_mode)
        .def_rw("failure_severity", &ComponentResponseRow::failure_severity)
        .def_rw("failure_mode_names", &ComponentResponseRow::failure_mode_names)
        .def_rw("failure_mode_severities", &ComponentResponseRow::failure_mode_severities)
        .def_rw("failure_mode_source", &ComponentResponseRow::failure_mode_source)
        .def_rw("failure_mode_authority", &ComponentResponseRow::failure_mode_authority)
        .def_rw("integrity_before", &ComponentResponseRow::integrity_before)
        .def_rw("integrity_after", &ComponentResponseRow::integrity_after)
        .def_rw("redundancy_group_availability_before",
                &ComponentResponseRow::redundancy_group_availability_before)
        .def_rw("redundancy_group_availability_after",
                &ComponentResponseRow::redundancy_group_availability_after);

    // The def_rw list is owned by the X-macro field list; exposed property
    // names and their order stay identical to the EffectsEvent declaration.
    nb::class_<EffectsEvent>(m, "EffectsEvent")
        .def(nb::init<>())
#define EF_EFFECTS_EVENT_FIELD(type, name, default_value) .def_rw(#name, &EffectsEvent::name)
#define EF_EFFECTS_EVENT_RESULT_FIELD(type, name, default_value)                                   \
    .def_rw(#name, &EffectsEvent::name)
#include "runtime/contracts/detail/effects_event_fields.inc"
#undef EF_EFFECTS_EVENT_RESULT_FIELD
#undef EF_EFFECTS_EVENT_FIELD
        ;

    nb::class_<KillChainApproachFact>(m, "KillChainApproachFact")
        .def(nb::init<>())
        .def_rw("owner_stage", &KillChainApproachFact::owner_stage)
        .def_rw("closest_distance_m", &KillChainApproachFact::closest_distance_m)
        .def_rw("closest_point_local_forward_m",
                &KillChainApproachFact::closest_point_local_forward_m)
        .def_rw("closest_point_local_right_m", &KillChainApproachFact::closest_point_local_right_m)
        .def_rw("closest_point_local_up_m", &KillChainApproachFact::closest_point_local_up_m)
        .def_rw("closure_mps", &KillChainApproachFact::closure_mps)
        .def_rw("nearest_approach_time_s", &KillChainApproachFact::nearest_approach_time_s);

    nb::class_<KillChainFuzeDecision>(m, "KillChainFuzeDecision")
        .def(nb::init<>())
        .def_rw("owner_stage", &KillChainFuzeDecision::owner_stage)
        .def_rw("fuze_type", &KillChainFuzeDecision::fuze_type)
        .def_rw("detonated", &KillChainFuzeDecision::detonated)
        .def_rw("outcome_state", &KillChainFuzeDecision::outcome_state)
        .def_rw("detonation_time_s", &KillChainFuzeDecision::detonation_time_s)
        .def_rw("detonation_probability", &KillChainFuzeDecision::detonation_probability)
        .def_rw("fuze_quality", &KillChainFuzeDecision::fuze_quality)
        .def_rw("sensor_opportunity_score", &KillChainFuzeDecision::sensor_opportunity_score)
        .def_rw("terminal_track_valid", &KillChainFuzeDecision::terminal_track_valid)
        .def_rw("target_detected", &KillChainFuzeDecision::target_detected)
        .def_rw("target_detection_confidence", &KillChainFuzeDecision::target_detection_confidence)
        .def_rw("target_detection_threshold", &KillChainFuzeDecision::target_detection_threshold)
        .def_rw("detonation_point_source", &KillChainFuzeDecision::detonation_point_source);

    nb::class_<KillChainComponentLoadFact>(m, "KillChainComponentLoadFact")
        .def(nb::init<>())
        .def_rw("owner_stage", &KillChainComponentLoadFact::owner_stage)
        .def_rw("component_name", &KillChainComponentLoadFact::component_name)
        .def_rw("component_system", &KillChainComponentLoadFact::component_system)
        .def_rw("component_redundancy_group_id",
                &KillChainComponentLoadFact::component_redundancy_group_id)
        .def_rw("direct_hit", &KillChainComponentLoadFact::direct_hit)
        .def_rw("distance_m", &KillChainComponentLoadFact::distance_m)
        .def_rw("effect_scale", &KillChainComponentLoadFact::effect_scale)
        .def_rw("spatial_intersection_fraction",
                &KillChainComponentLoadFact::spatial_intersection_fraction)
        .def_rw("pattern_weight", &KillChainComponentLoadFact::pattern_weight)
        .def_rw("orientation_weight", &KillChainComponentLoadFact::orientation_weight)
        .def_rw("receiver_exposure_fraction",
                &KillChainComponentLoadFact::receiver_exposure_fraction)
        .def_rw("armor_transmission", &KillChainComponentLoadFact::armor_transmission)
        .def_rw("sampling_confidence", &KillChainComponentLoadFact::sampling_confidence)
        .def_rw("load_intensity_scale", &KillChainComponentLoadFact::load_intensity_scale)
        .def_rw("fragment_energy_j", &KillChainComponentLoadFact::fragment_energy_j)
        .def_rw("fragment_areal_density_per_m2",
                &KillChainComponentLoadFact::fragment_areal_density_per_m2)
        .def_rw("penetration_margin", &KillChainComponentLoadFact::penetration_margin)
        .def_rw("blast_overpressure_kpa", &KillChainComponentLoadFact::blast_overpressure_kpa)
        .def_rw("blast_impulse_kpa_ms", &KillChainComponentLoadFact::blast_impulse_kpa_ms)
        .def_rw("blast_scaled_distance_m_kg13",
                &KillChainComponentLoadFact::blast_scaled_distance_m_kg13)
        .def_rw("rod_cut_margin", &KillChainComponentLoadFact::rod_cut_margin)
        .def_rw("surface_incidence_cos", &KillChainComponentLoadFact::surface_incidence_cos);

    nb::class_<KillChainWarheadLoadField>(m, "KillChainWarheadLoadField")
        .def(nb::init<>())
        .def_rw("owner_stage", &KillChainWarheadLoadField::owner_stage)
        .def_rw("effect_family", &KillChainWarheadLoadField::effect_family)
        .def_rw("warhead_mass_kg", &KillChainWarheadLoadField::warhead_mass_kg)
        .def_rw("lethal_radius_m", &KillChainWarheadLoadField::lethal_radius_m)
        .def_rw("spatial_effect_scale", &KillChainWarheadLoadField::spatial_effect_scale)
        .def_rw("armor_transmission", &KillChainWarheadLoadField::armor_transmission)
        .def_rw("receiver_exposure_fraction",
                &KillChainWarheadLoadField::receiver_exposure_fraction)
        .def_rw("mechanism_effect_scale", &KillChainWarheadLoadField::mechanism_effect_scale)
        .def_rw("projected_hitbox_count", &KillChainWarheadLoadField::projected_hitbox_count)
        .def_rw("spatial_sample_count", &KillChainWarheadLoadField::spatial_sample_count)
        .def_rw("spatial_hit_estimate", &KillChainWarheadLoadField::spatial_hit_estimate)
        .def_rw("spatial_hit_fraction", &KillChainWarheadLoadField::spatial_hit_fraction)
        .def_rw("spatial_energy_scale", &KillChainWarheadLoadField::spatial_energy_scale)
        .def_rw("spatial_pattern_scale", &KillChainWarheadLoadField::spatial_pattern_scale)
        .def_rw("orientation_pattern_scale", &KillChainWarheadLoadField::orientation_pattern_scale)
        .def_rw("fragment_energy_j", &KillChainWarheadLoadField::fragment_energy_j)
        .def_rw("fragment_areal_density_per_m2",
                &KillChainWarheadLoadField::fragment_areal_density_per_m2)
        .def_rw("penetration_margin", &KillChainWarheadLoadField::penetration_margin)
        .def_rw("blast_overpressure_kpa", &KillChainWarheadLoadField::blast_overpressure_kpa)
        .def_rw("blast_impulse_kpa_ms", &KillChainWarheadLoadField::blast_impulse_kpa_ms)
        .def_rw("blast_scaled_distance_m_kg13",
                &KillChainWarheadLoadField::blast_scaled_distance_m_kg13)
        .def_rw("rod_cut_margin", &KillChainWarheadLoadField::rod_cut_margin)
        .def_rw("surface_incidence_cos", &KillChainWarheadLoadField::surface_incidence_cos)
        .def_rw("component_loads", &KillChainWarheadLoadField::component_loads);

    nb::class_<KillChainTargetSusceptibility>(m, "KillChainTargetSusceptibility")
        .def(nb::init<>())
        .def_rw("owner_stage", &KillChainTargetSusceptibility::owner_stage)
        .def_rw("vulnerability_profile_present",
                &KillChainTargetSusceptibility::vulnerability_profile_present)
        .def_rw("vulnerability_profile_synthetic",
                &KillChainTargetSusceptibility::vulnerability_profile_synthetic)
        .def_rw("calibrated_evidence", &KillChainTargetSusceptibility::calibrated_evidence)
        .def_rw("pk_authority", &KillChainTargetSusceptibility::pk_authority)
        .def_rw("deterministic_fuze_authority",
                &KillChainTargetSusceptibility::deterministic_fuze_authority)
        .def_rw("calibration_status", &KillChainTargetSusceptibility::calibration_status)
        .def_rw("aspect_bucket", &KillChainTargetSusceptibility::aspect_bucket)
        .def_rw("family_scale", &KillChainTargetSusceptibility::family_scale)
        .def_rw("aspect_scale", &KillChainTargetSusceptibility::aspect_scale)
        .def_rw("closure_scale", &KillChainTargetSusceptibility::closure_scale)
        .def_rw("miss_distance_scale", &KillChainTargetSusceptibility::miss_distance_scale)
        .def_rw("effect_scale", &KillChainTargetSusceptibility::effect_scale);

    nb::class_<KillChainComponentResponseFact>(m, "KillChainComponentResponseFact")
        .def(nb::init<>())
        .def_rw("owner_stage", &KillChainComponentResponseFact::owner_stage)
        .def_rw("source_current_owner_stage",
                &KillChainComponentResponseFact::source_current_owner_stage)
        .def_rw("source_row_index", &KillChainComponentResponseFact::source_row_index)
        .def_rw("component_name", &KillChainComponentResponseFact::component_name)
        .def_rw("component_system", &KillChainComponentResponseFact::component_system)
        .def_rw("component_redundancy_group_id",
                &KillChainComponentResponseFact::component_redundancy_group_id)
        .def_rw("threshold_scale", &KillChainComponentResponseFact::threshold_scale)
        .def_rw("failure_probability", &KillChainComponentResponseFact::failure_probability)
        .def_rw("failure_sample", &KillChainComponentResponseFact::failure_sample)
        .def_rw("failure_probability_source",
                &KillChainComponentResponseFact::failure_probability_source)
        .def_rw("failure_probability_calibrated",
                &KillChainComponentResponseFact::failure_probability_calibrated)
        .def_rw("failure_probability_evidence_dataset_ref",
                &KillChainComponentResponseFact::failure_probability_evidence_dataset_ref)
        .def_rw("failure_probability_evidence_row_id",
                &KillChainComponentResponseFact::failure_probability_evidence_row_id)
        .def_rw("failure_probability_evidence_source_ref",
                &KillChainComponentResponseFact::failure_probability_evidence_source_ref)
        .def_rw("failure_probability_evidence_provenance",
                &KillChainComponentResponseFact::failure_probability_evidence_provenance)
        .def_rw("failure_probability_authority",
                &KillChainComponentResponseFact::failure_probability_authority)
        .def_rw("failure_probability_component_specific",
                &KillChainComponentResponseFact::failure_probability_component_specific)
        .def_rw("failure_probability_weapon_family",
                &KillChainComponentResponseFact::failure_probability_weapon_family)
        .def_rw("failure_probability_aspect_bucket",
                &KillChainComponentResponseFact::failure_probability_aspect_bucket)
        .def_rw("failure_probability_closure_bucket",
                &KillChainComponentResponseFact::failure_probability_closure_bucket)
        .def_rw("failure_probability_miss_distance_bucket",
                &KillChainComponentResponseFact::failure_probability_miss_distance_bucket)
        .def_rw("failure_probability_evidence_component_name",
                &KillChainComponentResponseFact::failure_probability_evidence_component_name)
        .def_rw("failure_probability_evidence_component_system",
                &KillChainComponentResponseFact::failure_probability_evidence_component_system)
        .def_rw("failure_probability_evidence_component_redundancy_group_id",
                &KillChainComponentResponseFact::
                    failure_probability_evidence_component_redundancy_group_id)
        .def_rw("failure_mode", &KillChainComponentResponseFact::failure_mode)
        .def_rw("failure_severity", &KillChainComponentResponseFact::failure_severity)
        .def_rw("failure_mode_names", &KillChainComponentResponseFact::failure_mode_names)
        .def_rw("failure_mode_severities", &KillChainComponentResponseFact::failure_mode_severities)
        .def_rw("failure_mode_source", &KillChainComponentResponseFact::failure_mode_source)
        .def_rw("failure_mode_authority", &KillChainComponentResponseFact::failure_mode_authority)
        .def_rw("integrity_before", &KillChainComponentResponseFact::integrity_before)
        .def_rw("integrity_after", &KillChainComponentResponseFact::integrity_after)
        .def_rw("redundancy_group_availability_before",
                &KillChainComponentResponseFact::redundancy_group_availability_before)
        .def_rw("redundancy_group_availability_after",
                &KillChainComponentResponseFact::redundancy_group_availability_after);

    nb::class_<KillChainConsequenceProjection>(m, "KillChainConsequenceProjection")
        .def(nb::init<>())
        .def_rw("owner_stage", &KillChainConsequenceProjection::owner_stage)
        .def_rw("outcome_state", &KillChainConsequenceProjection::outcome_state)
        .def_rw("component_hit_count", &KillChainConsequenceProjection::component_hit_count)
        .def_rw("component_failure_count", &KillChainConsequenceProjection::component_failure_count)
        .def_rw("primary_component_name", &KillChainConsequenceProjection::primary_component_name)
        .def_rw("primary_component_system",
                &KillChainConsequenceProjection::primary_component_system)
        .def_rw("primary_component_integrity",
                &KillChainConsequenceProjection::primary_component_integrity)
        .def_rw("redundancy_group_availability",
                &KillChainConsequenceProjection::redundancy_group_availability)
        .def_rw("air_system_hit_flags", &KillChainConsequenceProjection::air_system_hit_flags)
        .def_rw("air_system_spatial_scales",
                &KillChainConsequenceProjection::air_system_spatial_scales)
        .def_rw("vulnerability_scale_trace",
                &KillChainConsequenceProjection::vulnerability_scale_trace);

    nb::class_<KillChainRuntimeFacade>(m, "KillChainRuntimeFacade")
        .def(nb::init<>())
        .def_rw("schema_version", &KillChainRuntimeFacade::schema_version)
        .def_rw("schema_name", &KillChainRuntimeFacade::schema_name)
        .def_rw("runtime_dto_authority", &KillChainRuntimeFacade::runtime_dto_authority)
        .def_rw("runtime_parameter_retuning", &KillChainRuntimeFacade::runtime_parameter_retuning)
        .def_rw("calibration_authority", &KillChainRuntimeFacade::calibration_authority)
        .def_rw("real_world_pk", &KillChainRuntimeFacade::real_world_pk)
        .def_rw("approach_fact", &KillChainRuntimeFacade::approach_fact)
        .def_rw("fuze_decision", &KillChainRuntimeFacade::fuze_decision)
        .def_rw("warhead_load_field", &KillChainRuntimeFacade::warhead_load_field)
        .def_rw("target_susceptibility", &KillChainRuntimeFacade::target_susceptibility)
        .def_rw("component_responses", &KillChainRuntimeFacade::component_responses)
        .def_rw("consequence_projection", &KillChainRuntimeFacade::consequence_projection);

    m.def("make_kill_chain_runtime_facade", &make_kill_chain_runtime_facade, nb::arg("effects"));

    nb::class_<DamageReport>(m, "DamageReport")
        .def(nb::init<>())
        .def_rw("report_id", &DamageReport::report_id)
        .def_rw("target", &DamageReport::target)
        .def_rw("source_event_id", &DamageReport::source_event_id)
        .def_rw("hp_delta", &DamageReport::hp_delta)
        .def_rw("system_health_delta", &DamageReport::system_health_delta)
        .def_rw("platform_damage_state_delta", &DamageReport::platform_damage_state_delta)
        .def_rw("mission_kill", &DamageReport::mission_kill)
        .def_rw("mobility_kill", &DamageReport::mobility_kill)
        .def_rw("sensor_kill", &DamageReport::sensor_kill)
        .def_rw("survivability_kill", &DamageReport::survivability_kill)
        .def_rw("forced_landing", &DamageReport::forced_landing)
        .def_rw("flight_control_kill", &DamageReport::flight_control_kill)
        .def_rw("propulsion_kill", &DamageReport::propulsion_kill)
        .def_rw("crew_kill", &DamageReport::crew_kill)
        .def_rw("loss_state_from", &DamageReport::loss_state_from)
        .def_rw("loss_state_to", &DamageReport::loss_state_to)
        .def_rw("destroyed", &DamageReport::destroyed)
        .def_rw("report_time_s", &DamageReport::report_time_s)
        .def_rw("producer_node_id", &DamageReport::producer_node_id);

    nb::class_<DiagnosticsTrace>(m, "DiagnosticsTrace")
        .def(nb::init<>())
        .def_rw("trace_id", &DiagnosticsTrace::trace_id)
        .def_rw("parent_trace_id", &DiagnosticsTrace::parent_trace_id)
        .def_rw("chain_id", &DiagnosticsTrace::chain_id)
        .def_rw("track_id", &DiagnosticsTrace::track_id)
        .def_rw("launch_request_id", &DiagnosticsTrace::launch_request_id)
        .def_rw("launch_event_id", &DiagnosticsTrace::launch_event_id)
        .def_rw("munition", &DiagnosticsTrace::munition)
        .def_rw("effects_event_id", &DiagnosticsTrace::effects_event_id)
        .def_rw("damage_report_id", &DiagnosticsTrace::damage_report_id)
        .def_rw("observation_packet_version", &DiagnosticsTrace::observation_packet_version)
        .def_rw("source_snapshot_version", &DiagnosticsTrace::source_snapshot_version)
        .def_rw("barrier_id", &DiagnosticsTrace::barrier_id)
        .def_rw("barrier_detail", &DiagnosticsTrace::barrier_detail)
        .def_rw("source_time_s", &DiagnosticsTrace::source_time_s)
        .def_rw("source_node_id", &DiagnosticsTrace::source_node_id)
        .def_rw("export_node_id", &DiagnosticsTrace::export_node_id);

    nb::class_<IntentTargetRef>(m, "IntentTargetRef")
        .def(nb::init<>())
        .def_rw("world_index", &IntentTargetRef::world_index)
        .def_rw("entity_id", &IntentTargetRef::entity_id);

    nb::class_<ProducedIntentRef>(m, "ProducedIntentRef")
        .def(nb::init<>())
        .def_rw("kind", &ProducedIntentRef::kind)
        .def_rw("reference_id", &ProducedIntentRef::reference_id)
        .def_rw("target", &ProducedIntentRef::target);

    nb::class_<ActionInterfaceDescriptor>(m, "ActionInterfaceDescriptor")
        .def(nb::init<>())
        .def_rw("kind", &ActionInterfaceDescriptor::kind)
        .def_rw("payload_type", &ActionInterfaceDescriptor::payload_type);

    nb::class_<DecisionModelRef>(m, "DecisionModelRef")
        .def(nb::init<>())
        .def_rw("kind", &DecisionModelRef::kind)
        .def_rw("id", &DecisionModelRef::id);

    nb::class_<ActionHoldPolicy>(m, "ActionHoldPolicy")
        .def(nb::init<>())
        .def_rw("policy_id", &ActionHoldPolicy::policy_id)
        .def_rw("action_family", &ActionHoldPolicy::action_family)
        .def_rw("hold_mode", &ActionHoldPolicy::hold_mode)
        .def_rw("validity_duration_s", &ActionHoldPolicy::validity_duration_s)
        .def_rw("refresh_cadence_s", &ActionHoldPolicy::refresh_cadence_s)
        .def_rw("target_control_cadence_s", &ActionHoldPolicy::target_control_cadence_s)
        .def_rw("expiry_behavior", &ActionHoldPolicy::expiry_behavior)
        .def_rw("interpolation_mode", &ActionHoldPolicy::interpolation_mode)
        .def_rw("credit_assignment_latency_s", &ActionHoldPolicy::credit_assignment_latency_s)
        .def_rw("credit_assignment_attribution_note",
                &ActionHoldPolicy::credit_assignment_attribution_note)
        .def_rw("diagnostics_reason", &ActionHoldPolicy::diagnostics_reason);

    nb::class_<InformationStateSource>(m, "InformationStateSource")
        .def(nb::init<>())
        .def_rw("information_state_layer", &InformationStateSource::information_state_layer)
        .def_rw("source_label", &InformationStateSource::source_label)
        .def_rw("maintained_status", &InformationStateSource::maintained_status)
        .def_rw("observation_packet_ids", &InformationStateSource::observation_packet_ids)
        .def_rw("source_observation_versions", &InformationStateSource::source_observation_versions)
        .def_rw("diagnostics_reason", &InformationStateSource::diagnostics_reason);

    nb::class_<ConfidenceShape>(m, "ConfidenceShape")
        .def(nb::init<>())
        .def_rw("kind", &ConfidenceShape::kind)
        .def_rw("confidence", &ConfidenceShape::confidence)
        .def_rw("lower_bound", &ConfidenceShape::lower_bound)
        .def_rw("upper_bound", &ConfidenceShape::upper_bound);

    nb::class_<RoleDescriptor>(m, "RoleDescriptor")
        .def(nb::init<>())
        .def_rw("role_id", &RoleDescriptor::role_id)
        .def_rw("role_type", &RoleDescriptor::role_type);

    nb::class_<AgentAuthorityScope>(m, "AgentAuthorityScope")
        .def(nb::init<>())
        .def_rw("scope", &AgentAuthorityScope::scope)
        .def_rw("world_index", &AgentAuthorityScope::world_index)
        .def_rw("has_world_index", &AgentAuthorityScope::has_world_index)
        .def_rw("entity_ids", &AgentAuthorityScope::entity_ids)
        .def_rw("roster_id", &AgentAuthorityScope::roster_id)
        .def_rw("command_family", &AgentAuthorityScope::command_family);

    nb::class_<ActionIntentPacket>(m, "ActionIntentPacket")
        .def(nb::init<>())
        .def_rw("source_id", &ActionIntentPacket::source_id)
        .def_rw("effective_time_s", &ActionIntentPacket::effective_time_s)
        .def_rw("valid_until_s", &ActionIntentPacket::valid_until_s)
        .def_rw("target", &ActionIntentPacket::target)
        .def_rw("action_family", &ActionIntentPacket::action_family)
        .def_rw("merge_policy", &ActionIntentPacket::merge_policy)
        .def_rw("action_interface", &ActionIntentPacket::action_interface)
        .def_rw("has_pilot_action", &ActionIntentPacket::has_pilot_action)
        .def_rw("pilot_action", &ActionIntentPacket::pilot_action)
        .def_rw("has_mission_command", &ActionIntentPacket::has_mission_command)
        .def_rw("mission_command", &ActionIntentPacket::mission_command);

    nb::class_<CoordinationTargetRoster>(m, "CoordinationTargetRoster")
        .def(nb::init<>())
        .def_rw("world_index", &CoordinationTargetRoster::world_index)
        .def_rw("has_world_index", &CoordinationTargetRoster::has_world_index)
        .def_rw("roster_id", &CoordinationTargetRoster::roster_id)
        .def_rw("entity_ids", &CoordinationTargetRoster::entity_ids)
        .def_rw("role_ids", &CoordinationTargetRoster::role_ids);

    nb::class_<CoordinationIntentPacket>(m, "CoordinationIntentPacket")
        .def(nb::init<>())
        .def_rw("source_type", &CoordinationIntentPacket::source_type)
        .def_rw("source_id", &CoordinationIntentPacket::source_id)
        .def_rw("target_roster", &CoordinationIntentPacket::target_roster)
        .def_rw("update_clock", &CoordinationIntentPacket::update_clock)
        .def_rw("merge_policy", &CoordinationIntentPacket::merge_policy)
        .def_rw("produced_tasking_refs", &CoordinationIntentPacket::produced_tasking_refs)
        .def_rw("produced_leader_intent_refs",
                &CoordinationIntentPacket::produced_leader_intent_refs);

    nb::class_<AgentRole>(m, "AgentRole")
        .def(nb::init<>())
        .def_rw("role", &AgentRole::role)
        .def_rw("authority_scope", &AgentRole::authority_scope)
        .def_rw("information_state_source", &AgentRole::information_state_source)
        .def_rw("decision_model_ref", &AgentRole::decision_model_ref)
        .def_rw("action_interface", &AgentRole::action_interface);

    nb::class_<AgentRoleAuthorizationResult>(m, "AgentRoleAuthorizationResult")
        .def(nb::init<>())
        .def_rw("authorized", &AgentRoleAuthorizationResult::authorized)
        .def_rw("reason", &AgentRoleAuthorizationResult::reason);

    nb::class_<DecisionBelief>(m, "DecisionBelief")
        .def(nb::init<>())
        .def_rw("belief_id", &DecisionBelief::belief_id)
        .def_rw("information_state_layer", &DecisionBelief::information_state_layer)
        .def_rw("source_information_state", &DecisionBelief::source_information_state)
        .def_rw("source_observation_versions", &DecisionBelief::source_observation_versions)
        .def_rw("memory_or_estimator_ref", &DecisionBelief::memory_or_estimator_ref)
        .def_rw("confidence_shape", &DecisionBelief::confidence_shape)
        .def_rw("maintained_status", &DecisionBelief::maintained_status)
        .def_rw("diagnostics_reason", &DecisionBelief::diagnostics_reason)
        .def_rw("uses_truth_state", &DecisionBelief::uses_truth_state)
        .def_rw("uses_raw_ecs", &DecisionBelief::uses_raw_ecs);

    nb::class_<WorldEntityRef> world_entity_ref_class(m, "WorldEntityRef");
    world_entity_ref_class.def(nb::init<>());
#define EF_WORLD_ENTITY_REF_FIELD(type, name, default_value) \
    world_entity_ref_class.def_rw(#name, &WorldEntityRef::name);
#include "runtime/contracts/detail/world_entity_ref.inc"

    nb::class_<BatchWorldSetupRequest> batch_world_setup_request_class(
        m, "BatchWorldSetupRequest");
    batch_world_setup_request_class.def(nb::init<>());
#define EF_BATCH_WORLD_SETUP_REQUEST_FIELD(type, name, default_value) \
    batch_world_setup_request_class.def_rw(#name, &BatchWorldSetupRequest::name);
#include "runtime/facade/detail/batch_world_setup_request.inc"

    // NOTE(I26): the header field order (schema-owned, ABI/aggregate-init
    // order) declares setup_surface before rejection_reason, but this
    // binding has long registered rejection_reason first. That pre-existing
    // divergence is preserved here (parity baseline) instead of being
    // macro-expanded from the same X-macro as the header block.
    nb::class_<TypedPlatformSpawnResult>(m, "TypedPlatformSpawnResult")
        .def(nb::init<>())
        .def_rw("request_index", &TypedPlatformSpawnResult::request_index)
        .def_rw("world_index", &TypedPlatformSpawnResult::world_index)
        .def_rw("entity_id", &TypedPlatformSpawnResult::entity_id)
        .def_rw("admitted", &TypedPlatformSpawnResult::admitted)
        .def_rw("materialized", &TypedPlatformSpawnResult::materialized)
        .def_rw("fail_closed", &TypedPlatformSpawnResult::fail_closed)
        .def_rw("request_id", &TypedPlatformSpawnResult::request_id)
        .def_rw("source_type_name", &TypedPlatformSpawnResult::source_type_name)
        .def_rw("plan_id", &TypedPlatformSpawnResult::plan_id)
        .def_rw("capability_bundle_id", &TypedPlatformSpawnResult::capability_bundle_id)
        .def_rw("rejection_reason", &TypedPlatformSpawnResult::rejection_reason)
        .def_rw("setup_surface", &TypedPlatformSpawnResult::setup_surface)
        .def_rw("errors", &TypedPlatformSpawnResult::errors)
        .def_rw("evidence_refs", &TypedPlatformSpawnResult::evidence_refs);

    nb::class_<BatchWorldSetupResult> batch_world_setup_result_class(m, "BatchWorldSetupResult");
    batch_world_setup_result_class.def(nb::init<>());
#define EF_BATCH_WORLD_SETUP_RESULT_FIELD(type, name, default_value) \
    batch_world_setup_result_class.def_rw(#name, &BatchWorldSetupResult::name);
#include "runtime/facade/detail/batch_world_setup_result.inc"

    nb::class_<RuntimeWorldLayoutRequest> runtime_world_layout_request_class(
        m, "RuntimeWorldLayoutRequest");
    runtime_world_layout_request_class.def(nb::init<>());
#define EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(type, name, default_value) \
    runtime_world_layout_request_class.def_rw(#name, &RuntimeWorldLayoutRequest::name);
#include "runtime/facade/detail/runtime_world_layout_request.inc"

    nb::class_<RuntimeWorldLayoutResult> runtime_world_layout_result_class(
        m, "RuntimeWorldLayoutResult");
    runtime_world_layout_result_class.def(nb::init<>());
#define EF_RUNTIME_WORLD_LAYOUT_RESULT_FIELD(type, name, default_value) \
    runtime_world_layout_result_class.def_rw(#name, &RuntimeWorldLayoutResult::name);
#include "runtime/facade/detail/runtime_world_layout_result.inc"

    nb::class_<RuntimeCounterfactualBranchRequest> runtime_counterfactual_branch_request_class(
        m, "RuntimeCounterfactualBranchRequest");
    runtime_counterfactual_branch_request_class.def(nb::init<>());
#define EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(type, name, default_value) \
    runtime_counterfactual_branch_request_class.def_rw( \
        #name, &RuntimeCounterfactualBranchRequest::name);
#include "runtime/facade/detail/runtime_counterfactual_branch_request.inc"

    nb::class_<RuntimeCounterfactualRestoreRequest> runtime_counterfactual_restore_request_class(
        m, "RuntimeCounterfactualRestoreRequest");
    runtime_counterfactual_restore_request_class.def(nb::init<>());
#define EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD(type, name, default_value) \
    runtime_counterfactual_restore_request_class.def_rw( \
        #name, &RuntimeCounterfactualRestoreRequest::name);
#include "runtime/facade/detail/runtime_counterfactual_restore_request.inc"

    nb::class_<RuntimeCounterfactualRestoreResult> runtime_counterfactual_restore_result_class(
        m, "RuntimeCounterfactualRestoreResult");
    runtime_counterfactual_restore_result_class.def(nb::init<>());
#define EF_RUNTIME_COUNTERFACTUAL_RESTORE_RESULT_FIELD(type, name, default_value) \
    runtime_counterfactual_restore_result_class.def_rw( \
        #name, &RuntimeCounterfactualRestoreResult::name);
#include "runtime/facade/detail/runtime_counterfactual_restore_result.inc"

    nb::class_<RuntimeCounterfactualBranchResult> runtime_counterfactual_branch_result_class(
        m, "RuntimeCounterfactualBranchResult");
    runtime_counterfactual_branch_result_class.def(nb::init<>());
#define EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD(type, name, default_value) \
    runtime_counterfactual_branch_result_class.def_rw( \
        #name, &RuntimeCounterfactualBranchResult::name);
#include "runtime/facade/detail/runtime_counterfactual_branch_result.inc"

    nb::class_<RuntimeExperimentStepRequest> runtime_experiment_step_request_class(
        m, "RuntimeExperimentStepRequest");
    runtime_experiment_step_request_class.def(nb::init<>());
#define EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD(type, name, default_value) \
    runtime_experiment_step_request_class.def_rw(#name, &RuntimeExperimentStepRequest::name);
#include "runtime/facade/detail/runtime_experiment_step_request.inc"

    nb::class_<RuntimeExperimentRequest> runtime_experiment_request_class(
        m, "RuntimeExperimentRequest");
    runtime_experiment_request_class.def(nb::init<>());
#define EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(type, name, default_value) \
    runtime_experiment_request_class.def_rw(#name, &RuntimeExperimentRequest::name);
#include "runtime/facade/detail/runtime_experiment_request.inc"

    nb::class_<ObservationBatchRequest> observation_batch_request_class(
        m, "ObservationBatchRequest");
    observation_batch_request_class.def(nb::init<>());
#define EF_OBSERVATION_BATCH_REQUEST_FIELD(type, name, default_value) \
    observation_batch_request_class.def_rw(#name, &ObservationBatchRequest::name);
#include "runtime/facade/detail/observation_batch_request.inc"

    nb::class_<TaskingBatchRequest> tasking_batch_request_class(m, "TaskingBatchRequest");
    tasking_batch_request_class.def(nb::init<>());
#define EF_TASKING_BATCH_REQUEST_FIELD(type, name, default_value) \
    tasking_batch_request_class.def_rw(#name, &TaskingBatchRequest::name);
#include "runtime/facade/detail/tasking_batch_request.inc"

    nb::class_<EngagementBatchRequest>(m, "EngagementBatchRequest")
        .def(nb::init<>())
        .def_rw("refs", &EngagementBatchRequest::refs)
        .def_rw("trace_ids", &EngagementBatchRequest::trace_ids)
        .def_rw("include_track_packets", &EngagementBatchRequest::include_track_packets)
        .def_rw("include_launch_requests", &EngagementBatchRequest::include_launch_requests)
        .def_rw("include_launch_events", &EngagementBatchRequest::include_launch_events)
        .def_rw("include_munition_lifecycle_packets",
                &EngagementBatchRequest::include_munition_lifecycle_packets)
        .def_rw("include_effects_events", &EngagementBatchRequest::include_effects_events)
        .def_rw("include_damage_reports", &EngagementBatchRequest::include_damage_reports)
        .def_rw("include_diagnostics_traces", &EngagementBatchRequest::include_diagnostics_traces);

    nb::class_<ExecutionBatchStepRequest> execution_batch_step_request_class(
        m, "ExecutionBatchStepRequest");
    execution_batch_step_request_class.def(nb::init<>());
#define EF_EXECUTION_BATCH_STEP_REQUEST_FIELD(type, name, default_value) \
    execution_batch_step_request_class.def_rw(#name, &ExecutionBatchStepRequest::name);
#include "runtime/facade/detail/execution_batch_step_request.inc"

    nb::class_<RewardTerm> reward_term_class(m, "RewardTerm");
    reward_term_class.def(nb::init<>());
#define EF_REWARD_TERM_FIELD(type, name, default_value) \
    reward_term_class.def_rw(#name, &RewardTerm::name);
#include "runtime/contracts/detail/reward_term.inc"

    nb::class_<RewardReport> reward_report_class(m, "RewardReport");
    reward_report_class.def(nb::init<>());
#define EF_REWARD_REPORT_FIELD(type, name, default_value) \
    reward_report_class.def_rw(#name, &RewardReport::name);
#include "runtime/contracts/detail/reward_report.inc"

    nb::class_<TerminationSpec> termination_spec_class(m, "TerminationSpec");
    termination_spec_class.def(nb::init<>());
#define EF_TERMINATION_SPEC_FIELD(type, name, default_value) \
    termination_spec_class.def_rw(#name, &TerminationSpec::name);
#include "runtime/contracts/detail/termination_spec.inc"

    nb::class_<ObservationViewSpec> observation_view_spec_class(m, "ObservationViewSpec");
    observation_view_spec_class.def(nb::init<>());
#define EF_OBSERVATION_VIEW_SPEC_FIELD(type, name, default_value) \
    observation_view_spec_class.def_rw(#name, &ObservationViewSpec::name);
#include "runtime/contracts/detail/observation_view_spec.inc"

    nb::class_<ObservationViewCompatibilityReport> observation_view_compatibility_report_class(
        m, "ObservationViewCompatibilityReport");
    observation_view_compatibility_report_class.def(nb::init<>());
#define EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD(type, name, default_value) \
    observation_view_compatibility_report_class.def_rw( \
        #name, &ObservationViewCompatibilityReport::name);
#include "runtime/contracts/detail/observation_view_compatibility_report.inc"

    m.def("evaluate_observation_view_checkpoint_compatibility",
          &evaluate_observation_view_checkpoint_compatibility, nb::arg("checkpoint"),
          nb::arg("provider"));
    m.def("make_exact_evaluation_cpu_reference_fidelity_request",
          &runtime::fidelity::make_exact_evaluation_cpu_reference_request);
    m.def("admit_fidelity_profile_request", &runtime::fidelity::admit_fidelity_profile_request,
          nb::arg("request"));
    m.def("validate_typed_platform_spawn_request", &validate_typed_platform_spawn_request,
          nb::arg("request"));
    m.def("information_state_source_has_valid_label", &information_state_source_has_valid_label,
          nb::arg("source"));
    m.def("agent_role_has_maintained_authority_shape", &agent_role_has_maintained_authority_shape,
          nb::arg("role"));
    m.def("agent_role_action_interface_matches_authority_scope",
          &agent_role_action_interface_matches_authority_scope, nb::arg("role"));
    m.def("authorize_maintained_action_intent", &authorize_maintained_action_intent,
          nb::arg("role"), nb::arg("intent"));
    m.def("authorize_maintained_coordination_intent", &authorize_maintained_coordination_intent,
          nb::arg("role"), nb::arg("intent"));
    m.def("decision_belief_requires_diagnostics_only", &decision_belief_requires_diagnostics_only,
          nb::arg("belief"));
    m.def("decision_belief_has_valid_provenance", &decision_belief_has_valid_provenance,
          nb::arg("belief"));

    nb::class_<ObservationBatchPacket> observation_batch_packet_class(m, "ObservationBatchPacket");
    observation_batch_packet_class.def(nb::init<>());
#define EF_OBSERVATION_BATCH_PACKET_FIELD(type, name, default_value) \
    observation_batch_packet_class.def_rw(#name, &ObservationBatchPacket::name);
#include "runtime/facade/detail/observation_batch_packet.inc"

    nb::class_<TaskingBatchPacket> tasking_batch_packet_class(m, "TaskingBatchPacket");
    tasking_batch_packet_class.def(nb::init<>());
#define EF_TASKING_BATCH_PACKET_FIELD(type, name, default_value) \
    tasking_batch_packet_class.def_rw(#name, &TaskingBatchPacket::name);
#include "runtime/facade/detail/tasking_batch_packet.inc"

    nb::class_<EngagementEventPacket>(m, "EngagementEventPacket")
        .def(nb::init<>())
        .def_rw("snapshot_version", &EngagementEventPacket::snapshot_version)
        .def_rw("barrier_id", &EngagementEventPacket::barrier_id)
        .def_rw("barrier_sequence", &EngagementEventPacket::barrier_sequence)
        .def_rw("barrier_detail", &EngagementEventPacket::barrier_detail)
        .def_rw("source_time_s", &EngagementEventPacket::source_time_s)
        .def_rw("producer_node_id", &EngagementEventPacket::producer_node_id)
        .def_rw("packet_provenance", &EngagementEventPacket::packet_provenance)
        .def_rw("diagnostics_provenance", &EngagementEventPacket::diagnostics_provenance)
        .def_rw("refs", &EngagementEventPacket::refs)
        .def_rw("trace_ids", &EngagementEventPacket::trace_ids)
        .def_rw("track_packets", &EngagementEventPacket::track_packets)
        .def_rw("launch_requests", &EngagementEventPacket::launch_requests)
        .def_rw("launch_events", &EngagementEventPacket::launch_events)
        .def_rw("munition_lifecycle_packets", &EngagementEventPacket::munition_lifecycle_packets)
        .def_rw("effects_events", &EngagementEventPacket::effects_events)
        .def_rw("nearest_approach_events", &EngagementEventPacket::nearest_approach_events)
        .def_rw("fuze_evaluation_events", &EngagementEventPacket::fuze_evaluation_events)
        .def_rw("warhead_mechanism_events", &EngagementEventPacket::warhead_mechanism_events)
        .def_rw("spatial_coverage_events", &EngagementEventPacket::spatial_coverage_events)
        .def_rw("component_load_events", &EngagementEventPacket::component_load_events)
        .def_rw("component_damage_events", &EngagementEventPacket::component_damage_events)
        .def_rw("platform_consequence_events", &EngagementEventPacket::platform_consequence_events)
        .def_rw("structural_breakup_events", &EngagementEventPacket::structural_breakup_events)
        .def_rw("lifecycle_transition_events", &EngagementEventPacket::lifecycle_transition_events)
        .def_rw("training_projection_events", &EngagementEventPacket::training_projection_events)
        .def_rw("damage_reports", &EngagementEventPacket::damage_reports)
        .def_rw("diagnostics_traces", &EngagementEventPacket::diagnostics_traces);

    nb::class_<ExecutionBatchStepResult>(m, "ExecutionBatchStepResult")
        .def(nb::init<>())
        .def_rw("step_results", &ExecutionBatchStepResult::step_results)
        .def_rw("execution_episode_states", &ExecutionBatchStepResult::execution_episode_states)
        .def_rw("rewards", &ExecutionBatchStepResult::rewards)
        .def_rw("terminated", &ExecutionBatchStepResult::terminated)
        .def_rw("truncated", &ExecutionBatchStepResult::truncated)
        .def_rw("status_vectors", &ExecutionBatchStepResult::status_vectors)
        .def_rw("termination_reasons", &ExecutionBatchStepResult::termination_reasons)
        .def_rw("termination_specs", &ExecutionBatchStepResult::termination_specs)
        .def_rw("reward_breakdown_jsons", &ExecutionBatchStepResult::reward_breakdown_jsons)
        .def_rw("reward_reports", &ExecutionBatchStepResult::reward_reports)
        .def_rw("step_infos", &ExecutionBatchStepResult::step_infos)
        .def_rw("step_info_valid_flags", &ExecutionBatchStepResult::step_info_valid_flags)
        .def_rw("controller_state_changed_flags",
                &ExecutionBatchStepResult::controller_state_changed_flags)
        .def_rw("observation_packet", &ExecutionBatchStepResult::observation_packet)
        .def_rw("tasking_packet", &ExecutionBatchStepResult::tasking_packet);

    nb::class_<MissionCommandSharedCoreDirective>(m, "MissionCommandSharedCoreDirective")
        .def(nb::init<>())
        .def_rw("cmd_heading_deg", &MissionCommandSharedCoreDirective::cmd_heading_deg)
        .def_rw("cmd_altitude_m", &MissionCommandSharedCoreDirective::cmd_altitude_m)
        .def_rw("cmd_speed_mps", &MissionCommandSharedCoreDirective::cmd_speed_mps)
        .def_rw("command_code", &MissionCommandSharedCoreDirective::command_code)
        .def_rw("route_ref_id", &MissionCommandSharedCoreDirective::route_ref_id)
        .def_rw("roe_state", &MissionCommandSharedCoreDirective::roe_state)
        .def_rw("engagement_authority_holder_id",
                &MissionCommandSharedCoreDirective::engagement_authority_holder_id)
        .def_rw("engagement_authority_grantor_id",
                &MissionCommandSharedCoreDirective::engagement_authority_grantor_id)
        .def_rw("assigned_target_id", &MissionCommandSharedCoreDirective::assigned_target_id)
        .def_rw("threat_state", &MissionCommandSharedCoreDirective::threat_state)
        .def_rw("assigned_target_track_id",
                &MissionCommandSharedCoreDirective::assigned_target_track_id)
        .def_rw("assigned_target_source_id",
                &MissionCommandSharedCoreDirective::assigned_target_source_id)
        .def_rw("assigned_target_snapshot_time_s",
                &MissionCommandSharedCoreDirective::assigned_target_snapshot_time_s)
        .def_rw("authorization_to_fire", &MissionCommandSharedCoreDirective::authorization_to_fire)
        .def_rw("active", &MissionCommandSharedCoreDirective::active);

    nb::class_<MissionCommandAir::RecoveryDirective>(m, "MissionCommandAirRecoveryDirective")
        .def(nb::init<>())
        .def_rw("recovery_base_id", &MissionCommandAir::RecoveryDirective::recovery_base_id)
        .def_rw("recovery_runway_id", &MissionCommandAir::RecoveryDirective::recovery_runway_id)
        .def_rw("recovery_approach_type",
                &MissionCommandAir::RecoveryDirective::recovery_approach_type);

    nb::class_<MissionCommandAir::TakeoffDirective>(m, "MissionCommandAirTakeoffDirective")
        .def(nb::init<>())
        .def_rw("takeoff_procedure_id", &MissionCommandAir::TakeoffDirective::takeoff_procedure_id)
        .def_rw("takeoff_clearance_id", &MissionCommandAir::TakeoffDirective::takeoff_clearance_id)
        .def_rw("takeoff_interval_s", &MissionCommandAir::TakeoffDirective::takeoff_interval_s)
        .def_rw("runway_slot_id", &MissionCommandAir::TakeoffDirective::runway_slot_id);

    nb::class_<MissionCommandAir::FormationDirective>(m, "MissionCommandAirFormationDirective")
        .def(nb::init<>())
        .def_rw("formation_id", &MissionCommandAir::FormationDirective::formation_id)
        .def_rw("form_offset_x", &MissionCommandAir::FormationDirective::form_offset_x)
        .def_rw("form_offset_y", &MissionCommandAir::FormationDirective::form_offset_y)
        .def_rw("form_offset_z", &MissionCommandAir::FormationDirective::form_offset_z);

    nb::class_<MissionCommandNaval::StationingDirective>(m,
                                                         "MissionCommandNavalStationingDirective")
        .def(nb::init<>())
        .def_rw("reference_entity_id",
                &MissionCommandNaval::StationingDirective::reference_entity_id)
        .def_rw("station_radius_m", &MissionCommandNaval::StationingDirective::station_radius_m)
        .def_rw("station_bearing_deg",
                &MissionCommandNaval::StationingDirective::station_bearing_deg);

    nb::class_<MissionCommandNaval::EmbarkedHeloDirective>(
        m, "MissionCommandNavalEmbarkedHeloDirective")
        .def(nb::init<>())
        .def_rw("embarked_helo_entity_id",
                &MissionCommandNaval::EmbarkedHeloDirective::embarked_helo_entity_id)
        .def_rw("launch_helo", &MissionCommandNaval::EmbarkedHeloDirective::launch_helo)
        .def_rw("recover_helo", &MissionCommandNaval::EmbarkedHeloDirective::recover_helo)
        .def_rw("relay_oth_targeting",
                &MissionCommandNaval::EmbarkedHeloDirective::relay_oth_targeting);

    nb::class_<LeaderIntentAir::RecoveryDirective>(m, "LeaderIntentAirRecoveryDirective")
        .def(nb::init<>())
        .def_rw("recovery_base_id", &LeaderIntentAir::RecoveryDirective::recovery_base_id)
        .def_rw("recovery_runway_id", &LeaderIntentAir::RecoveryDirective::recovery_runway_id)
        .def_rw("recovery_approach_type",
                &LeaderIntentAir::RecoveryDirective::recovery_approach_type);

    nb::class_<LeaderIntentAir::TakeoffDirective>(m, "LeaderIntentAirTakeoffDirective")
        .def(nb::init<>())
        .def_rw("takeoff_procedure_id", &LeaderIntentAir::TakeoffDirective::takeoff_procedure_id)
        .def_rw("takeoff_clearance_id", &LeaderIntentAir::TakeoffDirective::takeoff_clearance_id)
        .def_rw("takeoff_interval_s", &LeaderIntentAir::TakeoffDirective::takeoff_interval_s)
        .def_rw("runway_slot_id", &LeaderIntentAir::TakeoffDirective::runway_slot_id);

    nb::class_<LeaderIntentAir::FormationDirective>(m, "LeaderIntentAirFormationDirective")
        .def(nb::init<>())
        .def_rw("formation_id", &LeaderIntentAir::FormationDirective::formation_id)
        .def_rw("form_offset_x", &LeaderIntentAir::FormationDirective::form_offset_x)
        .def_rw("form_offset_y", &LeaderIntentAir::FormationDirective::form_offset_y)
        .def_rw("form_offset_z", &LeaderIntentAir::FormationDirective::form_offset_z);

    nb::class_<LeaderIntentNaval::CommandAuthorityDirective>(
        m, "LeaderIntentNavalCommandAuthorityDirective")
        .def(nb::init<>())
        .def_rw("warfare_role_code",
                &LeaderIntentNaval::CommandAuthorityDirective::warfare_role_code)
        .def_rw("officer_in_tactical_command",
                &LeaderIntentNaval::CommandAuthorityDirective::officer_in_tactical_command);

    nb::class_<PilotReportNaval::CommandAuthorityDirective>(
        m, "PilotReportNavalCommandAuthorityDirective")
        .def(nb::init<>())
        .def_rw("warfare_role_code",
                &PilotReportNaval::CommandAuthorityDirective::warfare_role_code)
        .def_rw("officer_in_tactical_command",
                &PilotReportNaval::CommandAuthorityDirective::officer_in_tactical_command);

    nb::class_<MissionCommandMaintainedBatchContract>(m, "MissionCommandMaintainedBatchContract")
        .def(nb::init<>())
        .def_rw("shared_core", &MissionCommandMaintainedBatchContract::shared_core)
        .def_rw("air_recovery", &MissionCommandMaintainedBatchContract::air_recovery)
        .def_rw("air_takeoff", &MissionCommandMaintainedBatchContract::air_takeoff)
        .def_rw("air_formation", &MissionCommandMaintainedBatchContract::air_formation)
        .def_rw("naval_stationing", &MissionCommandMaintainedBatchContract::naval_stationing)
        .def_rw("naval_embarked_helo", &MissionCommandMaintainedBatchContract::naval_embarked_helo);

    nb::class_<TaskOrderMaintainedBatchContract>(m, "TaskOrderMaintainedBatchContract")
        .def(nb::init<>())
        .def_rw("shared_core", &TaskOrderMaintainedBatchContract::shared_core)
        .def_rw("air_tasking_identity", &TaskOrderMaintainedBatchContract::air_tasking_identity)
        .def_rw("air_stationing", &TaskOrderMaintainedBatchContract::air_stationing)
        .def_rw("air_recovery", &TaskOrderMaintainedBatchContract::air_recovery)
        .def_rw("air_takeoff", &TaskOrderMaintainedBatchContract::air_takeoff)
        .def_rw("air_formation", &TaskOrderMaintainedBatchContract::air_formation)
        .def_rw("naval_command_authority",
                &TaskOrderMaintainedBatchContract::naval_command_authority)
        .def_rw("naval_stationing", &TaskOrderMaintainedBatchContract::naval_stationing);

    nb::class_<LeaderIntentMaintainedBatchContract>(m, "LeaderIntentMaintainedBatchContract")
        .def(nb::init<>())
        .def_rw("shared_core", &LeaderIntentMaintainedBatchContract::shared_core)
        .def_rw("phase_id", &LeaderIntentMaintainedBatchContract::phase_id)
        .def_rw("element_phase_id", &LeaderIntentMaintainedBatchContract::element_phase_id)
        .def_rw("air_recovery", &LeaderIntentMaintainedBatchContract::air_recovery)
        .def_rw("formation_mode_id", &LeaderIntentMaintainedBatchContract::formation_mode_id)
        .def_rw("join_required_flag", &LeaderIntentMaintainedBatchContract::join_required_flag)
        .def_rw("rejoin_required_flag", &LeaderIntentMaintainedBatchContract::rejoin_required_flag)
        .def_rw("air_takeoff", &LeaderIntentMaintainedBatchContract::air_takeoff)
        .def_rw("air_formation", &LeaderIntentMaintainedBatchContract::air_formation)
        .def_rw("naval_command_authority",
                &LeaderIntentMaintainedBatchContract::naval_command_authority);

    nb::class_<PilotReportMaintainedBatchContract>(m, "PilotReportMaintainedBatchContract")
        .def(nb::init<>())
        .def_rw("shared_core", &PilotReportMaintainedBatchContract::shared_core)
        .def_rw("air", &PilotReportMaintainedBatchContract::air)
        .def_rw("naval_command_authority",
                &PilotReportMaintainedBatchContract::naval_command_authority);

    m.def(
        "mission_command_maintained_batch_contract",
        [](const MissionCommand &command) {
            return mission_command_maintained_batch_contract(command);
        },
        nb::arg("command"));
    m.def(
        "leader_intent_maintained_batch_contract",
        [](const LeaderIntent &intent) { return leader_intent_maintained_batch_contract(intent); },
        nb::arg("intent"));
    m.def(
        "pilot_report_maintained_batch_contract",
        [](const PilotReport &report) { return pilot_report_maintained_batch_contract(report); },
        nb::arg("report"));

    nb::class_<RuntimeExperimentAncestry> runtime_experiment_ancestry_class(
        m, "RuntimeExperimentAncestry");
    runtime_experiment_ancestry_class.def(nb::init<>());
#define EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(type, name, default_value) \
    runtime_experiment_ancestry_class.def_rw(#name, &RuntimeExperimentAncestry::name);
#include "runtime/facade/detail/runtime_experiment_ancestry.inc"

    nb::class_<RuntimeExperimentResult> runtime_experiment_result_class(
        m, "RuntimeExperimentResult");
    runtime_experiment_result_class.def(nb::init<>());
#define EF_RUNTIME_EXPERIMENT_RESULT_FIELD(type, name, default_value) \
    runtime_experiment_result_class.def_rw(#name, &RuntimeExperimentResult::name);
#include "runtime/facade/detail/runtime_experiment_result.inc"

    // NOTE(I26): RuntimeWindowActionRequest is not schema-generated. Its
    // header field list (runtime_facade_types.h) is ABI-ordered as
    // action_intent, source_layer, input_snapshot_version,
    // clock_domain_metadata, cadence_control -- but clock_domain_metadata
    // is a nested, never-bound type (no Python duplication to unify) and
    // this binding's registration order/coverage already diverges from
    // that ABI order (cadence_control before source_layer/
    // input_snapshot_version; clock_domain_metadata omitted). Left
    // hand-written and skipped from schema ownership; see the I26
    // sub-family report for the recorded skip rationale. Its nested
    // CadenceControl type is independently schema-owned below.
    nb::class_<RuntimeWindowActionRequest>(m, "RuntimeWindowActionRequest")
        .def(nb::init<>())
        .def_rw("action_intent", &RuntimeWindowActionRequest::action_intent)
        .def_rw("cadence_control", &RuntimeWindowActionRequest::cadence_control)
        .def_rw("source_layer", &RuntimeWindowActionRequest::source_layer)
        .def_rw("input_snapshot_version", &RuntimeWindowActionRequest::input_snapshot_version);

    nb::class_<RuntimeWindowInputRecord> runtime_window_input_record_class(
        m, "RuntimeWindowInputRecord");
    runtime_window_input_record_class.def(nb::init<>());
#define EF_RUNTIME_WINDOW_INPUT_RECORD_FIELD(type, name, default_value) \
    runtime_window_input_record_class.def_rw(#name, &RuntimeWindowInputRecord::name);
#include "runtime/facade/detail/runtime_window_input_record.inc"

    nb::class_<RuntimeWindowSchedulingContext> runtime_window_scheduling_context_class(
        m, "RuntimeWindowSchedulingContext");
    runtime_window_scheduling_context_class.def(nb::init<>());
#define EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD(type, name, default_value) \
    runtime_window_scheduling_context_class.def_rw(#name, &RuntimeWindowSchedulingContext::name);
#include "runtime/facade/detail/runtime_window_scheduling_context.inc"

    nb::class_<RuntimeWindowBarrierRecord> runtime_window_barrier_record_class(
        m, "RuntimeWindowBarrierRecord");
    runtime_window_barrier_record_class.def(nb::init<>());
#define EF_RUNTIME_WINDOW_BARRIER_RECORD_FIELD(type, name, default_value) \
    runtime_window_barrier_record_class.def_rw(#name, &RuntimeWindowBarrierRecord::name);
#include "runtime/facade/detail/runtime_window_barrier_record.inc"

    nb::class_<RuntimeWindowVisibilityRecord> runtime_window_visibility_record_class(
        m, "RuntimeWindowVisibilityRecord");
    runtime_window_visibility_record_class.def(nb::init<>());
#define EF_RUNTIME_WINDOW_VISIBILITY_RECORD_FIELD(type, name, default_value) \
    runtime_window_visibility_record_class.def_rw(#name, &RuntimeWindowVisibilityRecord::name);
#include "runtime/facade/detail/runtime_window_visibility_record.inc"

    // NOTE(I26): the RuntimeWindowNodeExecutionRecord/CadenceControl/
    // Cadence/CadenceConfig/CadenceTraceRecord/Request/Result bindings
    // below have long registered properties out of the header's ABI
    // declaration order (several alphabetically); left hand-written and
    // skipped from binding-side schema ownership so registration order/
    // dir() sequence stays byte-for-byte unchanged. Each struct's C++
    // field list is still schema-owned on the header side (see
    // runtime_facade_types.h); see the I26 sub-family report for the
    // recorded partial-coverage rationale.
    nb::class_<RuntimeWindowNodeExecutionRecord>(m, "RuntimeWindowNodeExecutionRecord")
        .def(nb::init<>())
        .def_rw("barrier_order", &RuntimeWindowNodeExecutionRecord::barrier_order)
        .def_rw("clock_domain", &RuntimeWindowNodeExecutionRecord::clock_domain)
        .def_rw("clock_merge_policy", &RuntimeWindowNodeExecutionRecord::clock_merge_policy)
        .def_rw("decision_barrier_id", &RuntimeWindowNodeExecutionRecord::decision_barrier_id)
        .def_rw("decision_reason", &RuntimeWindowNodeExecutionRecord::decision_reason)
        .def_rw("execution_state", &RuntimeWindowNodeExecutionRecord::execution_state)
        .def_rw("node_id", &RuntimeWindowNodeExecutionRecord::node_id)
        .def_rw("read_snapshot_policy", &RuntimeWindowNodeExecutionRecord::read_snapshot_policy)
        .def_rw("source_snapshot_version",
                &RuntimeWindowNodeExecutionRecord::source_snapshot_version)
        .def_rw("source_time_s", &RuntimeWindowNodeExecutionRecord::source_time_s)
        .def_rw("target_window_id", &RuntimeWindowNodeExecutionRecord::target_window_id)
        .def_rw("trigger_source", &RuntimeWindowNodeExecutionRecord::trigger_source)
        .def_rw("write_commit_policy", &RuntimeWindowNodeExecutionRecord::write_commit_policy)
        .def_rw("visible_input_count", &RuntimeWindowNodeExecutionRecord::visible_input_count);

    nb::class_<RuntimeWindowActionRequest::CadenceControl>(m, "RuntimeWindowCadenceControl")
        .def(nb::init<>())
        .def_rw("enabled", &RuntimeWindowActionRequest::CadenceControl::enabled)
        .def_rw("expiry_time_s", &RuntimeWindowActionRequest::CadenceControl::expiry_time_s)
        .def_rw("has_expiry_time", &RuntimeWindowActionRequest::CadenceControl::has_expiry_time)
        .def_rw("hold_policy", &RuntimeWindowActionRequest::CadenceControl::hold_policy)
        .def_rw("source_cadence_domain",
                &RuntimeWindowActionRequest::CadenceControl::source_cadence_domain)
        .def_rw("source_tick", &RuntimeWindowActionRequest::CadenceControl::source_tick);

    nb::class_<RuntimeWindowCadence>(m, "RuntimeWindowCadence")
        .def(nb::init<>())
        .def_rw("barrier_id", &RuntimeWindowCadence::barrier_id)
        .def_rw("domain", &RuntimeWindowCadence::domain)
        .def_rw("interval_s", &RuntimeWindowCadence::interval_s)
        .def_rw("merge_policy", &RuntimeWindowCadence::merge_policy)
        .def_rw("tick_count", &RuntimeWindowCadence::tick_count);

    nb::class_<RuntimeWindowCadenceConfig>(m, "RuntimeWindowCadenceConfig")
        .def(nb::init<>())
        .def_rw("domains", &RuntimeWindowCadenceConfig::domains)
        .def_rw("window_duration_s", &RuntimeWindowCadenceConfig::window_duration_s);

    nb::class_<RuntimeWindowCadenceTraceRecord>(m, "RuntimeWindowCadenceTraceRecord")
        .def(nb::init<>())
        .def_rw("barrier_id", &RuntimeWindowCadenceTraceRecord::barrier_id)
        .def_rw("cadence_merge_policy", &RuntimeWindowCadenceTraceRecord::cadence_merge_policy)
        .def_rw("clock_domain", &RuntimeWindowCadenceTraceRecord::clock_domain)
        .def_rw("clock_merge_policy", &RuntimeWindowCadenceTraceRecord::clock_merge_policy)
        .def_rw("decision", &RuntimeWindowCadenceTraceRecord::decision)
        .def_rw("decision_reason", &RuntimeWindowCadenceTraceRecord::decision_reason)
        .def_rw("deferred", &RuntimeWindowCadenceTraceRecord::deferred)
        .def_rw("diagnostics_only", &RuntimeWindowCadenceTraceRecord::diagnostics_only)
        .def_rw("domain", &RuntimeWindowCadenceTraceRecord::domain)
        .def_rw("expired", &RuntimeWindowCadenceTraceRecord::expired)
        .def_rw("held", &RuntimeWindowCadenceTraceRecord::held)
        .def_rw("node_id", &RuntimeWindowCadenceTraceRecord::node_id)
        .def_rw("relation", &RuntimeWindowCadenceTraceRecord::relation)
        .def_rw("source", &RuntimeWindowCadenceTraceRecord::source)
        .def_rw("tick", &RuntimeWindowCadenceTraceRecord::tick);

    nb::class_<RuntimeWindowRequest>(m, "RuntimeWindowRequest")
        .def(nb::init<>())
        .def_rw("window_id", &RuntimeWindowRequest::window_id)
        .def_rw("world_id", &RuntimeWindowRequest::world_id)
        .def_rw("source_time_s", &RuntimeWindowRequest::source_time_s)
        .def_rw("action_requests", &RuntimeWindowRequest::action_requests)
        .def_rw("cadence_config", &RuntimeWindowRequest::cadence_config)
        .def_rw("observation_request", &RuntimeWindowRequest::observation_request)
        .def_rw("engagement_request", &RuntimeWindowRequest::engagement_request)
        .def_rw("export_observation", &RuntimeWindowRequest::export_observation)
        .def_rw("export_engagement", &RuntimeWindowRequest::export_engagement)
        .def_rw("export_diagnostics", &RuntimeWindowRequest::export_diagnostics);

    nb::class_<RuntimeWindowResult>(m, "RuntimeWindowResult")
        .def(nb::init<>())
        .def_rw("context", &RuntimeWindowResult::context)
        .def_rw("barrier_trace", &RuntimeWindowResult::barrier_trace)
        .def_rw("cadence_config", &RuntimeWindowResult::cadence_config)
        .def_rw("cadence_trace", &RuntimeWindowResult::cadence_trace)
        .def_rw("visibility_trace", &RuntimeWindowResult::visibility_trace)
        .def_rw("executed_nodes", &RuntimeWindowResult::executed_nodes)
        .def_rw("injected_inputs", &RuntimeWindowResult::injected_inputs)
        .def_rw("observation_packet", &RuntimeWindowResult::observation_packet)
        .def_rw("engagement_packet", &RuntimeWindowResult::engagement_packet)
        .def_rw("diagnostics_traces", &RuntimeWindowResult::diagnostics_traces);

    nb::class_<WorldTerrainAssignment> world_terrain_assignment_class(
        m, "WorldTerrainAssignment");
    world_terrain_assignment_class.def(nb::init<>());
#define EF_WORLD_TERRAIN_ASSIGNMENT_FIELD(type, name, default_value) \
    world_terrain_assignment_class.def_rw(#name, &WorldTerrainAssignment::name);
#include "runtime/contracts/detail/world_terrain_assignment.inc"

    nb::class_<WorldWindAssignment> world_wind_assignment_class(m, "WorldWindAssignment");
    world_wind_assignment_class.def(nb::init<>());
#define EF_WORLD_WIND_ASSIGNMENT_FIELD(type, name, default_value) \
    world_wind_assignment_class.def_rw(#name, &WorldWindAssignment::name);
#include "runtime/contracts/detail/world_wind_assignment.inc"

    nb::class_<WorldZoneDefinition> world_zone_definition_class(m, "WorldZoneDefinition");
    world_zone_definition_class.def(nb::init<>());
#define EF_WORLD_ZONE_DEFINITION_FIELD(type, name, default_value) \
    world_zone_definition_class.def_rw(#name, &WorldZoneDefinition::name);
#include "runtime/contracts/detail/world_zone_definition.inc"

    nb::class_<WorldSpawnRequest> world_spawn_request_class(m, "WorldSpawnRequest");
    world_spawn_request_class.def(nb::init<>());
#define EF_WORLD_SPAWN_REQUEST_FIELD(type, name, default_value) \
    world_spawn_request_class.def_rw(#name, &WorldSpawnRequest::name);
#include "runtime/contracts/detail/world_spawn_request.inc"

    nb::class_<WorldPilotActionAssignment> world_pilot_action_assignment_class(
        m, "WorldPilotActionAssignment");
    world_pilot_action_assignment_class.def(nb::init<>());
#define EF_WORLD_PILOT_ACTION_ASSIGNMENT_FIELD(type, name, default_value) \
    world_pilot_action_assignment_class.def_rw(#name, &WorldPilotActionAssignment::name);
#include "runtime/contracts/detail/world_pilot_action_assignment.inc"

    nb::class_<WorldMissionCommandAssignment>(m, "WorldMissionCommandAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldMissionCommandAssignment::world_index)
        .def_rw("entity_id", &WorldMissionCommandAssignment::entity_id)
        .def_rw("command", &WorldMissionCommandAssignment::command);

    nb::class_<WorldMissionCommandMaintainedAssignment>(m,
                                                        "WorldMissionCommandMaintainedAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldMissionCommandMaintainedAssignment::world_index)
        .def_rw("entity_id", &WorldMissionCommandMaintainedAssignment::entity_id)
        .def_rw("mission_command", &WorldMissionCommandMaintainedAssignment::mission_command);

    nb::class_<WorldTaskOrderMaintainedAssignment>(m, "WorldTaskOrderMaintainedAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldTaskOrderMaintainedAssignment::world_index)
        .def_rw("entity_id", &WorldTaskOrderMaintainedAssignment::entity_id)
        .def_rw("task_order", &WorldTaskOrderMaintainedAssignment::task_order);

    nb::class_<WorldLeaderIntentAssignment>(m, "WorldLeaderIntentAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldLeaderIntentAssignment::world_index)
        .def_rw("entity_id", &WorldLeaderIntentAssignment::entity_id)
        .def_rw("intent", &WorldLeaderIntentAssignment::intent);

    nb::class_<WorldLeaderIntentMaintainedAssignment>(m, "WorldLeaderIntentMaintainedAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldLeaderIntentMaintainedAssignment::world_index)
        .def_rw("entity_id", &WorldLeaderIntentMaintainedAssignment::entity_id)
        .def_rw("leader_intent", &WorldLeaderIntentMaintainedAssignment::leader_intent);

    nb::class_<WorldPilotReportAssignment>(m, "WorldPilotReportAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldPilotReportAssignment::world_index)
        .def_rw("entity_id", &WorldPilotReportAssignment::entity_id)
        .def_rw("report", &WorldPilotReportAssignment::report);

    nb::class_<WorldPilotReportMaintainedAssignment>(m, "WorldPilotReportMaintainedAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldPilotReportMaintainedAssignment::world_index)
        .def_rw("entity_id", &WorldPilotReportMaintainedAssignment::entity_id)
        .def_rw("pilot_report", &WorldPilotReportMaintainedAssignment::pilot_report);

    nb::class_<WorldExecutionEpisodeStepRequest> world_execution_episode_step_request_class(
        m, "WorldExecutionEpisodeStepRequest");
    world_execution_episode_step_request_class.def(nb::init<>());
#define EF_WORLD_EXECUTION_EPISODE_STEP_REQUEST_FIELD(type, name, default_value) \
    world_execution_episode_step_request_class.def_rw(                           \
        #name, &WorldExecutionEpisodeStepRequest::name);
#include "runtime/contracts/detail/world_execution_episode_step_request.inc"

    nb::class_<WorldBatchRuntime>(m, "WorldBatchRuntime")
        .def(nb::init<size_t>(), nb::arg("world_count") = 0)
        .def("world_count", &WorldBatchRuntime::world_count)
        .def("resize", &WorldBatchRuntime::resize, nb::arg("world_count"))
        .def("set_worker_threads", &WorldBatchRuntime::set_worker_threads,
             nb::arg("worker_threads"))
        .def("worker_threads", &WorldBatchRuntime::worker_threads)
        .def("effective_worker_threads", &WorldBatchRuntime::effective_worker_threads)
        .def("world_raw_quarantine",
             nb::overload_cast<size_t>(&WorldBatchRuntime::world_raw_quarantine),
             nb::rv_policy::reference_internal, nb::arg("index"))
        .def("reset_batch", &WorldBatchRuntime::reset_batch,
             nb::arg("seeds") = std::vector<uint32_t>{})
        .def("step_batch", &WorldBatchRuntime::step_batch)
        .def("step_worlds", &WorldBatchRuntime::step_worlds, nb::arg("world_indices"))
        .def("load_database", &WorldBatchRuntime::load_database, nb::arg("path"))
        .def(
            "load_unit_definitions",
            [](WorldBatchRuntime &self, const std::string &path) {
                std::string error;
                bool ok = self.load_unit_definitions(path, &error);
                if (!ok && !error.empty()) {
                    spdlog::warn("WorldBatchRuntime failed to load unit definitions: {}", error);
                }
                return ok;
            },
            nb::arg("path"))
        .def("set_time_step", &WorldBatchRuntime::set_time_step, nb::arg("dt"))
        .def("set_terrain_types_batch", &WorldBatchRuntime::set_terrain_types_batch,
             nb::arg("assignments"))
        .def("set_winds_batch", &WorldBatchRuntime::set_winds_batch, nb::arg("assignments"))
        .def("clear_zones_batch", &WorldBatchRuntime::clear_zones_batch,
             nb::arg("world_indices") = std::vector<uint64_t>{})
        .def("add_zones_batch", &WorldBatchRuntime::add_zones_batch, nb::arg("zones"))
        .def("spawn_units_batch", &WorldBatchRuntime::spawn_units_batch, nb::arg("requests"))
        .def("apply_world_setup_batch", &WorldBatchRuntime::apply_world_setup_batch,
             nb::arg("seeds"), nb::arg("terrain_assignments"), nb::arg("wind_assignments"),
             nb::arg("zones"), nb::arg("requests"), nb::arg("time_steps") = std::vector<double>{})
        .def("apply_world_layout", &WorldBatchRuntime::apply_world_layout, nb::arg("world_index"),
             nb::arg("seed"), nb::arg("terrain_type"), nb::arg("wind_speed_mps"),
             nb::arg("wind_dir_from_deg"), nb::arg("wind_shear_mps_per_km"),
             nb::arg("maritime_configured"), nb::arg("sea_state"), nb::arg("wave_heading_deg"),
             nb::arg("wave_period_s"), nb::arg("zones"), nb::arg("requests"),
             nb::arg("time_steps") = std::vector<double>{})
        .def("world_time_step", &WorldBatchRuntime::world_time_step, nb::arg("world_index"))
        .def("set_pilot_actions_batch", &WorldBatchRuntime::set_pilot_actions_batch,
             nb::arg("assignments"))
        .def("apply_launch_requests_batch", &WorldBatchRuntime::apply_launch_requests_batch,
             nb::arg("requests"))
        .def("set_mission_commands_batch", &WorldBatchRuntime::set_mission_commands_batch,
             nb::arg("assignments"))
        .def("set_mission_commands_maintained_batch",
             &WorldBatchRuntime::set_mission_commands_maintained_batch, nb::arg("assignments"))
        .def("set_task_orders_maintained_batch",
             &WorldBatchRuntime::set_task_orders_maintained_batch, nb::arg("assignments"))
        .def("set_leader_intents_batch", &WorldBatchRuntime::set_leader_intents_batch,
             nb::arg("assignments"))
        .def("set_leader_intents_maintained_batch",
             &WorldBatchRuntime::set_leader_intents_maintained_batch, nb::arg("assignments"))
        .def("set_pilot_reports_batch", &WorldBatchRuntime::set_pilot_reports_batch,
             nb::arg("assignments"))
        .def("set_pilot_reports_maintained_batch",
             &WorldBatchRuntime::set_pilot_reports_maintained_batch, nb::arg("assignments"))
        .def("clear_execution_episode_controller_batch",
             &WorldBatchRuntime::clear_execution_episode_controller_batch)
        .def("prime_execution_episode_controller_batch",
             &WorldBatchRuntime::prime_execution_episode_controller_batch, nb::arg("refs"),
             nb::arg("states"))
        .def("execution_episode_controller_ready",
             &WorldBatchRuntime::execution_episode_controller_ready, nb::arg("world_index"))
        .def("export_execution_episode_states_batch",
             &WorldBatchRuntime::export_execution_episode_states_batch, nb::arg("refs"))
        .def("evaluate_execution_episode_batch",
             &WorldBatchRuntime::evaluate_execution_episode_batch, nb::arg("requests"))
        .def("step_execution_episode_batch", &WorldBatchRuntime::step_execution_episode_batch,
             nb::arg("requests"))
        .def("step_execution_episode_results_batch",
             &WorldBatchRuntime::step_execution_episode_results_batch, nb::arg("requests"))
        .def("get_agent_observations_batch", &WorldBatchRuntime::get_agent_observations_batch,
             nb::arg("refs"))
        .def("get_instrument_states_batch", &WorldBatchRuntime::get_instrument_states_batch,
             nb::arg("refs"))
        .def("get_mission_commands_batch", &WorldBatchRuntime::get_mission_commands_batch,
             nb::arg("refs"))
        .def("get_mission_commands_maintained_batch",
             &WorldBatchRuntime::get_mission_commands_maintained_batch, nb::arg("refs"))
        .def("get_task_orders_maintained_batch",
             &WorldBatchRuntime::get_task_orders_maintained_batch, nb::arg("refs"))
        .def("get_leader_intents_batch", &WorldBatchRuntime::get_leader_intents_batch,
             nb::arg("refs"))
        .def("get_leader_intents_maintained_batch",
             &WorldBatchRuntime::get_leader_intents_maintained_batch, nb::arg("refs"))
        .def("get_pilot_reports_batch", &WorldBatchRuntime::get_pilot_reports_batch,
             nb::arg("refs"))
        .def("get_pilot_reports_maintained_batch",
             &WorldBatchRuntime::get_pilot_reports_maintained_batch, nb::arg("refs"))
        .def("get_sensor_candidate_ids_batch", &WorldBatchRuntime::get_sensor_candidate_ids_batch,
             nb::arg("refs"), nb::arg("use_gpu") = false)
        .def("get_visual_candidate_ids_batch", &WorldBatchRuntime::get_visual_candidate_ids_batch,
             nb::arg("refs"), nb::arg("range_m") = 25000.0, nb::arg("use_gpu") = false)
        .def("get_comm_candidate_ids_batch", &WorldBatchRuntime::get_comm_candidate_ids_batch,
             nb::arg("refs"), nb::arg("use_gpu") = false);

    // Maintained runtime facade surface for frontend-facing batch use cases.
    nb::class_<RuntimeFacade>(m, "RuntimeFacade")
        .def(nb::init<size_t>(), nb::arg("world_count") = 0)
        .def(nb::init<const RuntimeBatchConfig &>(), nb::arg("config"))
        .def("configure_batch", &RuntimeFacade::configure_batch, nb::arg("config"))
        .def("batch_config", &RuntimeFacade::batch_config)
        .def("capabilities", &RuntimeFacade::capabilities)
        .def("admit_fidelity_request", &RuntimeFacade::admit_fidelity_request, nb::arg("request"))
        .def("snapshot_counterfactual_entity", &RuntimeFacade::snapshot_counterfactual_entity,
             nb::arg("ref"), nb::arg("fidelity_admission"), nb::arg("cadence_reason"),
             nb::arg("evidence_refs"))
        .def("restore_counterfactual_snapshot", &RuntimeFacade::restore_counterfactual_snapshot,
             nb::arg("request"))
        .def("run_counterfactual_branch", &RuntimeFacade::run_counterfactual_branch,
             nb::arg("request"))
        .def("run_counterfactual_experiment", &RuntimeFacade::run_counterfactual_experiment,
             nb::arg("request"))
        .def("world_count", &RuntimeFacade::world_count)
        .def("resize", &RuntimeFacade::resize, nb::arg("world_count"))
        .def("set_worker_threads", &RuntimeFacade::set_worker_threads, nb::arg("worker_threads"))
        .def("worker_threads", &RuntimeFacade::worker_threads)
        .def("effective_worker_threads", &RuntimeFacade::effective_worker_threads)
        .def("load_database", &RuntimeFacade::load_database, nb::arg("path"))
        .def(
            "load_unit_definitions",
            [](RuntimeFacade &self, const std::string &path) {
                std::string error;
                bool ok = self.load_unit_definitions(path, &error);
                if (!ok && !error.empty()) {
                    spdlog::warn("RuntimeFacade failed to load unit definitions: {}", error);
                }
                return ok;
            },
            nb::arg("path"))
        .def("reset_batch", [](RuntimeFacade &self) { self.reset_batch(BatchResetRequest{}); })
        .def("reset_batch", &RuntimeFacade::reset_batch, nb::arg("request"))
        .def("step_batch", &RuntimeFacade::step_batch)
        .def("apply_world_setup_batch", &RuntimeFacade::apply_world_setup_batch, nb::arg("seeds"),
             nb::arg("terrain_assignments"), nb::arg("wind_assignments"), nb::arg("zones"),
             nb::arg("requests"), nb::arg("time_steps") = std::vector<double>{})
        .def("apply_world_setup", &RuntimeFacade::apply_world_setup, nb::arg("request"))
        .def("apply_world_layout", &RuntimeFacade::apply_world_layout, nb::arg("request"))
        .def("world_time_step", &RuntimeFacade::world_time_step, nb::arg("world_index"))
        .def("get_sensor_candidate_ids_batch", &RuntimeFacade::get_sensor_candidate_ids_batch,
             nb::arg("refs"), nb::arg("use_gpu") = false)
        .def("get_visual_candidate_ids_batch", &RuntimeFacade::get_visual_candidate_ids_batch,
             nb::arg("refs"), nb::arg("range_m") = 25000.0, nb::arg("use_gpu") = false)
        .def("get_comm_candidate_ids_batch", &RuntimeFacade::get_comm_candidate_ids_batch,
             nb::arg("refs"), nb::arg("use_gpu") = false)
        .def("set_pilot_actions_batch", &RuntimeFacade::set_pilot_actions_batch,
             nb::arg("assignments"))
        .def("apply_launch_requests_batch", &RuntimeFacade::apply_launch_requests_batch,
             nb::arg("requests"))
        .def("set_mission_commands_maintained_batch",
             &RuntimeFacade::set_mission_commands_maintained_batch, nb::arg("assignments"))
        .def("set_task_orders_maintained_batch", &RuntimeFacade::set_task_orders_maintained_batch,
             nb::arg("assignments"))
        .def("set_leader_intents_maintained_batch",
             &RuntimeFacade::set_leader_intents_maintained_batch, nb::arg("assignments"))
        .def("set_pilot_reports_maintained_batch",
             &RuntimeFacade::set_pilot_reports_maintained_batch, nb::arg("assignments"))
        .def("clear_execution_episode_batch", &RuntimeFacade::clear_execution_episode_batch)
        .def("prime_execution_episode_batch", &RuntimeFacade::prime_execution_episode_batch,
             nb::arg("refs"), nb::arg("states"))
        .def("execution_episode_ready", &RuntimeFacade::execution_episode_ready,
             nb::arg("world_index"))
        .def("export_execution_episode_states", &RuntimeFacade::export_execution_episode_states,
             nb::arg("refs"))
        .def("evaluate_execution_batch", &RuntimeFacade::evaluate_execution_batch,
             nb::arg("requests"))
        .def("step_execution_products_batch", &RuntimeFacade::step_execution_products_batch,
             nb::arg("requests"))
        .def("step_execution_batch", &RuntimeFacade::step_execution_batch, nb::arg("request"))
        .def("get_agent_observations_batch", &RuntimeFacade::get_agent_observations_batch,
             nb::arg("refs"))
        .def("get_instrument_states_batch", &RuntimeFacade::get_instrument_states_batch,
             nb::arg("refs"))
        .def("get_mission_commands_maintained_batch",
             &RuntimeFacade::get_mission_commands_maintained_batch, nb::arg("refs"))
        .def("get_task_orders_maintained_batch", &RuntimeFacade::get_task_orders_maintained_batch,
             nb::arg("refs"))
        .def("get_leader_intents_maintained_batch",
             &RuntimeFacade::get_leader_intents_maintained_batch, nb::arg("refs"))
        .def("get_pilot_reports_maintained_batch",
             &RuntimeFacade::get_pilot_reports_maintained_batch, nb::arg("refs"))
        .def(
            "export_observation_packet",
            [](const RuntimeFacade &self, const std::vector<WorldEntityRef> &refs) {
                return self.export_observation_packet(refs);
            },
            nb::arg("refs"))
        .def(
            "export_observation_packet",
            [](const RuntimeFacade &self, const ObservationBatchRequest &request) {
                return self.export_observation_packet(request);
            },
            nb::arg("request"))
        .def("export_tasking_packet", &RuntimeFacade::export_tasking_packet, nb::arg("request"))
        .def("export_engagement_event_packet", &RuntimeFacade::export_engagement_event_packet,
             nb::arg("request"))
        .def("export_diagnostics_traces", &RuntimeFacade::export_diagnostics_traces,
             nb::arg("request"))
        .def("run_window", &RuntimeFacade::run_window, nb::arg("request"));
}
