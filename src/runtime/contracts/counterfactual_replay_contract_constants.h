#pragma once

#include <string_view>

namespace runtime::counterfactual {

inline constexpr std::string_view kDeterministicReplayEventOrderSortKey =
    "timestamp_priority_event_id";
inline constexpr std::string_view kReplayRestoreSupportBoundaryUnsupported =
    "restore_unsupported_until_snapshot_restore_proof";
inline constexpr std::string_view kReplayRestoreSupportBoundaryHostOwnedFacadeStateOnly =
    "host_owned_facade_state_only";

inline constexpr std::string_view kReplayEnvelopeRejectionMissingEnvelopeId =
    "replay_envelope_id_required";
inline constexpr std::string_view kReplayEnvelopeRejectionMissingRunId = "replay_run_id_required";
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
    "snapshot_restore_unsupported";
inline constexpr std::string_view kReplayEnvelopeRejectionRestoreClaimUnsupported =
    "snapshot_restore_claim_not_supported";
inline constexpr std::string_view kReplayEnvelopeRejectionRestoreBoundaryInvalid =
    "snapshot_restore_boundary_not_supported";

inline constexpr std::string_view kBranchPointRejectionMissingBranchPointId =
    "branch_point_id_required";
inline constexpr std::string_view kBranchPointRejectionMissingReplayEnvelopeId =
    "branch_point_replay_envelope_id_required";
inline constexpr std::string_view kBranchPointRejectionReplayEnvelopeMismatch =
    "branch_point_replay_envelope_mismatch";
inline constexpr std::string_view kBranchPointRejectionIdentityMismatch =
    "branch_point_identity_mismatch";

inline constexpr std::string_view kWorldlineBranchSupportStateMetadataOnly = "metadata_only";
inline constexpr std::string_view kWorldlineBranchSupportStateAdmitted = "admitted";
inline constexpr std::string_view kWorldlineBranchSupportStateRejected = "rejected";
inline constexpr std::string_view kWorldlineBranchSupportStateRestoreUnsupported =
    "restore_unsupported";

inline constexpr std::string_view kWorldlineBranchMutationIntentMetadataOnly = "metadata_only";
inline constexpr std::string_view kWorldlineBranchMutationIntentSupportStateOnly =
    "support_state_only";
inline constexpr std::string_view kWorldlineBranchMutationIntentRawAuthoritativeStateMutation =
    "raw_authoritative_state_mutation";

inline constexpr std::string_view kWorldlineBranchRejectionMissingBaselineWorldlineId =
    "worldline_branch_baseline_worldline_id_required";
inline constexpr std::string_view kWorldlineBranchRejectionMissingParentWorldlineId =
    "worldline_branch_parent_worldline_id_required";
inline constexpr std::string_view kWorldlineBranchRejectionMissingChildWorldlineId =
    "worldline_branch_child_worldline_id_required";
inline constexpr std::string_view kWorldlineBranchRejectionChildWorldlineCollision =
    "worldline_branch_child_worldline_id_collision";
inline constexpr std::string_view kWorldlineBranchRejectionMissingBranchPointRef =
    "worldline_branch_branch_point_ref_required";
inline constexpr std::string_view kWorldlineBranchRejectionMissingReplayEnvelopeRef =
    "worldline_branch_replay_envelope_ref_required";
inline constexpr std::string_view kWorldlineBranchRejectionBranchPointRefMismatch =
    "worldline_branch_branch_point_ref_mismatch";
inline constexpr std::string_view kWorldlineBranchRejectionReplayEnvelopeRefMismatch =
    "worldline_branch_replay_envelope_ref_mismatch";
inline constexpr std::string_view kWorldlineBranchRejectionMissingBranchReason =
    "worldline_branch_reason_required";
inline constexpr std::string_view kWorldlineBranchRejectionMissingInterventionIntent =
    "worldline_branch_intervention_intent_required";
inline constexpr std::string_view kWorldlineBranchRejectionMissingMutationIntent =
    "worldline_branch_mutation_intent_required";
inline constexpr std::string_view kWorldlineBranchRejectionInvalidMutationIntent =
    "worldline_branch_mutation_intent_invalid";
inline constexpr std::string_view kWorldlineBranchRejectionMetadataOnlyBoundaryRequired =
    "worldline_branch_metadata_only_boundary_required";
inline constexpr std::string_view kWorldlineBranchRejectionRawStateMutationForbidden =
    "worldline_branch_raw_authoritative_state_mutation_forbidden";
inline constexpr std::string_view kWorldlineBranchRejectionMissingSourceRef =
    "worldline_branch_source_ref_required";
inline constexpr std::string_view kWorldlineBranchRejectionMissingProvenanceRef =
    "worldline_branch_provenance_ref_required";
inline constexpr std::string_view kWorldlineBranchRejectionInvalidSourceLabel =
    "worldline_branch_source_label_invalid";
inline constexpr std::string_view kWorldlineBranchRejectionMissingEvidenceRefs =
    "worldline_branch_evidence_refs_required";
inline constexpr std::string_view kWorldlineBranchRejectionInvalidSupportState =
    "worldline_branch_support_state_invalid";
inline constexpr std::string_view kWorldlineBranchRejectionRestoreUnsupportedBoundary =
    "worldline_branch_restore_unsupported";
inline constexpr std::string_view kWorldlineBranchRejectionRestoreClaimUnsupported =
    "worldline_branch_restore_claim_not_supported";
inline constexpr std::string_view kWorldlineBranchRejectionRestoreBoundaryInvalid =
    "worldline_branch_restore_boundary_not_supported";

inline constexpr std::string_view kCounterfactualAdmissionStateAdmitted = "admitted";
inline constexpr std::string_view kCounterfactualAdmissionStateRejected = "rejected";
inline constexpr std::string_view kCounterfactualAdmissionStateRestoreUnsupported =
    "restore_unsupported";

inline constexpr std::string_view kCounterfactualInterventionKindObservationWithhold =
    "observation_withhold";
inline constexpr std::string_view kCounterfactualInterventionKindPolicySubstitution =
    "policy_substitution";
inline constexpr std::string_view kCounterfactualInterventionKindCommandVariant = "command_variant";
inline constexpr std::string_view kCounterfactualInterventionKindSpawnVariantRequest =
    "spawn_variant_request";
inline constexpr std::string_view kCounterfactualInterventionKindRawAuthoritativeStateMutation =
    "raw_authoritative_state_mutation";

inline constexpr std::string_view kCounterfactualSourceOperatorRequest = "operator_request";
inline constexpr std::string_view kCounterfactualSourceAnalystRequest = "analyst_request";
inline constexpr std::string_view kCounterfactualSourceExperimentPlan = "experiment_plan";
inline constexpr std::string_view kCounterfactualSourceCounterfactualBranch =
    "counterfactual_branch";

inline constexpr std::string_view kCounterfactualCapabilityRefPrefixBundle = "capability_bundle:";
inline constexpr std::string_view kCounterfactualCapabilityRefPrefixResolvedSpawnPlan =
    "resolved_spawn_plan:";

inline constexpr std::string_view kCounterfactualRequestRejectionMissingRequestId =
    "counterfactual_request_id_required";
inline constexpr std::string_view kCounterfactualRequestRejectionMissingBaselineWorldlineId =
    "counterfactual_baseline_worldline_id_required";
inline constexpr std::string_view kCounterfactualRequestRejectionBaselineWorldlineMismatch =
    "counterfactual_baseline_worldline_id_mismatch";
inline constexpr std::string_view kCounterfactualRequestRejectionMissingInterventionKind =
    "counterfactual_intervention_kind_required";
inline constexpr std::string_view kCounterfactualRequestRejectionUnsupportedInterventionKind =
    "counterfactual_intervention_kind_not_supported";
inline constexpr std::string_view kCounterfactualRequestRejectionMissingSource =
    "counterfactual_source_required";
inline constexpr std::string_view kCounterfactualRequestRejectionUnsupportedSource =
    "counterfactual_source_not_supported";
inline constexpr std::string_view kCounterfactualRequestRejectionMissingAuthorityRef =
    "counterfactual_authority_ref_required";
inline constexpr std::string_view kCounterfactualRequestRejectionMissingProvenanceRef =
    "counterfactual_provenance_ref_required";
inline constexpr std::string_view kCounterfactualRequestRejectionInvalidAuthorityScope =
    "counterfactual_authority_scope_invalid";
inline constexpr std::string_view kCounterfactualRequestRejectionInvalidAuthoritySource =
    "counterfactual_authority_information_source_invalid";
inline constexpr std::string_view kCounterfactualRequestRejectionMissingAuthorityEvidenceRefs =
    "counterfactual_authority_evidence_refs_required";
inline constexpr std::string_view kCounterfactualRequestRejectionMissingBackendProfileRef =
    "counterfactual_backend_profile_ref_required";
inline constexpr std::string_view kCounterfactualRequestRejectionUnsupportedBackendProfileRef =
    "counterfactual_backend_profile_ref_not_found";
inline constexpr std::string_view kCounterfactualRequestRejectionInvalidBackendProfileRef =
    "counterfactual_backend_profile_ref_invalid";
inline constexpr std::string_view kCounterfactualRequestRejectionMissingFidelityProfileRef =
    "counterfactual_fidelity_profile_ref_required";
inline constexpr std::string_view kCounterfactualRequestRejectionUnsupportedFidelityProfileRef =
    "counterfactual_fidelity_profile_ref_not_supported";
inline constexpr std::string_view kCounterfactualRequestRejectionMissingCapabilityRefs =
    "counterfactual_capability_refs_required";
inline constexpr std::string_view kCounterfactualRequestRejectionUnsupportedCapabilityRef =
    "counterfactual_capability_ref_not_supported";
inline constexpr std::string_view kCounterfactualRequestRejectionMissingEvidenceRefs =
    "counterfactual_evidence_refs_required";
inline constexpr std::string_view
    kCounterfactualRequestRejectionWorldlineSupportStatePreclaimForbidden =
        "counterfactual_worldline_support_state_preclaim_forbidden";
inline constexpr std::string_view kCounterfactualRequestRejectionRawStateMutationForbidden =
    "counterfactual_raw_authoritative_state_mutation_forbidden";
inline constexpr std::string_view kCounterfactualRequestRejectionRestoreUnsupportedBoundary =
    "counterfactual_snapshot_restore_unsupported";

inline constexpr std::string_view kScenarioGenerationArtifactKindRequestMetadata =
    "scenario_generation_request_metadata";
inline constexpr std::string_view kScenarioGenerationContractVersionRequestV1 =
    "scenario_generation_request.v1";
inline constexpr std::string_view kScenarioGenerationKindScenarioVariation = "scenario_variation";
inline constexpr std::string_view kScenarioGenerationKindAdversaryPlacement = "adversary_placement";
inline constexpr std::string_view kScenarioGenerationKindRoutePerturbation = "route_perturbation";
inline constexpr std::string_view kScenarioGenerationKindMissionPerturbation =
    "mission_perturbation";
inline constexpr std::string_view kScenarioGenerationKindStressorInjection = "stressor_injection";
inline constexpr std::string_view kScenarioGenerationSourceAnalystAuthored = "analyst_authored";
inline constexpr std::string_view kScenarioGenerationSourceCounterfactualBranch =
    "counterfactual_branch";
inline constexpr std::string_view kScenarioGenerationSourceCurriculumGeneration =
    "curriculum_generation";
inline constexpr std::string_view kScenarioGenerationSourceEvaluationReplay = "evaluation_replay";
inline constexpr std::string_view kScenarioGenerationEvidenceKindBaselineScenario =
    "baseline_scenario";
inline constexpr std::string_view kScenarioGenerationEvidenceKindBranchPoint = "branch_point";
inline constexpr std::string_view kScenarioGenerationEvidenceKindCapabilityBundle =
    "capability_bundle";
inline constexpr std::string_view kScenarioGenerationEvidenceKindLearningEvidence =
    "learning_evidence";
inline constexpr std::string_view kScenarioGenerationEvidenceKindReplayEnvelope = "replay_envelope";
inline constexpr std::string_view kScenarioGenerationEvidenceKindReviewNote = "review_note";

inline constexpr std::string_view kExperimentProfileObservationStatusObserved = "observed";
inline constexpr std::string_view kExperimentProfileObservationStatusProposed = "proposed";
inline constexpr std::string_view kExperimentProfileObservationStatusBlocked = "blocked";
inline constexpr std::string_view kExperimentProfileObservationStatusUnsupported = "unsupported";

inline constexpr std::string_view kExperimentProfileClaimScopeDescriptive = "descriptive";
inline constexpr std::string_view kExperimentProfileClaimScopeComparative = "comparative";
inline constexpr std::string_view kExperimentProfileClaimScopeGatingRelated = "gating_related";

inline constexpr std::string_view kExperimentEvidenceClaimBoundaryNonTruthClaim =
    "non_truth_claim_observation_only";
inline constexpr std::string_view kExperimentEvidencePromotionStateNotPromoted = "not_promoted";

inline constexpr std::string_view kExperimentEvidenceBridgeRejectionMissingExperimentRunId =
    "experiment_evidence_run_id_required";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionMissingComparisonId =
    "experiment_evidence_comparison_id_required";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionMissingReplayRunId =
    "experiment_evidence_replay_run_id_required";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionMissingBaselineWorldlineId =
    "experiment_evidence_baseline_worldline_id_required";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionMissingVariantWorldlineId =
    "experiment_evidence_variant_worldline_id_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionMissingCounterfactualRequestRef =
        "experiment_evidence_counterfactual_request_ref_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionMissingCounterfactualAdmissionRef =
        "experiment_evidence_counterfactual_admission_ref_required";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionMissingReplayEnvelopeRef =
    "experiment_evidence_replay_envelope_ref_required";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionMissingBranchPointRef =
    "experiment_evidence_branch_point_ref_required";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionMissingGeneratedInputRef =
    "experiment_evidence_generated_input_ref_required";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionMissingBackendProfileRef =
    "experiment_evidence_backend_profile_ref_required";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionMissingFidelityProfileRef =
    "experiment_evidence_fidelity_profile_ref_required";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionMissingCapabilityRefs =
    "experiment_evidence_capability_refs_required";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionMissingProfileObservationRefs =
    "experiment_evidence_profile_observation_refs_required";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionMissingEvidenceRefs =
    "experiment_evidence_refs_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionCounterfactualAdmissionRequired =
        "experiment_evidence_counterfactual_admission_required";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionCounterfactualRequestMismatch =
    "experiment_evidence_counterfactual_request_mismatch";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionBaselineWorldlineMismatch =
    "experiment_evidence_baseline_worldline_id_mismatch";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionVariantWorldlineMismatch =
    "experiment_evidence_variant_worldline_id_mismatch";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionReplayRunIdMismatch =
    "experiment_evidence_replay_run_id_mismatch";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionReplayEnvelopeRefMismatch =
    "experiment_evidence_replay_envelope_ref_mismatch";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionBranchPointRefMismatch =
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
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionGeneratedInputVersionRequired =
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
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionGeneratedInputEvidenceRequired =
    "experiment_evidence_generated_input_evidence_required";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionGeneratedInputReplayEnvelopeMismatch =
        "experiment_evidence_generated_input_replay_envelope_ref_mismatch";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionGeneratedInputBranchPointMismatch =
        "experiment_evidence_generated_input_branch_point_ref_mismatch";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionBackendProfileRefMismatch =
    "experiment_evidence_backend_profile_ref_mismatch";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionFidelityProfileRefMismatch =
    "experiment_evidence_fidelity_profile_ref_mismatch";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionCapabilityRefMismatch =
    "experiment_evidence_capability_ref_mismatch";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionGeneratedInputCapabilityRefUnsupported =
        "experiment_evidence_generated_input_capability_ref_not_supported";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionProfileObservationRefRequired =
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
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionTruthClaimForbidden =
    "experiment_evidence_truth_claim_forbidden";
inline constexpr std::string_view kExperimentEvidenceBridgeRejectionSupportPromotionForbidden =
    "experiment_evidence_support_promotion_forbidden";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionProfileObservationTruthClaimForbidden =
        "experiment_evidence_profile_observation_truth_claim_forbidden";
inline constexpr std::string_view
    kExperimentEvidenceBridgeRejectionProfileObservationSupportPromotionForbidden =
        "experiment_evidence_profile_observation_support_promotion_forbidden";

} // namespace runtime::counterfactual
