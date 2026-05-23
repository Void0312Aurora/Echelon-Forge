#pragma once

#include <string>
#include <vector>

#include "runtime/contracts/backend_profile_contracts.h"
#include "runtime/contracts/counterfactual_replay_replay_validation.h"
#include "runtime/contracts/fidelity_profile_contracts.h"

namespace runtime::counterfactual {

[[nodiscard]] inline std::vector<std::string>
ordered_counterfactual_request_evidence_refs(
    const CounterfactualExperimentRequest& request
) {
    std::vector<std::string> refs = {
        "baseline_worldline_id=" + request.baseline_worldline_id,
        "replay_envelope_id=" + request.replay_envelope.replay_envelope_id,
        "branch_point_id=" + request.branch_point.branch_point_id,
        "worldline_child_id=" + request.worldline_branch_metadata.child_worldline_id,
        "source=" + request.source,
        "authority_ref=" + request.authority_ref,
        "provenance_ref=" + request.provenance_ref,
        "backend_profile_ref=" + request.backend_profile_ref,
        "fidelity_profile_ref=" + request.fidelity_profile_ref,
    };
    refs.reserve(
        refs.size() + request.capability_refs.size() +
        request.authority_evidence_refs.size() + request.evidence_refs.size()
    );
    for (const auto& capability_ref : request.capability_refs) {
        refs.push_back("capability_ref=" + capability_ref);
    }
    for (const auto& authority_evidence_ref : request.authority_evidence_refs) {
        refs.push_back("authority_evidence_ref=" + authority_evidence_ref);
    }
    for (const auto& evidence_ref : request.evidence_refs) {
        refs.push_back("evidence_ref=" + evidence_ref);
    }
    return refs;
}

[[nodiscard]] inline ReplayContractValidationResult validate_counterfactual_authority_surface(
    const CounterfactualExperimentRequest& request
) {
    ReplayContractValidationResult result{};

    if (replay_contract_is_blank(request.authority_ref)) {
        result.reject(std::string(kCounterfactualRequestRejectionMissingAuthorityRef));
        result.add_error("authority_ref is required");
    }
    if (replay_contract_is_blank(request.provenance_ref)) {
        result.reject(std::string(kCounterfactualRequestRejectionMissingProvenanceRef));
        result.add_error("provenance_ref is required");
    }
    if (!agent_authority_scope_has_required_shape(request.authority_scope)) {
        result.reject(
            std::string(kCounterfactualRequestRejectionInvalidAuthorityScope)
        );
        result.add_error(
            "authority_scope must carry a valid WP12 authority shape"
        );
    }
    if (!maintained_information_state_source_is_authorized_for_agent_role(
            request.authority_information_state)) {
        result.reject(
            std::string(kCounterfactualRequestRejectionInvalidAuthoritySource)
        );
        result.add_error(
            "authority_information_state must be maintained AgentObservation or DecisionBelief provenance"
        );
    }
    if (request.authority_evidence_refs.empty() ||
        replay_contract_has_blank_value(request.authority_evidence_refs)) {
        result.reject(
            std::string(
                kCounterfactualRequestRejectionMissingAuthorityEvidenceRefs
            )
        );
        result.add_error(
            "authority_evidence_refs must not be empty or contain blank entries"
        );
    }

    return result;
}

[[nodiscard]] inline ReplayContractValidationResult
validate_counterfactual_backend_and_fidelity_refs(
    const CounterfactualExperimentRequest& request
) {
    ReplayContractValidationResult result{};
    const backend_profiles::BackendProfileContract* profile = nullptr;

    if (replay_contract_is_blank(request.backend_profile_ref)) {
        result.reject(
            std::string(
                kCounterfactualRequestRejectionMissingBackendProfileRef
            )
        );
        result.add_error("backend_profile_ref is required");
    } else {
        profile = backend_profiles::find_backend_profile_contract(
            request.backend_profile_ref
        );
        if (profile == nullptr) {
            result.reject(
                std::string(
                    kCounterfactualRequestRejectionUnsupportedBackendProfileRef
                )
            );
            result.add_error(
                "backend_profile_ref must resolve to a registered backend profile"
            );
        } else {
            const backend_profiles::BackendProfileValidationResult profile_result =
                backend_profiles::validate_backend_profile_contract(*profile);
            if (!profile_result.valid) {
                result.reject(
                    std::string(
                        kCounterfactualRequestRejectionInvalidBackendProfileRef
                    )
                );
                for (const auto& error : profile_result.errors) {
                    result.add_error("backend_profile_ref validation: " + error);
                }
            }
        }
    }

    if (replay_contract_is_blank(request.fidelity_profile_ref)) {
        result.reject(
            std::string(
                kCounterfactualRequestRejectionMissingFidelityProfileRef
            )
        );
        result.add_error("fidelity_profile_ref is required");
    } else if (profile != nullptr) {
        fidelity::FidelityProfileRequest fidelity_request{};
        fidelity_request.request_label = request.fidelity_profile_ref;
        fidelity_request.backend_profile_id = request.backend_profile_ref;
        fidelity_request.parity_budget_ref = profile->parity_budget_ref;
        fidelity_request.model_family_scope = {
            "P0-P10 semantic lifecycle",
            "counterfactual_admission",
        };
        fidelity_request.validation_gate =
            "WP15-C counterfactual admission evidence constraint";
        fidelity_request.facade_evidence_refs = request.evidence_refs;
        const fidelity::FidelityProfileAdmissionResult fidelity_result =
            fidelity::admit_fidelity_profile_request(fidelity_request);
        if (!fidelity_result.admitted) {
            result.reject(
                std::string(
                    kCounterfactualRequestRejectionUnsupportedFidelityProfileRef
                )
            );
            if (!fidelity_result.rejection_reason.empty()) {
                result.add_error(
                    "fidelity_profile_ref rejection: " +
                    fidelity_result.rejection_reason
                );
            }
            result.errors.insert(
                result.errors.end(),
                fidelity_result.errors.begin(),
                fidelity_result.errors.end()
            );
        }
    }

    return result;
}

[[nodiscard]] inline ReplayContractValidationResult
validate_counterfactual_experiment_request(
    const CounterfactualExperimentRequest& request
) {
    ReplayContractValidationResult result{};

    if (replay_contract_is_blank(request.request_id)) {
        result.reject(std::string(kCounterfactualRequestRejectionMissingRequestId));
        result.add_error("request_id is required");
    }
    if (replay_contract_is_blank(request.baseline_worldline_id)) {
        result.reject(
            std::string(
                kCounterfactualRequestRejectionMissingBaselineWorldlineId
            )
        );
        result.add_error("baseline_worldline_id is required");
    }
    if (replay_contract_is_blank(request.intervention_kind)) {
        result.reject(
            std::string(
                kCounterfactualRequestRejectionMissingInterventionKind
            )
        );
        result.add_error("intervention_kind is required");
    } else if (!is_known_counterfactual_intervention_kind(
                   request.intervention_kind)) {
        result.reject(
            std::string(
                kCounterfactualRequestRejectionUnsupportedInterventionKind
            )
        );
        result.add_error(
            "intervention_kind is outside the maintained WP15-C vocabulary"
        );
    }
    if (replay_contract_is_blank(request.source)) {
        result.reject(std::string(kCounterfactualRequestRejectionMissingSource));
        result.add_error("source is required");
    } else if (!is_known_counterfactual_source(request.source)) {
        result.reject(
            std::string(kCounterfactualRequestRejectionUnsupportedSource)
        );
        result.add_error("source is outside the maintained WP15-C vocabulary");
    }
    if (request.requests_authoritative_state_mutation ||
        request.intervention_kind ==
            kCounterfactualInterventionKindRawAuthoritativeStateMutation ||
        request.worldline_branch_metadata.requests_authoritative_state_mutation ||
        request.worldline_branch_metadata.mutation_intent ==
            kWorldlineBranchMutationIntentRawAuthoritativeStateMutation) {
        result.reject(
            std::string(
                kCounterfactualRequestRejectionRawStateMutationForbidden
            )
        );
        result.add_error(
            "raw authoritative state mutation cannot be requested through WP15-C admission"
        );
    }
    if (request.snapshot_restore_supported) {
        result.reject(
            std::string(
                kCounterfactualRequestRejectionRestoreUnsupportedBoundary
            )
        );
        result.add_error("snapshot_restore_supported must remain false in WP15-C");
    }
    if (request.restore_support_boundary !=
        kReplayRestoreSupportBoundaryUnsupported) {
        result.reject(
            std::string(
                kCounterfactualRequestRejectionRestoreUnsupportedBoundary
            )
        );
        result.add_error(
            "restore_support_boundary must remain restore_unsupported_until_snapshot_restore_proof"
        );
    }

    absorb_replay_validation(
        &result,
        validate_worldline_branch_metadata_against_branch_point(
            request.worldline_branch_metadata,
            request.branch_point,
            request.replay_envelope
        )
    );
    absorb_replay_validation(
        &result,
        validate_counterfactual_authority_surface(request)
    );
    absorb_replay_validation(
        &result,
        validate_counterfactual_backend_and_fidelity_refs(request)
    );

    if (!replay_contract_is_blank(request.baseline_worldline_id) &&
        request.worldline_branch_metadata.baseline_worldline_id !=
            request.baseline_worldline_id) {
        result.reject(
            std::string(
                kCounterfactualRequestRejectionBaselineWorldlineMismatch
            )
        );
        result.add_error(
            "baseline_worldline_id must match worldline_branch_metadata.baseline_worldline_id"
        );
    }
    if (request.worldline_branch_metadata.support_state !=
        kWorldlineBranchSupportStateMetadataOnly) {
        result.reject(
            std::string(
                kCounterfactualRequestRejectionWorldlineSupportStatePreclaimForbidden
            )
        );
        result.add_error(
            "worldline_branch_metadata.support_state must remain metadata_only before admission"
        );
    }
    if (request.capability_refs.empty() ||
        replay_contract_has_blank_value(request.capability_refs)) {
        result.reject(
            std::string(kCounterfactualRequestRejectionMissingCapabilityRefs)
        );
        result.add_error(
            "capability_refs must not be empty or contain blank entries"
        );
    } else {
        for (const auto& capability_ref : request.capability_refs) {
            if (!is_supported_counterfactual_capability_ref(capability_ref)) {
                result.reject(
                    std::string(
                        kCounterfactualRequestRejectionUnsupportedCapabilityRef
                    )
                );
                result.add_error(
                    "capability_refs must use capability_bundle: or resolved_spawn_plan: refs"
                );
                break;
            }
        }
    }
    if (request.evidence_refs.empty() ||
        replay_contract_has_blank_value(request.evidence_refs)) {
        result.reject(
            std::string(kCounterfactualRequestRejectionMissingEvidenceRefs)
        );
        result.add_error(
            "evidence_refs must not be empty or contain blank entries"
        );
    }

    return result;
}

[[nodiscard]] inline CounterfactualAdmissionResult
admit_counterfactual_experiment_request(
    const CounterfactualExperimentRequest& request
) {
    CounterfactualAdmissionResult result{};
    result.request_id = request.request_id;
    result.baseline_worldline_id = request.baseline_worldline_id;
    result.child_worldline_id = request.worldline_branch_metadata.child_worldline_id;
    result.replay_envelope_id = request.replay_envelope.replay_envelope_id;
    result.branch_point_id = request.branch_point.branch_point_id;
    result.intervention_kind = request.intervention_kind;
    result.source = request.source;
    result.authority_ref = request.authority_ref;
    result.provenance_ref = request.provenance_ref;
    result.backend_profile_ref = request.backend_profile_ref;
    result.fidelity_profile_ref = request.fidelity_profile_ref;
    result.capability_refs = request.capability_refs;
    result.restore_support_boundary = request.restore_support_boundary;
    result.evidence_refs = ordered_counterfactual_request_evidence_refs(request);

    const ReplayContractValidationResult validation =
        validate_counterfactual_experiment_request(request);
    if (!validation.valid) {
        result.reject(validation.rejection_reason);
        result.errors.insert(
            result.errors.end(),
            validation.errors.begin(),
            validation.errors.end()
        );
        return result;
    }

    if (request.requests_executable_branch) {
        result.admission_state =
            std::string(kCounterfactualAdmissionStateRestoreUnsupported);
        result.worldline_support_state =
            std::string(kWorldlineBranchSupportStateRestoreUnsupported);
        result.rejection_reason = std::string(
            kCounterfactualRequestRejectionRestoreUnsupportedBoundary
        );
        return result;
    }

    result.admitted = true;
    result.admission_state = std::string(kCounterfactualAdmissionStateAdmitted);
    result.worldline_support_state =
        std::string(kWorldlineBranchSupportStateMetadataOnly);
    return result;
}

}  // namespace runtime::counterfactual
