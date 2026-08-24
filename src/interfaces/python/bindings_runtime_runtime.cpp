#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include "runtime/facade/runtime_facade.h"

void bind_runtime_runtime(nb::module_ &m) {
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

    nb::class_<DeviceResidentOutputDescriptor> device_resident_output_descriptor_class(
        m, "DeviceResidentOutputDescriptor");
    device_resident_output_descriptor_class.def(nb::init<>());
#define EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD(type, name, default_value)                      \
    device_resident_output_descriptor_class.def_rw(#name, &DeviceResidentOutputDescriptor::name);
#include "runtime/facade/detail/runtime/resident_device_output_descriptor.inc"
}
