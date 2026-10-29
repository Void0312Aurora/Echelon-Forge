#include "runtime_branch_contract.h"

#include <algorithm>
#include <cctype>
#include <utility>

namespace runtime::host {

namespace {

bool is_lower_sha256(const std::string &value) noexcept {
    if (value.size() != 64) {
        return false;
    }
    return std::all_of(value.begin(), value.end(), [](unsigned char byte) {
        return std::isdigit(byte) != 0 || (byte >= 'a' && byte <= 'f');
    });
}

RuntimeBranchStatus failure(RuntimeBranchError error, const char *detail) {
    return {.error = error, .detail = detail};
}

RuntimeStateTransferStatus transfer_failure(const RuntimeBranchStatus &status) {
    return {.error = status.error == RuntimeBranchError::ProductionForbidden
                         ? RuntimeStateTransferError::ProductionAuthorityForbidden
                         : RuntimeStateTransferError::InvalidArgument,
            .detail = status.detail};
}

RuntimeStateTransferStatus state_failure(RuntimeStateTransferError error, const char *detail) {
    return {.error = error, .detail = detail};
}

bool same_snapshot(const RuntimeEpisodeCoordinatorSnapshot &lhs,
                   const RuntimeEpisodeCoordinatorSnapshot &rhs) noexcept {
    return lhs.episode == rhs.episode && lhs.phase == rhs.phase &&
           lhs.step_sequence == rhs.step_sequence && lhs.barrier_sequence == rhs.barrier_sequence &&
           lhs.snapshot_id == rhs.snapshot_id && lhs.snapshot_sha256 == rhs.snapshot_sha256;
}

bool same_scope(const RuntimeEpisodeRef &parent, const RuntimeEpisodeRef &child) noexcept {
    return parent.episode_id == child.episode_id &&
           parent.episode_generation == child.episode_generation &&
           parent.world.world_slot == child.world.world_slot &&
           parent.world.world_generation == child.world.world_generation;
}

} // namespace

bool RuntimeBranchRef::well_formed() const noexcept {
    return branch_id.well_formed() && parent_snapshot_id.well_formed() &&
           child_resource_id.well_formed() && parent_episode.well_formed() &&
           parent_step_sequence > 0 && depth > 0 && is_lower_sha256(parent_snapshot_sha256) &&
           is_lower_sha256(intervention_sha256);
}

RuntimeBranchStatus
validate_runtime_branch_fork_request(const RuntimeBranchForkRequest &request) noexcept {
    const auto &parent = request.parent_snapshot;
    if (!parent.episode.well_formed() || !parent.snapshot_id.well_formed() ||
        parent.step_sequence == 0 || !is_lower_sha256(parent.snapshot_sha256)) {
        return failure(RuntimeBranchError::InvalidParentSnapshot,
                       "branch parent snapshot is not a complete native identity");
    }
    if (parent.phase != RuntimeEpisodePhase::Running) {
        return failure(RuntimeBranchError::ParentNotRunning,
                       "branch parent must be a running episode boundary");
    }
    if (!request.branch_id.well_formed()) {
        return failure(RuntimeBranchError::InvalidBranchIdentity,
                       "branch identity must be a non-zero native identity");
    }
    if (!is_lower_sha256(request.intervention_sha256)) {
        return failure(RuntimeBranchError::InvalidInterventionDigest,
                       "branch intervention must be a lowercase SHA-256 digest");
    }
    if (request.horizon == 0) {
        return failure(RuntimeBranchError::InvalidHorizon,
                       "branch horizon must be greater than zero");
    }
    if (!request.require_parent_immutable) {
        return failure(RuntimeBranchError::ParentImmutabilityRequired,
                       "branch admission requires an immutable parent snapshot");
    }
    if (request.production_authorized) {
        return failure(RuntimeBranchError::ProductionForbidden,
                       "branch contract is dark/shadow until native gates pass");
    }
    if (!request.parent_plan_sha256.empty() && !is_lower_sha256(request.parent_plan_sha256)) {
        return failure(RuntimeBranchError::InvalidParentSnapshot,
                       "parent plan binding must be a lowercase SHA-256 digest");
    }
    return {};
}

RuntimeBranchStatus
validate_runtime_branch_fork_proof(const RuntimeBranchForkProof &proof) noexcept {
    if (!proof.branch.well_formed()) {
        return failure(RuntimeBranchError::InvalidBranchIdentity,
                       "branch proof does not carry a complete branch reference");
    }
    if (!proof.parent_barrier_sealed || !proof.state_scope_complete || !proof.sibling_isolated ||
        !proof.external_side_effects_quarantined) {
        return failure(
            RuntimeBranchError::IncompleteIsolationProof,
            "branch proof is missing a parent, state-scope, isolation, or side-effect gate");
    }
    if (proof.production_authorized) {
        return failure(RuntimeBranchError::ProductionForbidden,
                       "branch proof cannot authorize production publication");
    }
    return {};
}

RuntimeNativeSiblingBranchResult
RuntimeNativeSiblingBranchExecutor::execute(RuntimeNativeSiblingBranchRequest request) {
    RuntimeNativeSiblingBranchResult result;
    result.branch_status = validate_runtime_branch_fork_request(request.admission);
    if (!result.branch_status) {
        result.status = transfer_failure(result.branch_status);
        return result;
    }
    if (request.parent_coordinator == nullptr || request.source_owner_registry == nullptr ||
        request.child_owner_registry == nullptr ||
        request.source_owner_registry == request.child_owner_registry ||
        request.source_resource_identity == request.child_resource_identity ||
        !request.source_resource_identity.well_formed() ||
        !request.child_resource_identity.well_formed() ||
        !request.branch_authority_nonce.well_formed() || request.lifecycle_ticket == 0 ||
        request.candidate_sequence == 0 || !request.begin_child_state_transfer ||
        !request.end_child_state_transfer ||
        request.evidence.source_final_mutation_fence_sequence == 0) {
        result.status =
            state_failure(RuntimeStateTransferError::InvalidArgument,
                          "native sibling branch admission is incomplete or aliases owners");
        return result;
    }

    const auto current_parent = request.parent_coordinator->snapshot();
    if (!same_snapshot(current_parent, request.admission.parent_snapshot)) {
        result.status = state_failure(RuntimeStateTransferError::StaleIntent,
                                      "branch parent snapshot changed before admission");
        return result;
    }
    if (!request.child_episode.well_formed() ||
        !same_scope(request.admission.parent_snapshot.episode, request.child_episode) ||
        request.child_episode.world.incarnation ==
            request.admission.parent_snapshot.episode.world.incarnation ||
        !request.child_snapshot_id.well_formed() ||
        !is_lower_sha256(request.child_snapshot_sha256) ||
        (request.child_episode_control != nullptr &&
         request.child_episode_control->resource_identity() != request.child_resource_identity) ||
        request.census.source_slot != request.admission.parent_snapshot.episode.world.incarnation ||
        (!request.admission.parent_plan_sha256.empty() &&
         request.transfer_profile.source_plan_sha256 != request.admission.parent_plan_sha256)) {
        result.status =
            state_failure(RuntimeStateTransferError::InvalidArgument,
                          "child episode or transfer binding does not match the parent");
        return result;
    }
    if (request.source_owner_registry->bound_resource_identity() !=
            request.source_resource_identity ||
        request.child_owner_registry->bound_resource_identity() !=
            request.child_resource_identity ||
        request.source_owner_registry->owner_binding_token() == nullptr ||
        request.child_owner_registry->owner_binding_token() == nullptr ||
        request.source_owner_registry->owner_binding_token() ==
            request.child_owner_registry->owner_binding_token()) {
        result.status =
            state_failure(RuntimeStateTransferError::SemanticEvidenceMissing,
                          "branch owner registries are not independently resource-bound");
        return result;
    }
    if (request.evidence.production_authorized) {
        result.status = state_failure(RuntimeStateTransferError::ProductionAuthorityForbidden,
                                      "native sibling branch remains dark/shadow only");
        return result;
    }

    auto barrier = request.parent_coordinator->open_branch_barrier(
        request.admission.parent_snapshot.episode, request.admission.parent_snapshot.step_sequence);
    if (!barrier.status) {
        result.status = barrier.status;
        return result;
    }
    const RuntimeEpisodeCoordinatorSnapshot barrier_snapshot = barrier.capability.snapshot();
    const auto binding = barrier.capability.bind_for_host(
        request.branch_authority_nonce, barrier_snapshot.episode.world.world_slot);
    if (!binding) {
        (void)request.parent_coordinator->abort_branch_barrier(std::move(barrier.capability));
        result.status = binding;
        return result;
    }

    if (request.derive_census_from_source) {
        if (!request.census.entries.empty()) {
            (void)request.parent_coordinator->abort_branch_barrier(std::move(barrier.capability));
            result.status = state_failure(
                RuntimeStateTransferError::InvalidArgument,
                "source-derived branch census cannot be combined with caller entries");
            return result;
        }
        const auto source_export = request.source_owner_registry->export_source(
            request.transfer_profile, request.census.source_slot,
            RuntimeStateOwnerExportContext{.barrier_snapshot = barrier_snapshot,
                                           .source_read_only_result_leases = 0,
                                           .cooperative_cancellation_acknowledged = true});
        if (!source_export.status) {
            (void)request.parent_coordinator->abort_branch_barrier(std::move(barrier.capability));
            result.status = source_export.status;
            return result;
        }
        request.census = source_export.census;
    }

    auto child_created = RuntimeEpisodeCoordinatorCandidate::create({
        .initial_episode = request.child_episode,
        .initial_phase = RuntimeEpisodePhase::Running,
        .initial_snapshot_id = request.child_snapshot_id,
        .initial_snapshot_sha256 = request.child_snapshot_sha256,
        .initial_step_sequence = barrier_snapshot.step_sequence,
        .initial_barrier_sequence = barrier_snapshot.barrier_sequence,
        .production_authorized = false,
    });
    if (!child_created.status || child_created.coordinator == nullptr) {
        (void)request.parent_coordinator->abort_branch_barrier(std::move(barrier.capability));
        result.status = child_created.status
                            ? state_failure(RuntimeStateTransferError::InvalidArgument,
                                            "child coordinator allocation failed")
                            : child_created.status;
        return result;
    }
    auto child_coordinator = std::move(child_created.coordinator);

    const auto parent_coordinator = request.parent_coordinator;
    const std::string source_plan = request.transfer_profile.source_plan_sha256;
    const std::string target_plan = request.transfer_profile.target_plan_sha256;
    auto host_quiescence = RuntimeHostQuiescenceCapability::mint_for_branch(
        barrier_snapshot.episode.world.incarnation, source_plan, target_plan,
        request.source_resource_identity, request.child_resource_identity,
        request.source_owner_registry, request.child_owner_registry, request.branch_authority_nonce,
        [parent_coordinator, barrier_snapshot]() noexcept {
            const auto current = parent_coordinator->snapshot();
            return current.phase == RuntimeEpisodePhase::BranchBarrier &&
                   current.episode == barrier_snapshot.episode &&
                   current.step_sequence == barrier_snapshot.step_sequence &&
                   current.barrier_sequence == barrier_snapshot.barrier_sequence;
        },
        []() noexcept {}, std::move(request.begin_child_state_transfer),
        []() noexcept { return true; }, std::move(request.end_child_state_transfer),
        request.lifecycle_ticket, request.candidate_sequence,
        request.evidence.source_final_mutation_fence_sequence, 0, true);

    RuntimeStateTransferValidationRequest validation{
        .profile = std::move(request.transfer_profile),
        .census = std::move(request.census),
        .evidence = request.evidence,
        .host_quiescence = std::move(host_quiescence),
        .episode_barrier = std::move(barrier.capability),
    };
    auto validated = RuntimeStateTransferValidator::validate(std::move(validation));
    if (!validated.status) {
        result.status = validated.status;
        return result;
    }
    auto transfer = std::move(validated.transfer);
    const auto prepared = transfer.prepare_for_host(
        barrier_snapshot.episode.world.incarnation, source_plan, target_plan,
        request.child_resource_identity, request.lifecycle_ticket, request.candidate_sequence,
        request.evidence.source_final_mutation_fence_sequence);
    if (!prepared) {
        result.status = prepared;
        return result;
    }
    const auto committed = transfer.commit_for_host();
    if (!committed) {
        result.status = committed;
        return result;
    }
    transfer.release_host_transfer_fence();

    result.parent_snapshot = request.parent_coordinator->snapshot();
    result.child_snapshot = child_coordinator->snapshot();
    result.state_bundle_sha256 = std::string(transfer.state_bundle_sha256());
    result.branch = {
        .branch_id = request.admission.branch_id,
        .parent_snapshot_id = request.admission.parent_snapshot.snapshot_id,
        .child_resource_id = request.child_resource_identity,
        .parent_episode = request.admission.parent_snapshot.episode,
        .parent_step_sequence = request.admission.parent_snapshot.step_sequence,
        .depth = 1,
        .parent_snapshot_sha256 = request.admission.parent_snapshot.snapshot_sha256,
        .intervention_sha256 = request.admission.intervention_sha256,
    };
    RuntimeBranchForkProof proof{
        .branch = result.branch,
        .parent_barrier_sealed = result.parent_snapshot.phase == RuntimeEpisodePhase::Running,
        .state_scope_complete = !result.state_bundle_sha256.empty(),
        .sibling_isolated = request.source_resource_identity != request.child_resource_identity,
        .external_side_effects_quarantined = true,
        .production_authorized = false,
    };
    result.branch_status = validate_runtime_branch_fork_proof(proof);
    if (!result.branch_status) {
        result.status = transfer_failure(result.branch_status);
        return result;
    }
    result.child_coordinator = std::move(child_coordinator);
    result.child_episode_control = std::move(request.child_episode_control);
    result.status = {};
    return result;
}

} // namespace runtime::host
