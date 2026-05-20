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

void bind_runtime(nb::module_& m) {
    nb::class_<RuntimeCapabilities>(m, "RuntimeCapabilities")
        .def(nb::init<>())
        .def_rw("supports_batch_runtime", &RuntimeCapabilities::supports_batch_runtime)
        .def_rw(
            "supports_compiled_episode_controller",
            &RuntimeCapabilities::supports_compiled_episode_controller
        )
        .def_rw(
            "supports_compiled_execution_step",
            &RuntimeCapabilities::supports_compiled_execution_step
        )
        .def_rw("supports_gpu_visual", &RuntimeCapabilities::supports_gpu_visual)
        .def_rw("supports_gpu_observation", &RuntimeCapabilities::supports_gpu_observation)
        .def_rw("supports_gpu_flight_shaping", &RuntimeCapabilities::supports_gpu_flight_shaping)
        .def_rw("supports_device_observation_view", &RuntimeCapabilities::supports_device_observation_view)
        .def_rw("supports_resident_state", &RuntimeCapabilities::supports_resident_state)
        .def_rw("supports_exact_gpu_backend", &RuntimeCapabilities::supports_exact_gpu_backend)
        .def_rw("supports_shadow_compare", &RuntimeCapabilities::supports_shadow_compare)
        .def_rw(
            "maintained_baseline_backend_profile_id",
            &RuntimeCapabilities::maintained_baseline_backend_profile_id
        )
        .def_rw(
            "maintained_baseline_parity_budget_ref",
            &RuntimeCapabilities::maintained_baseline_parity_budget_ref
        )
        .def_rw(
            "maintained_baseline_profile_status",
            &RuntimeCapabilities::maintained_baseline_profile_status
        )
        .def_rw(
            "device_observation_view_candidate_profile_id",
            &RuntimeCapabilities::device_observation_view_candidate_profile_id
        )
        .def_rw(
            "device_observation_view_rejection_reason",
            &RuntimeCapabilities::device_observation_view_rejection_reason
        )
        .def_rw(
            "exact_gpu_backend_candidate_profile_id",
            &RuntimeCapabilities::exact_gpu_backend_candidate_profile_id
        )
        .def_rw(
            "exact_gpu_backend_rejection_reason",
            &RuntimeCapabilities::exact_gpu_backend_rejection_reason
        )
        .def_rw(
            "resident_state_candidate_profile_id",
            &RuntimeCapabilities::resident_state_candidate_profile_id
        )
        .def_rw(
            "resident_state_candidate_parity_budget_ref",
            &RuntimeCapabilities::resident_state_candidate_parity_budget_ref
        )
        .def_rw(
            "resident_state_rejection_reason",
            &RuntimeCapabilities::resident_state_rejection_reason
        )
        .def_rw(
            "shadow_compare_candidate_profile_id",
            &RuntimeCapabilities::shadow_compare_candidate_profile_id
        )
        .def_rw(
            "shadow_compare_candidate_parity_budget_ref",
            &RuntimeCapabilities::shadow_compare_candidate_parity_budget_ref
        )
        .def_rw(
            "shadow_compare_rejection_reason",
            &RuntimeCapabilities::shadow_compare_rejection_reason
        )
        .def_rw(
            "multi_fidelity_rejection_reason",
            &RuntimeCapabilities::multi_fidelity_rejection_reason
        );

    nb::class_<RuntimeBatchConfig>(m, "RuntimeBatchConfig")
        .def(nb::init<>())
        .def_rw("world_count", &RuntimeBatchConfig::world_count)
        .def_rw("worker_threads", &RuntimeBatchConfig::worker_threads);

    nb::class_<runtime::fidelity::FidelityProfileRequest>(m, "FidelityProfileRequest")
        .def(nb::init<>())
        .def_rw("request_label", &runtime::fidelity::FidelityProfileRequest::request_label)
        .def_rw(
            "backend_profile_id",
            &runtime::fidelity::FidelityProfileRequest::backend_profile_id
        )
        .def_rw(
            "parity_budget_ref",
            &runtime::fidelity::FidelityProfileRequest::parity_budget_ref
        )
        .def_rw(
            "model_family_scope",
            &runtime::fidelity::FidelityProfileRequest::model_family_scope
        )
        .def_rw(
            "validation_gate",
            &runtime::fidelity::FidelityProfileRequest::validation_gate
        )
        .def_rw(
            "facade_evidence_refs",
            &runtime::fidelity::FidelityProfileRequest::facade_evidence_refs
        )
        .def_rw(
            "requests_adaptive_scheduling",
            &runtime::fidelity::FidelityProfileRequest::requests_adaptive_scheduling
        )
        .def_rw(
            "requests_learned_model_provider",
            &runtime::fidelity::FidelityProfileRequest::requests_learned_model_provider
        )
        .def_rw(
            "requests_approximate_execution",
            &runtime::fidelity::FidelityProfileRequest::requests_approximate_execution
        )
        .def_rw(
            "requests_exact_gpu_backend",
            &runtime::fidelity::FidelityProfileRequest::requests_exact_gpu_backend
        )
        .def_rw(
            "requests_resident_state",
            &runtime::fidelity::FidelityProfileRequest::requests_resident_state
        )
        .def_rw(
            "requests_shadow_compare",
            &runtime::fidelity::FidelityProfileRequest::requests_shadow_compare
        );

    nb::class_<runtime::fidelity::FidelityProfileAdmissionResult>(
        m,
        "FidelityProfileAdmissionResult"
    )
        .def(nb::init<>())
        .def_rw("admitted", &runtime::fidelity::FidelityProfileAdmissionResult::admitted)
        .def_rw(
            "baseline_exact_evaluation",
            &runtime::fidelity::FidelityProfileAdmissionResult::baseline_exact_evaluation
        )
        .def_rw(
            "request_label",
            &runtime::fidelity::FidelityProfileAdmissionResult::request_label
        )
        .def_rw(
            "backend_profile_id",
            &runtime::fidelity::FidelityProfileAdmissionResult::backend_profile_id
        )
        .def_rw(
            "parity_budget_ref",
            &runtime::fidelity::FidelityProfileAdmissionResult::parity_budget_ref
        )
        .def_rw(
            "rejection_reason",
            &runtime::fidelity::FidelityProfileAdmissionResult::rejection_reason
        )
        .def_rw("errors", &runtime::fidelity::FidelityProfileAdmissionResult::errors)
        .def_rw(
            "evidence_refs",
            &runtime::fidelity::FidelityProfileAdmissionResult::evidence_refs
        );

    nb::class_<runtime::platform_capabilities::Capability>(m, "PlatformCapability")
        .def(nb::init<>())
        .def_rw(
            "capability_id",
            &runtime::platform_capabilities::Capability::capability_id
        )
        .def_rw("family", &runtime::platform_capabilities::Capability::family)
        .def_rw(
            "capability_type",
            &runtime::platform_capabilities::Capability::capability_type
        )
        .def_rw(
            "implementation_ref",
            &runtime::platform_capabilities::Capability::implementation_ref
        )
        .def_rw(
            "requires_capability_ids",
            &runtime::platform_capabilities::Capability::requires_capability_ids
        )
        .def_rw(
            "evidence_refs",
            &runtime::platform_capabilities::Capability::evidence_refs
        )
        .def_rw("required", &runtime::platform_capabilities::Capability::required)
        .def_rw("supported", &runtime::platform_capabilities::Capability::supported)
        .def_rw(
            "unsupported_reason",
            &runtime::platform_capabilities::Capability::unsupported_reason
        );

    nb::class_<runtime::platform_capabilities::CapabilityBundle>(
        m,
        "CapabilityBundle"
    )
        .def(nb::init<>())
        .def_rw(
            "bundle_id",
            &runtime::platform_capabilities::CapabilityBundle::bundle_id
        )
        .def_rw(
            "source_type_name",
            &runtime::platform_capabilities::CapabilityBundle::source_type_name
        )
        .def_rw(
            "capabilities",
            &runtime::platform_capabilities::CapabilityBundle::capabilities
        )
        .def_rw(
            "template_evidence_ref",
            &runtime::platform_capabilities::CapabilityBundle::template_evidence_ref
        )
        .def_rw(
            "evidence_refs",
            &runtime::platform_capabilities::CapabilityBundle::evidence_refs
        )
        .def_rw(
            "compatibility_path_preserved",
            &runtime::platform_capabilities::CapabilityBundle::compatibility_path_preserved
        )
        .def_rw(
            "diagnostics_reason",
            &runtime::platform_capabilities::CapabilityBundle::diagnostics_reason
        );

    nb::class_<runtime::platform_capabilities::ResolvedPlatformSpawnPlan>(
        m,
        "ResolvedPlatformSpawnPlan"
    )
        .def(nb::init<>())
        .def_rw(
            "plan_id",
            &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::plan_id
        )
        .def_rw(
            "source_request_kind",
            &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::source_request_kind
        )
        .def_rw(
            "source_type_name",
            &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::source_type_name
        )
        .def_rw(
            "capability_bundle_id",
            &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::capability_bundle_id
        )
        .def_rw(
            "resolved_platform_definition_ref",
            &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::resolved_platform_definition_ref
        )
        .def_rw(
            "materialization_strategy",
            &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::materialization_strategy
        )
        .def_rw(
            "template_evidence_ref",
            &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::template_evidence_ref
        )
        .def_rw(
            "resolution_evidence_ref",
            &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::resolution_evidence_ref
        )
        .def_rw(
            "materialization_evidence_ref",
            &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::materialization_evidence_ref
        )
        .def_rw(
            "evidence_refs",
            &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::evidence_refs
        )
        .def_rw(
            "resolved_capabilities",
            &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::resolved_capabilities
        )
        .def_rw(
            "rejected_capability_ids",
            &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::rejected_capability_ids
        )
        .def_rw(
            "compatibility_path_preserved",
            &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::compatibility_path_preserved
        )
        .def_rw(
            "admitted",
            &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::admitted
        )
        .def_rw(
            "rejection_reason",
            &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::rejection_reason
        )
        .def_rw(
            "diagnostics_reason",
            &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::diagnostics_reason
        );

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
        .def_rw(
            "capability_bundle",
            &TypedPlatformSpawnRequest::capability_bundle
        )
        .def_rw(
            "resolved_spawn_plan",
            &TypedPlatformSpawnRequest::resolved_spawn_plan
        )
        .def_rw(
            "facade_evidence_refs",
            &TypedPlatformSpawnRequest::facade_evidence_refs
        )
        .def_rw(
            "compatibility_path_preserved",
            &TypedPlatformSpawnRequest::compatibility_path_preserved
        );

    nb::class_<TypedPlatformSpawnValidationResult>(
        m,
        "TypedPlatformSpawnValidationResult"
    )
        .def(nb::init<>())
        .def_rw("valid", &TypedPlatformSpawnValidationResult::valid)
        .def_rw("fail_closed", &TypedPlatformSpawnValidationResult::fail_closed)
        .def_rw(
            "rejection_reason",
            &TypedPlatformSpawnValidationResult::rejection_reason
        )
        .def_rw("errors", &TypedPlatformSpawnValidationResult::errors);

    nb::class_<BatchResetRequest>(m, "BatchResetRequest")
        .def(nb::init<>())
        .def_rw("seeds", &BatchResetRequest::seeds);

    nb::class_<EngagementEntityRef>(m, "EngagementEntityRef")
        .def(nb::init<>())
        .def_rw("world_index", &EngagementEntityRef::world_index)
        .def_rw("entity_id", &EngagementEntityRef::entity_id);

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

    nb::class_<EffectsEvent>(m, "EffectsEvent")
        .def(nb::init<>())
        .def_rw("event_id", &EffectsEvent::event_id)
        .def_rw("munition", &EffectsEvent::munition)
        .def_rw("target", &EffectsEvent::target)
        .def_rw("trigger_type", &EffectsEvent::trigger_type)
        .def_rw("outcome_state", &EffectsEvent::outcome_state)
        .def_rw("detonation_time_s", &EffectsEvent::detonation_time_s)
        .def_rw("nearest_approach_time_s", &EffectsEvent::nearest_approach_time_s)
        .def_rw("quality", &EffectsEvent::quality)
        .def_rw("confidence", &EffectsEvent::confidence)
        .def_rw("effect_family", &EffectsEvent::effect_family)
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
        .def_rw(
            "credit_assignment_latency_s",
            &ActionHoldPolicy::credit_assignment_latency_s
        )
        .def_rw(
            "credit_assignment_attribution_note",
            &ActionHoldPolicy::credit_assignment_attribution_note
        )
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
        .def_rw(
            "produced_leader_intent_refs",
            &CoordinationIntentPacket::produced_leader_intent_refs
        );

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

    nb::class_<BatchWorldSetupRequest>(m, "BatchWorldSetupRequest")
        .def(nb::init<>())
        .def_rw("seeds", &BatchWorldSetupRequest::seeds)
        .def_rw("terrain_assignments", &BatchWorldSetupRequest::terrain_assignments)
        .def_rw("wind_assignments", &BatchWorldSetupRequest::wind_assignments)
        .def_rw("zones", &BatchWorldSetupRequest::zones)
        .def_rw("spawn_requests", &BatchWorldSetupRequest::spawn_requests)
        .def_rw(
            "typed_platform_spawn_requests",
            &BatchWorldSetupRequest::typed_platform_spawn_requests
        )
        .def_rw("time_steps", &BatchWorldSetupRequest::time_steps);

    nb::class_<BatchWorldSetupResult>(m, "BatchWorldSetupResult")
        .def(nb::init<>())
        .def_rw("entity_ids", &BatchWorldSetupResult::entity_ids);

    nb::class_<ObservationBatchRequest>(m, "ObservationBatchRequest")
        .def(nb::init<>())
        .def_rw("refs", &ObservationBatchRequest::refs)
        .def_rw("include_agent_observations", &ObservationBatchRequest::include_agent_observations)
        .def_rw("include_instrument_states", &ObservationBatchRequest::include_instrument_states)
        .def_rw("include_mission_commands", &ObservationBatchRequest::include_mission_commands)
        .def_rw("include_task_orders", &ObservationBatchRequest::include_task_orders)
        .def_rw("include_leader_intents", &ObservationBatchRequest::include_leader_intents)
        .def_rw("include_pilot_reports", &ObservationBatchRequest::include_pilot_reports);

    nb::class_<EngagementBatchRequest>(m, "EngagementBatchRequest")
        .def(nb::init<>())
        .def_rw("refs", &EngagementBatchRequest::refs)
        .def_rw("trace_ids", &EngagementBatchRequest::trace_ids)
        .def_rw("include_track_packets", &EngagementBatchRequest::include_track_packets)
        .def_rw("include_launch_requests", &EngagementBatchRequest::include_launch_requests)
        .def_rw("include_launch_events", &EngagementBatchRequest::include_launch_events)
        .def_rw(
            "include_munition_lifecycle_packets",
            &EngagementBatchRequest::include_munition_lifecycle_packets
        )
        .def_rw("include_effects_events", &EngagementBatchRequest::include_effects_events)
        .def_rw("include_damage_reports", &EngagementBatchRequest::include_damage_reports)
        .def_rw("include_diagnostics_traces", &EngagementBatchRequest::include_diagnostics_traces);

    nb::class_<ExecutionBatchStepRequest>(m, "ExecutionBatchStepRequest")
        .def(nb::init<>())
        .def_rw("step_requests", &ExecutionBatchStepRequest::step_requests)
        .def_rw("include_agent_observations", &ExecutionBatchStepRequest::include_agent_observations)
        .def_rw("include_instrument_states", &ExecutionBatchStepRequest::include_instrument_states)
        .def_rw("include_mission_commands", &ExecutionBatchStepRequest::include_mission_commands)
        .def_rw("include_task_orders", &ExecutionBatchStepRequest::include_task_orders)
        .def_rw("include_leader_intents", &ExecutionBatchStepRequest::include_leader_intents)
        .def_rw("include_pilot_reports", &ExecutionBatchStepRequest::include_pilot_reports);

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
        .def_rw("allow_unknown_optional_fields", &ObservationViewSpec::allow_unknown_optional_fields)
        .def_rw("allow_missing_optional_fields", &ObservationViewSpec::allow_missing_optional_fields);

    nb::class_<ObservationViewCompatibilityReport>(m, "ObservationViewCompatibilityReport")
        .def(nb::init<>())
        .def_rw("compatible", &ObservationViewCompatibilityReport::compatible)
        .def_rw("major_compatible", &ObservationViewCompatibilityReport::major_compatible)
        .def_rw(
            "required_fields_satisfied",
            &ObservationViewCompatibilityReport::required_fields_satisfied
        )
        .def_rw(
            "optional_field_drift_allowed",
            &ObservationViewCompatibilityReport::optional_field_drift_allowed
        )
        .def_rw(
            "missing_required_fields",
            &ObservationViewCompatibilityReport::missing_required_fields
        )
        .def_rw(
            "unknown_optional_fields",
            &ObservationViewCompatibilityReport::unknown_optional_fields
        )
        .def_rw(
            "missing_optional_fields",
            &ObservationViewCompatibilityReport::missing_optional_fields
        );

    m.def(
        "evaluate_observation_view_checkpoint_compatibility",
        &evaluate_observation_view_checkpoint_compatibility,
        nb::arg("checkpoint"),
        nb::arg("provider")
    );
    m.def(
        "make_exact_evaluation_cpu_reference_fidelity_request",
        &runtime::fidelity::make_exact_evaluation_cpu_reference_request
    );
    m.def(
        "admit_fidelity_profile_request",
        &runtime::fidelity::admit_fidelity_profile_request,
        nb::arg("request")
    );
    m.def(
        "validate_typed_platform_spawn_request",
        &validate_typed_platform_spawn_request,
        nb::arg("request")
    );
    m.def(
        "information_state_source_has_valid_label",
        &information_state_source_has_valid_label,
        nb::arg("source")
    );
    m.def(
        "agent_role_has_maintained_authority_shape",
        &agent_role_has_maintained_authority_shape,
        nb::arg("role")
    );
    m.def(
        "agent_role_action_interface_matches_authority_scope",
        &agent_role_action_interface_matches_authority_scope,
        nb::arg("role")
    );
    m.def(
        "authorize_maintained_action_intent",
        &authorize_maintained_action_intent,
        nb::arg("role"),
        nb::arg("intent")
    );
    m.def(
        "authorize_maintained_coordination_intent",
        &authorize_maintained_coordination_intent,
        nb::arg("role"),
        nb::arg("intent")
    );
    m.def(
        "decision_belief_requires_diagnostics_only",
        &decision_belief_requires_diagnostics_only,
        nb::arg("belief")
    );
    m.def(
        "decision_belief_has_valid_provenance",
        &decision_belief_has_valid_provenance,
        nb::arg("belief")
    );

    nb::class_<ObservationBatchPacket>(m, "ObservationBatchPacket")
        .def(nb::init<>())
        .def_rw("snapshot_version", &ObservationBatchPacket::snapshot_version)
        .def_rw("barrier_id", &ObservationBatchPacket::barrier_id)
        .def_rw("source_time_s", &ObservationBatchPacket::source_time_s)
        .def_rw("provenance", &ObservationBatchPacket::provenance)
        .def_rw("refs", &ObservationBatchPacket::refs)
        .def_rw("agent_observations", &ObservationBatchPacket::agent_observations)
        .def_rw("instrument_states", &ObservationBatchPacket::instrument_states)
        .def_rw("mission_commands", &ObservationBatchPacket::mission_commands)
        .def_rw("task_orders", &ObservationBatchPacket::task_orders)
        .def_rw("leader_intents", &ObservationBatchPacket::leader_intents)
        .def_rw("pilot_reports", &ObservationBatchPacket::pilot_reports);

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
        .def_rw(
            "munition_lifecycle_packets",
            &EngagementEventPacket::munition_lifecycle_packets
        )
        .def_rw("effects_events", &EngagementEventPacket::effects_events)
        .def_rw("damage_reports", &EngagementEventPacket::damage_reports)
        .def_rw("diagnostics_traces", &EngagementEventPacket::diagnostics_traces);

    nb::class_<ExecutionBatchStepResult>(m, "ExecutionBatchStepResult")
        .def(nb::init<>())
        .def_rw("step_results", &ExecutionBatchStepResult::step_results)
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
        .def_rw(
            "controller_state_changed_flags",
            &ExecutionBatchStepResult::controller_state_changed_flags
        )
        .def_rw("observation_packet", &ExecutionBatchStepResult::observation_packet);

    nb::class_<WorldEntityRef>(m, "WorldEntityRef")
        .def(nb::init<>())
        .def_rw("world_index", &WorldEntityRef::world_index)
        .def_rw("entity_id", &WorldEntityRef::entity_id);

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
        .def_rw("weapon_cooldown_override_enabled", &WorldSpawnRequest::weapon_cooldown_override_enabled)
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

    nb::class_<WorldTaskOrderAssignment>(m, "WorldTaskOrderAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldTaskOrderAssignment::world_index)
        .def_rw("entity_id", &WorldTaskOrderAssignment::entity_id)
        .def_rw("order", &WorldTaskOrderAssignment::order);

    nb::class_<WorldLeaderIntentAssignment>(m, "WorldLeaderIntentAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldLeaderIntentAssignment::world_index)
        .def_rw("entity_id", &WorldLeaderIntentAssignment::entity_id)
        .def_rw("intent", &WorldLeaderIntentAssignment::intent);

    nb::class_<WorldPilotReportAssignment>(m, "WorldPilotReportAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldPilotReportAssignment::world_index)
        .def_rw("entity_id", &WorldPilotReportAssignment::entity_id)
        .def_rw("report", &WorldPilotReportAssignment::report);

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
        .def("set_worker_threads", &WorldBatchRuntime::set_worker_threads, nb::arg("worker_threads"))
        .def("worker_threads", &WorldBatchRuntime::worker_threads)
        .def("effective_worker_threads", &WorldBatchRuntime::effective_worker_threads)
        .def("world", nb::overload_cast<size_t>(&WorldBatchRuntime::world), nb::rv_policy::reference_internal, nb::arg("index"))
        .def("reset_batch", &WorldBatchRuntime::reset_batch, nb::arg("seeds") = std::vector<uint32_t>{})
        .def("step_batch", &WorldBatchRuntime::step_batch)
        .def("step_worlds", &WorldBatchRuntime::step_worlds, nb::arg("world_indices"))
        .def("load_database", &WorldBatchRuntime::load_database, nb::arg("path"))
        .def("load_unit_definitions", [](WorldBatchRuntime& self, const std::string& path) {
            std::string error;
            bool ok = self.load_unit_definitions(path, &error);
            if (!ok && !error.empty()) {
                spdlog::warn("WorldBatchRuntime failed to load unit definitions: {}", error);
            }
            return ok;
        }, nb::arg("path"))
        .def("set_time_step", &WorldBatchRuntime::set_time_step, nb::arg("dt"))
        .def("set_terrain_types_batch", &WorldBatchRuntime::set_terrain_types_batch, nb::arg("assignments"))
        .def("set_winds_batch", &WorldBatchRuntime::set_winds_batch, nb::arg("assignments"))
        .def("clear_zones_batch", &WorldBatchRuntime::clear_zones_batch, nb::arg("world_indices") = std::vector<uint64_t>{})
        .def("add_zones_batch", &WorldBatchRuntime::add_zones_batch, nb::arg("zones"))
        .def("spawn_units_batch", &WorldBatchRuntime::spawn_units_batch, nb::arg("requests"))
        .def(
            "apply_world_setup_batch",
            &WorldBatchRuntime::apply_world_setup_batch,
            nb::arg("seeds"),
            nb::arg("terrain_assignments"),
            nb::arg("wind_assignments"),
            nb::arg("zones"),
            nb::arg("requests"),
            nb::arg("time_steps") = std::vector<double>{}
        )
        .def("set_pilot_actions_batch", &WorldBatchRuntime::set_pilot_actions_batch, nb::arg("assignments"))
        .def("set_mission_commands_batch", &WorldBatchRuntime::set_mission_commands_batch, nb::arg("assignments"))
        .def("set_task_orders_batch", &WorldBatchRuntime::set_task_orders_batch, nb::arg("assignments"))
        .def("set_leader_intents_batch", &WorldBatchRuntime::set_leader_intents_batch, nb::arg("assignments"))
        .def("set_pilot_reports_batch", &WorldBatchRuntime::set_pilot_reports_batch, nb::arg("assignments"))
        .def("clear_execution_episode_controller_batch", &WorldBatchRuntime::clear_execution_episode_controller_batch)
        .def(
            "prime_execution_episode_controller_batch",
            &WorldBatchRuntime::prime_execution_episode_controller_batch,
            nb::arg("refs"),
            nb::arg("states")
        )
        .def(
            "execution_episode_controller_ready",
            &WorldBatchRuntime::execution_episode_controller_ready,
            nb::arg("world_index")
        )
        .def(
            "export_execution_episode_states_batch",
            &WorldBatchRuntime::export_execution_episode_states_batch,
            nb::arg("refs")
        )
        .def(
            "evaluate_execution_episode_batch",
            &WorldBatchRuntime::evaluate_execution_episode_batch,
            nb::arg("requests")
        )
        .def(
            "step_execution_episode_batch",
            &WorldBatchRuntime::step_execution_episode_batch,
            nb::arg("requests")
        )
        .def(
            "step_execution_episode_results_batch",
            &WorldBatchRuntime::step_execution_episode_results_batch,
            nb::arg("requests")
        )
        .def("get_agent_observations_batch", &WorldBatchRuntime::get_agent_observations_batch, nb::arg("refs"))
        .def("get_instrument_states_batch", &WorldBatchRuntime::get_instrument_states_batch, nb::arg("refs"))
        .def("get_mission_commands_batch", &WorldBatchRuntime::get_mission_commands_batch, nb::arg("refs"))
        .def("get_task_orders_batch", &WorldBatchRuntime::get_task_orders_batch, nb::arg("refs"))
        .def("get_leader_intents_batch", &WorldBatchRuntime::get_leader_intents_batch, nb::arg("refs"))
        .def("get_pilot_reports_batch", &WorldBatchRuntime::get_pilot_reports_batch, nb::arg("refs"))
        .def(
            "get_sensor_candidate_ids_batch",
            &WorldBatchRuntime::get_sensor_candidate_ids_batch,
            nb::arg("refs"),
            nb::arg("use_gpu") = false
        )
        .def(
            "get_visual_candidate_ids_batch",
            &WorldBatchRuntime::get_visual_candidate_ids_batch,
            nb::arg("refs"),
            nb::arg("range_m") = 25000.0,
            nb::arg("use_gpu") = false
        )
        .def(
            "get_comm_candidate_ids_batch",
            &WorldBatchRuntime::get_comm_candidate_ids_batch,
            nb::arg("refs"),
            nb::arg("use_gpu") = false
        );

    // Maintained runtime facade surface for frontend-facing batch use cases.
    nb::class_<RuntimeFacade>(m, "RuntimeFacade")
        .def(nb::init<size_t>(), nb::arg("world_count") = 0)
        .def(nb::init<const RuntimeBatchConfig&>(), nb::arg("config"))
        .def("configure_batch", &RuntimeFacade::configure_batch, nb::arg("config"))
        .def("batch_config", &RuntimeFacade::batch_config)
        .def("capabilities", &RuntimeFacade::capabilities)
        .def("world_count", &RuntimeFacade::world_count)
        .def("resize", &RuntimeFacade::resize, nb::arg("world_count"))
        .def("set_worker_threads", &RuntimeFacade::set_worker_threads, nb::arg("worker_threads"))
        .def("worker_threads", &RuntimeFacade::worker_threads)
        .def("effective_worker_threads", &RuntimeFacade::effective_worker_threads)
        .def("runtime", nb::overload_cast<>(&RuntimeFacade::runtime), nb::rv_policy::reference_internal)
        .def("load_database", &RuntimeFacade::load_database, nb::arg("path"))
        .def("load_unit_definitions", [](RuntimeFacade& self, const std::string& path) {
            std::string error;
            bool ok = self.load_unit_definitions(path, &error);
            if (!ok && !error.empty()) {
                spdlog::warn("RuntimeFacade failed to load unit definitions: {}", error);
            }
            return ok;
        }, nb::arg("path"))
        .def("reset_batch", &RuntimeFacade::reset_batch, nb::arg("request") = BatchResetRequest{})
        .def("step_batch", &RuntimeFacade::step_batch)
        .def(
            "apply_world_setup_batch",
            &RuntimeFacade::apply_world_setup_batch,
            nb::arg("seeds"),
            nb::arg("terrain_assignments"),
            nb::arg("wind_assignments"),
            nb::arg("zones"),
            nb::arg("requests"),
            nb::arg("time_steps") = std::vector<double>{}
        )
        .def("apply_world_setup", &RuntimeFacade::apply_world_setup, nb::arg("request"))
        .def("set_pilot_actions_batch", &RuntimeFacade::set_pilot_actions_batch, nb::arg("assignments"))
        .def("set_mission_commands_batch", &RuntimeFacade::set_mission_commands_batch, nb::arg("assignments"))
        .def("set_task_orders_batch", &RuntimeFacade::set_task_orders_batch, nb::arg("assignments"))
        .def("set_leader_intents_batch", &RuntimeFacade::set_leader_intents_batch, nb::arg("assignments"))
        .def("set_pilot_reports_batch", &RuntimeFacade::set_pilot_reports_batch, nb::arg("assignments"))
        .def("clear_execution_episode_batch", &RuntimeFacade::clear_execution_episode_batch)
        .def(
            "prime_execution_episode_batch",
            &RuntimeFacade::prime_execution_episode_batch,
            nb::arg("refs"),
            nb::arg("states")
        )
        .def("execution_episode_ready", &RuntimeFacade::execution_episode_ready, nb::arg("world_index"))
        .def(
            "export_execution_episode_states",
            &RuntimeFacade::export_execution_episode_states,
            nb::arg("refs")
        )
        .def(
            "evaluate_execution_batch",
            &RuntimeFacade::evaluate_execution_batch,
            nb::arg("requests")
        )
        .def(
            "step_execution_products_batch",
            &RuntimeFacade::step_execution_products_batch,
            nb::arg("requests")
        )
        .def(
            "step_execution_batch",
            &RuntimeFacade::step_execution_batch,
            nb::arg("request")
        )
        .def("get_agent_observations_batch", &RuntimeFacade::get_agent_observations_batch, nb::arg("refs"))
        .def("get_instrument_states_batch", &RuntimeFacade::get_instrument_states_batch, nb::arg("refs"))
        .def("get_mission_commands_batch", &RuntimeFacade::get_mission_commands_batch, nb::arg("refs"))
        .def("get_task_orders_batch", &RuntimeFacade::get_task_orders_batch, nb::arg("refs"))
        .def("get_leader_intents_batch", &RuntimeFacade::get_leader_intents_batch, nb::arg("refs"))
        .def("get_pilot_reports_batch", &RuntimeFacade::get_pilot_reports_batch, nb::arg("refs"))
        .def(
            "export_observation_packet",
            [](const RuntimeFacade& self, const std::vector<WorldEntityRef>& refs) {
                return self.export_observation_packet(refs);
            },
            nb::arg("refs")
        )
        .def(
            "export_observation_packet",
            [](const RuntimeFacade& self, const ObservationBatchRequest& request) {
                return self.export_observation_packet(request);
            },
            nb::arg("request")
        )
        .def(
            "export_engagement_event_packet",
            &RuntimeFacade::export_engagement_event_packet,
            nb::arg("request")
        )
        .def(
            "export_diagnostics_traces",
            &RuntimeFacade::export_diagnostics_traces,
            nb::arg("request")
        );
}
