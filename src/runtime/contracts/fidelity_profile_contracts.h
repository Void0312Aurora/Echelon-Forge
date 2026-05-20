#pragma once

#include <algorithm>
#include <cctype>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "runtime/contracts/backend_profile_contracts.h"
#include "runtime/contracts/parity_budget_contracts.h"

namespace runtime::fidelity {

inline constexpr std::string_view kFidelityProfileLabelExactEvaluation =
    "exact_evaluation";
inline constexpr std::string_view kFidelityProfileLabelFastTraining =
    "fast_training";
inline constexpr std::string_view kFidelityProfileLabelSensorHeavy =
    "sensor_heavy";
inline constexpr std::string_view kFidelityProfileLabelWeaponEffectsHeavy =
    "weapon_effects_heavy";
inline constexpr std::string_view kFidelityProfileLabelLargeScaleSwarm =
    "large_scale_swarm";
inline constexpr std::string_view kFidelityProfileLabelSinglePlatformPhysics =
    "single_platform_physics";

inline constexpr std::string_view kFidelityProfileRejectionMissingLabel =
    "fidelity_profile_label_required";
inline constexpr std::string_view kFidelityProfileRejectionUnsupportedLabel =
    "fidelity_profile_label_not_maintained";
inline constexpr std::string_view kFidelityProfileRejectionMissingBackendProfile =
    "fidelity_profile_requires_backend_profile_id";
inline constexpr std::string_view kFidelityProfileRejectionRequiresMaintainedBackendProfile =
    "fidelity_profile_requires_maintained_backend_profile";
inline constexpr std::string_view kFidelityProfileRejectionMissingBudget =
    "fidelity_profile_requires_parity_budget_ref";
inline constexpr std::string_view kFidelityProfileRejectionRequiresAcceptedBudget =
    "fidelity_profile_requires_accepted_budget";
inline constexpr std::string_view kFidelityProfileRejectionMissingModelScope =
    "fidelity_profile_requires_model_family_scope";
inline constexpr std::string_view kFidelityProfileRejectionMissingValidationGate =
    "fidelity_profile_requires_validation_gate";
inline constexpr std::string_view kFidelityProfileRejectionMissingFacadeEvidence =
    "fidelity_profile_requires_facade_evidence";
inline constexpr std::string_view kFidelityProfileRejectionAdaptiveScheduling =
    "adaptive_fidelity_scheduling_not_implemented";
inline constexpr std::string_view kFidelityProfileRejectionLearnedProvider =
    "learned_model_provider_not_implemented";
inline constexpr std::string_view kFidelityProfileRejectionApproximateExecution =
    "approximate_fidelity_execution_not_maintained";
inline constexpr std::string_view kFidelityProfileRejectionExactGpu =
    "exact_gpu_fidelity_requires_maintained_backend_profile";
inline constexpr std::string_view kFidelityProfileRejectionResidentState =
    "resident_state_fidelity_requires_maintained_backend_profile";
inline constexpr std::string_view kFidelityProfileRejectionShadowCompare =
    "shadow_fidelity_requires_maintained_backend_profile";

struct FidelityProfileRequest {
    std::string request_label;
    std::string backend_profile_id;
    std::string parity_budget_ref;
    std::vector<std::string> model_family_scope;
    std::string validation_gate;
    std::vector<std::string> facade_evidence_refs;
    bool requests_adaptive_scheduling = false;
    bool requests_learned_model_provider = false;
    bool requests_approximate_execution = false;
    bool requests_exact_gpu_backend = false;
    bool requests_resident_state = false;
    bool requests_shadow_compare = false;
};

struct FidelityProfileAdmissionResult {
    bool admitted = false;
    bool baseline_exact_evaluation = false;
    std::string request_label;
    std::string backend_profile_id;
    std::string parity_budget_ref;
    std::string rejection_reason;
    std::vector<std::string> errors;
    std::vector<std::string> evidence_refs;

    void reject(std::string reason) {
        admitted = false;
        if (rejection_reason.empty()) {
            rejection_reason = std::move(reason);
        }
    }

    void add_error(std::string error) {
        errors.push_back(std::move(error));
    }
};

[[nodiscard]] inline bool is_blank(std::string_view value) {
    return std::all_of(value.begin(), value.end(), [](unsigned char c) {
        return std::isspace(c) != 0;
    });
}

[[nodiscard]] inline bool is_known_fidelity_profile_label(std::string_view label) {
    return label == kFidelityProfileLabelExactEvaluation ||
        label == kFidelityProfileLabelFastTraining ||
        label == kFidelityProfileLabelSensorHeavy ||
        label == kFidelityProfileLabelWeaponEffectsHeavy ||
        label == kFidelityProfileLabelLargeScaleSwarm ||
        label == kFidelityProfileLabelSinglePlatformPhysics;
}

[[nodiscard]] inline bool contains_blank_value(const std::vector<std::string>& values) {
    return std::any_of(values.begin(), values.end(), [](const std::string& value) {
        return is_blank(value);
    });
}

[[nodiscard]] inline FidelityProfileRequest
make_exact_evaluation_cpu_reference_request() {
    return FidelityProfileRequest{
        .request_label = std::string(kFidelityProfileLabelExactEvaluation),
        .backend_profile_id = std::string(
            backend_profiles::kBackendProfileIdCpuExactReference
        ),
        .parity_budget_ref = std::string(parity::kParityBudgetCpuExactReferenceV1),
        .model_family_scope = {
            "P0-P10 semantic lifecycle",
            "observation_packet",
            "diagnostics_trace",
        },
        .validation_gate =
            "WP13-D exact-evaluation baseline admission; no accelerated support implied",
        .facade_evidence_refs = {
            "RuntimeFacade.capabilities",
            "ObservationBatchPacket",
            "ExecutionBatchStepResult",
        },
    };
}

[[nodiscard]] inline FidelityProfileAdmissionResult reject_fidelity_request(
    const FidelityProfileRequest& request,
    std::string_view reason,
    std::string error
) {
    FidelityProfileAdmissionResult result{};
    result.request_label = request.request_label;
    result.backend_profile_id = request.backend_profile_id;
    result.parity_budget_ref = request.parity_budget_ref;
    result.reject(std::string(reason));
    result.add_error(std::move(error));
    return result;
}

[[nodiscard]] inline FidelityProfileAdmissionResult admit_fidelity_profile_request(
    const FidelityProfileRequest& request
) {
    if (is_blank(request.request_label)) {
        return reject_fidelity_request(
            request,
            kFidelityProfileRejectionMissingLabel,
            "request_label is required"
        );
    }
    if (!is_known_fidelity_profile_label(request.request_label)) {
        return reject_fidelity_request(
            request,
            kFidelityProfileRejectionUnsupportedLabel,
            "request_label is not in the maintained request vocabulary"
        );
    }
    if (request.requests_adaptive_scheduling) {
        return reject_fidelity_request(
            request,
            kFidelityProfileRejectionAdaptiveScheduling,
            "adaptive fidelity scheduling is outside WP13-D"
        );
    }
    if (request.requests_learned_model_provider) {
        return reject_fidelity_request(
            request,
            kFidelityProfileRejectionLearnedProvider,
            "learned ModelProvider runtime is outside WP13-D"
        );
    }
    if (request.requests_approximate_execution) {
        return reject_fidelity_request(
            request,
            kFidelityProfileRejectionApproximateExecution,
            "approximate fidelity execution is not maintained"
        );
    }
    if (request.requests_exact_gpu_backend) {
        return reject_fidelity_request(
            request,
            kFidelityProfileRejectionExactGpu,
            "exact GPU fidelity requires a maintained backend profile"
        );
    }
    if (request.requests_resident_state) {
        return reject_fidelity_request(
            request,
            kFidelityProfileRejectionResidentState,
            "resident-state fidelity requires a maintained backend profile"
        );
    }
    if (request.requests_shadow_compare) {
        return reject_fidelity_request(
            request,
            kFidelityProfileRejectionShadowCompare,
            "shadow-backed fidelity requires a maintained backend profile"
        );
    }
    if (is_blank(request.backend_profile_id)) {
        return reject_fidelity_request(
            request,
            kFidelityProfileRejectionMissingBackendProfile,
            "backend_profile_id is required"
        );
    }

    const backend_profiles::BackendProfileContract* profile =
        backend_profiles::find_backend_profile_contract(request.backend_profile_id);
    if (profile == nullptr || !backend_profiles::is_maintained_backend_profile(*profile)) {
        return reject_fidelity_request(
            request,
            kFidelityProfileRejectionRequiresMaintainedBackendProfile,
            "backend_profile_id must resolve to a maintained backend profile"
        );
    }

    const backend_profiles::BackendProfileValidationResult profile_result =
        backend_profiles::validate_maintained_backend_profile_contract(*profile);
    if (!profile_result.valid) {
        FidelityProfileAdmissionResult result = reject_fidelity_request(
            request,
            kFidelityProfileRejectionRequiresMaintainedBackendProfile,
            "maintained backend profile metadata did not validate"
        );
        result.errors.insert(
            result.errors.end(),
            profile_result.errors.begin(),
            profile_result.errors.end()
        );
        return result;
    }

    if (is_blank(request.parity_budget_ref)) {
        return reject_fidelity_request(
            request,
            kFidelityProfileRejectionMissingBudget,
            "parity_budget_ref is required"
        );
    }

    const parity::ParityBudgetValidationResult budget_result =
        parity::validate_profile_owned_parity_budget(
            profile->backend_profile_id,
            profile->profile_class,
            request.parity_budget_ref
        );
    if (!budget_result.valid || !budget_result.accepted_for_maintained_use) {
        FidelityProfileAdmissionResult result = reject_fidelity_request(
            request,
            kFidelityProfileRejectionRequiresAcceptedBudget,
            "parity_budget_ref must resolve to an accepted maintained budget"
        );
        if (!budget_result.rejection_reason.empty()) {
            result.add_error("budget rejection: " + budget_result.rejection_reason);
        }
        result.errors.insert(
            result.errors.end(),
            budget_result.errors.begin(),
            budget_result.errors.end()
        );
        return result;
    }

    if (request.model_family_scope.empty() ||
        contains_blank_value(request.model_family_scope)) {
        return reject_fidelity_request(
            request,
            kFidelityProfileRejectionMissingModelScope,
            "model_family_scope is required and cannot contain blank entries"
        );
    }
    if (is_blank(request.validation_gate)) {
        return reject_fidelity_request(
            request,
            kFidelityProfileRejectionMissingValidationGate,
            "validation_gate is required"
        );
    }
    if (request.facade_evidence_refs.empty() ||
        contains_blank_value(request.facade_evidence_refs)) {
        return reject_fidelity_request(
            request,
            kFidelityProfileRejectionMissingFacadeEvidence,
            "facade_evidence_refs is required and cannot contain blank entries"
        );
    }

    if (request.request_label != kFidelityProfileLabelExactEvaluation) {
        return reject_fidelity_request(
            request,
            kFidelityProfileRejectionUnsupportedLabel,
            "only exact_evaluation is admitted by the WP13-D baseline gate"
        );
    }

    FidelityProfileAdmissionResult result{};
    result.admitted = true;
    result.baseline_exact_evaluation = true;
    result.request_label = request.request_label;
    result.backend_profile_id = request.backend_profile_id;
    result.parity_budget_ref = request.parity_budget_ref;
    result.evidence_refs = request.facade_evidence_refs;
    return result;
}

}  // namespace runtime::fidelity
