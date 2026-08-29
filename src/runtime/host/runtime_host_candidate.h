#pragma once

#include <echelon_forge/runtime_contracts/runtime_identity.h>

#include "runtime_state_transfer_candidate.h"

#include <cstddef>
#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace runtime::host {

using echelon_forge::runtime_contracts::v1::RuntimeEpisodeRef;
using echelon_forge::runtime_contracts::v1::RuntimeHostIdentity;
using echelon_forge::runtime_contracts::v1::RuntimeIdentity128;
using echelon_forge::runtime_contracts::v1::RuntimeIncarnationRef;
using echelon_forge::runtime_contracts::v1::RuntimeRequestRef;
using echelon_forge::runtime_contracts::v1::RuntimeResultRef;

// P4-A deliberately has no production mode. Production publication remains a
// P5-D decision and cannot be enabled by a runtime flag on this candidate.
enum class RuntimeHostMode : std::uint8_t {
    Dark,
    Shadow,
};

enum class RuntimeHostState : std::uint8_t {
    Absent,
    Active,
    Faulted,
    ShuttingDown,
    Stopped,
    FailStopped,
};

enum class RuntimeSlotState : std::uint8_t {
    Constructing,
    Validating,
    Ready,
    InitialCommitReady,
    Quiescing,
    TransferCommitReady,
    RecoveryQuiesced,
    RecoveryCommitReady,
    Publishing,
    Active,
    ActiveFaulted,
    ShuttingDown,
    Draining,
    Reclaiming,
    Quarantined,
    CandidateFailed,
    Retired,
};

enum class RuntimeHostTransactionKind : std::uint8_t {
    Initial,
    Replacement,
    CheckpointRecovery,
};

enum class RuntimeLeaseKind : std::uint8_t {
    TruthMutating,
    ReadOnlyResult,
};

enum class RuntimeSlotCasOperation : std::uint8_t {
    InitialPublish,
    ReplacementPublish,
    RecoveryPublish,
    ShutdownUnpublish,
    QuiesceTimeoutUnpublish,
    FaultTimeoutUnpublish,
};

enum class RuntimeHostError : std::uint8_t {
    None,
    InvalidArgument,
    ProductionAuthorityForbidden,
    HostTerminal,
    HostStateMismatch,
    CandidateBusy,
    CandidateNotFound,
    InvalidCandidateState,
    StaleExpectedSlot,
    DrainBackpressure,
    QuarantineBackpressure,
    TruthLeasesOutstanding,
    InvalidCommitProof,
    PublicationRaceLost,
    AdmissionClosed,
    StaleReference,
    ResultMismatch,
    DuplicateResult,
    ResourceReleaseFailed,
    CancellationPending,
    LeaseCountExhausted,
    LifecycleDeadlineExpired,
    EpochExhausted,
    TicketExhausted,
    RequestSequenceExhausted,
    ShutdownPending,
    QuarantineUnresolved,
};

struct RuntimeHostStatus {
    RuntimeHostError error = RuntimeHostError::None;
    std::string detail;

    [[nodiscard]] explicit operator bool() const noexcept {
        return error == RuntimeHostError::None;
    }
};

struct RuntimePlanBinding {
    std::string plan_id;
    std::string plan_sha256;

    [[nodiscard]] bool well_formed() const noexcept;
    bool operator==(const RuntimePlanBinding &) const = default;
};

// The host owns the control object until resources are explicitly released.
// Hooks are called outside the host mutex. They must be noexcept; cancellation
// reports an acknowledgement so publication cannot overtake a blocked hook.
class RuntimeInstanceControl {
  public:
    virtual ~RuntimeInstanceControl() = default;
    [[nodiscard]] virtual RuntimeIdentity128 resource_identity() const noexcept = 0;
    // The native episode adapter is acquired with the instance owner and kept
    // by the host slot. Callers never supply a control object to a submission.
    [[nodiscard]] virtual std::shared_ptr<RuntimeNativeEpisodeControl>
    native_episode_control() const noexcept = 0;
    [[nodiscard]] virtual std::shared_ptr<RuntimeStateTransferOwnerRegistry>
    state_transfer_owner_registry() const noexcept = 0;
    [[nodiscard]] virtual bool request_cooperative_cancel() noexcept = 0;
    [[nodiscard]] virtual bool release_resources() noexcept = 0;
    [[nodiscard]] virtual bool resources_released() const noexcept = 0;
};

class RuntimeHostCasFaultInjector {
  public:
    virtual ~RuntimeHostCasFaultInjector() = default;
    [[nodiscard]] virtual bool force_loss(RuntimeSlotCasOperation operation) noexcept = 0;
};

struct RuntimeHostConfig {
    // The host owns boot identity minting. Callers may choose a stable logical
    // host ID, but cannot replay a previous process boot ID.
    RuntimeIdentity128 host_id;
    RuntimeHostMode mode = RuntimeHostMode::Dark;
    // Internal dark/shadow model-testing seam. The target is not installed or
    // exposed to production consumers.
    std::shared_ptr<RuntimeHostCasFaultInjector> cas_fault_injector;
};

struct RuntimeCandidateHandle {
    RuntimeHostIdentity host;
    RuntimeIdentity128 host_instance_nonce;
    std::uint64_t lifecycle_ticket = 0;
    std::uint64_t candidate_sequence = 0;
    RuntimeHostTransactionKind transaction_kind = RuntimeHostTransactionKind::Initial;

    [[nodiscard]] bool well_formed() const noexcept {
        return host.well_formed() && host_instance_nonce.well_formed() &&
               lifecycle_ticket != 0 && candidate_sequence != 0;
    }
    bool operator==(const RuntimeCandidateHandle &) const = default;
};

struct RuntimeCandidateRequest {
    RuntimeHostTransactionKind transaction_kind = RuntimeHostTransactionKind::Initial;
    std::optional<RuntimeIncarnationRef> expected_slot;
    RuntimePlanBinding plan;
    std::shared_ptr<RuntimeInstanceControl> control;
    std::uint64_t lifecycle_deadline_tick = 0;
    // Immutable world-slot cardinality for the candidate instance. Zero means
    // inherit the active slot cardinality during replacement/recovery; an
    // initial publication with zero admits no shadow world capability.
    std::uint64_t world_slot_count = 1;
};

class RuntimeShadowEpisodeCapability {
  public:
    RuntimeShadowEpisodeCapability() = default;
    [[nodiscard]] bool valid() const noexcept;
    [[nodiscard]] RuntimeEpisodeRef episode() const noexcept;
    [[nodiscard]] RuntimeIdentity128 resource_identity() const noexcept;

  private:
    friend class RuntimeHostCandidate;
    RuntimeHostIdentity host_;
    RuntimeIdentity128 host_instance_nonce_;
    RuntimeIdentity128 resource_identity_;
    RuntimeEpisodeRef episode_;
    std::uint64_t capability_sequence_ = 0;
};

struct RuntimeShadowEpisodeAdmission {
    RuntimeHostStatus status;
    RuntimeShadowEpisodeCapability capability;
};

struct RuntimeCandidateValidationProof {
    bool static_plan_validated = false;
    bool resources_ready = false;
    bool shadow_probe_passed = false;
    bool unreachable_from_production = false;
    bool production_authorized = false;
};

struct RuntimeInitialCommitProof {
    std::string lifecycle_evidence_sha256;
    bool dark_evidence_sealed = false;
    bool production_authorized = false;
};

struct RuntimeTransferCommitProof {
    RuntimeValidatedStateTransfer validated_transfer;
    bool production_authorized = false;
    std::uint64_t drain_deadline_tick = 0;
};

struct RuntimeReplacementQuiescenceResult {
    RuntimeHostStatus status;
    RuntimeHostQuiescenceCapability capability;
};

struct RuntimeRecoveryCommitProof {
    RuntimeIncarnationRef source_faulted_slot;
    std::string checkpoint_id;
    std::string checkpoint_sha256;
    bool checkpoint_admitted = false;
    bool source_truth_exported = false;
    bool candidate_import_probe_passed = false;
    bool production_authorized = false;
    std::uint64_t drain_deadline_tick = 0;
};

struct RuntimeCandidateBeginResult {
    RuntimeHostStatus status;
    RuntimeCandidateHandle handle;
};

struct RuntimePublicationResult {
    RuntimeHostStatus status;
    RuntimeIncarnationRef published_slot;
    std::uint64_t publication_ticket = 0;
};

struct RuntimeSlotSnapshot {
    std::uint64_t candidate_sequence = 0;
    RuntimeSlotState state = RuntimeSlotState::Constructing;
    RuntimePlanBinding plan;
    RuntimeIncarnationRef incarnation;
    bool admission_open = false;
    bool result_publication_open = false;
    std::size_t truth_mutating_leases = 0;
    std::size_t read_only_result_leases = 0;
    std::uint64_t final_transfer_fence_sequence = 0;
    std::uint64_t drain_deadline_tick = 0;
    bool resources_released = false;
};

struct RuntimeHostSnapshot {
    RuntimeHostIdentity identity;
    RuntimeHostMode mode = RuntimeHostMode::Dark;
    RuntimeHostState state = RuntimeHostState::Absent;
    RuntimeIdentity128 host_instance_nonce;
    bool production_authorized = false;
    std::uint64_t last_lifecycle_ticket = 0;
    std::uint64_t last_request_sequence = 0;
    std::uint64_t shutdown_ticket = 0;
    std::uint64_t last_publication_ticket = 0;
    std::optional<RuntimeSlotSnapshot> active;
    std::optional<RuntimeSlotSnapshot> candidate;
    std::optional<RuntimeSlotSnapshot> draining;
    std::vector<RuntimeSlotSnapshot> quarantined;
    std::optional<RuntimeSlotSnapshot> shutdown_pending;
    std::uint64_t retired_incarnation_high_watermark = 0;
};

struct RuntimeShutdownResult {
    RuntimeHostStatus status;
    std::uint64_t shutdown_ticket = 0;
    RuntimeHostState state = RuntimeHostState::Absent;
    std::uint64_t publication_ticket = 0;
};

struct RuntimeHostSharedState;
struct RuntimeLeaseToken;

class RuntimeInstanceLease {
  public:
    RuntimeInstanceLease() = default;
    RuntimeInstanceLease(RuntimeInstanceLease &&) noexcept;
    RuntimeInstanceLease &operator=(RuntimeInstanceLease &&) noexcept;
    RuntimeInstanceLease(const RuntimeInstanceLease &) = delete;
    RuntimeInstanceLease &operator=(const RuntimeInstanceLease &) = delete;
    ~RuntimeInstanceLease();

    [[nodiscard]] bool valid() const noexcept;
    [[nodiscard]] RuntimeLeaseKind kind() const noexcept;
    [[nodiscard]] RuntimeRequestRef request_ref() const noexcept;
    void settle() noexcept;

  private:
    friend class RuntimeHostCandidate;
    explicit RuntimeInstanceLease(std::shared_ptr<RuntimeLeaseToken> token) noexcept;
    std::shared_ptr<RuntimeLeaseToken> token_;
};

struct RuntimeLeaseAdmission {
    RuntimeHostStatus status;
    RuntimeInstanceLease lease;
    RuntimeRequestRef request_ref;
};

class RuntimeHostCandidate {
  public:
    explicit RuntimeHostCandidate(RuntimeHostConfig config);
    RuntimeHostCandidate(const RuntimeHostCandidate &) = delete;
    RuntimeHostCandidate &operator=(const RuntimeHostCandidate &) = delete;
    RuntimeHostCandidate(RuntimeHostCandidate &&) noexcept;
    RuntimeHostCandidate &operator=(RuntimeHostCandidate &&) noexcept;
    ~RuntimeHostCandidate();

    [[nodiscard]] RuntimeCandidateBeginResult
    begin_candidate(const RuntimeCandidateRequest &request);
    [[nodiscard]] RuntimeHostStatus
    validate_candidate(const RuntimeCandidateHandle &handle,
                       const RuntimeCandidateValidationProof &proof);
    [[nodiscard]] RuntimePublicationResult
    commit_initial(const RuntimeCandidateHandle &handle,
                   const RuntimeInitialCommitProof &proof);
    [[nodiscard]] RuntimeHostStatus
    prepare_replacement(const RuntimeCandidateHandle &handle,
                        RuntimeTransferCommitProof &&proof);
    [[nodiscard]] RuntimeReplacementQuiescenceResult
    quiesce_replacement_source(const RuntimeCandidateHandle &handle);
    [[nodiscard]] RuntimeHostStatus
    prepare_checkpoint_recovery(const RuntimeCandidateHandle &handle,
                                const RuntimeRecoveryCommitProof &proof);
    [[nodiscard]] RuntimePublicationResult
    commit_prepared_candidate(const RuntimeCandidateHandle &handle);
    [[nodiscard]] RuntimeHostStatus abort_candidate(const RuntimeCandidateHandle &handle);

    [[nodiscard]] RuntimeHostStatus
    mark_active_faulted(const RuntimeIncarnationRef &expected_slot,
                        std::uint64_t fault_deadline_tick = 0);
    [[nodiscard]] RuntimeShadowEpisodeAdmission
    admit_shadow_episode(RuntimeNativeEpisodeCapability &&native_episode);
    [[nodiscard]] RuntimeShadowEpisodeAdmission
    issue_shadow_episode(std::uint64_t world_slot);
    [[nodiscard]] RuntimeHostStatus
    release_shadow_episode(const RuntimeShadowEpisodeCapability &capability);
    [[nodiscard]] RuntimeEpisodeTransitionResult
    submit_shadow_episode(const RuntimeShadowEpisodeCapability &episode,
                          const RuntimeEpisodeTransitionIntent &intent);
    [[nodiscard]] RuntimeEpisodeBarrierAdmission
    open_shadow_replacement_barrier(const RuntimeEpisodeRef &expected_episode,
                                    std::uint64_t expected_step_sequence);
    [[nodiscard]] RuntimeEpisodeBarrierAdmission
    open_shadow_replacement_barrier(std::uint64_t world_slot);
    [[nodiscard]] RuntimeLeaseAdmission acquire_lease(
                                                      const RuntimeShadowEpisodeCapability &episode,
                                                      RuntimeLeaseKind kind);
    [[nodiscard]] RuntimeHostStatus
    validate_result(const RuntimeInstanceLease &lease, const RuntimeResultRef &result) const;

    [[nodiscard]] RuntimeShutdownResult begin_shutdown(std::uint64_t now_tick,
                                                       std::uint64_t deadline_tick);
    [[nodiscard]] RuntimeHostStatus poll(std::uint64_t now_tick);
    [[nodiscard]] RuntimeHostStatus retry_quarantined_reclamation();
    [[nodiscard]] RuntimeHostSnapshot snapshot() const;

    [[nodiscard]] static std::size_t orphaned_host_count() noexcept;
    [[nodiscard]] static RuntimeHostStatus retry_orphaned_reclamation();

  private:
    std::shared_ptr<RuntimeHostSharedState> state_;
};

} // namespace runtime::host
