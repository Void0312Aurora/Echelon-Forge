#pragma once

#include <algorithm>
#include <cctype>
#include <cmath>
#include <string>
#include <string_view>
#include <vector>

#include "runtime/contracts/counterfactual_replay_contract_types.h"

namespace runtime::counterfactual {

[[nodiscard]] inline bool replay_contract_is_blank(std::string_view value) {
    return value.empty() || std::all_of(value.begin(), value.end(), [](unsigned char c) {
        return std::isspace(c) != 0;
    });
}

[[nodiscard]] inline bool replay_contract_has_finite_time(double value) {
    return std::isfinite(value) != 0;
}

[[nodiscard]] inline bool replay_contract_has_blank_value(
    const std::vector<std::string>& values
) {
    return std::any_of(values.begin(), values.end(), [](const std::string& value) {
        return replay_contract_is_blank(value);
    });
}

[[nodiscard]] inline bool is_known_worldline_branch_support_state(
    std::string_view support_state
) {
    return support_state == kWorldlineBranchSupportStateMetadataOnly ||
        support_state == kWorldlineBranchSupportStateAdmitted ||
        support_state == kWorldlineBranchSupportStateRejected ||
        support_state == kWorldlineBranchSupportStateRestoreUnsupported;
}

[[nodiscard]] inline bool is_supported_snapshot_restore_boundary(
    std::string_view boundary
) {
    return boundary == kReplayRestoreSupportBoundaryUnsupported ||
        boundary == kReplayRestoreSupportBoundaryHostOwnedFacadeStateOnly;
}

[[nodiscard]] inline bool is_known_worldline_branch_mutation_intent(
    std::string_view mutation_intent
) {
    return mutation_intent == kWorldlineBranchMutationIntentMetadataOnly ||
        mutation_intent == kWorldlineBranchMutationIntentSupportStateOnly ||
        mutation_intent ==
            kWorldlineBranchMutationIntentRawAuthoritativeStateMutation;
}

[[nodiscard]] inline bool is_known_counterfactual_intervention_kind(
    std::string_view intervention_kind
) {
    return intervention_kind == kCounterfactualInterventionKindObservationWithhold ||
        intervention_kind == kCounterfactualInterventionKindPolicySubstitution ||
        intervention_kind == kCounterfactualInterventionKindCommandVariant ||
        intervention_kind == kCounterfactualInterventionKindSpawnVariantRequest ||
        intervention_kind ==
            kCounterfactualInterventionKindRawAuthoritativeStateMutation;
}

[[nodiscard]] inline bool is_known_counterfactual_source(
    std::string_view source
) {
    return source == kCounterfactualSourceOperatorRequest ||
        source == kCounterfactualSourceAnalystRequest ||
        source == kCounterfactualSourceExperimentPlan ||
        source == kCounterfactualSourceCounterfactualBranch;
}

[[nodiscard]] inline bool is_supported_counterfactual_capability_ref(
    std::string_view capability_ref
) {
    return capability_ref.rfind(kCounterfactualCapabilityRefPrefixBundle, 0) == 0 ||
        capability_ref.rfind(kCounterfactualCapabilityRefPrefixResolvedSpawnPlan, 0) == 0;
}

[[nodiscard]] inline bool is_known_scenario_generation_kind(
    std::string_view generation_kind
) {
    return generation_kind == kScenarioGenerationKindScenarioVariation ||
        generation_kind == kScenarioGenerationKindAdversaryPlacement ||
        generation_kind == kScenarioGenerationKindRoutePerturbation ||
        generation_kind == kScenarioGenerationKindMissionPerturbation ||
        generation_kind == kScenarioGenerationKindStressorInjection;
}

[[nodiscard]] inline bool is_known_scenario_generation_source(
    std::string_view source
) {
    return source == kScenarioGenerationSourceAnalystAuthored ||
        source == kScenarioGenerationSourceCounterfactualBranch ||
        source == kScenarioGenerationSourceCurriculumGeneration ||
        source == kScenarioGenerationSourceEvaluationReplay;
}

[[nodiscard]] inline bool is_known_scenario_generation_evidence_kind(
    std::string_view evidence_kind
) {
    return evidence_kind == kScenarioGenerationEvidenceKindBaselineScenario ||
        evidence_kind == kScenarioGenerationEvidenceKindBranchPoint ||
        evidence_kind == kScenarioGenerationEvidenceKindCapabilityBundle ||
        evidence_kind == kScenarioGenerationEvidenceKindLearningEvidence ||
        evidence_kind == kScenarioGenerationEvidenceKindReplayEnvelope ||
        evidence_kind == kScenarioGenerationEvidenceKindReviewNote;
}

[[nodiscard]] inline bool is_known_experiment_profile_observation_status(
    std::string_view status
) {
    return status == kExperimentProfileObservationStatusObserved ||
        status == kExperimentProfileObservationStatusProposed ||
        status == kExperimentProfileObservationStatusBlocked ||
        status == kExperimentProfileObservationStatusUnsupported;
}

[[nodiscard]] inline bool is_known_experiment_profile_claim_scope(
    std::string_view claim_scope
) {
    return claim_scope == kExperimentProfileClaimScopeDescriptive ||
        claim_scope == kExperimentProfileClaimScopeComparative ||
        claim_scope == kExperimentProfileClaimScopeGatingRelated;
}

inline void absorb_experiment_bridge_validation(
    ExperimentEvidenceBridgeValidationResult* into,
    const ExperimentEvidenceBridgeValidationResult& from
) {
    if (into == nullptr || from.valid) {
        return;
    }
    if (into->rejection_reason.empty() && !from.rejection_reason.empty()) {
        into->rejection_reason = from.rejection_reason;
    }
    into->valid = false;
    into->fail_closed = into->fail_closed || from.fail_closed;
    into->errors.insert(into->errors.end(), from.errors.begin(), from.errors.end());
}

inline void absorb_replay_validation(
    ReplayContractValidationResult* into,
    const ReplayContractValidationResult& from
) {
    if (into == nullptr || from.valid) {
        return;
    }
    if (into->rejection_reason.empty() && !from.rejection_reason.empty()) {
        into->rejection_reason = from.rejection_reason;
    }
    into->valid = false;
    into->errors.insert(into->errors.end(), from.errors.begin(), from.errors.end());
}

}  // namespace runtime::counterfactual
