#include "interfaces/python/binding_utils.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include <spdlog/spdlog.h>

#include "core/engine/world_batch_runtime.h"
#include "runtime/contracts/counterfactual_replay_contracts.h"
#include "runtime/contracts/engagement_contracts.h"
#include "runtime/contracts/fidelity_profile_contracts.h"
#include "runtime/contracts/platform_capability_contracts.h"
#include "runtime/contracts/policy_contracts.h"
#include "runtime/facade/runtime_facade.h"

void bind_runtime(nb::module_ &m) {
    nb::class_<RuntimeCapabilities> runtime_capabilities_class(m, "RuntimeCapabilities");
    runtime_capabilities_class.def(nb::init<>());
#define EF_RUNTIME_CAPABILITIES_FIELD(type, name, default_value)                                   \
    runtime_capabilities_class.def_rw(#name, &RuntimeCapabilities::name);
#include "runtime/facade/detail/runtime/runtime_capabilities.inc"

    nb::class_<RuntimeBatchConfig> runtime_batch_config_class(m, "RuntimeBatchConfig");
    runtime_batch_config_class.def(nb::init<>());
#define EF_RUNTIME_BATCH_CONFIG_FIELD(type, name, default_value)                                   \
    runtime_batch_config_class.def_rw(#name, &RuntimeBatchConfig::name);
#include "runtime/facade/detail/runtime/runtime_batch_config.inc"

    nb::class_<runtime::composition_evidence_contracts::ProviderVersionEvidence>(
        m, "RuntimeProviderVersionEvidence")
        .def(nb::init<>())
        .def_rw("provider_id",
                &runtime::composition_evidence_contracts::ProviderVersionEvidence::provider_id)
        .def_rw("implementation_version", &runtime::composition_evidence_contracts::
                                              ProviderVersionEvidence::implementation_version);

    nb::class_<runtime::composition_evidence_contracts::BackendEvidence>(
        m, "RuntimeBackendCompositionEvidence")
        .def(nb::init<>())
        .def_rw("provider_id",
                &runtime::composition_evidence_contracts::BackendEvidence::provider_id)
        .def_rw("implementation_version",
                &runtime::composition_evidence_contracts::BackendEvidence::implementation_version)
        .def_rw("backend_profile_id",
                &runtime::composition_evidence_contracts::BackendEvidence::backend_profile_id)
        .def_rw("admitted_capabilities",
                &runtime::composition_evidence_contracts::BackendEvidence::admitted_capabilities);

    nb::class_<runtime::composition_evidence_contracts::ScopeGenerationEvidence>(
        m, "RuntimeScopeGenerationEvidence")
        .def(nb::init<>())
        .def_rw("scope", &runtime::composition_evidence_contracts::ScopeGenerationEvidence::scope)
        .def_rw("instance_id",
                &runtime::composition_evidence_contracts::ScopeGenerationEvidence::instance_id)
        .def_rw("generation",
                &runtime::composition_evidence_contracts::ScopeGenerationEvidence::generation);

    nb::class_<runtime::composition_evidence_contracts::WorldInstanceEvidence>(
        m, "RuntimeWorldInstanceEvidence")
        .def(nb::init<>())
        .def_rw("world_index",
                &runtime::composition_evidence_contracts::WorldInstanceEvidence::world_index)
        .def_rw("scope_generations",
                &runtime::composition_evidence_contracts::WorldInstanceEvidence::scope_generations);

    nb::class_<RuntimeCompositionEvidence>(m, "RuntimeCompositionEvidence")
        .def(nb::init<>())
        .def_rw("schema_version", &RuntimeCompositionEvidence::schema_version)
        .def_rw("evidence_contract_version", &RuntimeCompositionEvidence::evidence_contract_version)
        .def_rw("composition_id", &RuntimeCompositionEvidence::composition_id)
        .def_rw("requested_profile_id", &RuntimeCompositionEvidence::requested_profile_id)
        .def_rw("requested_profile_version", &RuntimeCompositionEvidence::requested_profile_version)
        .def_rw("runtime_request_sha256", &RuntimeCompositionEvidence::runtime_request_sha256)
        .def_rw("requested_manifest_sha256", &RuntimeCompositionEvidence::requested_manifest_sha256)
        .def_rw("resolved_manifest_sha256", &RuntimeCompositionEvidence::resolved_manifest_sha256)
        .def_rw("catalog_lock_sha256", &RuntimeCompositionEvidence::catalog_lock_sha256)
        .def_rw("profile_projection_sha256", &RuntimeCompositionEvidence::profile_projection_sha256)
        .def_rw("resolver_contract_version", &RuntimeCompositionEvidence::resolver_contract_version)
        .def_rw("provider_versions", &RuntimeCompositionEvidence::provider_versions)
        .def_rw("backend", &RuntimeCompositionEvidence::backend)
        .def_rw("executable_graph_sha256", &RuntimeCompositionEvidence::executable_graph_sha256)
        .def_rw("stage_contract_version", &RuntimeCompositionEvidence::stage_contract_version)
        .def_rw("host_mode", &RuntimeCompositionEvidence::host_mode)
        .def_rw("binding_version", &RuntimeCompositionEvidence::binding_version)
        .def_rw("world_instances", &RuntimeCompositionEvidence::world_instances)
        .def_rw("canonicalization", &RuntimeCompositionEvidence::canonicalization)
        .def_rw("hash_algorithm", &RuntimeCompositionEvidence::hash_algorithm)
        .def_rw("canonical_json", &RuntimeCompositionEvidence::canonical_json)
        .def_rw("evidence_sha256", &RuntimeCompositionEvidence::evidence_sha256);

    nb::class_<RuntimeCompositionEvidenceResult>(m, "RuntimeCompositionEvidenceResult")
        .def(nb::init<>())
        .def_rw("available", &RuntimeCompositionEvidenceResult::available)
        .def_rw("evidence", &RuntimeCompositionEvidenceResult::evidence)
        .def_rw("error_code", &RuntimeCompositionEvidenceResult::error_code)
        .def_rw("error_detail", &RuntimeCompositionEvidenceResult::error_detail);

    nb::class_<RuntimeCompositionEvidenceComparison>(m, "RuntimeCompositionEvidenceComparison")
        .def(nb::init<>())
        .def_rw("compatible", &RuntimeCompositionEvidenceComparison::compatible)
        .def_rw("mismatches", &RuntimeCompositionEvidenceComparison::mismatches);

    nb::class_<RuntimeBackendRequest>(m, "RuntimeBackendRequest")
        .def(nb::init<>())
        .def_rw("backend_profile_id", &RuntimeBackendRequest::backend_profile_id)
        .def_rw("capability_manifest_id", &RuntimeBackendRequest::capability_manifest_id)
        .def_rw("parity_budget_ref", &RuntimeBackendRequest::parity_budget_ref)
        .def_rw("requested_feature_ids", &RuntimeBackendRequest::requested_feature_ids)
        .def_rw("allow_unmaintained_candidate",
                &RuntimeBackendRequest::allow_unmaintained_candidate);

    nb::class_<RuntimeBackendAdmission>(m, "RuntimeBackendAdmission")
        .def(nb::init<>())
        .def_rw("admitted", &RuntimeBackendAdmission::admitted)
        .def_rw("maintained_selection", &RuntimeBackendAdmission::maintained_selection)
        .def_rw("experimental_selection", &RuntimeBackendAdmission::experimental_selection)
        .def_rw("backend_profile_id", &RuntimeBackendAdmission::backend_profile_id)
        .def_rw("capability_manifest_id", &RuntimeBackendAdmission::capability_manifest_id)
        .def_rw("parity_budget_ref", &RuntimeBackendAdmission::parity_budget_ref)
        .def_rw("admitted_feature_ids", &RuntimeBackendAdmission::admitted_feature_ids)
        .def_rw("rejection_reason", &RuntimeBackendAdmission::rejection_reason)
        .def_rw("errors", &RuntimeBackendAdmission::errors);

    nb::class_<RuntimeFidelityRequest> runtime_fidelity_request_class(m, "RuntimeFidelityRequest");
    runtime_fidelity_request_class.def(nb::init<>());
#define EF_RUNTIME_FIDELITY_REQUEST_FIELD(type, name, default_value)                               \
    runtime_fidelity_request_class.def_rw(#name, &RuntimeFidelityRequest::name);
#include "runtime/facade/detail/runtime/runtime_fidelity_request.inc"

    nb::class_<RuntimeFidelityAdmission> runtime_fidelity_admission_class(
        m, "RuntimeFidelityAdmission");
    runtime_fidelity_admission_class.def(nb::init<>());
#define EF_RUNTIME_FIDELITY_ADMISSION_FIELD(type, name, default_value)                             \
    runtime_fidelity_admission_class.def_rw(#name, &RuntimeFidelityAdmission::name);
#include "runtime/facade/detail/runtime/runtime_fidelity_admission.inc"

    nb::class_<RuntimeCounterfactualSnapshot> runtime_counterfactual_snapshot_class(
        m, "RuntimeCounterfactualSnapshot");
    runtime_counterfactual_snapshot_class.def(nb::init<>());
#define EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(type, name, default_value)                        \
    runtime_counterfactual_snapshot_class.def_rw(#name, &RuntimeCounterfactualSnapshot::name);
#include "runtime/facade/detail/runtime/runtime_counterfactual_snapshot.inc"

    nb::class_<RuntimeWorldlineComparison> runtime_worldline_comparison_class(
        m, "RuntimeWorldlineComparison");
    runtime_worldline_comparison_class.def(nb::init<>());
#define EF_RUNTIME_WORLDLINE_COMPARISON_FIELD(type, name, default_value)                           \
    runtime_worldline_comparison_class.def_rw(#name, &RuntimeWorldlineComparison::name);
#include "runtime/facade/detail/runtime/runtime_worldline_comparison.inc"

    nb::class_<DeviceResidentOutputDescriptor> device_resident_output_descriptor_class(
        m, "DeviceResidentOutputDescriptor");
    device_resident_output_descriptor_class.def(nb::init<>());
#define EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD(type, name, default_value)                      \
    device_resident_output_descriptor_class.def_rw(#name, &DeviceResidentOutputDescriptor::name);
#include "runtime/facade/detail/runtime/resident_device_output_descriptor.inc"

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
#define EF_PLATFORM_CAPABILITY_FIELD(type, name, default_value)                                    \
    platform_capability_class.def_rw(#name, &runtime::platform_capabilities::Capability::name);
#include "runtime/contracts/detail/platform/platform_capability.inc"

    nb::class_<runtime::platform_capabilities::CapabilityBundle> capability_bundle_class(
        m, "CapabilityBundle");
    capability_bundle_class.def(nb::init<>());
#define EF_CAPABILITY_BUNDLE_FIELD(type, name, default_value)                                      \
    capability_bundle_class.def_rw(#name, &runtime::platform_capabilities::CapabilityBundle::name);
#include "runtime/contracts/detail/platform/capability_bundle.inc"

    nb::class_<runtime::platform_capabilities::ResolvedPlatformSpawnPlan>
        resolved_platform_spawn_plan_class(m, "ResolvedPlatformSpawnPlan");
    resolved_platform_spawn_plan_class.def(nb::init<>());
#define EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(type, name, default_value)                           \
    resolved_platform_spawn_plan_class.def_rw(                                                     \
        #name, &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::name);
#include "runtime/contracts/detail/platform/resolved_platform_spawn_plan.inc"

    nb::class_<TypedPlatformSpawnRequest> typed_platform_spawn_request_class(
        m, "TypedPlatformSpawnRequest");
    typed_platform_spawn_request_class.def(nb::init<>());
#define EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(type, name, default_value)                           \
    typed_platform_spawn_request_class.def_rw(#name, &TypedPlatformSpawnRequest::name);
#include "runtime/contracts/detail/platform/typed_platform_spawn_request.inc"

    nb::class_<TypedPlatformSpawnValidationResult> typed_platform_spawn_validation_result_class(
        m, "TypedPlatformSpawnValidationResult");
    typed_platform_spawn_validation_result_class.def(nb::init<>());
#define EF_TYPED_PLATFORM_SPAWN_VALIDATION_RESULT_FIELD(type, name, default_value)                 \
    typed_platform_spawn_validation_result_class.def_rw(                                           \
        #name, &TypedPlatformSpawnValidationResult::name);
#include "runtime/contracts/detail/platform/typed_platform_spawn_validation_result.inc"

    nb::class_<BatchResetRequest> batch_reset_request_class(m, "BatchResetRequest");
    batch_reset_request_class.def(nb::init<>());
#define EF_BATCH_RESET_REQUEST_FIELD(type, name, default_value)                                    \
    batch_reset_request_class.def_rw(#name, &BatchResetRequest::name);
#include "runtime/facade/detail/batch/batch_reset_request.inc"

    nb::class_<EngagementEntityRef> engagement_entity_ref_class(m, "EngagementEntityRef");
    engagement_entity_ref_class.def(nb::init<>());
#define EF_ENGAGEMENT_ENTITY_REF_FIELD(type, name, default_value)                                  \
    engagement_entity_ref_class.def_rw(#name, &EngagementEntityRef::name);
#include "runtime/contracts/detail/engagement/engagement_entity_ref.inc"

    nb::class_<LethalityChainHeader> lethality_chain_header_class(m, "LethalityChainHeader");
    lethality_chain_header_class.def(nb::init<>());
#define EF_LETHALITY_CHAIN_HEADER_FIELD(type, name, default_value)                                 \
    lethality_chain_header_class.def_rw(#name, &LethalityChainHeader::name);
#include "runtime/contracts/detail/engagement/lethality_chain_header.inc"

    nb::class_<NearestApproachEvent> nearest_approach_event_class(m, "NearestApproachEvent");
    nearest_approach_event_class.def(nb::init<>());
#define EF_NEAREST_APPROACH_EVENT_FIELD(type, name, default_value)                                 \
    nearest_approach_event_class.def_rw(#name, &NearestApproachEvent::name);
#include "runtime/contracts/detail/engagement/nearest_approach_event.inc"

    nb::class_<FuzeEvaluationEvent> fuze_evaluation_event_class(m, "FuzeEvaluationEvent");
    fuze_evaluation_event_class.def(nb::init<>());
#define EF_FUZE_EVALUATION_EVENT_FIELD(type, name, default_value)                                  \
    fuze_evaluation_event_class.def_rw(#name, &FuzeEvaluationEvent::name);
#include "runtime/contracts/detail/engagement/fuze_evaluation_event.inc"

    nb::class_<WarheadMechanismEvent> warhead_mechanism_event_class(m, "WarheadMechanismEvent");
    warhead_mechanism_event_class.def(nb::init<>());
#define EF_WARHEAD_MECHANISM_EVENT_FIELD(type, name, default_value)                                \
    warhead_mechanism_event_class.def_rw(#name, &WarheadMechanismEvent::name);
#include "runtime/contracts/detail/engagement/warhead_mechanism_event.inc"

    nb::class_<SpatialCoverageEvent> spatial_coverage_event_class(m, "SpatialCoverageEvent");
    spatial_coverage_event_class.def(nb::init<>());
#define EF_SPATIAL_COVERAGE_EVENT_FIELD(type, name, default_value)                                 \
    spatial_coverage_event_class.def_rw(#name, &SpatialCoverageEvent::name);
#include "runtime/contracts/detail/engagement/spatial_coverage_event.inc"

    nb::class_<ComponentLoadEvent> component_load_event_class(m, "ComponentLoadEvent");
    component_load_event_class.def(nb::init<>());
#define EF_COMPONENT_LOAD_EVENT_FIELD(type, name, default_value)                                   \
    component_load_event_class.def_rw(#name, &ComponentLoadEvent::name);
#include "runtime/contracts/detail/damage/component_load_event.inc"

    nb::class_<ComponentDamageEvent> component_damage_event_class(m, "ComponentDamageEvent");
    component_damage_event_class.def(nb::init<>());
#define EF_COMPONENT_DAMAGE_EVENT_FIELD(type, name, default_value)                                 \
    component_damage_event_class.def_rw(#name, &ComponentDamageEvent::name);
#include "runtime/contracts/detail/damage/component_damage_event.inc"

    nb::class_<PlatformConsequenceEvent> platform_consequence_event_class(
        m, "PlatformConsequenceEvent");
    platform_consequence_event_class.def(nb::init<>());
#define EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(type, name, default_value)                             \
    platform_consequence_event_class.def_rw(#name, &PlatformConsequenceEvent::name);
#include "runtime/contracts/detail/damage/platform_consequence_event.inc"

    nb::class_<StructuralBreakupEvent> structural_breakup_event_class(m, "StructuralBreakupEvent");
    structural_breakup_event_class.def(nb::init<>());
#define EF_STRUCTURAL_BREAKUP_EVENT_FIELD(type, name, default_value)                               \
    structural_breakup_event_class.def_rw(#name, &StructuralBreakupEvent::name);
#include "runtime/contracts/detail/damage/structural_breakup_event.inc"

    nb::class_<LifecycleTransitionEvent> lifecycle_transition_event_class(
        m, "LifecycleTransitionEvent");
    lifecycle_transition_event_class.def(nb::init<>());
#define EF_LIFECYCLE_TRANSITION_EVENT_FIELD(type, name, default_value)                             \
    lifecycle_transition_event_class.def_rw(#name, &LifecycleTransitionEvent::name);
#include "runtime/contracts/detail/damage/lifecycle_transition_event.inc"

    nb::class_<TrainingProjectionEvent> training_projection_event_class(m,
                                                                        "TrainingProjectionEvent");
    training_projection_event_class.def(nb::init<>());
#define EF_TRAINING_PROJECTION_EVENT_FIELD(type, name, default_value)                              \
    training_projection_event_class.def_rw(#name, &TrainingProjectionEvent::name);
#include "runtime/contracts/detail/damage/training_projection_event.inc"

    nb::class_<TrackPacket> track_packet_class(m, "TrackPacket");
    track_packet_class.def(nb::init<>());
#define EF_TRACK_PACKET_FIELD(type, name, default_value)                                           \
    track_packet_class.def_rw(#name, &TrackPacket::name);
#include "runtime/contracts/detail/engagement/track_packet.inc"

    nb::class_<LaunchRequest> launch_request_class(m, "LaunchRequest");
    launch_request_class.def(nb::init<>());
#define EF_LAUNCH_REQUEST_FIELD(type, name, default_value)                                         \
    launch_request_class.def_rw(#name, &LaunchRequest::name);
#include "runtime/contracts/detail/engagement/launch_request.inc"

    nb::class_<LaunchEvent> launch_event_class(m, "LaunchEvent");
    launch_event_class.def(nb::init<>());
#define EF_LAUNCH_EVENT_FIELD(type, name, default_value)                                           \
    launch_event_class.def_rw(#name, &LaunchEvent::name);
#include "runtime/contracts/detail/engagement/launch_event.inc"

    nb::class_<MunitionLifecyclePacket> munition_lifecycle_packet_class(m,
                                                                        "MunitionLifecyclePacket");
    munition_lifecycle_packet_class.def(nb::init<>());
#define EF_MUNITION_LIFECYCLE_PACKET_FIELD(type, name, default_value)                              \
    munition_lifecycle_packet_class.def_rw(#name, &MunitionLifecyclePacket::name);
#include "runtime/contracts/detail/engagement/munition_lifecycle_packet.inc"

    nb::class_<ComponentMechanismLoadRow> component_mechanism_load_row_class(
        m, "ComponentMechanismLoadRow");
    component_mechanism_load_row_class.def(nb::init<>());
#define EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(type, name, default_value)                           \
    component_mechanism_load_row_class.def_rw(#name, &ComponentMechanismLoadRow::name);
#include "runtime/contracts/detail/damage/component_mechanism_load_row.inc"

    nb::class_<ComponentResponseRow> component_response_row_class(m, "ComponentResponseRow");
    component_response_row_class.def(nb::init<>());
#define EF_COMPONENT_RESPONSE_ROW_FIELD(type, name, default_value)                                 \
    component_response_row_class.def_rw(#name, &ComponentResponseRow::name);
#include "runtime/contracts/detail/damage/component_response_row.inc"

    // The def_rw list is owned by the X-macro field list; exposed property
    // names and their order stay identical to the EffectsEvent declaration.
    nb::class_<EffectsEvent>(m, "EffectsEvent").def(nb::init<>())
#define EF_EFFECTS_EVENT_FIELD(type, name, default_value) .def_rw(#name, &EffectsEvent::name)
#define EF_EFFECTS_EVENT_RESULT_FIELD(type, name, default_value) .def_rw(#name, &EffectsEvent::name)
#include "runtime/contracts/detail/damage/effects_event_fields.inc"
#undef EF_EFFECTS_EVENT_RESULT_FIELD
#undef EF_EFFECTS_EVENT_FIELD
        ;

    nb::class_<KillChainApproachFact> kill_chain_approach_fact_class(m, "KillChainApproachFact");
    kill_chain_approach_fact_class.def(nb::init<>());
#define EF_KILL_CHAIN_APPROACH_FACT_FIELD(type, name, default_value)                               \
    kill_chain_approach_fact_class.def_rw(#name, &KillChainApproachFact::name);
#include "runtime/contracts/detail/kill_chain/kill_chain_approach_fact.inc"

    nb::class_<KillChainFuzeDecision> kill_chain_fuze_decision_class(m, "KillChainFuzeDecision");
    kill_chain_fuze_decision_class.def(nb::init<>());
#define EF_KILL_CHAIN_FUZE_DECISION_FIELD(type, name, default_value)                               \
    kill_chain_fuze_decision_class.def_rw(#name, &KillChainFuzeDecision::name);
#include "runtime/contracts/detail/kill_chain/kill_chain_fuze_decision.inc"

    nb::class_<KillChainComponentLoadFact> kill_chain_component_load_fact_class(
        m, "KillChainComponentLoadFact");
    kill_chain_component_load_fact_class.def(nb::init<>());
#define EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(type, name, default_value)                         \
    kill_chain_component_load_fact_class.def_rw(#name, &KillChainComponentLoadFact::name);
#include "runtime/contracts/detail/kill_chain/kill_chain_component_load_fact.inc"

    nb::class_<KillChainWarheadLoadField> kill_chain_warhead_load_field_class(
        m, "KillChainWarheadLoadField");
    kill_chain_warhead_load_field_class.def(nb::init<>());
#define EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(type, name, default_value)                          \
    kill_chain_warhead_load_field_class.def_rw(#name, &KillChainWarheadLoadField::name);
#include "runtime/contracts/detail/kill_chain/kill_chain_warhead_load_field.inc"

    nb::class_<KillChainTargetSusceptibility> kill_chain_target_susceptibility_class(
        m, "KillChainTargetSusceptibility");
    kill_chain_target_susceptibility_class.def(nb::init<>());
#define EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD(type, name, default_value)                       \
    kill_chain_target_susceptibility_class.def_rw(#name, &KillChainTargetSusceptibility::name);
#include "runtime/contracts/detail/kill_chain/kill_chain_target_susceptibility.inc"

    nb::class_<KillChainComponentResponseFact> kill_chain_component_response_fact_class(
        m, "KillChainComponentResponseFact");
    kill_chain_component_response_fact_class.def(nb::init<>());
#define EF_KILL_CHAIN_COMPONENT_RESPONSE_FACT_FIELD(type, name, default_value)                     \
    kill_chain_component_response_fact_class.def_rw(#name, &KillChainComponentResponseFact::name);
#include "runtime/contracts/detail/kill_chain/kill_chain_component_response_fact.inc"

    nb::class_<KillChainConsequenceProjection> kill_chain_consequence_projection_class(
        m, "KillChainConsequenceProjection");
    kill_chain_consequence_projection_class.def(nb::init<>());
#define EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD(type, name, default_value)                      \
    kill_chain_consequence_projection_class.def_rw(#name, &KillChainConsequenceProjection::name);
#include "runtime/contracts/detail/kill_chain/kill_chain_consequence_projection.inc"

    nb::class_<KillChainRuntimeFacade> kill_chain_runtime_facade_class(m, "KillChainRuntimeFacade");
    kill_chain_runtime_facade_class.def(nb::init<>());
#define EF_KILL_CHAIN_RUNTIME_FACADE_FIELD(type, name, default_value)                              \
    kill_chain_runtime_facade_class.def_rw(#name, &KillChainRuntimeFacade::name);
#include "runtime/contracts/detail/kill_chain/kill_chain_runtime_facade.inc"

    m.def("make_kill_chain_runtime_facade", &make_kill_chain_runtime_facade, nb::arg("effects"));

    nb::class_<DamageReport> damage_report_class(m, "DamageReport");
    damage_report_class.def(nb::init<>());
#define EF_DAMAGE_REPORT_FIELD(type, name, default_value)                                          \
    damage_report_class.def_rw(#name, &DamageReport::name);
#include "runtime/contracts/detail/damage/damage_report.inc"

    nb::class_<DiagnosticsTrace> diagnostics_trace_class(m, "DiagnosticsTrace");
    diagnostics_trace_class.def(nb::init<>());
#define EF_DIAGNOSTICS_TRACE_FIELD(type, name, default_value)                                      \
    diagnostics_trace_class.def_rw(#name, &DiagnosticsTrace::name);
#include "runtime/contracts/detail/engagement/diagnostics_trace.inc"

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
#define EF_WORLD_ENTITY_REF_FIELD(type, name, default_value)                                       \
    world_entity_ref_class.def_rw(#name, &WorldEntityRef::name);
#include "runtime/contracts/detail/platform/world_entity_ref.inc"

    nb::class_<BatchWorldSetupRequest> batch_world_setup_request_class(m, "BatchWorldSetupRequest");
    batch_world_setup_request_class.def(nb::init<>());
#define EF_BATCH_WORLD_SETUP_REQUEST_FIELD(type, name, default_value)                              \
    batch_world_setup_request_class.def_rw(#name, &BatchWorldSetupRequest::name);
#include "runtime/facade/detail/batch/batch_world_setup_request.inc"

    // Field-order note: the header field order (schema-owned, ABI/aggregate-init
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
#define EF_BATCH_WORLD_SETUP_RESULT_FIELD(type, name, default_value)                               \
    batch_world_setup_result_class.def_rw(#name, &BatchWorldSetupResult::name);
#include "runtime/facade/detail/batch/batch_world_setup_result.inc"

    nb::class_<RuntimeWorldLayoutRequest> runtime_world_layout_request_class(
        m, "RuntimeWorldLayoutRequest");
    runtime_world_layout_request_class.def(nb::init<>());
#define EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(type, name, default_value)                           \
    runtime_world_layout_request_class.def_rw(#name, &RuntimeWorldLayoutRequest::name);
#include "runtime/facade/detail/runtime/runtime_world_layout_request.inc"

    nb::class_<RuntimeWorldLayoutResult> runtime_world_layout_result_class(
        m, "RuntimeWorldLayoutResult");
    runtime_world_layout_result_class.def(nb::init<>());
#define EF_RUNTIME_WORLD_LAYOUT_RESULT_FIELD(type, name, default_value)                            \
    runtime_world_layout_result_class.def_rw(#name, &RuntimeWorldLayoutResult::name);
#include "runtime/facade/detail/runtime/runtime_world_layout_result.inc"

    nb::class_<RuntimeCounterfactualBranchRequest> runtime_counterfactual_branch_request_class(
        m, "RuntimeCounterfactualBranchRequest");
    runtime_counterfactual_branch_request_class.def(nb::init<>());
#define EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(type, name, default_value)                  \
    runtime_counterfactual_branch_request_class.def_rw(#name,                                      \
                                                       &RuntimeCounterfactualBranchRequest::name);
#include "runtime/facade/detail/runtime/runtime_counterfactual_branch_request.inc"

    nb::class_<RuntimeCounterfactualRestoreRequest> runtime_counterfactual_restore_request_class(
        m, "RuntimeCounterfactualRestoreRequest");
    runtime_counterfactual_restore_request_class.def(nb::init<>());
#define EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD(type, name, default_value)                 \
    runtime_counterfactual_restore_request_class.def_rw(                                           \
        #name, &RuntimeCounterfactualRestoreRequest::name);
#include "runtime/facade/detail/runtime/runtime_counterfactual_restore_request.inc"

    nb::class_<RuntimeCounterfactualRestoreResult> runtime_counterfactual_restore_result_class(
        m, "RuntimeCounterfactualRestoreResult");
    runtime_counterfactual_restore_result_class.def(nb::init<>());
#define EF_RUNTIME_COUNTERFACTUAL_RESTORE_RESULT_FIELD(type, name, default_value)                  \
    runtime_counterfactual_restore_result_class.def_rw(#name,                                      \
                                                       &RuntimeCounterfactualRestoreResult::name);
#include "runtime/facade/detail/runtime/runtime_counterfactual_restore_result.inc"

    nb::class_<RuntimeCounterfactualBranchResult> runtime_counterfactual_branch_result_class(
        m, "RuntimeCounterfactualBranchResult");
    runtime_counterfactual_branch_result_class.def(nb::init<>());
#define EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD(type, name, default_value)                   \
    runtime_counterfactual_branch_result_class.def_rw(#name,                                       \
                                                      &RuntimeCounterfactualBranchResult::name);
#include "runtime/facade/detail/runtime/runtime_counterfactual_branch_result.inc"

    nb::class_<RuntimeExperimentStepRequest> runtime_experiment_step_request_class(
        m, "RuntimeExperimentStepRequest");
    runtime_experiment_step_request_class.def(nb::init<>());
#define EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD(type, name, default_value)                        \
    runtime_experiment_step_request_class.def_rw(#name, &RuntimeExperimentStepRequest::name);
#include "runtime/facade/detail/runtime/runtime_experiment_step_request.inc"

    nb::class_<RuntimeExperimentRequest> runtime_experiment_request_class(
        m, "RuntimeExperimentRequest");
    runtime_experiment_request_class.def(nb::init<>());
#define EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(type, name, default_value)                             \
    runtime_experiment_request_class.def_rw(#name, &RuntimeExperimentRequest::name);
#include "runtime/facade/detail/runtime/runtime_experiment_request.inc"

    nb::class_<ObservationBatchRequest> observation_batch_request_class(m,
                                                                        "ObservationBatchRequest");
    observation_batch_request_class.def(nb::init<>());
#define EF_OBSERVATION_BATCH_REQUEST_FIELD(type, name, default_value)                              \
    observation_batch_request_class.def_rw(#name, &ObservationBatchRequest::name);
#include "runtime/facade/detail/batch/observation_batch_request.inc"

    nb::class_<TaskingBatchRequest> tasking_batch_request_class(m, "TaskingBatchRequest");
    tasking_batch_request_class.def(nb::init<>());
#define EF_TASKING_BATCH_REQUEST_FIELD(type, name, default_value)                                  \
    tasking_batch_request_class.def_rw(#name, &TaskingBatchRequest::name);
#include "runtime/facade/detail/batch/tasking_batch_request.inc"

    nb::class_<EngagementBatchRequest> engagement_batch_request_class(m, "EngagementBatchRequest");
    engagement_batch_request_class.def(nb::init<>());
#define EF_ENGAGEMENT_BATCH_REQUEST_FIELD(type, name, default_value)                               \
    engagement_batch_request_class.def_rw(#name, &EngagementBatchRequest::name);
#include "runtime/facade/detail/batch/engagement_batch_request.inc"

    nb::class_<ExecutionBatchStepRequest> execution_batch_step_request_class(
        m, "ExecutionBatchStepRequest");
    execution_batch_step_request_class.def(nb::init<>());
#define EF_EXECUTION_BATCH_STEP_REQUEST_FIELD(type, name, default_value)                           \
    execution_batch_step_request_class.def_rw(#name, &ExecutionBatchStepRequest::name);
#include "runtime/facade/detail/batch/execution_batch_step_request.inc"

    nb::class_<RewardTerm> reward_term_class(m, "RewardTerm");
    reward_term_class.def(nb::init<>());
#define EF_REWARD_TERM_FIELD(type, name, default_value)                                            \
    reward_term_class.def_rw(#name, &RewardTerm::name);
#include "runtime/contracts/detail/learning/reward_term.inc"

    nb::class_<RewardReport> reward_report_class(m, "RewardReport");
    reward_report_class.def(nb::init<>());
#define EF_REWARD_REPORT_FIELD(type, name, default_value)                                          \
    reward_report_class.def_rw(#name, &RewardReport::name);
#include "runtime/contracts/detail/learning/reward_report.inc"

    nb::class_<TerminationSpec> termination_spec_class(m, "TerminationSpec");
    termination_spec_class.def(nb::init<>());
#define EF_TERMINATION_SPEC_FIELD(type, name, default_value)                                       \
    termination_spec_class.def_rw(#name, &TerminationSpec::name);
#include "runtime/contracts/detail/learning/termination_spec.inc"

    nb::class_<ObservationViewSpec> observation_view_spec_class(m, "ObservationViewSpec");
    observation_view_spec_class.def(nb::init<>());
#define EF_OBSERVATION_VIEW_SPEC_FIELD(type, name, default_value)                                  \
    observation_view_spec_class.def_rw(#name, &ObservationViewSpec::name);
#include "runtime/contracts/detail/learning/observation_view_spec.inc"

    nb::class_<ObservationViewCompatibilityReport> observation_view_compatibility_report_class(
        m, "ObservationViewCompatibilityReport");
    observation_view_compatibility_report_class.def(nb::init<>());
#define EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD(type, name, default_value)                  \
    observation_view_compatibility_report_class.def_rw(#name,                                      \
                                                       &ObservationViewCompatibilityReport::name);
#include "runtime/contracts/detail/learning/observation_view_compatibility_report.inc"

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
#define EF_OBSERVATION_BATCH_PACKET_FIELD(type, name, default_value)                               \
    observation_batch_packet_class.def_rw(#name, &ObservationBatchPacket::name);
#include "runtime/facade/detail/batch/observation_batch_packet.inc"

    nb::class_<TaskingBatchPacket> tasking_batch_packet_class(m, "TaskingBatchPacket");
    tasking_batch_packet_class.def(nb::init<>());
#define EF_TASKING_BATCH_PACKET_FIELD(type, name, default_value)                                   \
    tasking_batch_packet_class.def_rw(#name, &TaskingBatchPacket::name);
#include "runtime/facade/detail/batch/tasking_batch_packet.inc"

    nb::class_<EngagementEventPacket> engagement_event_packet_class(m, "EngagementEventPacket");
    engagement_event_packet_class.def(nb::init<>());
#define EF_ENGAGEMENT_EVENT_PACKET_FIELD(type, name, default_value)                                \
    engagement_event_packet_class.def_rw(#name, &EngagementEventPacket::name);
#include "runtime/facade/detail/batch/engagement_event_packet.inc"

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

    // Binding-coverage note: MissionCommandMaintainedBatchContract/
    // TaskOrderMaintainedBatchContract/
    // LeaderIntentMaintainedBatchContract/PilotReportMaintainedBatchContract header
    // field blocks are schema-owned (tools/maintenance/dto_schema), but each of these
    // four bindings has long registered every field except its own trailing
    // ground_static_task/ground_static_status field (a pre-existing binding-surface
    // omission; TaskOrder's omitted field stays reachable through the
    // task_order_maintained_ground_static_task free function). That never-bound
    // field is preserved here as-is (parity baseline) instead of being
    // macro-expanded from the same X-macro as the header block.
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
#define EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(type, name, default_value)                            \
    runtime_experiment_ancestry_class.def_rw(#name, &RuntimeExperimentAncestry::name);
#include "runtime/facade/detail/runtime/runtime_experiment_ancestry.inc"

    nb::class_<RuntimeExperimentResult> runtime_experiment_result_class(m,
                                                                        "RuntimeExperimentResult");
    runtime_experiment_result_class.def(nb::init<>());
#define EF_RUNTIME_EXPERIMENT_RESULT_FIELD(type, name, default_value)                              \
    runtime_experiment_result_class.def_rw(#name, &RuntimeExperimentResult::name);
#include "runtime/facade/detail/runtime/runtime_experiment_result.inc"

    // Schema-ownership note: RuntimeWindowActionRequest is not schema-generated. Its
    // header field list (runtime_facade_types.h) is ABI-ordered as
    // action_intent, source_layer, input_snapshot_version,
    // clock_domain_metadata, cadence_control -- but clock_domain_metadata
    // is a nested, never-bound type (no Python duplication to unify) and
    // this binding's registration order/coverage already diverges from
    // that ABI order (cadence_control before source_layer/
    // input_snapshot_version; clock_domain_metadata omitted). Left
    // hand-written and skipped from schema ownership; see the binding-schema
    // audit for the recorded skip rationale. Its nested
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
#define EF_RUNTIME_WINDOW_INPUT_RECORD_FIELD(type, name, default_value)                            \
    runtime_window_input_record_class.def_rw(#name, &RuntimeWindowInputRecord::name);
#include "runtime/facade/detail/window/runtime_window_input_record.inc"

    nb::class_<RuntimeWindowSchedulingContext> runtime_window_scheduling_context_class(
        m, "RuntimeWindowSchedulingContext");
    runtime_window_scheduling_context_class.def(nb::init<>());
#define EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD(type, name, default_value)                      \
    runtime_window_scheduling_context_class.def_rw(#name, &RuntimeWindowSchedulingContext::name);
#include "runtime/facade/detail/window/runtime_window_scheduling_context.inc"

    nb::class_<RuntimeWindowBarrierRecord> runtime_window_barrier_record_class(
        m, "RuntimeWindowBarrierRecord");
    runtime_window_barrier_record_class.def(nb::init<>());
#define EF_RUNTIME_WINDOW_BARRIER_RECORD_FIELD(type, name, default_value)                          \
    runtime_window_barrier_record_class.def_rw(#name, &RuntimeWindowBarrierRecord::name);
#include "runtime/facade/detail/window/runtime_window_barrier_record.inc"

    nb::class_<RuntimeWindowVisibilityRecord> runtime_window_visibility_record_class(
        m, "RuntimeWindowVisibilityRecord");
    runtime_window_visibility_record_class.def(nb::init<>());
#define EF_RUNTIME_WINDOW_VISIBILITY_RECORD_FIELD(type, name, default_value)                       \
    runtime_window_visibility_record_class.def_rw(#name, &RuntimeWindowVisibilityRecord::name);
#include "runtime/facade/detail/window/runtime_window_visibility_record.inc"

    // Binding-order note: the RuntimeWindowNodeExecutionRecord/CadenceControl/
    // Cadence/CadenceConfig/CadenceTraceRecord/Request/Result bindings
    // below have long registered properties out of the header's ABI
    // declaration order (several alphabetically); left hand-written and
    // skipped from binding-side schema ownership so registration order/
    // dir() sequence stays byte-for-byte unchanged. Each struct's C++
    // field list is still schema-owned on the header side (see
    // runtime_facade_types.h); see the binding-schema audit for the
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

    // Additive read surface for the replay contract types plus the fail-closed
    // validator, allowing the maintained Python run to validate the envelope
    // assembled from its own window products
    // (RuntimeFacade::build_maintained_replay_envelope). Nothing on an
    // existing path constructs or consumes these bindings.
    nb::class_<runtime::counterfactual::ReplaySnapshotRef>(m, "ReplaySnapshotRef")
        .def(nb::init<>())
        .def_rw("snapshot_version_ref",
                &runtime::counterfactual::ReplaySnapshotRef::snapshot_version_ref);

    nb::class_<runtime::counterfactual::ReplayBarrierRef>(m, "ReplayBarrierRef")
        .def(nb::init<>())
        .def_rw("barrier_id", &runtime::counterfactual::ReplayBarrierRef::barrier_id)
        .def_rw("barrier_sequence", &runtime::counterfactual::ReplayBarrierRef::barrier_sequence)
        .def_rw("barrier_detail", &runtime::counterfactual::ReplayBarrierRef::barrier_detail);

    nb::class_<runtime::counterfactual::ReplayEventOrderRef>(m, "ReplayEventOrderRef")
        .def(nb::init<>())
        .def_rw("sort_key", &runtime::counterfactual::ReplayEventOrderRef::sort_key)
        .def_rw("event_id", &runtime::counterfactual::ReplayEventOrderRef::event_id)
        .def_rw("producer_node_id",
                &runtime::counterfactual::ReplayEventOrderRef::producer_node_id);

    nb::class_<runtime::counterfactual::ReplayFacadeProvenanceRef>(m, "ReplayFacadeProvenanceRef")
        .def(nb::init<>())
        .def_rw("packet_ref", &runtime::counterfactual::ReplayFacadeProvenanceRef::packet_ref)
        .def_rw("packet_kind", &runtime::counterfactual::ReplayFacadeProvenanceRef::packet_kind)
        .def_rw("information_state_source",
                &runtime::counterfactual::ReplayFacadeProvenanceRef::information_state_source);

    nb::class_<runtime::counterfactual::ReplayEnvelope>(m, "ReplayEnvelope")
        .def(nb::init<>())
        .def_rw("replay_envelope_id", &runtime::counterfactual::ReplayEnvelope::replay_envelope_id)
        .def_rw("run_id", &runtime::counterfactual::ReplayEnvelope::run_id)
        .def_rw("episode_id", &runtime::counterfactual::ReplayEnvelope::episode_id)
        .def_rw("has_deterministic_seed",
                &runtime::counterfactual::ReplayEnvelope::has_deterministic_seed)
        .def_rw("deterministic_seed", &runtime::counterfactual::ReplayEnvelope::deterministic_seed)
        .def_rw("has_source_time", &runtime::counterfactual::ReplayEnvelope::has_source_time)
        .def_rw("source_time_s", &runtime::counterfactual::ReplayEnvelope::source_time_s)
        .def_rw("snapshot_ref", &runtime::counterfactual::ReplayEnvelope::snapshot_ref)
        .def_rw("barrier_ref", &runtime::counterfactual::ReplayEnvelope::barrier_ref)
        .def_rw("event_order_ref", &runtime::counterfactual::ReplayEnvelope::event_order_ref)
        .def_rw("facade_provenance_ref",
                &runtime::counterfactual::ReplayEnvelope::facade_provenance_ref)
        .def_rw("snapshot_restore_supported",
                &runtime::counterfactual::ReplayEnvelope::snapshot_restore_supported)
        .def_rw("restore_support_boundary",
                &runtime::counterfactual::ReplayEnvelope::restore_support_boundary);

    nb::class_<runtime::counterfactual::ReplayContractValidationResult>(
        m, "ReplayContractValidationResult")
        .def(nb::init<>())
        .def_rw("valid", &runtime::counterfactual::ReplayContractValidationResult::valid)
        .def_rw("errors", &runtime::counterfactual::ReplayContractValidationResult::errors)
        .def_rw("rejection_reason",
                &runtime::counterfactual::ReplayContractValidationResult::rejection_reason);

    nb::class_<runtime::counterfactual::MaintainedReplayEnvelopeResult>(
        m, "MaintainedReplayEnvelopeResult")
        .def(nb::init<>())
        .def_rw("admitted", &runtime::counterfactual::MaintainedReplayEnvelopeResult::admitted)
        .def_rw("envelope", &runtime::counterfactual::MaintainedReplayEnvelopeResult::envelope)
        .def_rw("rejection_reason",
                &runtime::counterfactual::MaintainedReplayEnvelopeResult::rejection_reason)
        .def_rw("errors", &runtime::counterfactual::MaintainedReplayEnvelopeResult::errors)
        .def_rw("evidence_refs",
                &runtime::counterfactual::MaintainedReplayEnvelopeResult::evidence_refs);

    m.def("validate_replay_envelope", &runtime::counterfactual::validate_replay_envelope,
          nb::arg("envelope"));

    // Additive read surface for the maintained engagement-packet ancestry
    // producer.
    // (RuntimeFacade::build_maintained_packet_ancestry). Nothing on an existing
    // path constructs or consumes these bindings. The typed lineage ref reuses
    // the shared typed-lineage vocabulary (ref_id / evidence_kind /
    // provenance_label) already owned by the C++ contract type.
    nb::class_<runtime::counterfactual::ScenarioGenerationEvidenceMetadataRef>(
        m, "ScenarioGenerationEvidenceMetadataRef")
        .def(nb::init<>())
        .def_rw("ref_id", &runtime::counterfactual::ScenarioGenerationEvidenceMetadataRef::ref_id)
        .def_rw("evidence_kind",
                &runtime::counterfactual::ScenarioGenerationEvidenceMetadataRef::evidence_kind)
        .def_rw("provenance_label",
                &runtime::counterfactual::ScenarioGenerationEvidenceMetadataRef::provenance_label);

    nb::class_<MaintainedEngagementPacketAncestry>(m, "MaintainedEngagementPacketAncestry")
        .def(nb::init<>())
        .def_rw("packet_ancestry_id", &MaintainedEngagementPacketAncestry::packet_ancestry_id)
        .def_rw("run_id", &MaintainedEngagementPacketAncestry::run_id)
        .def_rw("episode_id", &MaintainedEngagementPacketAncestry::episode_id)
        .def_rw("anchor_trace_id", &MaintainedEngagementPacketAncestry::anchor_trace_id)
        .def_rw("parent_trace_id", &MaintainedEngagementPacketAncestry::parent_trace_id)
        .def_rw("replay_envelope_ref", &MaintainedEngagementPacketAncestry::replay_envelope_ref)
        .def_rw("parent_event_order_ref",
                &MaintainedEngagementPacketAncestry::parent_event_order_ref)
        .def_rw("lineage_refs", &MaintainedEngagementPacketAncestry::lineage_refs)
        .def_rw("ancestral_traces", &MaintainedEngagementPacketAncestry::ancestral_traces);

    nb::class_<MaintainedPacketAncestryResult>(m, "MaintainedPacketAncestryResult")
        .def(nb::init<>())
        .def_rw("admitted", &MaintainedPacketAncestryResult::admitted)
        .def_rw("ancestry", &MaintainedPacketAncestryResult::ancestry)
        .def_rw("rejection_reason", &MaintainedPacketAncestryResult::rejection_reason)
        .def_rw("errors", &MaintainedPacketAncestryResult::errors)
        .def_rw("evidence_refs", &MaintainedPacketAncestryResult::evidence_refs);

    // Additive read surface for the maintained worldline/counterfactual
    // comparison producer
    // (RuntimeFacade::build_maintained_worldline_comparison). Nothing on an
    // existing path constructs or consumes these bindings. The DTO carries
    // evidence ids only (no truth-state copies -- the no-truth-promotion red
    // line documented on the C++ type in runtime_facade_types.h).
    nb::class_<MaintainedWorldlineComparison>(m, "MaintainedWorldlineComparison")
        .def(nb::init<>())
        .def_rw("comparison_id", &MaintainedWorldlineComparison::comparison_id)
        .def_rw("run_id", &MaintainedWorldlineComparison::run_id)
        .def_rw("episode_id", &MaintainedWorldlineComparison::episode_id)
        .def_rw("baseline_worldline_id", &MaintainedWorldlineComparison::baseline_worldline_id)
        .def_rw("candidate_worldline_id", &MaintainedWorldlineComparison::candidate_worldline_id)
        .def_rw("baseline_anchor_trace_id",
                &MaintainedWorldlineComparison::baseline_anchor_trace_id)
        .def_rw("candidate_anchor_trace_id",
                &MaintainedWorldlineComparison::candidate_anchor_trace_id)
        .def_rw("baseline_replay_envelope_ref",
                &MaintainedWorldlineComparison::baseline_replay_envelope_ref)
        .def_rw("candidate_replay_envelope_ref",
                &MaintainedWorldlineComparison::candidate_replay_envelope_ref)
        .def_rw("baseline_packet_ancestry_ref",
                &MaintainedWorldlineComparison::baseline_packet_ancestry_ref)
        .def_rw("candidate_packet_ancestry_ref",
                &MaintainedWorldlineComparison::candidate_packet_ancestry_ref)
        .def_rw("baseline_event_order_ref",
                &MaintainedWorldlineComparison::baseline_event_order_ref)
        .def_rw("candidate_event_order_ref",
                &MaintainedWorldlineComparison::candidate_event_order_ref)
        .def_rw("baseline_snapshot_version_ref",
                &MaintainedWorldlineComparison::baseline_snapshot_version_ref)
        .def_rw("candidate_snapshot_version_ref",
                &MaintainedWorldlineComparison::candidate_snapshot_version_ref)
        .def_rw("baseline_deterministic_seed",
                &MaintainedWorldlineComparison::baseline_deterministic_seed)
        .def_rw("candidate_deterministic_seed",
                &MaintainedWorldlineComparison::candidate_deterministic_seed)
        .def_rw("deterministic_seed_matched",
                &MaintainedWorldlineComparison::deterministic_seed_matched)
        .def_rw("claim_scope", &MaintainedWorldlineComparison::claim_scope)
        .def_rw("truth_claim", &MaintainedWorldlineComparison::truth_claim)
        .def_rw("promoted_to_support", &MaintainedWorldlineComparison::promoted_to_support)
        .def_rw("lineage_refs", &MaintainedWorldlineComparison::lineage_refs);

    nb::class_<MaintainedWorldlineComparisonResult>(m, "MaintainedWorldlineComparisonResult")
        .def(nb::init<>())
        .def_rw("admitted", &MaintainedWorldlineComparisonResult::admitted)
        .def_rw("comparison", &MaintainedWorldlineComparisonResult::comparison)
        .def_rw("rejection_reason", &MaintainedWorldlineComparisonResult::rejection_reason)
        .def_rw("errors", &MaintainedWorldlineComparisonResult::errors)
        .def_rw("evidence_refs", &MaintainedWorldlineComparisonResult::evidence_refs);

    nb::class_<WorldTerrainAssignment> world_terrain_assignment_class(m, "WorldTerrainAssignment");
    world_terrain_assignment_class.def(nb::init<>());
#define EF_WORLD_TERRAIN_ASSIGNMENT_FIELD(type, name, default_value)                               \
    world_terrain_assignment_class.def_rw(#name, &WorldTerrainAssignment::name);
#include "runtime/contracts/detail/platform/world_terrain_assignment.inc"

    nb::class_<WorldWindAssignment> world_wind_assignment_class(m, "WorldWindAssignment");
    world_wind_assignment_class.def(nb::init<>());
#define EF_WORLD_WIND_ASSIGNMENT_FIELD(type, name, default_value)                                  \
    world_wind_assignment_class.def_rw(#name, &WorldWindAssignment::name);
#include "runtime/contracts/detail/platform/world_wind_assignment.inc"

    nb::class_<WorldSunAssignment>(m, "WorldSunAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldSunAssignment::world_index)
        .def_rw("azimuth_deg", &WorldSunAssignment::azimuth_deg)
        .def_rw("elevation_deg", &WorldSunAssignment::elevation_deg);

    nb::class_<WorldZoneDefinition> world_zone_definition_class(m, "WorldZoneDefinition");
    world_zone_definition_class.def(nb::init<>());
#define EF_WORLD_ZONE_DEFINITION_FIELD(type, name, default_value)                                  \
    world_zone_definition_class.def_rw(#name, &WorldZoneDefinition::name);
#include "runtime/contracts/detail/platform/world_zone_definition.inc"

    nb::class_<WorldSpawnRequest> world_spawn_request_class(m, "WorldSpawnRequest");
    world_spawn_request_class.def(nb::init<>());
#define EF_WORLD_SPAWN_REQUEST_FIELD(type, name, default_value)                                    \
    world_spawn_request_class.def_rw(#name, &WorldSpawnRequest::name);
#include "runtime/contracts/detail/platform/world_spawn_request.inc"

    nb::class_<WorldPilotActionAssignment> world_pilot_action_assignment_class(
        m, "WorldPilotActionAssignment");
    world_pilot_action_assignment_class.def(nb::init<>());
#define EF_WORLD_PILOT_ACTION_ASSIGNMENT_FIELD(type, name, default_value)                          \
    world_pilot_action_assignment_class.def_rw(#name, &WorldPilotActionAssignment::name);
#include "runtime/contracts/detail/tasking/world_pilot_action_assignment.inc"

    nb::class_<WorldMissionCommandAssignment> world_mission_command_assignment_class(
        m, "WorldMissionCommandAssignment");
    world_mission_command_assignment_class.def(nb::init<>());
#define EF_WORLD_MISSION_COMMAND_ASSIGNMENT_FIELD(type, name, default_value)                       \
    world_mission_command_assignment_class.def_rw(#name, &WorldMissionCommandAssignment::name);
#include "runtime/contracts/detail/tasking/world_mission_command_assignment.inc"

    nb::class_<WorldMissionCommandMaintainedAssignment>
        world_mission_command_maintained_assignment_class(
            m, "WorldMissionCommandMaintainedAssignment");
    world_mission_command_maintained_assignment_class.def(nb::init<>());
#define EF_WORLD_MISSION_COMMAND_MAINTAINED_ASSIGNMENT_FIELD(type, name, default_value)            \
    world_mission_command_maintained_assignment_class.def_rw(                                      \
        #name, &WorldMissionCommandMaintainedAssignment::name);
#include "runtime/contracts/detail/tasking/world_mission_command_maintained_assignment.inc"

    nb::class_<WorldTaskOrderMaintainedAssignment> world_task_order_maintained_assignment_class(
        m, "WorldTaskOrderMaintainedAssignment");
    world_task_order_maintained_assignment_class.def(nb::init<>());
#define EF_WORLD_TASK_ORDER_MAINTAINED_ASSIGNMENT_FIELD(type, name, default_value)                 \
    world_task_order_maintained_assignment_class.def_rw(                                           \
        #name, &WorldTaskOrderMaintainedAssignment::name);
#include "runtime/contracts/detail/tasking/world_task_order_maintained_assignment.inc"

    nb::class_<WorldLeaderIntentAssignment> world_leader_intent_assignment_class(
        m, "WorldLeaderIntentAssignment");
    world_leader_intent_assignment_class.def(nb::init<>());
#define EF_WORLD_LEADER_INTENT_ASSIGNMENT_FIELD(type, name, default_value)                         \
    world_leader_intent_assignment_class.def_rw(#name, &WorldLeaderIntentAssignment::name);
#include "runtime/contracts/detail/tasking/world_leader_intent_assignment.inc"

    nb::class_<WorldLeaderIntentMaintainedAssignment>
        world_leader_intent_maintained_assignment_class(m, "WorldLeaderIntentMaintainedAssignment");
    world_leader_intent_maintained_assignment_class.def(nb::init<>());
#define EF_WORLD_LEADER_INTENT_MAINTAINED_ASSIGNMENT_FIELD(type, name, default_value)              \
    world_leader_intent_maintained_assignment_class.def_rw(                                        \
        #name, &WorldLeaderIntentMaintainedAssignment::name);
#include "runtime/contracts/detail/tasking/world_leader_intent_maintained_assignment.inc"

    nb::class_<WorldPilotReportAssignment> world_pilot_report_assignment_class(
        m, "WorldPilotReportAssignment");
    world_pilot_report_assignment_class.def(nb::init<>());
#define EF_WORLD_PILOT_REPORT_ASSIGNMENT_FIELD(type, name, default_value)                          \
    world_pilot_report_assignment_class.def_rw(#name, &WorldPilotReportAssignment::name);
#include "runtime/contracts/detail/tasking/world_pilot_report_assignment.inc"

    nb::class_<WorldPilotReportMaintainedAssignment> world_pilot_report_maintained_assignment_class(
        m, "WorldPilotReportMaintainedAssignment");
    world_pilot_report_maintained_assignment_class.def(nb::init<>());
#define EF_WORLD_PILOT_REPORT_MAINTAINED_ASSIGNMENT_FIELD(type, name, default_value)               \
    world_pilot_report_maintained_assignment_class.def_rw(                                         \
        #name, &WorldPilotReportMaintainedAssignment::name);
#include "runtime/contracts/detail/tasking/world_pilot_report_maintained_assignment.inc"

    nb::class_<WorldExecutionEpisodeStepRequest> world_execution_episode_step_request_class(
        m, "WorldExecutionEpisodeStepRequest");
    world_execution_episode_step_request_class.def(nb::init<>());
#define EF_WORLD_EXECUTION_EPISODE_STEP_REQUEST_FIELD(type, name, default_value)                   \
    world_execution_episode_step_request_class.def_rw(#name,                                       \
                                                      &WorldExecutionEpisodeStepRequest::name);
#include "runtime/contracts/detail/tasking/world_execution_episode_step_request.inc"

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
        .def("set_suns_batch", &WorldBatchRuntime::set_suns_batch, nb::arg("assignments"))
        .def("clear_zones_batch", &WorldBatchRuntime::clear_zones_batch,
             nb::arg("world_indices") = std::vector<uint64_t>{})
        .def("add_zones_batch", &WorldBatchRuntime::add_zones_batch, nb::arg("zones"))
        .def("spawn_units_batch", &WorldBatchRuntime::spawn_units_batch, nb::arg("requests"))
        .def("apply_world_setup_batch", &WorldBatchRuntime::apply_world_setup_batch,
             nb::arg("seeds"), nb::arg("terrain_assignments"), nb::arg("wind_assignments"),
             nb::arg("zones"), nb::arg("requests"), nb::arg("time_steps") = std::vector<double>{},
             nb::arg("sun_assignments") = std::vector<WorldSunAssignment>{})
        .def("apply_world_layout", &WorldBatchRuntime::apply_world_layout, nb::arg("world_index"),
             nb::arg("seed"), nb::arg("terrain_type"), nb::arg("wind_speed_mps"),
             nb::arg("wind_dir_from_deg"), nb::arg("wind_shear_mps_per_km"),
             nb::arg("maritime_configured"), nb::arg("sea_state"), nb::arg("wave_heading_deg"),
             nb::arg("wave_period_s"), nb::arg("zones"), nb::arg("requests"),
             nb::arg("time_steps") = std::vector<double>{}, nb::arg("sun_azimuth_deg") = 0.0,
             nb::arg("sun_elevation_deg") = 45.0)
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
        .def("export_composition_evidence", &RuntimeFacade::export_composition_evidence)
        .def("compare_composition_evidence", &RuntimeFacade::compare_composition_evidence,
             nb::arg("expected"))
        .def("admit_backend_request", &RuntimeFacade::admit_backend_request, nb::arg("request"))
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
             nb::arg("requests"), nb::arg("time_steps") = std::vector<double>{},
             nb::arg("sun_assignments") = std::vector<WorldSunAssignment>{})
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
        .def("run_window", &RuntimeFacade::run_window, nb::arg("request"))
        // Additive run-global snapshot-version and trace-id producers. They are
        // not wired into any existing export path without explicit opt-in.
        .def("allocate_run_snapshot_version", &RuntimeFacade::allocate_run_snapshot_version)
        .def("peek_next_run_snapshot_version", &RuntimeFacade::peek_next_run_snapshot_version)
        .def("allocate_trace_id", &RuntimeFacade::allocate_trace_id)
        .def("peek_next_trace_id", &RuntimeFacade::peek_next_trace_id)
        // Additive read-only declaration export of the maintained observation
        // view.
        // Not wired into any existing export path; gated against the Python
        // registry by the export-parity architecture test.
        .def("describe_maintained_observation_view",
             &RuntimeFacade::describe_maintained_observation_view)
        // Additive read-only maintained-run replay-envelope producer. Not wired
        // into any existing path; only meaningful against window evidence
        // stamped by the facade-evidence opt-in
        // (use_facade_evidence_producers=True) adapter path. See the
        // declaration comment in runtime_facade.h for the field sources, the
        // "replay:maintained:*" id namespace, and the opt-in
        // `run_snapshot_version` qualification (default 0 = off, keeping
        // the packet's per-export provenance string byte-identical).
        .def("build_maintained_replay_envelope", &RuntimeFacade::build_maintained_replay_envelope,
             nb::arg("window_result"), nb::arg("run_id"), nb::arg("episode_id"),
             nb::arg("deterministic_seed"), nb::arg("run_snapshot_version") = 0)
        // Additive read-only maintained engagement-packet ancestry producer. It
        // is not wired into any existing path and is only meaningful against
        // window evidence stamped by the facade-evidence opt-in
        // (use_facade_evidence_producers=True) adapter path.
        // See the declaration comment in runtime_facade.h for the gate order,
        // the "ancestry:maintained:*" id namespace, and the root semantics of
        // parent_trace_id = 0 (default = no parent linkage, keeping every
        // trace copy's parent_trace_id at the existing default 0).
        .def("build_maintained_packet_ancestry", &RuntimeFacade::build_maintained_packet_ancestry,
             nb::arg("window_result"), nb::arg("run_id"), nb::arg("episode_id"),
             nb::arg("deterministic_seed"), nb::arg("parent_trace_id") = 0)
        // Additive read-only maintained worldline/counterfactual comparison
        // producer. It is not wired into any existing path and is only
        // meaningful against window evidence
        // stamped by the facade-evidence opt-in (use_facade_evidence_producers=True)
        // adapter path. See the declaration comment in runtime_facade.h for
        // the gate order, the "comparison:maintained:*" /
        // "worldline:maintained:*" id namespaces, and the no-truth-promotion
        // red line (evidence ids only, never copies of truth state).
        .def("build_maintained_worldline_comparison",
             &RuntimeFacade::build_maintained_worldline_comparison,
             nb::arg("baseline_window_result"), nb::arg("candidate_window_result"),
             nb::arg("run_id"), nb::arg("episode_id"), nb::arg("baseline_deterministic_seed"),
             nb::arg("candidate_deterministic_seed"), nb::arg("baseline_parent_trace_id") = 0,
             nb::arg("candidate_parent_trace_id") = 0);
}
