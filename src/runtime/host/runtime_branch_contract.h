#pragma once

#include "runtime_state_transfer_candidate.h"

#include <cstdint>
#include <functional>
#include <memory>
#include <string>

namespace runtime::host {

// This contract describes a sibling branch admission. It deliberately does
// not contain a state payload: the native state-transfer owner remains the
// only authority for export/import bytes.
enum class RuntimeBranchError : std::uint8_t {
    None,
    InvalidParentSnapshot,
    InvalidBranchIdentity,
    InvalidInterventionDigest,
    InvalidHorizon,
    ParentNotRunning,
    ParentImmutabilityRequired,
    ProductionForbidden,
    IncompleteIsolationProof,
};

struct RuntimeBranchStatus {
    RuntimeBranchError error = RuntimeBranchError::None;
    std::string detail;

    [[nodiscard]] explicit operator bool() const noexcept {
        return error == RuntimeBranchError::None;
    }
};

struct RuntimeBranchForkRequest {
    RuntimeEpisodeCoordinatorSnapshot parent_snapshot;
    RuntimeIdentity128 branch_id;
    std::string parent_plan_sha256;
    std::string intervention_sha256;
    std::uint64_t horizon = 0;
    bool require_parent_immutable = true;
    bool production_authorized = false;
};

struct RuntimeBranchRef {
    RuntimeIdentity128 branch_id;
    RuntimeIdentity128 parent_snapshot_id;
    RuntimeIdentity128 child_resource_id;
    RuntimeEpisodeRef parent_episode;
    std::uint64_t parent_step_sequence = 0;
    std::uint64_t depth = 0;
    std::string parent_snapshot_sha256;
    std::string intervention_sha256;

    [[nodiscard]] bool well_formed() const noexcept;
};

struct RuntimeBranchForkProof {
    RuntimeBranchRef branch;
    bool parent_barrier_sealed = false;
    bool state_scope_complete = false;
    bool sibling_isolated = false;
    bool external_side_effects_quarantined = false;
    bool production_authorized = false;
};

// The native sibling executor is intentionally a host-neutral seam.  It uses
// the parent coordinator's branch barrier and the same twelve owner adapters
// as replacement transfer, but it never publishes the child through a host
// slot.  A caller must provide a distinct, owner-bound child registry and a
// fresh child episode identity; omission or aliasing fails closed.
struct RuntimeNativeSiblingBranchRequest {
    RuntimeBranchForkRequest admission;
    RuntimeEpisodeCoordinatorCandidate *parent_coordinator = nullptr;
    RuntimeStateTransferProfile transfer_profile;
    RuntimeStateCensus census;
    // A native caller may provide only the census binding shell and ask the
    // source owner to fill the twelve exact entries after the branch barrier
    // is open. Hand-authored entries remain accepted only when this is false.
    bool derive_census_from_source = false;
    RuntimeStateTransferEvidence evidence;
    std::shared_ptr<RuntimeStateTransferOwnerRegistry> source_owner_registry;
    std::shared_ptr<RuntimeStateTransferOwnerRegistry> child_owner_registry;
    RuntimeIdentity128 source_resource_identity;
    RuntimeIdentity128 child_resource_identity;
    RuntimeIdentity128 branch_authority_nonce;
    RuntimeEpisodeRef child_episode;
    RuntimeIdentity128 child_snapshot_id;
    std::string child_snapshot_sha256;
    // Optional native episode control lets a caller continue the admitted
    // child through the same coordinator receipt path. When supplied, its
    // resource identity must match child_resource_identity; an absent control
    // leaves the branch creation-only and never fabricates child stepping.
    std::shared_ptr<RuntimeNativeEpisodeControl> child_episode_control;
    // The child owner must expose a real exclusivity fence. A missing fence
    // is rejected instead of being treated as a no-op transfer hook.
    std::function<bool()> begin_child_state_transfer;
    std::function<void()> end_child_state_transfer;
    std::uint64_t lifecycle_ticket = 1;
    std::uint64_t candidate_sequence = 1;
};

struct RuntimeNativeSiblingBranchResult {
    RuntimeStateTransferStatus status;
    RuntimeBranchStatus branch_status;
    RuntimeBranchRef branch;
    RuntimeEpisodeCoordinatorSnapshot parent_snapshot;
    RuntimeEpisodeCoordinatorSnapshot child_snapshot;
    std::unique_ptr<RuntimeEpisodeCoordinatorCandidate> child_coordinator;
    std::shared_ptr<RuntimeNativeEpisodeControl> child_episode_control;
    std::string state_bundle_sha256;
};

class RuntimeNativeSiblingBranchExecutor final {
  public:
    [[nodiscard]] static RuntimeNativeSiblingBranchResult
    execute(RuntimeNativeSiblingBranchRequest request);
};

[[nodiscard]] RuntimeBranchStatus
validate_runtime_branch_fork_request(const RuntimeBranchForkRequest &request) noexcept;

[[nodiscard]] RuntimeBranchStatus
validate_runtime_branch_fork_proof(const RuntimeBranchForkProof &proof) noexcept;

} // namespace runtime::host
