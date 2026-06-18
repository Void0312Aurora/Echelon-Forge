#include "runtime/facade/runtime_facade_internal.h"

#include "runtime/contracts/fidelity_profile_contracts.h"

#include <string>

namespace {

using namespace runtime_facade_internal;

runtime::fidelity::FidelityProfileRequest
fidelity_contract_request_from_facade(const RuntimeFidelityRequest &request) {
    return runtime::fidelity::FidelityProfileRequest{
        .request_label = request.request_label,
        .backend_profile_id = request.backend_profile_id,
        .parity_budget_ref = request.parity_budget_ref,
        .model_family_scope = request.model_family_scope,
        .validation_gate = request.validation_gate,
        .facade_evidence_refs = request.facade_evidence_refs,
        .requests_adaptive_scheduling = false,
        .requests_learned_model_provider = false,
        .requests_approximate_execution = false,
        .requests_exact_gpu_backend =
            request.provider_family != kRuntimeFidelityProviderFamilyNone &&
            request.provider_family != kRuntimeFidelityProviderFamilyReferenceCpu &&
            request.provider_family != "resident" && request.provider_family != "resident_state" &&
            request.provider_family != "shadow",
        .requests_resident_state =
            request.provider_family == "resident" || request.provider_family == "resident_state",
        .requests_shadow_compare = request.provider_family == "shadow",
    };
}

RuntimeFidelityAdmission runtime_fidelity_admission_from_contract(
    const RuntimeFidelityRequest &request,
    const runtime::fidelity::FidelityProfileAdmissionResult &contract_result) {
    RuntimeFidelityAdmission admission{};
    admission.admitted = contract_result.admitted;
    admission.baseline_exact_evaluation = contract_result.baseline_exact_evaluation;
    admission.request_label = contract_result.request_label;
    admission.backend_profile_id = contract_result.backend_profile_id;
    admission.parity_budget_ref = contract_result.parity_budget_ref;
    admission.requested_provider_family = request.provider_family;
    admission.rejection_reason = contract_result.rejection_reason;
    admission.errors = contract_result.errors;
    admission.evidence_refs = contract_result.evidence_refs;
    return admission;
}

} // namespace

void RuntimeFacade::configure_batch(const RuntimeBatchConfig &config) {
    runtime_->resize(config.world_count);
    runtime_->set_worker_threads(config.worker_threads);
}

RuntimeBatchConfig RuntimeFacade::batch_config() const noexcept {
    return RuntimeBatchConfig{
        .world_count = runtime_->world_count(),
        .worker_threads = runtime_->worker_threads(),
    };
}

RuntimeCapabilities RuntimeFacade::capabilities() const noexcept {
    return RuntimeCapabilities{
        .supports_batch_runtime = runtime_ != nullptr,
        .supports_compiled_episode_controller = true,
        .supports_compiled_execution_step = true,
        .supports_gpu_visual = false,
        .supports_gpu_observation = false,
        .supports_gpu_flight_shaping = false,
        .supports_device_observation_view = false,
        .supports_resident_state = false,
        .supports_exact_gpu_backend = false,
        .supports_shadow_compare = false,
        .maintained_baseline_backend_profile_id = std::string(kMaintainedBaselineBackendProfileId),
        .maintained_baseline_parity_budget_ref = std::string(kMaintainedBaselineParityBudgetRef),
        .maintained_baseline_profile_status = std::string(kMaintainedBaselineProfileStatus),
        .device_observation_view_candidate_profile_id =
            std::string(kDeviceObservationViewCandidateProfileId),
        .device_observation_view_rejection_reason =
            std::string(kDeviceObservationViewRejectionReason),
        .exact_gpu_backend_candidate_profile_id = std::string(kExactGpuBackendCandidateProfileId),
        .exact_gpu_backend_rejection_reason = std::string(kExactGpuBackendRejectionReason),
        .resident_state_candidate_profile_id = std::string(kResidentStateCandidateProfileId),
        .resident_state_candidate_parity_budget_ref =
            std::string(kResidentStateCandidateParityBudgetRef),
        .resident_state_rejection_reason = std::string(kResidentStateRejectionReason),
        .shadow_compare_candidate_profile_id = std::string(kShadowCompareCandidateProfileId),
        .shadow_compare_candidate_parity_budget_ref =
            std::string(kShadowCompareCandidateParityBudgetRef),
        .shadow_compare_rejection_reason = std::string(kShadowCompareRejectionReason),
        .multi_fidelity_rejection_reason = std::string(kMultiFidelityRejectionReason),
    };
}

RuntimeFidelityAdmission
RuntimeFacade::admit_fidelity_request(const RuntimeFidelityRequest &request) const {
    RuntimeFidelityRequest normalized = request;
    if (normalized.provider_family.empty()) {
        normalized.provider_family = std::string(kRuntimeFidelityProviderFamilyNone);
    }

    const runtime::fidelity::FidelityProfileAdmissionResult contract_result =
        runtime::fidelity::admit_fidelity_profile_request(
            fidelity_contract_request_from_facade(normalized));
    RuntimeFidelityAdmission admission =
        runtime_fidelity_admission_from_contract(normalized, contract_result);

    if (!contract_result.admitted) {
        return admission;
    }

    if (normalized.provider_family == kRuntimeFidelityProviderFamilyNone) {
        admission.selected_provider_family = std::string(kRuntimeFidelityProviderFamilyNone);
        if (find_stage_node_manifest(kWp10ObservationExportNodeId) != nullptr) {
            admission.selected_stage_node_id = std::string(kWp10ObservationExportNodeId);
        }
        return admission;
    }

    if (normalized.provider_family == kRuntimeFidelityProviderFamilyReferenceCpu) {
        admission.selected_provider_family =
            std::string(kRuntimeFidelityProviderFamilyReferenceCpu);
        if (find_stage_node_manifest(kWp10ObservationExportNodeId) != nullptr) {
            admission.selected_stage_node_id = std::string(kWp10ObservationExportNodeId);
        }
        return admission;
    }

    admission.admitted = false;
    admission.baseline_exact_evaluation = false;
    admission.selected_provider_family = std::string(kRuntimeFidelityProviderFamilyNone);
    admission.selected_stage_node_id.clear();
    if (normalized.provider_family == "resident" ||
        normalized.provider_family == "resident_state") {
        admission.rejection_reason =
            std::string(runtime::fidelity::kFidelityProfileRejectionResidentState);
    } else if (normalized.provider_family == "shadow") {
        admission.rejection_reason =
            std::string(runtime::fidelity::kFidelityProfileRejectionShadowCompare);
    } else {
        admission.rejection_reason =
            std::string(runtime::fidelity::kFidelityProfileRejectionExactGpu);
    }
    if (admission.errors.empty()) {
        admission.errors.push_back(
            "requested provider_family is not maintained by the facade-owned baseline");
    }
    return admission;
}

std::size_t RuntimeFacade::world_count() const noexcept {
    return runtime_->world_count();
}

void RuntimeFacade::resize(std::size_t world_count) {
    runtime_->resize(world_count);
}

void RuntimeFacade::set_worker_threads(std::size_t worker_threads) noexcept {
    runtime_->set_worker_threads(worker_threads);
}

std::size_t RuntimeFacade::worker_threads() const noexcept {
    return runtime_->worker_threads();
}

std::size_t RuntimeFacade::effective_worker_threads() const noexcept {
    return runtime_->effective_worker_threads();
}

bool RuntimeFacade::load_database(const std::string &path) {
    return runtime_->load_database(path);
}

bool RuntimeFacade::load_unit_definitions(const std::string &path, std::string *error) {
    return runtime_->load_unit_definitions(path, error);
}
