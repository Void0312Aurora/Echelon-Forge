#include "runtime/facade/runtime_facade_internal.h"

#include "runtime/contracts/cuda_resident_backend_admission.h"
#include "runtime/contracts/fidelity_profile_contracts.h"

#include <stdexcept>
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

runtime::cuda_resident::BackendRequest
backend_contract_request_from_facade(const RuntimeBackendRequest &request) {
    return runtime::cuda_resident::BackendRequest{
        .backend_profile_id = request.backend_profile_id,
        .capability_manifest_id = request.capability_manifest_id,
        .parity_budget_ref = request.parity_budget_ref,
        .requested_feature_ids = request.requested_feature_ids,
        .allow_unmaintained_candidate = request.allow_unmaintained_candidate,
    };
}

RuntimeBackendAdmission backend_admission_from_contract(
    const runtime::cuda_resident::BackendAdmissionResult &contract_result) {
    return RuntimeBackendAdmission{
        .admitted = contract_result.admitted,
        .maintained_selection = contract_result.maintained_selection,
        .experimental_selection = contract_result.experimental_selection,
        .backend_profile_id = contract_result.backend_profile_id,
        .capability_manifest_id = contract_result.capability_manifest_id,
        .parity_budget_ref = contract_result.parity_budget_ref,
        .admitted_feature_ids = contract_result.admitted_feature_ids,
        .rejection_reason = contract_result.rejection_reason,
        .errors = contract_result.errors,
    };
}

} // namespace

void RuntimeFacade::configure_batch(const RuntimeBatchConfig &config) {
    runtime_->configure(runtime::backend::ConfigureRequest{
        .world_count = config.world_count,
        .worker_threads = config.worker_threads,
    });
}

RuntimeBatchConfig RuntimeFacade::batch_config() const noexcept {
    const runtime::backend::Configuration config = runtime_->configuration();
    return RuntimeBatchConfig{
        .world_count = config.world_count,
        .worker_threads = config.worker_threads,
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

RuntimeBackendAdmission
RuntimeFacade::admit_backend_request(const RuntimeBackendRequest &request) const {
    // RB2 freezes the request/admission contract but does not construct a CUDA
    // backend. Keeping availability false here makes candidate selection fail
    // closed even in builds that contain older CUDA helper experiments.
    const runtime::cuda_resident::BackendAvailability availability{
        .compiled_experimental_backend = false,
    };
    return backend_admission_from_contract(runtime::cuda_resident::admit_backend_request(
        backend_contract_request_from_facade(request), availability));
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
        if (find_stage_node_manifest(kObservationExportNodeId) != nullptr) {
            admission.selected_stage_node_id = std::string(kObservationExportNodeId);
        }
        return admission;
    }

    if (normalized.provider_family == kRuntimeFidelityProviderFamilyReferenceCpu) {
        admission.selected_provider_family =
            std::string(kRuntimeFidelityProviderFamilyReferenceCpu);
        if (find_stage_node_manifest(kObservationExportNodeId) != nullptr) {
            admission.selected_stage_node_id = std::string(kObservationExportNodeId);
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
    return runtime_->configuration().world_count;
}

void RuntimeFacade::resize(std::size_t world_count) {
    runtime_->configure(runtime::backend::ConfigureRequest{.world_count = world_count});
}

void RuntimeFacade::set_worker_threads(std::size_t worker_threads) noexcept {
    runtime_->configure(runtime::backend::ConfigureRequest{.worker_threads = worker_threads});
}

std::size_t RuntimeFacade::worker_threads() const noexcept {
    return runtime_->configuration().worker_threads;
}

std::size_t RuntimeFacade::effective_worker_threads() const noexcept {
    return runtime_->configuration().effective_worker_threads;
}

bool RuntimeFacade::load_database(const std::string &path) {
    return runtime_
        ->load_content(runtime::backend::ContentRequest{
            .kind = runtime::backend::ContentKind::Database,
            .path = &path,
        })
        .loaded;
}

bool RuntimeFacade::load_unit_definitions(const std::string &path, std::string *error) {
    runtime::backend::ContentResult result =
        runtime_->load_content(runtime::backend::ContentRequest{
            .kind = runtime::backend::ContentKind::UnitDefinitions,
            .path = &path,
        });
    if (error != nullptr) {
        *error = result.error;
    }
    return result.loaded;
}

namespace {

// I54-R/I54-R2 fail-fast for invalidated evidence cursors, matching the
// facade/runtime family's existing throwing guards (std::out_of_range /
// std::invalid_argument in world_batch_runtime.cpp); std::logic_error is
// their shared base. The sentinel has two entry paths, so the message names
// both: a move transferred the run identity away, or the cursor exhausted its
// uint64 space (post-increment of UINT64_MAX wraps onto the sentinel).
[[noreturn]] void throw_evidence_allocator_invalidated() {
    throw std::logic_error(
        "RuntimeFacade evidence allocator invalidated: this facade was moved-from (the run "
        "identity transferred to the move destination) or the counter exhausted its uint64 "
        "id space");
}

} // namespace

// T10 evidence spine, slice 3 / I54 (VA-2, VA-8). Run-global monotone
// producers owned by the facade instance; see runtime_facade.h for the
// run-global boundary adjudication, the move/fail-fast semantics, and the
// uint64 exhaustion boundary (minting UINT64_MAX wraps the cursor onto the
// invalidated sentinel, after which the producers fail fast permanently).
// These are intentionally not invoked by any existing export path in this
// slice, so they perturb no serialized output.
std::uint64_t RuntimeFacade::allocate_run_snapshot_version() {
    if (next_run_snapshot_version_ == kInvalidatedEvidenceCursor) {
        throw_evidence_allocator_invalidated();
    }
    return next_run_snapshot_version_++;
}

std::uint64_t RuntimeFacade::peek_next_run_snapshot_version() const {
    if (next_run_snapshot_version_ == kInvalidatedEvidenceCursor) {
        throw_evidence_allocator_invalidated();
    }
    return next_run_snapshot_version_;
}

std::uint64_t RuntimeFacade::allocate_trace_id() {
    if (next_trace_id_ == kInvalidatedEvidenceCursor) {
        throw_evidence_allocator_invalidated();
    }
    return next_trace_id_++;
}

std::uint64_t RuntimeFacade::peek_next_trace_id() const {
    if (next_trace_id_ == kInvalidatedEvidenceCursor) {
        throw_evidence_allocator_invalidated();
    }
    return next_trace_id_;
}
