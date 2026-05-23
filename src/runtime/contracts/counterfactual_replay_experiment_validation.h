#pragma once

#include <algorithm>
#include <string>
#include <utility>
#include <vector>

#include "runtime/contracts/counterfactual_replay_counterfactual_validation.h"

namespace runtime::counterfactual {

[[nodiscard]] inline std::vector<std::string>
ordered_scenario_generation_request_metadata_evidence_refs(
    const ScenarioGenerationArtifactMetadata& artifact
) {
    std::vector<std::string> refs = {
        "generated_input_request_id=" + artifact.request.request_id,
        "generated_input_generation_kind=" + artifact.request.generation_kind,
        "generated_input_source=" + artifact.request.source,
        "generated_input_generator_version=" + artifact.request.generator_version,
        "generated_input_baseline_scenario_ref=" +
            artifact.request.baseline_scenario_ref,
        "generated_input_replay_envelope_ref=" +
            artifact.request.replay_envelope_ref,
        "generated_input_branch_point_ref=" + artifact.request.branch_point_ref,
    };
    refs.reserve(
        refs.size() + artifact.request.capability_refs.size() +
        artifact.request.evidence_refs.size()
    );
    for (const auto& capability_ref : artifact.request.capability_refs) {
        refs.push_back("generated_input_capability_ref=" + capability_ref);
    }
    for (const auto& evidence_ref : artifact.request.evidence_refs) {
        refs.push_back(
            "generated_input_evidence_ref=" + evidence_ref.evidence_kind + ":" +
            evidence_ref.ref_id + ":" + evidence_ref.provenance_label
        );
    }
    return refs;
}

[[nodiscard]] inline std::vector<std::string>
ordered_experiment_profile_observation_evidence_refs(
    const ExperimentProfileObservationRef& observation
) {
    std::vector<std::string> refs = {
        "profile_observation_ref=" + observation.observation_ref,
        "profile_ref=" + observation.profile_ref,
        "profile_status=" + observation.status,
        "profile_claim_scope=" + observation.claim_scope,
    };
    refs.reserve(refs.size() + observation.evidence_refs.size());
    for (const auto& evidence_ref : observation.evidence_refs) {
        refs.push_back("profile_evidence_ref=" + evidence_ref);
    }
    return refs;
}

[[nodiscard]] inline std::vector<std::string>
ordered_experiment_bridge_evidence_refs(
    const ExperimentEvidenceBridgeRecord& record
) {
    std::vector<std::string> refs = {
        "experiment_run_id=" + record.experiment_run_id,
        "comparison_id=" + record.comparison_id,
        "replay_run_id=" + record.replay_run_id,
        "baseline_worldline_id=" + record.baseline_worldline_id,
        "variant_worldline_id=" + record.variant_worldline_id,
        "counterfactual_request_ref=" + record.counterfactual_request_ref,
        "counterfactual_admission_ref=" + record.counterfactual_admission_ref,
        "replay_envelope_ref=" + record.replay_envelope_ref,
        "branch_point_ref=" + record.branch_point_ref,
        "generated_input_ref=" + record.generated_input_ref,
        "backend_profile_ref=" + record.backend_profile_ref,
        "fidelity_profile_ref=" + record.fidelity_profile_ref,
        "claim_boundary=" + record.claim_boundary,
        "promotion_state=" + record.promotion_state,
    };
    for (const auto& capability_ref : record.capability_refs) {
        refs.push_back("capability_ref=" + capability_ref);
    }
    for (const auto& observation : record.profile_observation_refs) {
        refs.push_back("profile_observation_ref=" + observation.observation_ref);
    }
    for (const auto& evidence_ref : record.evidence_refs) {
        refs.push_back("evidence_ref=" + evidence_ref);
    }
    return refs;
}

[[nodiscard]] inline ExperimentEvidenceBridgeValidationResult
validate_experiment_profile_observation_ref(
    const ExperimentProfileObservationRef& observation
) {
    ExperimentEvidenceBridgeValidationResult result{};

    if (replay_contract_is_blank(observation.observation_ref)) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionProfileObservationRefRequired
            )
        );
        result.add_error("profile_observation_refs[].observation_ref is required");
    }
    if (replay_contract_is_blank(observation.profile_ref)) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionProfileObservationRefRequired
            )
        );
        result.add_error("profile_observation_refs[].profile_ref is required");
    }
    if (!is_known_experiment_profile_observation_status(observation.status)) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionProfileObservationStatusInvalid
            )
        );
        result.add_error(
            "profile_observation_refs[].status must be observed, proposed, blocked, or unsupported"
        );
    }
    if (!is_known_experiment_profile_claim_scope(observation.claim_scope)) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionProfileObservationClaimScopeInvalid
            )
        );
        result.add_error(
            "profile_observation_refs[].claim_scope must be descriptive, comparative, or gating_related"
        );
    }
    if (observation.evidence_refs.empty() ||
        replay_contract_has_blank_value(observation.evidence_refs)) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionProfileObservationEvidenceRequired
            )
        );
        result.add_error(
            "profile_observation_refs[].evidence_refs must not be empty or contain blank entries"
        );
    }
    if (observation.truth_claim) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionProfileObservationTruthClaimForbidden
            )
        );
        result.add_error(
            "profile observations must remain non-truth-claim evidence observations"
        );
    }
    if (observation.promoted_to_support) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionProfileObservationSupportPromotionForbidden
            )
        );
        result.add_error(
            "profile observations must not promote maintained support"
        );
    }

    return result;
}

[[nodiscard]] inline ExperimentEvidenceBridgeValidationResult
validate_scenario_generation_artifact_metadata(
    const ScenarioGenerationArtifactMetadata& artifact
) {
    ExperimentEvidenceBridgeValidationResult result{};

    if (artifact.authoritative_state_mutation_allowed) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionGeneratedInputMutationForbidden
            )
        );
        result.add_error(
            "generated input metadata must not allow authoritative state mutation"
        );
    }
    if (artifact.artifact_kind != kScenarioGenerationArtifactKindRequestMetadata) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionGeneratedInputArtifactKindInvalid
            )
        );
        result.add_error(
            "artifact_kind must remain scenario_generation_request_metadata"
        );
    }
    if (replay_contract_is_blank(artifact.request.request_id)) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionGeneratedInputRequestIdRequired
            )
        );
        result.add_error("generated_input.request.request_id is required");
    }
    if (replay_contract_is_blank(artifact.request.request_version)) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionGeneratedInputVersionRequired
            )
        );
        result.add_error("generated_input.request.request_version is required");
    }
    if (replay_contract_is_blank(artifact.request.contract_version)) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionGeneratedInputContractVersionRequired
            )
        );
        result.add_error("generated_input.request.contract_version is required");
    }
    if (!is_known_scenario_generation_kind(artifact.request.generation_kind)) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionGeneratedInputGenerationKindUnsupported
            )
        );
        result.add_error(
            "generated_input.request.generation_kind must be a maintained WP15-D kind"
        );
    }
    if (!is_known_scenario_generation_source(artifact.request.source)) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionGeneratedInputSourceUnsupported
            )
        );
        result.add_error(
            "generated_input.request.source must be a maintained WP15-D source"
        );
    }
    if (replay_contract_is_blank(artifact.request.generator_version)) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionGeneratedInputGeneratorVersionRequired
            )
        );
        result.add_error("generated_input.request.generator_version is required");
    }
    if (!artifact.request.has_deterministic_seed) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionGeneratedInputDeterministicSeedRequired
            )
        );
        result.add_error(
            "generated_input.request.deterministic_seed is required"
        );
    }
    if (replay_contract_is_blank(artifact.request.baseline_scenario_ref)) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionGeneratedInputBaselineScenarioRequired
            )
        );
        result.add_error(
            "generated_input.request.baseline_scenario_ref is required"
        );
    }
    for (const auto& capability_ref : artifact.request.capability_refs) {
        if (!is_supported_counterfactual_capability_ref(capability_ref)) {
            result.reject(
                std::string(
                    kExperimentEvidenceBridgeRejectionGeneratedInputCapabilityRefUnsupported
                )
            );
            result.add_error(
                "generated_input.request.capability_refs must use capability_bundle: or resolved_spawn_plan: refs"
            );
            break;
        }
    }
    if (artifact.request.evidence_refs.empty()) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionGeneratedInputEvidenceRequired
            )
        );
        result.add_error(
            "generated_input.request.evidence_refs must not be empty"
        );
    } else {
        for (const auto& evidence_ref : artifact.request.evidence_refs) {
            if (replay_contract_is_blank(evidence_ref.ref_id)) {
                result.reject(
                    std::string(
                        kExperimentEvidenceBridgeRejectionGeneratedInputEvidenceRequired
                    )
                );
                result.add_error(
                    "generated_input.request.evidence_refs[].ref_id is required"
                );
                break;
            }
            if (!is_known_scenario_generation_evidence_kind(
                    evidence_ref.evidence_kind)) {
                result.reject(
                    std::string(
                        kExperimentEvidenceBridgeRejectionGeneratedInputEvidenceRequired
                    )
                );
                result.add_error(
                    "generated_input.request.evidence_refs[].evidence_kind must be maintained"
                );
                break;
            }
            if (replay_contract_is_blank(evidence_ref.provenance_label)) {
                result.reject(
                    std::string(
                        kExperimentEvidenceBridgeRejectionGeneratedInputEvidenceRequired
                    )
                );
                result.add_error(
                    "generated_input.request.evidence_refs[].provenance_label is required"
                );
                break;
            }
        }
    }

    return result;
}

[[nodiscard]] inline ExperimentEvidenceBridgeValidationResult
validate_experiment_evidence_bridge_record(
    const ExperimentEvidenceBridgeRecord& record,
    const CounterfactualAdmissionResult& admission,
    const ReplayEnvelope& replay_envelope,
    const ScenarioGenerationArtifactMetadata& generated_input
) {
    ExperimentEvidenceBridgeValidationResult result{};

    if (replay_contract_is_blank(record.experiment_run_id)) {
        result.reject(
            std::string(kExperimentEvidenceBridgeRejectionMissingExperimentRunId)
        );
        result.add_error("experiment_run_id is required");
    }
    if (replay_contract_is_blank(record.comparison_id)) {
        result.reject(
            std::string(kExperimentEvidenceBridgeRejectionMissingComparisonId)
        );
        result.add_error("comparison_id is required");
    }
    if (replay_contract_is_blank(record.replay_run_id)) {
        result.reject(
            std::string(kExperimentEvidenceBridgeRejectionMissingReplayRunId)
        );
        result.add_error("replay_run_id is required");
    }
    if (replay_contract_is_blank(record.baseline_worldline_id)) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionMissingBaselineWorldlineId
            )
        );
        result.add_error("baseline_worldline_id is required");
    }
    if (replay_contract_is_blank(record.variant_worldline_id)) {
        result.reject(
            std::string(kExperimentEvidenceBridgeRejectionMissingVariantWorldlineId)
        );
        result.add_error("variant_worldline_id is required");
    }
    if (replay_contract_is_blank(record.counterfactual_request_ref)) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionMissingCounterfactualRequestRef
            )
        );
        result.add_error("counterfactual_request_ref is required");
    }
    if (replay_contract_is_blank(record.counterfactual_admission_ref)) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionMissingCounterfactualAdmissionRef
            )
        );
        result.add_error("counterfactual_admission_ref is required");
    }
    if (replay_contract_is_blank(record.replay_envelope_ref)) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionMissingReplayEnvelopeRef
            )
        );
        result.add_error("replay_envelope_ref is required");
    }
    if (replay_contract_is_blank(record.branch_point_ref)) {
        result.reject(
            std::string(kExperimentEvidenceBridgeRejectionMissingBranchPointRef)
        );
        result.add_error("branch_point_ref is required");
    }
    if (replay_contract_is_blank(record.generated_input_ref)) {
        result.reject(
            std::string(kExperimentEvidenceBridgeRejectionMissingGeneratedInputRef)
        );
        result.add_error("generated_input_ref is required");
    }
    if (replay_contract_is_blank(record.backend_profile_ref)) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionMissingBackendProfileRef
            )
        );
        result.add_error("backend_profile_ref is required");
    }
    if (replay_contract_is_blank(record.fidelity_profile_ref)) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionMissingFidelityProfileRef
            )
        );
        result.add_error("fidelity_profile_ref is required");
    }
    if (record.capability_refs.empty() ||
        replay_contract_has_blank_value(record.capability_refs)) {
        result.reject(
            std::string(kExperimentEvidenceBridgeRejectionMissingCapabilityRefs)
        );
        result.add_error(
            "capability_refs must not be empty or contain blank entries"
        );
    }
    if (record.profile_observation_refs.empty()) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionMissingProfileObservationRefs
            )
        );
        result.add_error("profile_observation_refs must not be empty");
    }
    if (record.evidence_refs.empty() ||
        replay_contract_has_blank_value(record.evidence_refs)) {
        result.reject(
            std::string(kExperimentEvidenceBridgeRejectionMissingEvidenceRefs)
        );
        result.add_error("evidence_refs must not be empty or contain blank entries");
    }
    if (record.truth_claim ||
        record.claim_boundary != kExperimentEvidenceClaimBoundaryNonTruthClaim) {
        result.reject(
            std::string(kExperimentEvidenceBridgeRejectionTruthClaimForbidden)
        );
        result.add_error(
            "experiment evidence bridge records must remain non-truth-claim observations"
        );
    }
    if (record.promoted_to_support ||
        record.promotion_state != kExperimentEvidencePromotionStateNotPromoted) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionSupportPromotionForbidden
            )
        );
        result.add_error(
            "experiment evidence bridge records must not promote maintained support"
        );
    }

    if (!admission.admitted) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionCounterfactualAdmissionRequired
            )
        );
        result.add_error(
            "counterfactual admission must be admitted before experiment evidence is bridged"
        );
    }

    absorb_experiment_bridge_validation(
        &result,
        validate_scenario_generation_artifact_metadata(generated_input)
    );

    if (record.counterfactual_request_ref != admission.request_id ||
        record.counterfactual_admission_ref != admission.request_id) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionCounterfactualRequestMismatch
            )
        );
        result.add_error(
            "counterfactual request/admission refs must match admitted request_id"
        );
    }
    if (record.baseline_worldline_id != admission.baseline_worldline_id) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionBaselineWorldlineMismatch
            )
        );
        result.add_error(
            "baseline_worldline_id must match admitted baseline worldline id"
        );
    }
    if (record.variant_worldline_id != admission.child_worldline_id) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionVariantWorldlineMismatch
            )
        );
        result.add_error(
            "variant_worldline_id must match admitted child worldline id"
        );
    }
    if (record.replay_envelope_ref != admission.replay_envelope_id) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionReplayEnvelopeRefMismatch
            )
        );
        result.add_error(
            "replay_envelope_ref must match admitted replay envelope id"
        );
    }
    if (record.branch_point_ref != admission.branch_point_id) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionBranchPointRefMismatch
            )
        );
        result.add_error(
            "branch_point_ref must match admitted branch point id"
        );
    }
    if (record.replay_run_id != replay_envelope.run_id) {
        result.reject(
            std::string(kExperimentEvidenceBridgeRejectionReplayRunIdMismatch)
        );
        result.add_error("replay_run_id must match replay_envelope.run_id");
    }
    if (record.backend_profile_ref != admission.backend_profile_ref) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionBackendProfileRefMismatch
            )
        );
        result.add_error(
            "backend_profile_ref must match admitted backend profile ref"
        );
    }
    if (record.fidelity_profile_ref != admission.fidelity_profile_ref) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionFidelityProfileRefMismatch
            )
        );
        result.add_error(
            "fidelity_profile_ref must match admitted fidelity profile ref"
        );
    }
    if (record.replay_envelope_ref != generated_input.request.replay_envelope_ref) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionGeneratedInputReplayEnvelopeMismatch
            )
        );
        result.add_error(
            "generated input replay_envelope_ref must match experiment replay_envelope_ref"
        );
    }
    if (record.branch_point_ref != generated_input.request.branch_point_ref) {
        result.reject(
            std::string(
                kExperimentEvidenceBridgeRejectionGeneratedInputBranchPointMismatch
            )
        );
        result.add_error(
            "generated input branch_point_ref must match experiment branch_point_ref"
        );
    }
    if (record.generated_input_ref != generated_input.request.request_id) {
        result.reject(
            std::string(kExperimentEvidenceBridgeRejectionMissingGeneratedInputRef)
        );
        result.add_error(
            "generated_input_ref must match generated input request id"
        );
    }

    for (const auto& capability_ref : record.capability_refs) {
        if (!is_supported_counterfactual_capability_ref(capability_ref)) {
            result.reject(
                std::string(
                    kExperimentEvidenceBridgeRejectionGeneratedInputCapabilityRefUnsupported
                )
            );
            result.add_error(
                "capability_refs must use capability_bundle: or resolved_spawn_plan: refs"
            );
            break;
        }
        if (std::find(
                admission.capability_refs.begin(),
                admission.capability_refs.end(),
                capability_ref
            ) == admission.capability_refs.end()) {
            result.reject(
                std::string(
                    kExperimentEvidenceBridgeRejectionCapabilityRefMismatch
                )
            );
            result.add_error(
                "capability_refs must remain aligned with admitted capability refs"
            );
            break;
        }
    }

    for (const auto& observation : record.profile_observation_refs) {
        absorb_experiment_bridge_validation(
            &result,
            validate_experiment_profile_observation_ref(observation)
        );
    }

    return result;
}

[[nodiscard]] inline ExperimentEvidenceBridgeRecord
make_experiment_evidence_bridge_record(
    const CounterfactualAdmissionResult& admission,
    const ReplayEnvelope& replay_envelope,
    const ScenarioGenerationArtifactMetadata& generated_input,
    std::string experiment_run_id,
    std::string comparison_id,
    std::vector<ExperimentProfileObservationRef> profile_observation_refs,
    std::vector<std::string> evidence_refs
) {
    ExperimentEvidenceBridgeRecord record{};
    record.experiment_run_id = std::move(experiment_run_id);
    record.comparison_id = std::move(comparison_id);
    record.replay_run_id = replay_envelope.run_id;
    record.baseline_worldline_id = admission.baseline_worldline_id;
    record.variant_worldline_id = admission.child_worldline_id;
    record.counterfactual_request_ref = admission.request_id;
    record.counterfactual_admission_ref = admission.request_id;
    record.replay_envelope_ref = admission.replay_envelope_id;
    record.branch_point_ref = admission.branch_point_id;
    record.generated_input_ref = generated_input.request.request_id;
    record.backend_profile_ref = admission.backend_profile_ref;
    record.fidelity_profile_ref = admission.fidelity_profile_ref;
    record.capability_refs = admission.capability_refs;
    record.profile_observation_refs = std::move(profile_observation_refs);
    record.evidence_refs = std::move(evidence_refs);
    return record;
}

}  // namespace runtime::counterfactual
