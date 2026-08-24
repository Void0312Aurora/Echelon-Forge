#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include "runtime/contracts/fidelity_profile_contracts.h"
#include "runtime/facade/runtime_facade.h"

void bind_runtime_fidelity(nb::module_ &m) {
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
}
