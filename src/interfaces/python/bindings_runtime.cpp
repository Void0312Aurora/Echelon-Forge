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
    nb::class_<RuntimeCapabilities>(m, "RuntimeCapabilities")
        .def(nb::init<>())
        .def_rw("supports_batch_runtime", &RuntimeCapabilities::supports_batch_runtime)
        .def_rw("supports_compiled_episode_controller",
                &RuntimeCapabilities::supports_compiled_episode_controller)
        .def_rw("supports_compiled_execution_step",
                &RuntimeCapabilities::supports_compiled_execution_step)
        .def_rw("supports_gpu_visual", &RuntimeCapabilities::supports_gpu_visual)
        .def_rw("supports_gpu_observation", &RuntimeCapabilities::supports_gpu_observation)
        .def_rw("supports_gpu_flight_shaping", &RuntimeCapabilities::supports_gpu_flight_shaping)
        .def_rw("supports_device_observation_view",
                &RuntimeCapabilities::supports_device_observation_view)
        .def_rw("supports_resident_state", &RuntimeCapabilities::supports_resident_state)
        .def_rw("supports_exact_gpu_backend", &RuntimeCapabilities::supports_exact_gpu_backend)
        .def_rw("supports_shadow_compare", &RuntimeCapabilities::supports_shadow_compare)
        .def_rw("maintained_baseline_backend_profile_id",
                &RuntimeCapabilities::maintained_baseline_backend_profile_id)
        .def_rw("maintained_baseline_parity_budget_ref",
                &RuntimeCapabilities::maintained_baseline_parity_budget_ref)
        .def_rw("maintained_baseline_profile_status",
                &RuntimeCapabilities::maintained_baseline_profile_status)
        .def_rw("device_observation_view_candidate_profile_id",
                &RuntimeCapabilities::device_observation_view_candidate_profile_id)
        .def_rw("device_observation_view_rejection_reason",
                &RuntimeCapabilities::device_observation_view_rejection_reason)
        .def_rw("exact_gpu_backend_candidate_profile_id",
                &RuntimeCapabilities::exact_gpu_backend_candidate_profile_id)
        .def_rw("exact_gpu_backend_rejection_reason",
                &RuntimeCapabilities::exact_gpu_backend_rejection_reason)
        .def_rw("resident_state_candidate_profile_id",
                &RuntimeCapabilities::resident_state_candidate_profile_id)
        .def_rw("resident_state_candidate_parity_budget_ref",
                &RuntimeCapabilities::resident_state_candidate_parity_budget_ref)
        .def_rw("resident_state_rejection_reason",
                &RuntimeCapabilities::resident_state_rejection_reason)
        .def_rw("shadow_compare_candidate_profile_id",
                &RuntimeCapabilities::shadow_compare_candidate_profile_id)
        .def_rw("shadow_compare_candidate_parity_budget_ref",
                &RuntimeCapabilities::shadow_compare_candidate_parity_budget_ref)
        .def_rw("shadow_compare_rejection_reason",
                &RuntimeCapabilities::shadow_compare_rejection_reason)
        .def_rw("multi_fidelity_rejection_reason",
                &RuntimeCapabilities::multi_fidelity_rejection_reason);

    nb::class_<RuntimeBatchConfig>(m, "RuntimeBatchConfig")
        .def(nb::init<>())
        .def_rw("world_count", &RuntimeBatchConfig::world_count)
        .def_rw("worker_threads", &RuntimeBatchConfig::worker_threads);

    nb::class_<RuntimeFidelityRequest>(m, "RuntimeFidelityRequest")
        .def(nb::init<>())
        .def_rw("request_label", &RuntimeFidelityRequest::request_label)
        .def_rw("backend_profile_id", &RuntimeFidelityRequest::backend_profile_id)
        .def_rw("parity_budget_ref", &RuntimeFidelityRequest::parity_budget_ref)
        .def_rw("provider_family", &RuntimeFidelityRequest::provider_family)
        .def_rw("model_family_scope", &RuntimeFidelityRequest::model_family_scope)
        .def_rw("validation_gate", &RuntimeFidelityRequest::validation_gate)
        .def_rw("facade_evidence_refs", &RuntimeFidelityRequest::facade_evidence_refs);

    nb::class_<RuntimeFidelityAdmission>(m, "RuntimeFidelityAdmission")
        .def(nb::init<>())
        .def_rw("admitted", &RuntimeFidelityAdmission::admitted)
        .def_rw("baseline_exact_evaluation", &RuntimeFidelityAdmission::baseline_exact_evaluation)
        .def_rw("request_label", &RuntimeFidelityAdmission::request_label)
        .def_rw("backend_profile_id", &RuntimeFidelityAdmission::backend_profile_id)
        .def_rw("parity_budget_ref", &RuntimeFidelityAdmission::parity_budget_ref)
        .def_rw("requested_provider_family", &RuntimeFidelityAdmission::requested_provider_family)
        .def_rw("selected_provider_family", &RuntimeFidelityAdmission::selected_provider_family)
        .def_rw("selected_stage_node_id", &RuntimeFidelityAdmission::selected_stage_node_id)
        .def_rw("rejection_reason", &RuntimeFidelityAdmission::rejection_reason)
        .def_rw("errors", &RuntimeFidelityAdmission::errors)
        .def_rw("evidence_refs", &RuntimeFidelityAdmission::evidence_refs);

    nb::class_<RuntimeCounterfactualSnapshot>(m, "RuntimeCounterfactualSnapshot")
        .def(nb::init<>())
        .def_rw("worldline_id", &RuntimeCounterfactualSnapshot::worldline_id)
        .def_rw("parent_worldline_id", &RuntimeCounterfactualSnapshot::parent_worldline_id)
        .def_rw("deterministic_seed", &RuntimeCounterfactualSnapshot::deterministic_seed)
        .def_rw("world_index", &RuntimeCounterfactualSnapshot::world_index)
        .def_rw("entity_id", &RuntimeCounterfactualSnapshot::entity_id)
        .def_rw("x", &RuntimeCounterfactualSnapshot::x)
        .def_rw("y", &RuntimeCounterfactualSnapshot::y)
        .def_rw("z", &RuntimeCounterfactualSnapshot::z)
        .def_rw("vx", &RuntimeCounterfactualSnapshot::vx)
        .def_rw("vy", &RuntimeCounterfactualSnapshot::vy)
        .def_rw("vz", &RuntimeCounterfactualSnapshot::vz)
        .def_rw("heading", &RuntimeCounterfactualSnapshot::heading)
        .def_rw("pitch", &RuntimeCounterfactualSnapshot::pitch)
        .def_rw("roll", &RuntimeCounterfactualSnapshot::roll)
        .def_rw("snapshot_version", &RuntimeCounterfactualSnapshot::snapshot_version)
        .def_rw("barrier_id", &RuntimeCounterfactualSnapshot::barrier_id)
        .def_rw("fidelity_profile_id", &RuntimeCounterfactualSnapshot::fidelity_profile_id)
        .def_rw("provider_family", &RuntimeCounterfactualSnapshot::provider_family)
        .def_rw("selected_stage_node_id", &RuntimeCounterfactualSnapshot::selected_stage_node_id)
        .def_rw("cadence_reason", &RuntimeCounterfactualSnapshot::cadence_reason)
        .def_rw("evidence_refs", &RuntimeCounterfactualSnapshot::evidence_refs);

    nb::class_<RuntimeWorldlineComparison>(m, "RuntimeWorldlineComparison")
        .def(nb::init<>())
        .def_rw("comparable", &RuntimeWorldlineComparison::comparable)
        .def_rw("comparison_id", &RuntimeWorldlineComparison::comparison_id)
        .def_rw("parent_worldline_id", &RuntimeWorldlineComparison::parent_worldline_id)
        .def_rw("branch_worldline_id", &RuntimeWorldlineComparison::branch_worldline_id)
        .def_rw("barrier_id", &RuntimeWorldlineComparison::barrier_id)
        .def_rw("dx", &RuntimeWorldlineComparison::dx)
        .def_rw("dy", &RuntimeWorldlineComparison::dy)
        .def_rw("dz", &RuntimeWorldlineComparison::dz)
        .def_rw("dvx", &RuntimeWorldlineComparison::dvx)
        .def_rw("dvy", &RuntimeWorldlineComparison::dvy)
        .def_rw("dvz", &RuntimeWorldlineComparison::dvz)
        .def_rw("dheading", &RuntimeWorldlineComparison::dheading)
        .def_rw("evidence_refs", &RuntimeWorldlineComparison::evidence_refs);

    nb::class_<DeviceResidentOutputDescriptor>(m, "DeviceResidentOutputDescriptor")
        .def(nb::init<>())
        .def_rw("output_shape", &DeviceResidentOutputDescriptor::output_shape)
        .def_rw("dtype", &DeviceResidentOutputDescriptor::dtype)
        .def_rw("element_count", &DeviceResidentOutputDescriptor::element_count)
        .def_rw("source_snapshot", &DeviceResidentOutputDescriptor::source_snapshot)
        .def_rw("sync_or_export_barrier", &DeviceResidentOutputDescriptor::sync_or_export_barrier)
        .def_rw("host_visible_availability",
                &DeviceResidentOutputDescriptor::host_visible_availability)
        .def_rw("diagnostics_label", &DeviceResidentOutputDescriptor::diagnostics_label)
        .def_rw("consumer_constraints", &DeviceResidentOutputDescriptor::consumer_constraints);

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

    nb::class_<runtime::platform_capabilities::Capability>(m, "PlatformCapability")
        .def(nb::init<>())
        .def_rw("capability_id", &runtime::platform_capabilities::Capability::capability_id)
        .def_rw("family", &runtime::platform_capabilities::Capability::family)
        .def_rw("capability_type", &runtime::platform_capabilities::Capability::capability_type)
        .def_rw("implementation_ref",
                &runtime::platform_capabilities::Capability::implementation_ref)
        .def_rw("requires_capability_ids",
                &runtime::platform_capabilities::Capability::requires_capability_ids)
        .def_rw("evidence_refs", &runtime::platform_capabilities::Capability::evidence_refs)
        .def_rw("required", &runtime::platform_capabilities::Capability::required)
        .def_rw("supported", &runtime::platform_capabilities::Capability::supported)
        .def_rw("unsupported_reason",
                &runtime::platform_capabilities::Capability::unsupported_reason);

    nb::class_<runtime::platform_capabilities::CapabilityBundle>(m, "CapabilityBundle")
        .def(nb::init<>())
        .def_rw("bundle_id", &runtime::platform_capabilities::CapabilityBundle::bundle_id)
        .def_rw("source_type_name",
                &runtime::platform_capabilities::CapabilityBundle::source_type_name)
        .def_rw("capabilities", &runtime::platform_capabilities::CapabilityBundle::capabilities)
        .def_rw("template_evidence_ref",
                &runtime::platform_capabilities::CapabilityBundle::template_evidence_ref)
        .def_rw("evidence_refs", &runtime::platform_capabilities::CapabilityBundle::evidence_refs)
        .def_rw("type_name_projection_preserved",
                &runtime::platform_capabilities::CapabilityBundle::type_name_projection_preserved)
        .def_rw("diagnostics_reason",
                &runtime::platform_capabilities::CapabilityBundle::diagnostics_reason);

    nb::class_<runtime::platform_capabilities::ResolvedPlatformSpawnPlan>(
        m, "ResolvedPlatformSpawnPlan")
        .def(nb::init<>())
        .def_rw("plan_id", &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::plan_id)
        .def_rw("source_request_kind",
                &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::source_request_kind)
        .def_rw("source_type_name",
                &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::source_type_name)
        .def_rw("capability_bundle_id",
                &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::capability_bundle_id)
        .def_rw("resolved_platform_definition_ref",
                &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::
                    resolved_platform_definition_ref)
        .def_rw(
            "materialization_strategy",
            &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::materialization_strategy)
        .def_rw("template_evidence_ref",
                &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::template_evidence_ref)
        .def_rw("resolution_evidence_ref",
                &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::resolution_evidence_ref)
        .def_rw("materialization_evidence_ref",
                &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::
                    materialization_evidence_ref)
        .def_rw("evidence_refs",
                &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::evidence_refs)
        .def_rw("resolved_capabilities",
                &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::resolved_capabilities)
        .def_rw("rejected_capability_ids",
                &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::rejected_capability_ids)
        .def_rw("type_name_projection_preserved",
                &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::
                    type_name_projection_preserved)
        .def_rw("admitted", &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::admitted)
        .def_rw("rejection_reason",
                &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::rejection_reason)
        .def_rw("diagnostics_reason",
                &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::diagnostics_reason);

    nb::class_<TypedPlatformSpawnRequest>(m, "TypedPlatformSpawnRequest")
        .def(nb::init<>())
        .def_rw("world_index", &TypedPlatformSpawnRequest::world_index)
        .def_rw("side", &TypedPlatformSpawnRequest::side)
        .def_rw("request_id", &TypedPlatformSpawnRequest::request_id)
        .def_rw("source_type_name", &TypedPlatformSpawnRequest::source_type_name)
        .def_rw("entity_name", &TypedPlatformSpawnRequest::entity_name)
        .def_rw("is_agent", &TypedPlatformSpawnRequest::is_agent)
        .def_rw("x", &TypedPlatformSpawnRequest::x)
        .def_rw("y", &TypedPlatformSpawnRequest::y)
        .def_rw("z", &TypedPlatformSpawnRequest::z)
        .def_rw("heading", &TypedPlatformSpawnRequest::heading)
        .def_rw("pitch", &TypedPlatformSpawnRequest::pitch)
        .def_rw("roll", &TypedPlatformSpawnRequest::roll)
        .def_rw("vx", &TypedPlatformSpawnRequest::vx)
        .def_rw("vy", &TypedPlatformSpawnRequest::vy)
        .def_rw("vz", &TypedPlatformSpawnRequest::vz)
        .def_rw("capability_bundle", &TypedPlatformSpawnRequest::capability_bundle)
        .def_rw("resolved_spawn_plan", &TypedPlatformSpawnRequest::resolved_spawn_plan)
        .def_rw("facade_evidence_refs", &TypedPlatformSpawnRequest::facade_evidence_refs)
        .def_rw("type_name_projection_preserved",
                &TypedPlatformSpawnRequest::type_name_projection_preserved);

    nb::class_<TypedPlatformSpawnValidationResult>(m, "TypedPlatformSpawnValidationResult")
        .def(nb::init<>())
        .def_rw("valid", &TypedPlatformSpawnValidationResult::valid)
        .def_rw("fail_closed", &TypedPlatformSpawnValidationResult::fail_closed)
        .def_rw("rejection_reason", &TypedPlatformSpawnValidationResult::rejection_reason)
        .def_rw("errors", &TypedPlatformSpawnValidationResult::errors);

    nb::class_<BatchResetRequest>(m, "BatchResetRequest")
        .def(nb::init<>())
        .def_rw("seeds", &BatchResetRequest::seeds);

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
        .def_rw("trigger_radius_m", &FuzeEvaluationEvent::trigger_radius_m)
        .def_rw("contact_surface_distance_m", &FuzeEvaluationEvent::contact_surface_distance_m)
        .def_rw("contact_penetration_depth_m", &FuzeEvaluationEvent::contact_penetration_depth_m)
        .def_rw("contact_surface_tolerance_m", &FuzeEvaluationEvent::contact_surface_tolerance_m)
        .def_rw("contact_inside_hitbox", &FuzeEvaluationEvent::contact_inside_hitbox)
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
        .def_rw("fire_state", &PlatformConsequenceEvent::fire_state);

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
        .def_rw("component_threshold_scale", &ComponentMechanismLoadRow::component_threshold_scale)
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
        .def_rw("component_failure_probability",
                &ComponentMechanismLoadRow::component_failure_probability)
        .def_rw("component_failure_probability_source",
                &ComponentMechanismLoadRow::component_failure_probability_source)
        .def_rw("component_failure_probability_calibrated",
                &ComponentMechanismLoadRow::component_failure_probability_calibrated)
        .def_rw("component_failure_probability_evidence_dataset_ref",
                &ComponentMechanismLoadRow::component_failure_probability_evidence_dataset_ref)
        .def_rw("component_failure_probability_evidence_row_id",
                &ComponentMechanismLoadRow::component_failure_probability_evidence_row_id)
        .def_rw("component_failure_probability_evidence_source_ref",
                &ComponentMechanismLoadRow::component_failure_probability_evidence_source_ref)
        .def_rw("component_failure_probability_evidence_provenance",
                &ComponentMechanismLoadRow::component_failure_probability_evidence_provenance)
        .def_rw("component_failure_sample", &ComponentMechanismLoadRow::component_failure_sample)
        .def_rw("component_failure_probability_authority",
                &ComponentMechanismLoadRow::component_failure_probability_authority)
        .def_rw("component_failure_probability_component_specific",
                &ComponentMechanismLoadRow::component_failure_probability_component_specific)
        .def_rw("component_failure_probability_weapon_family",
                &ComponentMechanismLoadRow::component_failure_probability_weapon_family)
        .def_rw("component_failure_probability_aspect_bucket",
                &ComponentMechanismLoadRow::component_failure_probability_aspect_bucket)
        .def_rw("component_failure_probability_closure_bucket",
                &ComponentMechanismLoadRow::component_failure_probability_closure_bucket)
        .def_rw("component_failure_probability_miss_distance_bucket",
                &ComponentMechanismLoadRow::component_failure_probability_miss_distance_bucket)
        .def_rw("component_failure_probability_evidence_component_name",
                &ComponentMechanismLoadRow::component_failure_probability_evidence_component_name)
        .def_rw("component_failure_probability_evidence_component_system",
                &ComponentMechanismLoadRow::component_failure_probability_evidence_component_system)
        .def_rw("component_failure_probability_evidence_component_redundancy_group_id",
                &ComponentMechanismLoadRow::
                    component_failure_probability_evidence_component_redundancy_group_id)
        .def_rw("component_failure_primary_mode",
                &ComponentMechanismLoadRow::component_failure_primary_mode)
        .def_rw("component_failure_primary_mode_severity",
                &ComponentMechanismLoadRow::component_failure_primary_mode_severity)
        .def_rw("component_failure_mode_names",
                &ComponentMechanismLoadRow::component_failure_mode_names)
        .def_rw("component_failure_mode_severities",
                &ComponentMechanismLoadRow::component_failure_mode_severities)
        .def_rw("component_failure_mode_source",
                &ComponentMechanismLoadRow::component_failure_mode_source)
        .def_rw("component_failure_mode_authority",
                &ComponentMechanismLoadRow::component_failure_mode_authority)
        .def_rw("component_integrity_before",
                &ComponentMechanismLoadRow::component_integrity_before)
        .def_rw("component_integrity_after", &ComponentMechanismLoadRow::component_integrity_after)
        .def_rw("component_redundancy_group_availability_before",
                &ComponentMechanismLoadRow::component_redundancy_group_availability_before)
        .def_rw("component_redundancy_group_availability_after",
                &ComponentMechanismLoadRow::component_redundancy_group_availability_after)
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

    nb::class_<EffectsEvent>(m, "EffectsEvent")
        .def(nb::init<>())
        .def_rw("event_id", &EffectsEvent::event_id)
        .def_rw("munition", &EffectsEvent::munition)
        .def_rw("target", &EffectsEvent::target)
        .def_rw("trigger_type", &EffectsEvent::trigger_type)
        .def_rw("outcome_state", &EffectsEvent::outcome_state)
        .def_rw("detonation_time_s", &EffectsEvent::detonation_time_s)
        .def_rw("nearest_approach_time_s", &EffectsEvent::nearest_approach_time_s)
        .def_rw("miss_distance_m", &EffectsEvent::miss_distance_m)
        .def_rw("detonation_local_forward_m", &EffectsEvent::detonation_local_forward_m)
        .def_rw("detonation_local_right_m", &EffectsEvent::detonation_local_right_m)
        .def_rw("detonation_local_up_m", &EffectsEvent::detonation_local_up_m)
        .def_rw("detonation_heading_deg", &EffectsEvent::detonation_heading_deg)
        .def_rw("detonation_pitch_deg", &EffectsEvent::detonation_pitch_deg)
        .def_rw("detonation_roll_deg", &EffectsEvent::detonation_roll_deg)
        .def_rw("closure_mps", &EffectsEvent::closure_mps)
        .def_rw("missile_axis_forward", &EffectsEvent::missile_axis_forward)
        .def_rw("missile_axis_right", &EffectsEvent::missile_axis_right)
        .def_rw("missile_axis_up", &EffectsEvent::missile_axis_up)
        .def_rw("quality", &EffectsEvent::quality)
        .def_rw("confidence", &EffectsEvent::confidence)
        .def_rw("effect_family", &EffectsEvent::effect_family)
        .def_rw("warhead_mass_kg", &EffectsEvent::warhead_mass_kg)
        .def_rw("warhead_lethal_radius_m", &EffectsEvent::warhead_lethal_radius_m)
        .def_rw("warhead_profile_synthetic", &EffectsEvent::warhead_profile_synthetic)
        .def_rw("damage_scalar_synthetic", &EffectsEvent::damage_scalar_synthetic)
        .def_rw("fuze_type", &EffectsEvent::fuze_type)
        .def_rw("fuze_trigger_radius_m", &EffectsEvent::fuze_trigger_radius_m)
        .def_rw("fuze_delay_s", &EffectsEvent::fuze_delay_s)
        .def_rw("fuze_reliability", &EffectsEvent::fuze_reliability)
        .def_rw("fuze_profile_synthetic", &EffectsEvent::fuze_profile_synthetic)
        .def_rw("fuze_signature_source", &EffectsEvent::fuze_signature_source)
        .def_rw("fuze_target_signature", &EffectsEvent::fuze_target_signature)
        .def_rw("fuze_signature_scale", &EffectsEvent::fuze_signature_scale)
        .def_rw("fuze_effective_reliability", &EffectsEvent::fuze_effective_reliability)
        .def_rw("fuze_contact_surface_distance_m", &EffectsEvent::fuze_contact_surface_distance_m)
        .def_rw("fuze_contact_penetration_depth_m", &EffectsEvent::fuze_contact_penetration_depth_m)
        .def_rw("fuze_contact_surface_tolerance_m", &EffectsEvent::fuze_contact_surface_tolerance_m)
        .def_rw("fuze_contact_inside_hitbox", &EffectsEvent::fuze_contact_inside_hitbox)
        .def_rw("direct_hitbox_intersection", &EffectsEvent::direct_hitbox_intersection)
        .def_rw("projected_hitbox_count", &EffectsEvent::projected_hitbox_count)
        .def_rw("spatial_effect_scale", &EffectsEvent::spatial_effect_scale)
        .def_rw("mechanism_armor_scale", &EffectsEvent::mechanism_armor_scale)
        .def_rw("mechanism_exposure_scale", &EffectsEvent::mechanism_exposure_scale)
        .def_rw("mechanism_effect_scale", &EffectsEvent::mechanism_effect_scale)
        .def_rw("mechanism_fragment_energy_j", &EffectsEvent::mechanism_fragment_energy_j)
        .def_rw("mechanism_fragment_areal_density_per_m2",
                &EffectsEvent::mechanism_fragment_areal_density_per_m2)
        .def_rw("mechanism_penetration_margin", &EffectsEvent::mechanism_penetration_margin)
        .def_rw("mechanism_blast_overpressure_kpa", &EffectsEvent::mechanism_blast_overpressure_kpa)
        .def_rw("mechanism_blast_impulse_kpa_ms", &EffectsEvent::mechanism_blast_impulse_kpa_ms)
        .def_rw("mechanism_blast_scaled_distance_m_kg13",
                &EffectsEvent::mechanism_blast_scaled_distance_m_kg13)
        .def_rw("mechanism_rod_cut_margin", &EffectsEvent::mechanism_rod_cut_margin)
        .def_rw("mechanism_surface_incidence_cos", &EffectsEvent::mechanism_surface_incidence_cos)
        .def_rw("warhead_spatial_sample_count", &EffectsEvent::warhead_spatial_sample_count)
        .def_rw("warhead_spatial_hit_estimate", &EffectsEvent::warhead_spatial_hit_estimate)
        .def_rw("warhead_spatial_hit_fraction", &EffectsEvent::warhead_spatial_hit_fraction)
        .def_rw("warhead_spatial_energy_scale", &EffectsEvent::warhead_spatial_energy_scale)
        .def_rw("warhead_spatial_pattern_scale", &EffectsEvent::warhead_spatial_pattern_scale)
        .def_rw("warhead_orientation_axis_forward", &EffectsEvent::warhead_orientation_axis_forward)
        .def_rw("warhead_orientation_axis_right", &EffectsEvent::warhead_orientation_axis_right)
        .def_rw("warhead_orientation_axis_up", &EffectsEvent::warhead_orientation_axis_up)
        .def_rw("warhead_orientation_pattern_scale",
                &EffectsEvent::warhead_orientation_pattern_scale)
        .def_rw("component_threshold_scale", &EffectsEvent::component_threshold_scale)
        .def_rw("component_failure_probability", &EffectsEvent::component_failure_probability)
        .def_rw("component_failure_probability_source",
                &EffectsEvent::component_failure_probability_source)
        .def_rw("component_failure_probability_calibrated",
                &EffectsEvent::component_failure_probability_calibrated)
        .def_rw("component_failure_probability_evidence_dataset_ref",
                &EffectsEvent::component_failure_probability_evidence_dataset_ref)
        .def_rw("component_failure_probability_evidence_row_id",
                &EffectsEvent::component_failure_probability_evidence_row_id)
        .def_rw("component_failure_probability_evidence_source_ref",
                &EffectsEvent::component_failure_probability_evidence_source_ref)
        .def_rw("component_failure_probability_evidence_provenance",
                &EffectsEvent::component_failure_probability_evidence_provenance)
        .def_rw("component_failure_sample", &EffectsEvent::component_failure_sample)
        .def_rw("component_failure_count", &EffectsEvent::component_failure_count)
        .def_rw("component_hit_count", &EffectsEvent::component_hit_count)
        .def_rw("component_mechanism_load_rows", &EffectsEvent::component_mechanism_load_rows)
        .def_rw("component_primary_name", &EffectsEvent::component_primary_name)
        .def_rw("component_primary_system", &EffectsEvent::component_primary_system)
        .def_rw("component_primary_redundancy_group",
                &EffectsEvent::component_primary_redundancy_group)
        .def_rw("component_primary_critical", &EffectsEvent::component_primary_critical)
        .def_rw("component_primary_redundancy_group_id",
                &EffectsEvent::component_primary_redundancy_group_id)
        .def_rw("component_primary_integrity", &EffectsEvent::component_primary_integrity)
        .def_rw("component_primary_mechanism_fragment_energy_j",
                &EffectsEvent::component_primary_mechanism_fragment_energy_j)
        .def_rw("component_primary_mechanism_fragment_areal_density_per_m2",
                &EffectsEvent::component_primary_mechanism_fragment_areal_density_per_m2)
        .def_rw("component_primary_mechanism_penetration_margin",
                &EffectsEvent::component_primary_mechanism_penetration_margin)
        .def_rw("component_primary_mechanism_blast_overpressure_kpa",
                &EffectsEvent::component_primary_mechanism_blast_overpressure_kpa)
        .def_rw("component_primary_mechanism_blast_impulse_kpa_ms",
                &EffectsEvent::component_primary_mechanism_blast_impulse_kpa_ms)
        .def_rw("component_primary_mechanism_blast_scaled_distance_m_kg13",
                &EffectsEvent::component_primary_mechanism_blast_scaled_distance_m_kg13)
        .def_rw("component_primary_mechanism_rod_cut_margin",
                &EffectsEvent::component_primary_mechanism_rod_cut_margin)
        .def_rw("component_primary_mechanism_surface_incidence_cos",
                &EffectsEvent::component_primary_mechanism_surface_incidence_cos)
        .def_rw("component_redundancy_group_availability",
                &EffectsEvent::component_redundancy_group_availability)
        .def_rw("component_redundancy_group_member_count",
                &EffectsEvent::component_redundancy_group_member_count)
        .def_rw("component_redundancy_group_failed_count",
                &EffectsEvent::component_redundancy_group_failed_count)
        .def_rw("vulnerability_profile_present", &EffectsEvent::vulnerability_profile_present)
        .def_rw("vulnerability_profile_synthetic", &EffectsEvent::vulnerability_profile_synthetic)
        .def_rw("vulnerability_calibrated_evidence",
                &EffectsEvent::vulnerability_calibrated_evidence)
        .def_rw("vulnerability_pk_authority", &EffectsEvent::vulnerability_pk_authority)
        .def_rw("vulnerability_deterministic_fuze_authority",
                &EffectsEvent::vulnerability_deterministic_fuze_authority)
        .def_rw("vulnerability_evidence_dataset_valid",
                &EffectsEvent::vulnerability_evidence_dataset_valid)
        .def_rw("vulnerability_evidence_dataset_ref",
                &EffectsEvent::vulnerability_evidence_dataset_ref)
        .def_rw("vulnerability_calibration_status", &EffectsEvent::vulnerability_calibration_status)
        .def_rw("vulnerability_provenance", &EffectsEvent::vulnerability_provenance)
        .def_rw("vulnerability_evidence_schema_version",
                &EffectsEvent::vulnerability_evidence_schema_version)
        .def_rw("vulnerability_evidence_source_kind",
                &EffectsEvent::vulnerability_evidence_source_kind)
        .def_rw("vulnerability_evidence_source_ref",
                &EffectsEvent::vulnerability_evidence_source_ref)
        .def_rw("vulnerability_evidence_validation_artifact_ref",
                &EffectsEvent::vulnerability_evidence_validation_artifact_ref)
        .def_rw("vulnerability_evidence_validation_manifest_schema_version",
                &EffectsEvent::vulnerability_evidence_validation_manifest_schema_version)
        .def_rw("vulnerability_evidence_validation_status",
                &EffectsEvent::vulnerability_evidence_validation_status)
        .def_rw("vulnerability_evidence_validation_artifact_sha256",
                &EffectsEvent::vulnerability_evidence_validation_artifact_sha256)
        .def_rw("vulnerability_evidence_validated_surrogate_model_ref",
                &EffectsEvent::vulnerability_evidence_validated_surrogate_model_ref)
        .def_rw("vulnerability_evidence_validation_benchmark_ref",
                &EffectsEvent::vulnerability_evidence_validation_benchmark_ref)
        .def_rw("vulnerability_evidence_validation_metrics_ref",
                &EffectsEvent::vulnerability_evidence_validation_metrics_ref)
        .def_rw("vulnerability_evidence_validation_acceptance_criteria_ref",
                &EffectsEvent::vulnerability_evidence_validation_acceptance_criteria_ref)
        .def_rw("vulnerability_aspect_bucket", &EffectsEvent::vulnerability_aspect_bucket)
        .def_rw("vulnerability_family_scale", &EffectsEvent::vulnerability_family_scale)
        .def_rw("vulnerability_aspect_scale", &EffectsEvent::vulnerability_aspect_scale)
        .def_rw("vulnerability_closure_mps", &EffectsEvent::vulnerability_closure_mps)
        .def_rw("vulnerability_closure_scale", &EffectsEvent::vulnerability_closure_scale)
        .def_rw("vulnerability_miss_distance_scale",
                &EffectsEvent::vulnerability_miss_distance_scale)
        .def_rw("vulnerability_effect_scale", &EffectsEvent::vulnerability_effect_scale)
        .def_rw("vulnerability_effect_scale_source",
                &EffectsEvent::vulnerability_effect_scale_source)
        .def_rw("vulnerability_effect_scale_evidence_row_id",
                &EffectsEvent::vulnerability_effect_scale_evidence_row_id)
        .def_rw("vulnerability_effect_scale_evidence_source_ref",
                &EffectsEvent::vulnerability_effect_scale_evidence_source_ref)
        .def_rw("vulnerability_effect_scale_evidence_provenance",
                &EffectsEvent::vulnerability_effect_scale_evidence_provenance)
        .def_rw("producer_node_id", &EffectsEvent::producer_node_id);

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

    nb::class_<WorldEntityRef>(m, "WorldEntityRef")
        .def(nb::init<>())
        .def_rw("world_index", &WorldEntityRef::world_index)
        .def_rw("entity_id", &WorldEntityRef::entity_id);

    nb::class_<BatchWorldSetupRequest>(m, "BatchWorldSetupRequest")
        .def(nb::init<>())
        .def_rw("seeds", &BatchWorldSetupRequest::seeds)
        .def_rw("terrain_assignments", &BatchWorldSetupRequest::terrain_assignments)
        .def_rw("wind_assignments", &BatchWorldSetupRequest::wind_assignments)
        .def_rw("zones", &BatchWorldSetupRequest::zones)
        .def_rw("spawn_requests", &BatchWorldSetupRequest::spawn_requests)
        .def_rw("typed_platform_spawn_requests",
                &BatchWorldSetupRequest::typed_platform_spawn_requests)
        .def_rw("time_steps", &BatchWorldSetupRequest::time_steps);

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

    nb::class_<BatchWorldSetupResult>(m, "BatchWorldSetupResult")
        .def(nb::init<>())
        .def_rw("entity_ids", &BatchWorldSetupResult::entity_ids)
        .def_rw("typed_platform_spawn_results",
                &BatchWorldSetupResult::typed_platform_spawn_results);

    nb::class_<RuntimeWorldLayoutRequest>(m, "RuntimeWorldLayoutRequest")
        .def(nb::init<>())
        .def_rw("world_index", &RuntimeWorldLayoutRequest::world_index)
        .def_rw("seed", &RuntimeWorldLayoutRequest::seed)
        .def_rw("terrain_type", &RuntimeWorldLayoutRequest::terrain_type)
        .def_rw("wind_speed_mps", &RuntimeWorldLayoutRequest::wind_speed_mps)
        .def_rw("wind_dir_from_deg", &RuntimeWorldLayoutRequest::wind_dir_from_deg)
        .def_rw("wind_shear_mps_per_km", &RuntimeWorldLayoutRequest::wind_shear_mps_per_km)
        .def_rw("maritime_configured", &RuntimeWorldLayoutRequest::maritime_configured)
        .def_rw("sea_state", &RuntimeWorldLayoutRequest::sea_state)
        .def_rw("wave_heading_deg", &RuntimeWorldLayoutRequest::wave_heading_deg)
        .def_rw("wave_period_s", &RuntimeWorldLayoutRequest::wave_period_s)
        .def_rw("zones", &RuntimeWorldLayoutRequest::zones)
        .def_rw("spawn_requests", &RuntimeWorldLayoutRequest::spawn_requests)
        .def_rw("time_steps", &RuntimeWorldLayoutRequest::time_steps);

    nb::class_<RuntimeWorldLayoutResult>(m, "RuntimeWorldLayoutResult")
        .def(nb::init<>())
        .def_rw("world_index", &RuntimeWorldLayoutResult::world_index)
        .def_rw("entity_ids", &RuntimeWorldLayoutResult::entity_ids);

    nb::class_<RuntimeCounterfactualBranchRequest>(m, "RuntimeCounterfactualBranchRequest")
        .def(nb::init<>())
        .def_rw("baseline_setup", &RuntimeCounterfactualBranchRequest::baseline_setup)
        .def_rw("entity_ref", &RuntimeCounterfactualBranchRequest::entity_ref)
        .def_rw("fidelity_request", &RuntimeCounterfactualBranchRequest::fidelity_request)
        .def_rw("deterministic_seed", &RuntimeCounterfactualBranchRequest::deterministic_seed)
        .def_rw("replay_envelope_id", &RuntimeCounterfactualBranchRequest::replay_envelope_id)
        .def_rw("branch_point_id", &RuntimeCounterfactualBranchRequest::branch_point_id)
        .def_rw("branch_worldline_id", &RuntimeCounterfactualBranchRequest::branch_worldline_id)
        .def_rw("parent_worldline_id", &RuntimeCounterfactualBranchRequest::parent_worldline_id)
        .def_rw("restore_barrier_id", &RuntimeCounterfactualBranchRequest::restore_barrier_id)
        .def_rw("cadence_reason", &RuntimeCounterfactualBranchRequest::cadence_reason)
        .def_rw("mutation_dx", &RuntimeCounterfactualBranchRequest::mutation_dx)
        .def_rw("mutation_dy", &RuntimeCounterfactualBranchRequest::mutation_dy)
        .def_rw("mutation_dz", &RuntimeCounterfactualBranchRequest::mutation_dz)
        .def_rw("mutation_dvx", &RuntimeCounterfactualBranchRequest::mutation_dvx)
        .def_rw("mutation_dvy", &RuntimeCounterfactualBranchRequest::mutation_dvy)
        .def_rw("mutation_dvz", &RuntimeCounterfactualBranchRequest::mutation_dvz)
        .def_rw("mutation_dheading", &RuntimeCounterfactualBranchRequest::mutation_dheading)
        .def_rw("allow_raw_authoritative_state_mutation",
                &RuntimeCounterfactualBranchRequest::allow_raw_authoritative_state_mutation)
        .def_rw("evidence_refs", &RuntimeCounterfactualBranchRequest::evidence_refs);

    nb::class_<RuntimeCounterfactualRestoreRequest>(m, "RuntimeCounterfactualRestoreRequest")
        .def(nb::init<>())
        .def_rw("snapshot", &RuntimeCounterfactualRestoreRequest::snapshot)
        .def_rw("expected_worldline_id",
                &RuntimeCounterfactualRestoreRequest::expected_worldline_id)
        .def_rw("target_worldline_id", &RuntimeCounterfactualRestoreRequest::target_worldline_id)
        .def_rw("target_deterministic_seed",
                &RuntimeCounterfactualRestoreRequest::target_deterministic_seed)
        .def_rw("target_entity_ref", &RuntimeCounterfactualRestoreRequest::target_entity_ref)
        .def_rw("restore_barrier_id", &RuntimeCounterfactualRestoreRequest::restore_barrier_id)
        .def_rw("allow_raw_authoritative_state_mutation",
                &RuntimeCounterfactualRestoreRequest::allow_raw_authoritative_state_mutation)
        .def_rw("request_full_clone", &RuntimeCounterfactualRestoreRequest::request_full_clone)
        .def_rw("request_resident_state_restore",
                &RuntimeCounterfactualRestoreRequest::request_resident_state_restore)
        .def_rw("request_exact_gpu_restore",
                &RuntimeCounterfactualRestoreRequest::request_exact_gpu_restore)
        .def_rw("evidence_refs", &RuntimeCounterfactualRestoreRequest::evidence_refs);

    nb::class_<RuntimeCounterfactualRestoreResult>(m, "RuntimeCounterfactualRestoreResult")
        .def(nb::init<>())
        .def_rw("restored", &RuntimeCounterfactualRestoreResult::restored)
        .def_rw("rejection_reason", &RuntimeCounterfactualRestoreResult::rejection_reason)
        .def_rw("restored_snapshot", &RuntimeCounterfactualRestoreResult::restored_snapshot)
        .def_rw("evidence_refs", &RuntimeCounterfactualRestoreResult::evidence_refs);

    nb::class_<RuntimeCounterfactualBranchResult>(m, "RuntimeCounterfactualBranchResult")
        .def(nb::init<>())
        .def_rw("admitted", &RuntimeCounterfactualBranchResult::admitted)
        .def_rw("rejection_reason", &RuntimeCounterfactualBranchResult::rejection_reason)
        .def_rw("fidelity_admission", &RuntimeCounterfactualBranchResult::fidelity_admission)
        .def_rw("parent_snapshot", &RuntimeCounterfactualBranchResult::parent_snapshot)
        .def_rw("branch_snapshot", &RuntimeCounterfactualBranchResult::branch_snapshot)
        .def_rw("comparison", &RuntimeCounterfactualBranchResult::comparison)
        .def_rw("restore_result", &RuntimeCounterfactualBranchResult::restore_result)
        .def_rw("evidence_refs", &RuntimeCounterfactualBranchResult::evidence_refs);

    nb::class_<RuntimeExperimentStepRequest>(m, "RuntimeExperimentStepRequest")
        .def(nb::init<>())
        .def_rw("state", &RuntimeExperimentStepRequest::state)
        .def_rw("request", &RuntimeExperimentStepRequest::request)
        .def_rw("observation_ref", &RuntimeExperimentStepRequest::observation_ref)
        .def_rw("profile_ref", &RuntimeExperimentStepRequest::profile_ref)
        .def_rw("claim_scope", &RuntimeExperimentStepRequest::claim_scope)
        .def_rw("evidence_refs", &RuntimeExperimentStepRequest::evidence_refs);

    nb::class_<RuntimeExperimentRequest>(m, "RuntimeExperimentRequest")
        .def(nb::init<>())
        .def_rw("branch_request", &RuntimeExperimentRequest::branch_request)
        .def_rw("parent_step_requests", &RuntimeExperimentRequest::parent_step_requests)
        .def_rw("branch_step_requests", &RuntimeExperimentRequest::branch_step_requests)
        .def_rw("trace_ids", &RuntimeExperimentRequest::trace_ids)
        .def_rw("experiment_run_id", &RuntimeExperimentRequest::experiment_run_id)
        .def_rw("comparison_id", &RuntimeExperimentRequest::comparison_id)
        .def_rw("setup_ref", &RuntimeExperimentRequest::setup_ref)
        .def_rw("generation_ref", &RuntimeExperimentRequest::generation_ref)
        .def_rw("generated_input_ref", &RuntimeExperimentRequest::generated_input_ref)
        .def_rw("generated_input_kind", &RuntimeExperimentRequest::generated_input_kind)
        .def_rw("generated_input_source", &RuntimeExperimentRequest::generated_input_source)
        .def_rw("generated_input_generator_version",
                &RuntimeExperimentRequest::generated_input_generator_version)
        .def_rw("generated_input_baseline_scenario_ref",
                &RuntimeExperimentRequest::generated_input_baseline_scenario_ref)
        .def_rw("generated_input_evidence_refs",
                &RuntimeExperimentRequest::generated_input_evidence_refs)
        .def_rw("capability_refs", &RuntimeExperimentRequest::capability_refs)
        .def_rw("include_observations", &RuntimeExperimentRequest::include_observations)
        .def_rw("include_diagnostics_traces", &RuntimeExperimentRequest::include_diagnostics_traces)
        .def_rw("include_generated_input_ref",
                &RuntimeExperimentRequest::include_generated_input_ref)
        .def_rw("truth_claim", &RuntimeExperimentRequest::truth_claim)
        .def_rw("promoted_to_support", &RuntimeExperimentRequest::promoted_to_support)
        .def_rw("evidence_refs", &RuntimeExperimentRequest::evidence_refs);

    nb::class_<ObservationBatchRequest>(m, "ObservationBatchRequest")
        .def(nb::init<>())
        .def_rw("refs", &ObservationBatchRequest::refs)
        .def_rw("include_agent_observations", &ObservationBatchRequest::include_agent_observations)
        .def_rw("include_instrument_states", &ObservationBatchRequest::include_instrument_states);

    nb::class_<TaskingBatchRequest>(m, "TaskingBatchRequest")
        .def(nb::init<>())
        .def_rw("refs", &TaskingBatchRequest::refs)
        .def_rw("include_mission_command_contracts",
                &TaskingBatchRequest::include_mission_command_contracts)
        .def_rw("include_task_order_contracts", &TaskingBatchRequest::include_task_order_contracts)
        .def_rw("include_leader_intent_contracts",
                &TaskingBatchRequest::include_leader_intent_contracts)
        .def_rw("include_pilot_report_contracts",
                &TaskingBatchRequest::include_pilot_report_contracts);

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

    nb::class_<ExecutionBatchStepRequest>(m, "ExecutionBatchStepRequest")
        .def(nb::init<>())
        .def_rw("step_requests", &ExecutionBatchStepRequest::step_requests)
        .def_rw("include_agent_observations",
                &ExecutionBatchStepRequest::include_agent_observations)
        .def_rw("include_instrument_states", &ExecutionBatchStepRequest::include_instrument_states);

    nb::class_<RewardTerm>(m, "RewardTerm")
        .def(nb::init<>())
        .def_rw("name", &RewardTerm::name)
        .def_rw("value", &RewardTerm::value)
        .def_rw("term_owner", &RewardTerm::term_owner);

    nb::class_<RewardReport>(m, "RewardReport")
        .def(nb::init<>())
        .def_rw("fact_terms", &RewardReport::fact_terms)
        .def_rw("shaping_terms", &RewardReport::shaping_terms)
        .def_rw("fact_snapshot_version", &RewardReport::fact_snapshot_version)
        .def_rw("term_owner", &RewardReport::term_owner);

    nb::class_<TerminationSpec>(m, "TerminationSpec")
        .def(nb::init<>())
        .def_rw("reason", &TerminationSpec::reason)
        .def_rw("reason_source", &TerminationSpec::reason_source)
        .def_rw("snapshot_version", &TerminationSpec::snapshot_version);

    nb::class_<ObservationViewSpec>(m, "ObservationViewSpec")
        .def(nb::init<>())
        .def_rw("schema_version", &ObservationViewSpec::schema_version)
        .def_rw("required_fields", &ObservationViewSpec::required_fields)
        .def_rw("optional_fields", &ObservationViewSpec::optional_fields)
        .def_rw("reject_major_mismatch", &ObservationViewSpec::reject_major_mismatch)
        .def_rw("allow_minor_version_drift", &ObservationViewSpec::allow_minor_version_drift)
        .def_rw("allow_unknown_optional_fields",
                &ObservationViewSpec::allow_unknown_optional_fields)
        .def_rw("allow_missing_optional_fields",
                &ObservationViewSpec::allow_missing_optional_fields);

    nb::class_<ObservationViewCompatibilityReport>(m, "ObservationViewCompatibilityReport")
        .def(nb::init<>())
        .def_rw("compatible", &ObservationViewCompatibilityReport::compatible)
        .def_rw("major_compatible", &ObservationViewCompatibilityReport::major_compatible)
        .def_rw("required_fields_satisfied",
                &ObservationViewCompatibilityReport::required_fields_satisfied)
        .def_rw("optional_field_drift_allowed",
                &ObservationViewCompatibilityReport::optional_field_drift_allowed)
        .def_rw("missing_required_fields",
                &ObservationViewCompatibilityReport::missing_required_fields)
        .def_rw("unknown_optional_fields",
                &ObservationViewCompatibilityReport::unknown_optional_fields)
        .def_rw("missing_optional_fields",
                &ObservationViewCompatibilityReport::missing_optional_fields);

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

    nb::class_<ObservationBatchPacket>(m, "ObservationBatchPacket")
        .def(nb::init<>())
        .def_rw("snapshot_version", &ObservationBatchPacket::snapshot_version)
        .def_rw("barrier_id", &ObservationBatchPacket::barrier_id)
        .def_rw("source_time_s", &ObservationBatchPacket::source_time_s)
        .def_rw("provenance", &ObservationBatchPacket::provenance)
        .def_rw("refs", &ObservationBatchPacket::refs)
        .def_rw("agent_observations", &ObservationBatchPacket::agent_observations)
        .def_rw("instrument_states", &ObservationBatchPacket::instrument_states);

    nb::class_<TaskingBatchPacket>(m, "TaskingBatchPacket")
        .def(nb::init<>())
        .def_rw("snapshot_version", &TaskingBatchPacket::snapshot_version)
        .def_rw("barrier_id", &TaskingBatchPacket::barrier_id)
        .def_rw("source_time_s", &TaskingBatchPacket::source_time_s)
        .def_rw("provenance", &TaskingBatchPacket::provenance)
        .def_rw("refs", &TaskingBatchPacket::refs)
        .def_rw("mission_command_contracts", &TaskingBatchPacket::mission_command_contracts)
        .def_rw("task_order_contracts", &TaskingBatchPacket::task_order_contracts)
        .def_rw("leader_intent_contracts", &TaskingBatchPacket::leader_intent_contracts)
        .def_rw("pilot_report_contracts", &TaskingBatchPacket::pilot_report_contracts);

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

    nb::class_<RuntimeExperimentAncestry>(m, "RuntimeExperimentAncestry")
        .def(nb::init<>())
        .def_rw("evidence_bridge_valid", &RuntimeExperimentAncestry::evidence_bridge_valid)
        .def_rw("evidence_bridge_fail_closed",
                &RuntimeExperimentAncestry::evidence_bridge_fail_closed)
        .def_rw("evidence_bridge_rejection_reason",
                &RuntimeExperimentAncestry::evidence_bridge_rejection_reason)
        .def_rw("evidence_bridge_errors", &RuntimeExperimentAncestry::evidence_bridge_errors)
        .def_rw("counterfactual_request_ref",
                &RuntimeExperimentAncestry::counterfactual_request_ref)
        .def_rw("counterfactual_admission_ref",
                &RuntimeExperimentAncestry::counterfactual_admission_ref)
        .def_rw("setup_ref", &RuntimeExperimentAncestry::setup_ref)
        .def_rw("generation_ref", &RuntimeExperimentAncestry::generation_ref)
        .def_rw("replay_envelope_ref", &RuntimeExperimentAncestry::replay_envelope_ref)
        .def_rw("branch_point_ref", &RuntimeExperimentAncestry::branch_point_ref)
        .def_rw("generated_input_ref", &RuntimeExperimentAncestry::generated_input_ref)
        .def_rw("backend_profile_ref", &RuntimeExperimentAncestry::backend_profile_ref)
        .def_rw("fidelity_profile_ref", &RuntimeExperimentAncestry::fidelity_profile_ref)
        .def_rw("capability_refs", &RuntimeExperimentAncestry::capability_refs)
        .def_rw("profile_observation_refs", &RuntimeExperimentAncestry::profile_observation_refs)
        .def_rw("evidence_refs", &RuntimeExperimentAncestry::evidence_refs);

    nb::class_<RuntimeExperimentResult>(m, "RuntimeExperimentResult")
        .def(nb::init<>())
        .def_rw("admitted", &RuntimeExperimentResult::admitted)
        .def_rw("rejection_reason", &RuntimeExperimentResult::rejection_reason)
        .def_rw("branch_result", &RuntimeExperimentResult::branch_result)
        .def_rw("parent_observation_packet", &RuntimeExperimentResult::parent_observation_packet)
        .def_rw("branch_observation_packet", &RuntimeExperimentResult::branch_observation_packet)
        .def_rw("parent_step_result", &RuntimeExperimentResult::parent_step_result)
        .def_rw("branch_step_result", &RuntimeExperimentResult::branch_step_result)
        .def_rw("parent_diagnostics_traces", &RuntimeExperimentResult::parent_diagnostics_traces)
        .def_rw("branch_diagnostics_traces", &RuntimeExperimentResult::branch_diagnostics_traces)
        .def_rw("ancestry", &RuntimeExperimentResult::ancestry)
        .def_rw("evidence_refs", &RuntimeExperimentResult::evidence_refs);

    nb::class_<RuntimeWindowActionRequest>(m, "RuntimeWindowActionRequest")
        .def(nb::init<>())
        .def_rw("action_intent", &RuntimeWindowActionRequest::action_intent)
        .def_rw("cadence_control", &RuntimeWindowActionRequest::cadence_control)
        .def_rw("source_layer", &RuntimeWindowActionRequest::source_layer)
        .def_rw("input_snapshot_version", &RuntimeWindowActionRequest::input_snapshot_version);

    nb::class_<RuntimeWindowInputRecord>(m, "RuntimeWindowInputRecord")
        .def(nb::init<>())
        .def_rw("request", &RuntimeWindowInputRecord::request)
        .def_rw("reason", &RuntimeWindowInputRecord::reason);

    nb::class_<RuntimeWindowSchedulingContext>(m, "RuntimeWindowSchedulingContext")
        .def(nb::init<>())
        .def_rw("window_id", &RuntimeWindowSchedulingContext::window_id)
        .def_rw("world_id", &RuntimeWindowSchedulingContext::world_id)
        .def_rw("source_time_s", &RuntimeWindowSchedulingContext::source_time_s)
        .def_rw("barrier_sequence", &RuntimeWindowSchedulingContext::barrier_sequence)
        .def_rw("current_barrier_id", &RuntimeWindowSchedulingContext::current_barrier_id)
        .def_rw("accepted_inputs", &RuntimeWindowSchedulingContext::accepted_inputs)
        .def_rw("deferred_inputs", &RuntimeWindowSchedulingContext::deferred_inputs)
        .def_rw("rejected_inputs", &RuntimeWindowSchedulingContext::rejected_inputs)
        .def_rw("expired_inputs", &RuntimeWindowSchedulingContext::expired_inputs);

    nb::class_<RuntimeWindowBarrierRecord>(m, "RuntimeWindowBarrierRecord")
        .def(nb::init<>())
        .def_rw("sequence", &RuntimeWindowBarrierRecord::sequence)
        .def_rw("barrier_id", &RuntimeWindowBarrierRecord::barrier_id)
        .def_rw("node_id", &RuntimeWindowBarrierRecord::node_id);

    nb::class_<RuntimeWindowVisibilityRecord>(m, "RuntimeWindowVisibilityRecord")
        .def(nb::init<>())
        .def_rw("barrier_id", &RuntimeWindowVisibilityRecord::barrier_id)
        .def_rw("visible_input_count", &RuntimeWindowVisibilityRecord::visible_input_count);

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

    nb::class_<WorldTerrainAssignment>(m, "WorldTerrainAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldTerrainAssignment::world_index)
        .def_rw("terrain_type", &WorldTerrainAssignment::terrain_type);

    nb::class_<WorldWindAssignment>(m, "WorldWindAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldWindAssignment::world_index)
        .def_rw("speed_mps", &WorldWindAssignment::speed_mps)
        .def_rw("dir_from_deg", &WorldWindAssignment::dir_from_deg)
        .def_rw("shear_mps_per_km", &WorldWindAssignment::shear_mps_per_km);

    nb::class_<WorldZoneDefinition>(m, "WorldZoneDefinition")
        .def(nb::init<>())
        .def_rw("world_index", &WorldZoneDefinition::world_index)
        .def_rw("name", &WorldZoneDefinition::name)
        .def_rw("x", &WorldZoneDefinition::x)
        .def_rw("y", &WorldZoneDefinition::y)
        .def_rw("width", &WorldZoneDefinition::width)
        .def_rw("length", &WorldZoneDefinition::length)
        .def_rw("heading", &WorldZoneDefinition::heading)
        .def_rw("surface_type", &WorldZoneDefinition::surface_type);

    nb::class_<WorldSpawnRequest>(m, "WorldSpawnRequest")
        .def(nb::init<>())
        .def_rw("world_index", &WorldSpawnRequest::world_index)
        .def_rw("side", &WorldSpawnRequest::side)
        .def_rw("type_name", &WorldSpawnRequest::type_name)
        .def_rw("entity_name", &WorldSpawnRequest::entity_name)
        .def_rw("is_agent", &WorldSpawnRequest::is_agent)
        .def_rw("x", &WorldSpawnRequest::x)
        .def_rw("y", &WorldSpawnRequest::y)
        .def_rw("z", &WorldSpawnRequest::z)
        .def_rw("heading", &WorldSpawnRequest::heading)
        .def_rw("pitch", &WorldSpawnRequest::pitch)
        .def_rw("roll", &WorldSpawnRequest::roll)
        .def_rw("vx", &WorldSpawnRequest::vx)
        .def_rw("vy", &WorldSpawnRequest::vy)
        .def_rw("vz", &WorldSpawnRequest::vz)
        .def_rw("ammo_override_enabled", &WorldSpawnRequest::ammo_override_enabled)
        .def_rw("missiles_remaining", &WorldSpawnRequest::missiles_remaining)
        .def_rw("max_missiles", &WorldSpawnRequest::max_missiles)
        .def_rw("weapon_cooldown_override_enabled",
                &WorldSpawnRequest::weapon_cooldown_override_enabled)
        .def_rw("weapon_cooldown_s", &WorldSpawnRequest::weapon_cooldown_s)
        .def_rw("weapon_last_fire_time", &WorldSpawnRequest::weapon_last_fire_time);

    nb::class_<WorldPilotActionAssignment>(m, "WorldPilotActionAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldPilotActionAssignment::world_index)
        .def_rw("entity_id", &WorldPilotActionAssignment::entity_id)
        .def_rw("action", &WorldPilotActionAssignment::action);

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

    nb::class_<WorldExecutionEpisodeStepRequest>(m, "WorldExecutionEpisodeStepRequest")
        .def(nb::init<>())
        .def_rw("world_index", &WorldExecutionEpisodeStepRequest::world_index)
        .def_rw("entity_id", &WorldExecutionEpisodeStepRequest::entity_id)
        .def_rw("config", &WorldExecutionEpisodeStepRequest::config)
        .def_rw("env_state", &WorldExecutionEpisodeStepRequest::env_state);

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
        .def("run_wp10_window", &RuntimeFacade::run_wp10_window, nb::arg("request"));
}
