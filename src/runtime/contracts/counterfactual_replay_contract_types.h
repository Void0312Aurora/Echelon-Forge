#pragma once

#include <cstdint>
#include <string>
#include <utility>
#include <vector>

#include "runtime/contracts/counterfactual_replay_contract_constants.h"
#include "runtime/contracts/policy_contracts.h"

namespace runtime::counterfactual {

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

}  // namespace runtime::counterfactual
