#pragma once

#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "runtime/contracts/backend_profile_contracts.h"
#include "runtime/contracts/fidelity_profile_contracts.h"
#include "runtime/contracts/policy_contracts.h"

namespace runtime::counterfactual {

inline constexpr std::string_view kDeterministicReplayEventOrderSortKey =
    "timestamp_priority_event_id";
inline constexpr std::string_view kReplayRestoreSupportBoundaryUnsupported =
    "restore_unsupported_until_snapshot_restore_proof";

inline constexpr std::string_view kReplayEnvelopeRejectionMissingEnvelopeId =
    "replay_envelope_id_required";
inline constexpr std::string_view kReplayEnvelopeRejectionMissingRunId =
    "replay_run_id_required";
inline constexpr std::string_view kReplayEnvelopeRejectionMissingEpisodeId =
    "replay_episode_id_required";
inline constexpr std::string_view kReplayEnvelopeRejectionMissingDeterministicSeed =
    "replay_deterministic_seed_required";
inline constexpr std::string_view kReplayEnvelopeRejectionMissingSourceTime =
    "replay_source_time_required";
inline constexpr std::string_view kReplayEnvelopeRejectionMissingSnapshotVersionRef =
    "replay_snapshot_version_ref_required";
inline constexpr std::string_view kReplayEnvelopeRejectionMissingBarrierId =
    "replay_barrier_id_required";
inline constexpr std::string_view kReplayEnvelopeRejectionMissingEventOrderRef =
    "replay_event_order_ref_required";
inline constexpr std::string_view kReplayEnvelopeRejectionMissingFacadeProvenanceRef =
    "replay_facade_provenance_ref_required";
inline constexpr std::string_view kReplayEnvelopeRejectionInvalidFacadeProvenanceLabel =
    "replay_facade_provenance_label_invalid";
inline constexpr std::string_view kReplayEnvelopeRejectionRestoreUnsupportedBoundary =
    "snapshot_restore_unsupported_for_wp15a";
inline constexpr std::string_view kReplayEnvelopeRejectionRestoreClaimUnsupported =
    "snapshot_restore_claim_not_supported_for_wp15a";

inline constexpr std::string_view kBranchPointRejectionMissingBranchPointId =
    "branch_point_id_required";
inline constexpr std::string_view kBranchPointRejectionMissingReplayEnvelopeId =
    "branch_point_replay_envelope_id_required";
inline constexpr std::string_view kBranchPointRejectionReplayEnvelopeMismatch =
    "branch_point_replay_envelope_mismatch";
inline constexpr std::string_view kBranchPointRejectionIdentityMismatch =
    "branch_point_identity_mismatch";

inline constexpr std::string_view kWorldlineBranchSupportStateMetadataOnly =
    "metadata_only";
inline constexpr std::string_view kWorldlineBranchSupportStateAdmitted =
    "admitted";
inline constexpr std::string_view kWorldlineBranchSupportStateRejected =
    "rejected";
inline constexpr std::string_view kWorldlineBranchSupportStateRestoreUnsupported =
    "restore_unsupported";

inline constexpr std::string_view kWorldlineBranchMutationIntentMetadataOnly =
    "metadata_only";
inline constexpr std::string_view kWorldlineBranchMutationIntentSupportStateOnly =
    "support_state_only";
inline constexpr std::string_view
    kWorldlineBranchMutationIntentRawAuthoritativeStateMutation =
        "raw_authoritative_state_mutation";

inline constexpr std::string_view
    kWorldlineBranchRejectionMissingBaselineWorldlineId =
        "worldline_branch_baseline_worldline_id_required";
inline constexpr std::string_view
    kWorldlineBranchRejectionMissingParentWorldlineId =
        "worldline_branch_parent_worldline_id_required";
inline constexpr std::string_view
    kWorldlineBranchRejectionMissingChildWorldlineId =
        "worldline_branch_child_worldline_id_required";
inline constexpr std::string_view
    kWorldlineBranchRejectionChildWorldlineCollision =
        "worldline_branch_child_worldline_id_collision";
inline constexpr std::string_view
    kWorldlineBranchRejectionMissingBranchPointRef =
        "worldline_branch_branch_point_ref_required";
inline constexpr std::string_view
    kWorldlineBranchRejectionMissingReplayEnvelopeRef =
        "worldline_branch_replay_envelope_ref_required";
inline constexpr std::string_view
    kWorldlineBranchRejectionBranchPointRefMismatch =
        "worldline_branch_branch_point_ref_mismatch";
inline constexpr std::string_view
    kWorldlineBranchRejectionReplayEnvelopeRefMismatch =
        "worldline_branch_replay_envelope_ref_mismatch";
inline constexpr std::string_view kWorldlineBranchRejectionMissingBranchReason =
    "worldline_branch_reason_required";
inline constexpr std::string_view
    kWorldlineBranchRejectionMissingInterventionIntent =
        "worldline_branch_intervention_intent_required";
inline constexpr std::string_view
    kWorldlineBranchRejectionMissingMutationIntent =
        "worldline_branch_mutation_intent_required";
inline constexpr std::string_view
    kWorldlineBranchRejectionInvalidMutationIntent =
        "worldline_branch_mutation_intent_invalid";
inline constexpr std::string_view
    kWorldlineBranchRejectionMetadataOnlyBoundaryRequired =
        "worldline_branch_metadata_only_boundary_required";
inline constexpr std::string_view
    kWorldlineBranchRejectionRawStateMutationForbidden =
        "worldline_branch_raw_authoritative_state_mutation_forbidden";
inline constexpr std::string_view kWorldlineBranchRejectionMissingSourceRef =
    "worldline_branch_source_ref_required";
inline constexpr std::string_view kWorldlineBranchRejectionMissingProvenanceRef =
    "worldline_branch_provenance_ref_required";
inline constexpr std::string_view
    kWorldlineBranchRejectionInvalidSourceLabel =
        "worldline_branch_source_label_invalid";
inline constexpr std::string_view kWorldlineBranchRejectionMissingEvidenceRefs =
    "worldline_branch_evidence_refs_required";
inline constexpr std::string_view
    kWorldlineBranchRejectionInvalidSupportState =
        "worldline_branch_support_state_invalid";
inline constexpr std::string_view
    kWorldlineBranchRejectionRestoreUnsupportedBoundary =
        "worldline_branch_restore_unsupported_for_wp15b";
inline constexpr std::string_view
    kWorldlineBranchRejectionRestoreClaimUnsupported =
        "worldline_branch_restore_claim_not_supported_for_wp15b";

inline constexpr std::string_view kCounterfactualAdmissionStateAdmitted =
    "admitted";
inline constexpr std::string_view kCounterfactualAdmissionStateRejected =
    "rejected";
inline constexpr std::string_view kCounterfactualAdmissionStateRestoreUnsupported =
    "restore_unsupported";

inline constexpr std::string_view
    kCounterfactualInterventionKindObservationWithhold =
        "observation_withhold";
inline constexpr std::string_view
    kCounterfactualInterventionKindPolicySubstitution =
        "policy_substitution";
inline constexpr std::string_view
    kCounterfactualInterventionKindCommandVariant =
        "command_variant";
inline constexpr std::string_view
    kCounterfactualInterventionKindSpawnVariantRequest =
        "spawn_variant_request";
inline constexpr std::string_view
    kCounterfactualInterventionKindRawAuthoritativeStateMutation =
        "raw_authoritative_state_mutation";

inline constexpr std::string_view kCounterfactualSourceOperatorRequest =
    "operator_request";
inline constexpr std::string_view kCounterfactualSourceAnalystRequest =
    "analyst_request";
inline constexpr std::string_view kCounterfactualSourceExperimentPlan =
    "experiment_plan";
inline constexpr std::string_view kCounterfactualSourceCounterfactualBranch =
    "counterfactual_branch";

inline constexpr std::string_view
    kCounterfactualCapabilityRefPrefixBundle = "capability_bundle:";
inline constexpr std::string_view
    kCounterfactualCapabilityRefPrefixResolvedSpawnPlan = "resolved_spawn_plan:";

inline constexpr std::string_view
    kCounterfactualRequestRejectionMissingRequestId =
        "counterfactual_request_id_required";
inline constexpr std::string_view
    kCounterfactualRequestRejectionMissingBaselineWorldlineId =
        "counterfactual_baseline_worldline_id_required";
inline constexpr std::string_view
    kCounterfactualRequestRejectionBaselineWorldlineMismatch =
        "counterfactual_baseline_worldline_id_mismatch";
inline constexpr std::string_view
    kCounterfactualRequestRejectionMissingInterventionKind =
        "counterfactual_intervention_kind_required";
inline constexpr std::string_view
    kCounterfactualRequestRejectionUnsupportedInterventionKind =
        "counterfactual_intervention_kind_not_supported";
inline constexpr std::string_view
    kCounterfactualRequestRejectionMissingSource =
        "counterfactual_source_required";
inline constexpr std::string_view
    kCounterfactualRequestRejectionUnsupportedSource =
        "counterfactual_source_not_supported";
inline constexpr std::string_view
    kCounterfactualRequestRejectionMissingAuthorityRef =
        "counterfactual_authority_ref_required";
inline constexpr std::string_view
    kCounterfactualRequestRejectionMissingProvenanceRef =
        "counterfactual_provenance_ref_required";
inline constexpr std::string_view
    kCounterfactualRequestRejectionInvalidAuthorityScope =
        "counterfactual_authority_scope_invalid";
inline constexpr std::string_view
    kCounterfactualRequestRejectionInvalidAuthoritySource =
        "counterfactual_authority_information_source_invalid";
inline constexpr std::string_view
    kCounterfactualRequestRejectionMissingAuthorityEvidenceRefs =
        "counterfactual_authority_evidence_refs_required";
inline constexpr std::string_view
    kCounterfactualRequestRejectionMissingBackendProfileRef =
        "counterfactual_backend_profile_ref_required";
inline constexpr std::string_view
    kCounterfactualRequestRejectionUnsupportedBackendProfileRef =
        "counterfactual_backend_profile_ref_not_found";
inline constexpr std::string_view
    kCounterfactualRequestRejectionInvalidBackendProfileRef =
        "counterfactual_backend_profile_ref_invalid";
inline constexpr std::string_view
    kCounterfactualRequestRejectionMissingFidelityProfileRef =
        "counterfactual_fidelity_profile_ref_required";
inline constexpr std::string_view
    kCounterfactualRequestRejectionUnsupportedFidelityProfileRef =
        "counterfactual_fidelity_profile_ref_not_supported";
inline constexpr std::string_view
    kCounterfactualRequestRejectionMissingCapabilityRefs =
        "counterfactual_capability_refs_required";
inline constexpr std::string_view
    kCounterfactualRequestRejectionUnsupportedCapabilityRef =
        "counterfactual_capability_ref_not_supported";
inline constexpr std::string_view
    kCounterfactualRequestRejectionMissingEvidenceRefs =
        "counterfactual_evidence_refs_required";
inline constexpr std::string_view
    kCounterfactualRequestRejectionWorldlineSupportStatePreclaimForbidden =
        "counterfactual_worldline_support_state_preclaim_forbidden";
inline constexpr std::string_view
    kCounterfactualRequestRejectionRawStateMutationForbidden =
        "counterfactual_raw_authoritative_state_mutation_forbidden";
inline constexpr std::string_view
    kCounterfactualRequestRejectionRestoreUnsupportedBoundary =
        "counterfactual_snapshot_restore_unsupported_for_wp15c";

inline constexpr std::string_view
    kScenarioGenerationArtifactKindRequestMetadata =
        "scenario_generation_request_metadata";
inline constexpr std::string_view
    kScenarioGenerationContractVersionWp15RequestV1 =
        "wp15.scenario_generation_request.v1";
inline constexpr std::string_view kScenarioGenerationKindScenarioVariation =
    "scenario_variation";
inline constexpr std::string_view kScenarioGenerationKindAdversaryPlacement =
    "adversary_placement";
inline constexpr std::string_view kScenarioGenerationKindRoutePerturbation =
    "route_perturbation";
inline constexpr std::string_view kScenarioGenerationKindMissionPerturbation =
    "mission_perturbation";
inline constexpr std::string_view kScenarioGenerationKindStressorInjection =
    "stressor_injection";
inline constexpr std::string_view kScenarioGenerationSourceAnalystAuthored =
    "analyst_authored";
inline constexpr std::string_view kScenarioGenerationSourceCounterfactualBranch =
    "counterfactual_branch";
inline constexpr std::string_view kScenarioGenerationSourceCurriculumGeneration =
    "curriculum_generation";
inline constexpr std::string_view kScenarioGenerationSourceEvaluationReplay =
    "evaluation_replay";
inline constexpr std::string_view kScenarioGenerationEvidenceKindBaselineScenario =
    "baseline_scenario";
inline constexpr std::string_view kScenarioGenerationEvidenceKindBranchPoint =
    "branch_point";
inline constexpr std::string_view kScenarioGenerationEvidenceKindCapabilityBundle =
    "capability_bundle";
inline constexpr std::string_view kScenarioGenerationEvidenceKindLearningEvidence =
    "learning_evidence";
inline constexpr std::string_view kScenarioGenerationEvidenceKindReplayEnvelope =
    "replay_envelope";
inline constexpr std::string_view kScenarioGenerationEvidenceKindReviewNote =
    "review_note";

inline constexpr std::string_view kExperimentProfileObservationStatusObserved =
    "observed";
inline constexpr std::string_view kExperimentProfileObservationStatusProposed =
    "proposed";
inline constexpr std::string_view kExperimentProfileObservationStatusBlocked =
    "blocked";
inline constexpr std::string_view kExperimentProfileObservationStatusUnsupported =
    "unsupported";

inline constexpr std::string_view kExperimentProfileClaimScopeDescriptive =
    "descriptive";
inline constexpr std::string_view kExperimentProfileClaimScopeComparative =
    "comparative";
inline constexpr std::string_view kExperimentProfileClaimScopeGatingRelated =
    "gating_related";

inline constexpr std::string_view kExperimentEvidenceClaimBoundaryNonTruthClaim =
    "non_truth_claim_observation_only";
inline constexpr std::string_view kExperimentEvidencePromotionStateNotPromoted =
    "not_promoted";

inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionMissingExperimentRunId =
        "experiment_evidence_run_id_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionMissingComparisonId =
        "experiment_evidence_comparison_id_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionMissingReplayRunId =
        "experiment_evidence_replay_run_id_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionMissingBaselineWorldlineId =
        "experiment_evidence_baseline_worldline_id_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionMissingVariantWorldlineId =
        "experiment_evidence_variant_worldline_id_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionMissingCounterfactualRequestRef =
        "experiment_evidence_counterfactual_request_ref_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionMissingCounterfactualAdmissionRef =
        "experiment_evidence_counterfactual_admission_ref_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionMissingReplayEnvelopeRef =
        "experiment_evidence_replay_envelope_ref_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionMissingBranchPointRef =
        "experiment_evidence_branch_point_ref_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionMissingGeneratedInputRef =
        "experiment_evidence_generated_input_ref_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionMissingBackendProfileRef =
        "experiment_evidence_backend_profile_ref_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionMissingFidelityProfileRef =
        "experiment_evidence_fidelity_profile_ref_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionMissingCapabilityRefs =
        "experiment_evidence_capability_refs_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionMissingProfileObservationRefs =
        "experiment_evidence_profile_observation_refs_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionMissingEvidenceRefs =
        "experiment_evidence_refs_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionCounterfactualAdmissionRequired =
        "experiment_evidence_counterfactual_admission_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionCounterfactualRequestMismatch =
        "experiment_evidence_counterfactual_request_mismatch";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionBaselineWorldlineMismatch =
        "experiment_evidence_baseline_worldline_id_mismatch";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionVariantWorldlineMismatch =
        "experiment_evidence_variant_worldline_id_mismatch";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionReplayRunIdMismatch =
        "experiment_evidence_replay_run_id_mismatch";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionReplayEnvelopeRefMismatch =
        "experiment_evidence_replay_envelope_ref_mismatch";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionBranchPointRefMismatch =
        "experiment_evidence_branch_point_ref_mismatch";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionGeneratedInputMutationForbidden =
        "experiment_evidence_generated_input_mutation_forbidden";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionGeneratedInputArtifactKindInvalid =
        "experiment_evidence_generated_input_artifact_kind_invalid";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionGeneratedInputRequestIdRequired =
        "experiment_evidence_generated_input_request_id_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionGeneratedInputVersionRequired =
        "experiment_evidence_generated_input_version_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionGeneratedInputContractVersionRequired =
        "experiment_evidence_generated_input_contract_version_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionGeneratedInputGenerationKindUnsupported =
        "experiment_evidence_generated_input_generation_kind_not_supported";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionGeneratedInputSourceUnsupported =
        "experiment_evidence_generated_input_source_not_supported";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionGeneratedInputGeneratorVersionRequired =
        "experiment_evidence_generated_input_generator_version_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionGeneratedInputDeterministicSeedRequired =
        "experiment_evidence_generated_input_deterministic_seed_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionGeneratedInputBaselineScenarioRequired =
        "experiment_evidence_generated_input_baseline_scenario_ref_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionGeneratedInputEvidenceRequired =
        "experiment_evidence_generated_input_evidence_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionGeneratedInputReplayEnvelopeMismatch =
        "experiment_evidence_generated_input_replay_envelope_ref_mismatch";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionGeneratedInputBranchPointMismatch =
        "experiment_evidence_generated_input_branch_point_ref_mismatch";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionBackendProfileRefMismatch =
        "experiment_evidence_backend_profile_ref_mismatch";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionFidelityProfileRefMismatch =
        "experiment_evidence_fidelity_profile_ref_mismatch";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionCapabilityRefMismatch =
        "experiment_evidence_capability_ref_mismatch";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionGeneratedInputCapabilityRefUnsupported =
        "experiment_evidence_generated_input_capability_ref_not_supported";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionProfileObservationRefRequired =
        "experiment_evidence_profile_observation_ref_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionProfileObservationStatusInvalid =
        "experiment_evidence_profile_observation_status_invalid";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionProfileObservationClaimScopeInvalid =
        "experiment_evidence_profile_observation_claim_scope_invalid";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionProfileObservationEvidenceRequired =
        "experiment_evidence_profile_observation_evidence_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionTruthClaimForbidden =
        "experiment_evidence_truth_claim_forbidden";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionSupportPromotionForbidden =
        "experiment_evidence_support_promotion_forbidden";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionProfileObservationTruthClaimForbidden =
        "experiment_evidence_profile_observation_truth_claim_forbidden";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionProfileObservationSupportPromotionForbidden =
        "experiment_evidence_profile_observation_support_promotion_forbidden";

struct ReplaySnapshotRef {
    std::string snapshot_version_ref;
};

struct ReplayBarrierRef {
    std::string barrier_id;
    std::uint64_t barrier_sequence = 0;
    std::string barrier_detail = "window_commit";
};

struct ReplayEventOrderRef {
    std::string sort_key = std::string(kDeterministicReplayEventOrderSortKey);
    std::string event_id;
    std::string producer_node_id;
};

struct ReplayFacadeProvenanceRef {
    std::string packet_ref;
    std::string packet_kind = "ObservationBatchPacket";
    InformationStateSource information_state_source = make_information_state_source(
        kPolicyInformationStateAgentObservation,
        kPolicySourceLabelFacadeObservationPacket,
        kPolicyMaintainedStatusMaintained
    );
};

struct ReplayEnvelope {
    std::string replay_envelope_id;
    std::string run_id;
    std::string episode_id;
    bool has_deterministic_seed = false;
    std::uint64_t deterministic_seed = 0;
    bool has_source_time = false;
    double source_time_s = 0.0;
    ReplaySnapshotRef snapshot_ref{};
    ReplayBarrierRef barrier_ref{};
    ReplayEventOrderRef event_order_ref{};
    ReplayFacadeProvenanceRef facade_provenance_ref{};
    bool snapshot_restore_supported = false;
    std::string restore_support_boundary =
        std::string(kReplayRestoreSupportBoundaryUnsupported);
};

struct BranchPoint {
    std::string branch_point_id;
    std::string replay_envelope_id;
    std::string snapshot_version_ref;
    std::string barrier_id;
    std::string event_order_ref;
    std::string facade_packet_ref;
    bool snapshot_restore_supported = false;
    std::string restore_support_boundary =
        std::string(kReplayRestoreSupportBoundaryUnsupported);
};

struct WorldlineBranchMetadata {
    std::string baseline_worldline_id;
    std::string parent_worldline_id;
    std::string child_worldline_id;
    std::string branch_point_ref;
    std::string replay_envelope_ref;
    std::string branch_reason;
    std::string intervention_intent;
    std::string mutation_intent =
        std::string(kWorldlineBranchMutationIntentMetadataOnly);
    bool metadata_only = true;
    bool requests_authoritative_state_mutation = false;
    std::string source_ref;
    std::string provenance_ref;
    InformationStateSource source_information_state = make_information_state_source(
        kPolicyInformationStateDecisionBelief,
        kPolicySourceLabelObservationDerivedBelief,
        kPolicyMaintainedStatusDiagnosticsOnly
    );
    std::vector<std::string> evidence_refs;
    std::string support_state = std::string(kWorldlineBranchSupportStateMetadataOnly);
    bool snapshot_restore_supported = false;
    std::string restore_support_boundary =
        std::string(kReplayRestoreSupportBoundaryUnsupported);
};

struct CounterfactualExperimentRequest {
    std::string request_id;
    std::string baseline_worldline_id;
    ReplayEnvelope replay_envelope{};
    BranchPoint branch_point{};
    WorldlineBranchMetadata worldline_branch_metadata{};
    std::string intervention_kind;
    std::string source;
    std::string authority_ref;
    std::string provenance_ref;
    AgentAuthorityScope authority_scope{};
    InformationStateSource authority_information_state = make_information_state_source(
        kPolicyInformationStateDecisionBelief,
        kPolicySourceLabelObservationDerivedBelief,
        kPolicyMaintainedStatusMaintained
    );
    std::vector<std::string> authority_evidence_refs;
    std::string backend_profile_ref;
    std::string fidelity_profile_ref;
    std::vector<std::string> capability_refs;
    std::vector<std::string> evidence_refs;
    bool requests_executable_branch = false;
    bool requests_authoritative_state_mutation = false;
    bool snapshot_restore_supported = false;
    std::string restore_support_boundary =
        std::string(kReplayRestoreSupportBoundaryUnsupported);
};

struct ReplayContractValidationResult {
    bool valid = true;
    std::vector<std::string> errors;
    std::string rejection_reason;

    void add_error(std::string error) {
        valid = false;
        errors.push_back(std::move(error));
    }

    void reject(std::string reason) {
        valid = false;
        if (rejection_reason.empty()) {
            rejection_reason = std::move(reason);
        }
    }
};

struct ReplayRestoreSupportResult {
    bool supported = false;
    std::string replay_envelope_id;
    std::string rejection_reason;
};

struct WorldlineBranchSupportResult {
    bool supported = false;
    std::string child_worldline_id;
    std::string support_state =
        std::string(kWorldlineBranchSupportStateMetadataOnly);
    std::string rejection_reason;
};

struct CounterfactualAdmissionResult {
    bool admitted = false;
    bool snapshot_restore_supported = false;
    std::string request_id;
    std::string baseline_worldline_id;
    std::string child_worldline_id;
    std::string replay_envelope_id;
    std::string branch_point_id;
    std::string intervention_kind;
    std::string source;
    std::string authority_ref;
    std::string provenance_ref;
    std::string backend_profile_ref;
    std::string fidelity_profile_ref;
    std::vector<std::string> capability_refs;
    std::string admission_state =
        std::string(kCounterfactualAdmissionStateRejected);
    std::string worldline_support_state =
        std::string(kWorldlineBranchSupportStateRejected);
    std::string restore_support_boundary =
        std::string(kReplayRestoreSupportBoundaryUnsupported);
    std::string rejection_reason;
    std::vector<std::string> errors;
    std::vector<std::string> evidence_refs;

    void reject(std::string reason) {
        admitted = false;
        admission_state = std::string(kCounterfactualAdmissionStateRejected);
        worldline_support_state = std::string(kWorldlineBranchSupportStateRejected);
        if (rejection_reason.empty()) {
            rejection_reason = std::move(reason);
        }
    }

    void add_error(std::string error) {
        errors.push_back(std::move(error));
    }
};

struct ScenarioGenerationEvidenceMetadataRef {
    std::string ref_id;
    std::string evidence_kind;
    std::string provenance_label;
};

struct ScenarioGenerationRequestMetadata {
    std::string request_id;
    std::string request_version = "1";
    std::string contract_version =
        std::string(kScenarioGenerationContractVersionWp15RequestV1);
    std::string generation_kind;
    std::string source;
    std::string generator_version;
    bool has_deterministic_seed = false;
    std::uint64_t deterministic_seed = 0;
    std::string baseline_scenario_ref;
    std::string replay_envelope_ref;
    std::string branch_point_ref;
    std::vector<std::string> capability_refs;
    std::vector<ScenarioGenerationEvidenceMetadataRef> evidence_refs;
};

struct ScenarioGenerationArtifactMetadata {
    std::string artifact_kind =
        std::string(kScenarioGenerationArtifactKindRequestMetadata);
    bool authoritative_state_mutation_allowed = false;
    ScenarioGenerationRequestMetadata request{};
};

struct ExperimentProfileObservationRef {
    std::string observation_ref;
    std::string profile_ref;
    std::string status =
        std::string(kExperimentProfileObservationStatusObserved);
    std::string claim_scope =
        std::string(kExperimentProfileClaimScopeDescriptive);
    bool truth_claim = false;
    bool promoted_to_support = false;
    std::vector<std::string> evidence_refs;
};

struct ExperimentEvidenceBridgeRecord {
    std::string experiment_run_id;
    std::string comparison_id;
    std::string replay_run_id;
    std::string baseline_worldline_id;
    std::string variant_worldline_id;
    std::string counterfactual_request_ref;
    std::string counterfactual_admission_ref;
    std::string replay_envelope_ref;
    std::string branch_point_ref;
    std::string generated_input_ref;
    std::string backend_profile_ref;
    std::string fidelity_profile_ref;
    std::vector<std::string> capability_refs;
    std::vector<ExperimentProfileObservationRef> profile_observation_refs;
    std::vector<std::string> evidence_refs;
    bool truth_claim = false;
    bool promoted_to_support = false;
    std::string claim_boundary =
        std::string(kExperimentEvidenceClaimBoundaryNonTruthClaim);
    std::string promotion_state =
        std::string(kExperimentEvidencePromotionStateNotPromoted);
};

struct ExperimentEvidenceBridgeValidationResult {
    bool valid = true;
    bool fail_closed = false;
    std::string rejection_reason;
    std::vector<std::string> errors;

    void reject(std::string reason) {
        valid = false;
        fail_closed = true;
        if (rejection_reason.empty()) {
            rejection_reason = std::move(reason);
        }
    }

    void add_error(std::string error) {
        valid = false;
        errors.push_back(std::move(error));
    }
};

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

[[nodiscard]] inline ReplayContractValidationResult validate_replay_snapshot_ref(
    const ReplaySnapshotRef& snapshot_ref
) {
    ReplayContractValidationResult result{};
    if (replay_contract_is_blank(snapshot_ref.snapshot_version_ref)) {
        result.reject(std::string(kReplayEnvelopeRejectionMissingSnapshotVersionRef));
        result.add_error("snapshot_ref.snapshot_version_ref is required");
    }
    return result;
}

[[nodiscard]] inline ReplayContractValidationResult validate_replay_barrier_ref(
    const ReplayBarrierRef& barrier_ref
) {
    ReplayContractValidationResult result{};
    if (replay_contract_is_blank(barrier_ref.barrier_id)) {
        result.reject(std::string(kReplayEnvelopeRejectionMissingBarrierId));
        result.add_error("barrier_ref.barrier_id is required");
    }
    if (replay_contract_is_blank(barrier_ref.barrier_detail)) {
        result.add_error("barrier_ref.barrier_detail is required");
    }
    return result;
}

[[nodiscard]] inline ReplayContractValidationResult validate_replay_event_order_ref(
    const ReplayEventOrderRef& event_order_ref
) {
    ReplayContractValidationResult result{};
    if (replay_contract_is_blank(event_order_ref.event_id)) {
        result.reject(std::string(kReplayEnvelopeRejectionMissingEventOrderRef));
        result.add_error("event_order_ref.event_id is required");
    }
    if (replay_contract_is_blank(event_order_ref.producer_node_id)) {
        result.add_error("event_order_ref.producer_node_id is required");
    }
    if (event_order_ref.sort_key != kDeterministicReplayEventOrderSortKey) {
        result.add_error(
            "event_order_ref.sort_key must remain timestamp_priority_event_id"
        );
    }
    return result;
}

[[nodiscard]] inline ReplayContractValidationResult validate_replay_facade_provenance_ref(
    const ReplayFacadeProvenanceRef& provenance_ref
) {
    ReplayContractValidationResult result{};
    if (replay_contract_is_blank(provenance_ref.packet_ref)) {
        result.reject(std::string(kReplayEnvelopeRejectionMissingFacadeProvenanceRef));
        result.add_error("facade_provenance_ref.packet_ref is required");
    }
    if (replay_contract_is_blank(provenance_ref.packet_kind)) {
        result.add_error("facade_provenance_ref.packet_kind is required");
    }
    if (!information_state_source_has_valid_label(
            provenance_ref.information_state_source)) {
        result.reject(
            std::string(kReplayEnvelopeRejectionInvalidFacadeProvenanceLabel)
        );
        result.add_error(
            "facade_provenance_ref.information_state_source must carry a valid WP11 label"
        );
    }
    return result;
}

[[nodiscard]] inline ReplayContractValidationResult validate_replay_envelope(
    const ReplayEnvelope& envelope
) {
    ReplayContractValidationResult result{};

    if (replay_contract_is_blank(envelope.replay_envelope_id)) {
        result.reject(std::string(kReplayEnvelopeRejectionMissingEnvelopeId));
        result.add_error("replay_envelope_id is required");
    }
    if (replay_contract_is_blank(envelope.run_id)) {
        result.reject(std::string(kReplayEnvelopeRejectionMissingRunId));
        result.add_error("run_id is required");
    }
    if (replay_contract_is_blank(envelope.episode_id)) {
        result.reject(std::string(kReplayEnvelopeRejectionMissingEpisodeId));
        result.add_error("episode_id is required");
    }
    if (!envelope.has_deterministic_seed) {
        result.reject(std::string(kReplayEnvelopeRejectionMissingDeterministicSeed));
        result.add_error("deterministic_seed is required");
    }
    if (!envelope.has_source_time || !replay_contract_has_finite_time(envelope.source_time_s)) {
        result.reject(std::string(kReplayEnvelopeRejectionMissingSourceTime));
        result.add_error("source_time_s is required and must be finite");
    }
    if (envelope.snapshot_restore_supported) {
        result.reject(std::string(kReplayEnvelopeRejectionRestoreClaimUnsupported));
        result.add_error("snapshot_restore_supported must remain false in WP15-A");
    }
    if (envelope.restore_support_boundary != kReplayRestoreSupportBoundaryUnsupported) {
        result.reject(std::string(kReplayEnvelopeRejectionRestoreClaimUnsupported));
        result.add_error(
            "restore_support_boundary must remain restore_unsupported_until_snapshot_restore_proof"
        );
    }

    absorb_replay_validation(&result, validate_replay_snapshot_ref(envelope.snapshot_ref));
    absorb_replay_validation(&result, validate_replay_barrier_ref(envelope.barrier_ref));
    absorb_replay_validation(
        &result,
        validate_replay_event_order_ref(envelope.event_order_ref)
    );
    absorb_replay_validation(
        &result,
        validate_replay_facade_provenance_ref(envelope.facade_provenance_ref)
    );
    return result;
}

[[nodiscard]] inline std::string make_branch_point_identity(
    const ReplayEnvelope& envelope
) {
    return "branch_point:" + envelope.replay_envelope_id + ":" +
        envelope.snapshot_ref.snapshot_version_ref + ":" +
        envelope.barrier_ref.barrier_id + ":" + envelope.event_order_ref.event_id;
}

[[nodiscard]] inline std::vector<std::string> ordered_replay_envelope_evidence_refs(
    const ReplayEnvelope& envelope
) {
    return {
        "snapshot_version_ref=" + envelope.snapshot_ref.snapshot_version_ref,
        "barrier_id=" + envelope.barrier_ref.barrier_id,
        "event_order_ref=" + envelope.event_order_ref.event_id,
        "facade_provenance_ref=" + envelope.facade_provenance_ref.packet_ref,
    };
}

[[nodiscard]] inline std::vector<std::string> ordered_worldline_branch_evidence_refs(
    const WorldlineBranchMetadata& metadata
) {
    std::vector<std::string> refs = {
        "branch_point_ref=" + metadata.branch_point_ref,
        "replay_envelope_ref=" + metadata.replay_envelope_ref,
        "source_ref=" + metadata.source_ref,
        "provenance_ref=" + metadata.provenance_ref,
    };
    refs.reserve(refs.size() + metadata.evidence_refs.size());
    for (const auto& evidence_ref : metadata.evidence_refs) {
        refs.push_back("evidence_ref=" + evidence_ref);
    }
    return refs;
}

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

[[nodiscard]] inline ReplayContractValidationResult validate_branch_point(
    const BranchPoint& branch_point
) {
    ReplayContractValidationResult result{};
    if (replay_contract_is_blank(branch_point.branch_point_id)) {
        result.reject(std::string(kBranchPointRejectionMissingBranchPointId));
        result.add_error("branch_point_id is required");
    }
    if (replay_contract_is_blank(branch_point.replay_envelope_id)) {
        result.reject(std::string(kBranchPointRejectionMissingReplayEnvelopeId));
        result.add_error("replay_envelope_id is required");
    }
    if (replay_contract_is_blank(branch_point.snapshot_version_ref)) {
        result.reject(std::string(kReplayEnvelopeRejectionMissingSnapshotVersionRef));
        result.add_error("snapshot_version_ref is required");
    }
    if (replay_contract_is_blank(branch_point.barrier_id)) {
        result.reject(std::string(kReplayEnvelopeRejectionMissingBarrierId));
        result.add_error("barrier_id is required");
    }
    if (replay_contract_is_blank(branch_point.event_order_ref)) {
        result.reject(std::string(kReplayEnvelopeRejectionMissingEventOrderRef));
        result.add_error("event_order_ref is required");
    }
    if (replay_contract_is_blank(branch_point.facade_packet_ref)) {
        result.reject(std::string(kReplayEnvelopeRejectionMissingFacadeProvenanceRef));
        result.add_error("facade_packet_ref is required");
    }
    if (branch_point.snapshot_restore_supported) {
        result.reject(std::string(kReplayEnvelopeRejectionRestoreClaimUnsupported));
        result.add_error("branch_point.snapshot_restore_supported must remain false");
    }
    if (branch_point.restore_support_boundary != kReplayRestoreSupportBoundaryUnsupported) {
        result.reject(std::string(kReplayEnvelopeRejectionRestoreClaimUnsupported));
        result.add_error(
            "branch_point.restore_support_boundary must remain restore_unsupported_until_snapshot_restore_proof"
        );
    }
    return result;
}

[[nodiscard]] inline ReplayContractValidationResult validate_branch_point_against_replay_envelope(
    const BranchPoint& branch_point,
    const ReplayEnvelope& envelope
) {
    ReplayContractValidationResult result = validate_branch_point(branch_point);
    absorb_replay_validation(&result, validate_replay_envelope(envelope));

    if (branch_point.replay_envelope_id != envelope.replay_envelope_id) {
        result.reject(std::string(kBranchPointRejectionReplayEnvelopeMismatch));
        result.add_error(
            "branch_point.replay_envelope_id must match replay_envelope.replay_envelope_id"
        );
    }

    if (branch_point.snapshot_version_ref != envelope.snapshot_ref.snapshot_version_ref ||
        branch_point.barrier_id != envelope.barrier_ref.barrier_id ||
        branch_point.event_order_ref != envelope.event_order_ref.event_id ||
        branch_point.facade_packet_ref != envelope.facade_provenance_ref.packet_ref ||
        branch_point.branch_point_id != make_branch_point_identity(envelope)) {
        result.reject(std::string(kBranchPointRejectionIdentityMismatch));
        result.add_error(
            "branch_point identity must match replay envelope snapshot/barrier/event-order/facade refs"
        );
    }

    return result;
}

[[nodiscard]] inline ReplayRestoreSupportResult
validate_replay_envelope_for_snapshot_restore(const ReplayEnvelope& envelope) {
    ReplayRestoreSupportResult result{};
    result.replay_envelope_id = envelope.replay_envelope_id;

    const ReplayContractValidationResult validation = validate_replay_envelope(envelope);
    if (!validation.valid) {
        result.rejection_reason = validation.rejection_reason;
        return result;
    }

    result.rejection_reason =
        std::string(kReplayEnvelopeRejectionRestoreUnsupportedBoundary);
    return result;
}

[[nodiscard]] inline ReplayContractValidationResult validate_worldline_branch_metadata(
    const WorldlineBranchMetadata& metadata
) {
    ReplayContractValidationResult result{};

    if (replay_contract_is_blank(metadata.baseline_worldline_id)) {
        result.reject(std::string(kWorldlineBranchRejectionMissingBaselineWorldlineId));
        result.add_error("baseline_worldline_id is required");
    }
    if (replay_contract_is_blank(metadata.parent_worldline_id)) {
        result.reject(std::string(kWorldlineBranchRejectionMissingParentWorldlineId));
        result.add_error("parent_worldline_id is required");
    }
    if (replay_contract_is_blank(metadata.child_worldline_id)) {
        result.reject(std::string(kWorldlineBranchRejectionMissingChildWorldlineId));
        result.add_error("child_worldline_id is required");
    }
    if (!replay_contract_is_blank(metadata.child_worldline_id) &&
        (metadata.child_worldline_id == metadata.baseline_worldline_id ||
         metadata.child_worldline_id == metadata.parent_worldline_id)) {
        result.reject(std::string(kWorldlineBranchRejectionChildWorldlineCollision));
        result.add_error(
            "child_worldline_id must differ from baseline_worldline_id and parent_worldline_id"
        );
    }
    if (replay_contract_is_blank(metadata.branch_point_ref)) {
        result.reject(std::string(kWorldlineBranchRejectionMissingBranchPointRef));
        result.add_error("branch_point_ref is required");
    }
    if (replay_contract_is_blank(metadata.replay_envelope_ref)) {
        result.reject(std::string(kWorldlineBranchRejectionMissingReplayEnvelopeRef));
        result.add_error("replay_envelope_ref is required");
    }
    if (replay_contract_is_blank(metadata.branch_reason)) {
        result.reject(std::string(kWorldlineBranchRejectionMissingBranchReason));
        result.add_error("branch_reason is required");
    }
    if (replay_contract_is_blank(metadata.intervention_intent)) {
        result.reject(
            std::string(kWorldlineBranchRejectionMissingInterventionIntent)
        );
        result.add_error("intervention_intent is required");
    }
    if (replay_contract_is_blank(metadata.mutation_intent)) {
        result.reject(std::string(kWorldlineBranchRejectionMissingMutationIntent));
        result.add_error("mutation_intent is required");
    } else if (!is_known_worldline_branch_mutation_intent(
                   metadata.mutation_intent)) {
        result.reject(std::string(kWorldlineBranchRejectionInvalidMutationIntent));
        result.add_error(
            "mutation_intent must be metadata_only, support_state_only, or raw_authoritative_state_mutation"
        );
    }
    if (!metadata.metadata_only) {
        result.reject(
            std::string(kWorldlineBranchRejectionMetadataOnlyBoundaryRequired)
        );
        result.add_error("metadata_only must remain true in WP15-B");
    }
    if (metadata.requests_authoritative_state_mutation ||
        metadata.mutation_intent ==
            kWorldlineBranchMutationIntentRawAuthoritativeStateMutation) {
        result.reject(
            std::string(kWorldlineBranchRejectionRawStateMutationForbidden)
        );
        result.add_error(
            "raw authoritative state mutation is not allowed through worldline branch metadata"
        );
    }
    if (replay_contract_is_blank(metadata.source_ref)) {
        result.reject(std::string(kWorldlineBranchRejectionMissingSourceRef));
        result.add_error("source_ref is required");
    }
    if (replay_contract_is_blank(metadata.provenance_ref)) {
        result.reject(std::string(kWorldlineBranchRejectionMissingProvenanceRef));
        result.add_error("provenance_ref is required");
    }
    if (!information_state_source_has_valid_label(metadata.source_information_state)) {
        result.reject(std::string(kWorldlineBranchRejectionInvalidSourceLabel));
        result.add_error(
            "source_information_state must carry a valid WP11/WP12-compatible label"
        );
    }
    if (metadata.evidence_refs.empty()) {
        result.reject(std::string(kWorldlineBranchRejectionMissingEvidenceRefs));
        result.add_error("evidence_refs must not be empty");
    } else {
        for (const auto& evidence_ref : metadata.evidence_refs) {
            if (replay_contract_is_blank(evidence_ref)) {
                result.reject(std::string(kWorldlineBranchRejectionMissingEvidenceRefs));
                result.add_error("evidence_refs cannot contain blank entries");
                break;
            }
        }
    }
    if (!is_known_worldline_branch_support_state(metadata.support_state)) {
        result.reject(std::string(kWorldlineBranchRejectionInvalidSupportState));
        result.add_error(
            "support_state must be metadata_only, admitted, rejected, or restore_unsupported"
        );
    }
    if (metadata.snapshot_restore_supported) {
        result.reject(
            std::string(kWorldlineBranchRejectionRestoreClaimUnsupported)
        );
        result.add_error("snapshot_restore_supported must remain false in WP15-B");
    }
    if (metadata.restore_support_boundary !=
        kReplayRestoreSupportBoundaryUnsupported) {
        result.reject(
            std::string(kWorldlineBranchRejectionRestoreClaimUnsupported)
        );
        result.add_error(
            "restore_support_boundary must remain restore_unsupported_until_snapshot_restore_proof"
        );
    }

    return result;
}

[[nodiscard]] inline ReplayContractValidationResult
validate_worldline_branch_metadata_against_branch_point(
    const WorldlineBranchMetadata& metadata,
    const BranchPoint& branch_point,
    const ReplayEnvelope& envelope
) {
    ReplayContractValidationResult result =
        validate_worldline_branch_metadata(metadata);
    absorb_replay_validation(
        &result,
        validate_branch_point_against_replay_envelope(branch_point, envelope)
    );

    if (metadata.branch_point_ref != branch_point.branch_point_id) {
        result.reject(std::string(kWorldlineBranchRejectionBranchPointRefMismatch));
        result.add_error(
            "branch_point_ref must match branch_point.branch_point_id"
        );
    }
    if (metadata.replay_envelope_ref != envelope.replay_envelope_id ||
        metadata.replay_envelope_ref != branch_point.replay_envelope_id) {
        result.reject(
            std::string(kWorldlineBranchRejectionReplayEnvelopeRefMismatch)
        );
        result.add_error(
            "replay_envelope_ref must match replay_envelope.replay_envelope_id and branch_point.replay_envelope_id"
        );
    }

    return result;
}

[[nodiscard]] inline WorldlineBranchSupportResult
validate_worldline_branch_metadata_for_snapshot_restore(
    const WorldlineBranchMetadata& metadata,
    const BranchPoint& branch_point,
    const ReplayEnvelope& envelope
) {
    WorldlineBranchSupportResult result{};
    result.child_worldline_id = metadata.child_worldline_id;

    const ReplayContractValidationResult validation =
        validate_worldline_branch_metadata_against_branch_point(
            metadata,
            branch_point,
            envelope
        );
    if (!validation.valid) {
        result.support_state = std::string(kWorldlineBranchSupportStateRejected);
        result.rejection_reason = validation.rejection_reason;
        return result;
    }

    result.support_state =
        std::string(kWorldlineBranchSupportStateRestoreUnsupported);
    result.rejection_reason =
        std::string(kWorldlineBranchRejectionRestoreUnsupportedBoundary);
    return result;
}

[[nodiscard]] inline ReplayContractValidationResult
validate_counterfactual_authority_surface(
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
