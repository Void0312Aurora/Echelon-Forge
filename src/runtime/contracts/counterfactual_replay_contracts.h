#pragma once

#include <string>
#include <vector>

#include "runtime/contracts/counterfactual_replay_contract_constants.h"
#include "runtime/contracts/counterfactual_replay_contract_types.h"
#include "runtime/contracts/counterfactual_replay_contract_validation.h"

namespace runtime::counterfactual {

// Public umbrella header intentionally preserves the historic include path while
// delegating DTO and validation ownership to focused split headers.
// Compatibility markers retained for text-based architecture probes:
// snapshot_restore_supported = false

struct ReplaySnapshotRef;
struct ReplayBarrierRef;
struct ReplayEventOrderRef;
struct ReplayFacadeProvenanceRef;
struct ReplayEnvelope;
struct BranchPoint;
struct WorldlineBranchMetadata;
struct CounterfactualExperimentRequest;
struct ReplayContractValidationResult;
struct ReplayRestoreSupportResult;
struct WorldlineBranchSupportResult;
struct CounterfactualAdmissionResult;
struct ScenarioGenerationEvidenceMetadataRef;
struct ScenarioGenerationRequestMetadata;
struct ScenarioGenerationArtifactMetadata;
struct ExperimentProfileObservationRef;
struct ExperimentEvidenceBridgeRecord;
struct ExperimentEvidenceBridgeValidationResult;

[[nodiscard]] ReplayContractValidationResult validate_replay_snapshot_ref(
    const ReplaySnapshotRef& snapshot_ref
);
[[nodiscard]] ReplayContractValidationResult validate_replay_barrier_ref(
    const ReplayBarrierRef& barrier_ref
);
[[nodiscard]] ReplayContractValidationResult validate_replay_event_order_ref(
    const ReplayEventOrderRef& event_order_ref
);
[[nodiscard]] ReplayContractValidationResult validate_replay_facade_provenance_ref(
    const ReplayFacadeProvenanceRef& provenance_ref
);
[[nodiscard]] ReplayContractValidationResult validate_replay_envelope(
    const ReplayEnvelope& envelope
);
[[nodiscard]] std::string make_branch_point_identity(
    const ReplayEnvelope& envelope
);
[[nodiscard]] std::vector<std::string> ordered_replay_envelope_evidence_refs(
    const ReplayEnvelope& envelope
);
[[nodiscard]] std::vector<std::string> ordered_worldline_branch_evidence_refs(
    const WorldlineBranchMetadata& metadata
);
[[nodiscard]] std::vector<std::string> ordered_counterfactual_request_evidence_refs(
    const CounterfactualExperimentRequest& request
);
[[nodiscard]] ReplayContractValidationResult validate_branch_point_against_replay_envelope(
    const BranchPoint& branch_point,
    const ReplayEnvelope& envelope
);
[[nodiscard]] ReplayRestoreSupportResult validate_replay_envelope_for_snapshot_restore(
    const ReplayEnvelope& envelope
);
[[nodiscard]] ReplayContractValidationResult validate_worldline_branch_metadata(
    const WorldlineBranchMetadata& metadata
);
[[nodiscard]] ReplayContractValidationResult
validate_worldline_branch_metadata_against_branch_point(
    const WorldlineBranchMetadata& metadata,
    const BranchPoint& branch_point,
    const ReplayEnvelope& envelope
);
[[nodiscard]] WorldlineBranchSupportResult
validate_worldline_branch_metadata_for_snapshot_restore(
    const WorldlineBranchMetadata& metadata,
    const BranchPoint& branch_point,
    const ReplayEnvelope& envelope
);
[[nodiscard]] ReplayContractValidationResult validate_counterfactual_authority_surface(
    const CounterfactualExperimentRequest& request
);
[[nodiscard]] ReplayContractValidationResult validate_counterfactual_experiment_request(
    const CounterfactualExperimentRequest& request
);
[[nodiscard]] CounterfactualAdmissionResult admit_counterfactual_experiment_request(
    const CounterfactualExperimentRequest& request
);
[[nodiscard]] std::vector<std::string>
ordered_scenario_generation_request_metadata_evidence_refs(
    const ScenarioGenerationArtifactMetadata& artifact
);
[[nodiscard]] std::vector<std::string>
ordered_experiment_profile_observation_evidence_refs(
    const ExperimentProfileObservationRef& observation
);
[[nodiscard]] std::vector<std::string> ordered_experiment_bridge_evidence_refs(
    const ExperimentEvidenceBridgeRecord& record
);
[[nodiscard]] ExperimentEvidenceBridgeValidationResult
validate_scenario_generation_artifact_metadata(
    const ScenarioGenerationArtifactMetadata& artifact
);
[[nodiscard]] ExperimentEvidenceBridgeValidationResult
validate_experiment_profile_observation_ref(
    const ExperimentProfileObservationRef& observation
);
[[nodiscard]] ExperimentEvidenceBridgeValidationResult
validate_experiment_evidence_bridge_record(
    const ExperimentEvidenceBridgeRecord& record,
    const CounterfactualAdmissionResult& admission,
    const ReplayEnvelope& replay_envelope,
    const ScenarioGenerationArtifactMetadata& generated_input
);
[[nodiscard]] ExperimentEvidenceBridgeRecord make_experiment_evidence_bridge_record(
    const CounterfactualAdmissionResult& admission,
    const ReplayEnvelope& replay_envelope,
    const ScenarioGenerationArtifactMetadata& generated_input,
    std::string experiment_run_id,
    std::string comparison_id,
    std::vector<ExperimentProfileObservationRef> profile_observation_refs,
    std::vector<std::string> evidence_refs
);

}  // namespace runtime::counterfactual
