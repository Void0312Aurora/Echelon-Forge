#pragma once

#include <string>
#include <vector>

#include "runtime/contracts/counterfactual_replay_validation_helpers.h"

namespace runtime::counterfactual {

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
    if (!is_supported_snapshot_restore_boundary(envelope.restore_support_boundary)) {
        result.reject(std::string(kReplayEnvelopeRejectionRestoreBoundaryInvalid));
        result.add_error(
            "restore_support_boundary must be restore_unsupported_until_snapshot_restore_proof or host_owned_facade_state_only"
        );
    }
    if (envelope.snapshot_restore_supported) {
        if (envelope.restore_support_boundary !=
            kReplayRestoreSupportBoundaryHostOwnedFacadeStateOnly) {
            result.reject(std::string(kReplayEnvelopeRejectionRestoreClaimUnsupported));
            result.add_error(
                "snapshot_restore_supported requires host_owned_facade_state_only boundary"
            );
        }
    } else if (envelope.restore_support_boundary !=
               kReplayRestoreSupportBoundaryUnsupported) {
        result.reject(std::string(kReplayEnvelopeRejectionRestoreClaimUnsupported));
        result.add_error(
            "snapshot_restore_supported=false requires restore_unsupported_until_snapshot_restore_proof"
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
    if (!is_supported_snapshot_restore_boundary(branch_point.restore_support_boundary)) {
        result.reject(std::string(kReplayEnvelopeRejectionRestoreBoundaryInvalid));
        result.add_error(
            "branch_point.restore_support_boundary must be restore_unsupported_until_snapshot_restore_proof or host_owned_facade_state_only"
        );
    }
    if (branch_point.snapshot_restore_supported) {
        if (branch_point.restore_support_boundary !=
            kReplayRestoreSupportBoundaryHostOwnedFacadeStateOnly) {
            result.reject(std::string(kReplayEnvelopeRejectionRestoreClaimUnsupported));
            result.add_error(
                "branch_point.snapshot_restore_supported requires host_owned_facade_state_only boundary"
            );
        }
    } else if (branch_point.restore_support_boundary !=
               kReplayRestoreSupportBoundaryUnsupported) {
        result.reject(std::string(kReplayEnvelopeRejectionRestoreClaimUnsupported));
        result.add_error(
            "branch_point.snapshot_restore_supported=false requires restore_unsupported_until_snapshot_restore_proof"
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

    if (envelope.snapshot_restore_supported &&
        envelope.restore_support_boundary ==
            kReplayRestoreSupportBoundaryHostOwnedFacadeStateOnly) {
        result.supported = true;
        return result;
    }

    result.rejection_reason =
        std::string(kReplayEnvelopeRejectionRestoreUnsupportedBoundary);
    return result;
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
    if (!is_supported_snapshot_restore_boundary(metadata.restore_support_boundary)) {
        result.reject(std::string(kWorldlineBranchRejectionRestoreBoundaryInvalid));
        result.add_error(
            "restore_support_boundary must be restore_unsupported_until_snapshot_restore_proof or host_owned_facade_state_only"
        );
    }
    if (metadata.snapshot_restore_supported) {
        if (metadata.restore_support_boundary !=
            kReplayRestoreSupportBoundaryHostOwnedFacadeStateOnly) {
            result.reject(
                std::string(kWorldlineBranchRejectionRestoreClaimUnsupported)
            );
            result.add_error(
                "snapshot_restore_supported requires host_owned_facade_state_only boundary"
            );
        }
    } else if (metadata.restore_support_boundary !=
               kReplayRestoreSupportBoundaryUnsupported) {
        result.reject(
            std::string(kWorldlineBranchRejectionRestoreClaimUnsupported)
        );
        result.add_error(
            "snapshot_restore_supported=false requires restore_unsupported_until_snapshot_restore_proof"
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

    if (metadata.snapshot_restore_supported &&
        metadata.restore_support_boundary ==
            kReplayRestoreSupportBoundaryHostOwnedFacadeStateOnly) {
        result.supported = true;
        result.support_state = std::string(kWorldlineBranchSupportStateAdmitted);
        return result;
    }

    result.support_state =
        std::string(kWorldlineBranchSupportStateRestoreUnsupported);
    result.rejection_reason =
        std::string(kWorldlineBranchRejectionRestoreUnsupportedBoundary);
    return result;
}

}  // namespace runtime::counterfactual
