#include "interfaces/python/bindings_runtime_detail.h"

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
}
