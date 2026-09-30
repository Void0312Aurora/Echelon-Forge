#pragma once

#include <echelon_forge/runtime_contracts/runtime_identity.h>

#include <cstddef>
#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace runtime::host {

using echelon_forge::runtime_contracts::v1::RuntimeEpisodeRef;
using echelon_forge::runtime_contracts::v1::RuntimeIdentity128;
using echelon_forge::runtime_contracts::v1::RuntimeIncarnationRef;
using echelon_forge::runtime_contracts::v1::RuntimeWorldRef;

inline constexpr std::uint32_t kRuntimeEpisodeHandshakeGeneration = 1;
// The current schema is N=2.  Readers deliberately accept N and N-1 so a
// rolling replacement can bridge one producer generation without silently
// accepting an arbitrarily old state bundle.
inline constexpr std::uint32_t kRuntimeStateTransferContractGeneration = 2;
inline constexpr std::uint32_t kRuntimeStateTransferPreviousGeneration =
    kRuntimeStateTransferContractGeneration - 1;
inline constexpr std::size_t kRuntimeStateCategoryCount = 12;

enum class RuntimeStateCategory : std::uint8_t {
    CompositionProviderSystemGraph,
    EcsComponentTruth,
    RngState,
    ClockCadence,
    DelayedEventsQueues,
    CommandsLinksPendingIntent,
    EpisodeRewardTermination,
    PythonLoaderControllerCaches,
    BackendDeviceAllocationsLeases,
    InFlightRequestsResults,
    ExternalSideEffects,
    DiagnosticsTelemetry,
};

enum class RuntimeStateDisposition : std::uint8_t {
    Transfer,
    Rederive,
    Cancel,
    Drain,
    Reject,
    NotApplicable,
};

enum class RuntimeEpisodePhase : std::uint8_t {
    Running,
    Terminal,
    ReplacementBarrier,
    TransferCommitted,
    FailStopped,
};

enum class RuntimeEpisodeIntentKind : std::uint8_t {
    Action,
    Reset,
};

enum class RuntimeStateTransferError : std::uint8_t {
    None,
    InvalidArgument,
    ProductionAuthorityForbidden,
    DuplicateCoordinator,
    StaleIntent,
    IdempotencyConflict,
    AdmissionClosed,
    ConcurrentMutation,
    NativeMutationFailed,
    SequenceExhausted,
    ReceiptBudgetExhausted,
    ReceiptResyncRequired,
    ReceiptAcknowledgementInvalid,
    InvalidCensusProfile,
    MissingCategory,
    DuplicateCategory,
    OwnerMismatch,
    DispositionMismatch,
    SchemaMismatch,
    PayloadDigestMismatch,
    UnknownTruthField,
    SemanticEvidenceMissing,
    RawHandleTransferForbidden,
    UnsettledWork,
    ReplacementRejected,
    BarrierRequired,
    BarrierReplay,
    PlanMismatch,
    TransferAlreadyConsumed,
};

struct RuntimeStateTransferStatus {
    RuntimeStateTransferError error = RuntimeStateTransferError::None;
    std::string detail;

    [[nodiscard]] explicit operator bool() const noexcept {
        return error == RuntimeStateTransferError::None;
    }
};

struct RuntimeEpisodeCoordinatorConfig {
    RuntimeEpisodeRef initial_episode;
    RuntimeEpisodePhase initial_phase = RuntimeEpisodePhase::Running;
    RuntimeIdentity128 initial_snapshot_id;
    std::string initial_snapshot_sha256;
    std::uint64_t initial_step_sequence = 0;
    std::uint64_t initial_barrier_sequence = 0;
    bool production_authorized = false;
};

struct RuntimeEpisodeTransitionIntent {
    std::uint32_t protocol_generation = kRuntimeEpisodeHandshakeGeneration;
    RuntimeEpisodeIntentKind kind = RuntimeEpisodeIntentKind::Action;
    RuntimeEpisodeRef expected_episode;
    std::uint64_t expected_step_sequence = 0;
    RuntimeIdentity128 idempotency_key;
    std::string payload_sha256;
    bool production_authorized = false;
};

struct RuntimeNativeEpisodeCommand {
    RuntimeEpisodeTransitionIntent intent;
    RuntimeEpisodeRef authorized_episode_after;
    std::uint64_t authorized_resulting_step_sequence = 0;
};

// The native implementation applies only the coordinator-authored command and
// returns resulting snapshot facts. It cannot author episode identity or step
// sequence; an invalid applied result fail-stops the coordinator.
struct RuntimeNativeEpisodeMutation {
    bool applied = false;
    bool terminal = false;
    RuntimeIdentity128 snapshot_id;
    std::string snapshot_sha256;
};

class RuntimeNativeEpisodeControl {
  public:
    virtual ~RuntimeNativeEpisodeControl() = default;
    // The host checks this identity against the admitted instance resource
    // before allowing a native callback to mutate episode truth.  A production
    // adapter must derive it from the resource handle rather than caller DTOs.
    [[nodiscard]] virtual RuntimeIdentity128 resource_identity() const noexcept = 0;
    [[nodiscard]] virtual RuntimeNativeEpisodeMutation
    apply(const RuntimeNativeEpisodeCommand &command) noexcept = 0;
};

struct RuntimeEpisodeTransitionReceipt {
    std::uint32_t protocol_generation = kRuntimeEpisodeHandshakeGeneration;
    RuntimeEpisodeIntentKind kind = RuntimeEpisodeIntentKind::Action;
    RuntimeIdentity128 idempotency_key;
    RuntimeEpisodeRef episode_before;
    RuntimeEpisodeRef episode_after;
    std::uint64_t previous_step_sequence = 0;
    std::uint64_t resulting_step_sequence = 0;
    RuntimeEpisodePhase resulting_phase = RuntimeEpisodePhase::Running;
    bool terminal = false;
    bool reset_applied = false;
    RuntimeIdentity128 snapshot_id;
    std::string snapshot_sha256;
    std::uint64_t barrier_sequence = 0;
    std::string receipt_sha256;

    [[nodiscard]] bool well_formed() const noexcept;
    bool operator==(const RuntimeEpisodeTransitionReceipt &) const = default;
};

struct RuntimeEpisodeTransitionResult {
    RuntimeStateTransferStatus status;
    RuntimeEpisodeTransitionReceipt receipt;
    bool replayed = false;
};

struct RuntimeEpisodeCoordinatorSnapshot {
    RuntimeEpisodeRef episode;
    RuntimeEpisodePhase phase = RuntimeEpisodePhase::Running;
    std::uint64_t step_sequence = 0;
    std::uint64_t barrier_sequence = 0;
    RuntimeIdentity128 snapshot_id;
    std::string snapshot_sha256;
};

struct RuntimeEpisodeCoordinatorState;
struct RuntimeEpisodeBarrierToken;
struct RuntimeNativeEpisodeToken;
class RuntimeHostCandidate;

class RuntimeNativeEpisodeCapability {
  public:
    RuntimeNativeEpisodeCapability() = default;
    RuntimeNativeEpisodeCapability(RuntimeNativeEpisodeCapability &&) noexcept;
    RuntimeNativeEpisodeCapability &operator=(RuntimeNativeEpisodeCapability &&) noexcept;
    RuntimeNativeEpisodeCapability(const RuntimeNativeEpisodeCapability &) = delete;
    RuntimeNativeEpisodeCapability &operator=(const RuntimeNativeEpisodeCapability &) = delete;
    ~RuntimeNativeEpisodeCapability() = default;

    [[nodiscard]] bool valid() const noexcept;
    [[nodiscard]] RuntimeEpisodeRef episode() const noexcept;
    [[nodiscard]] std::uint64_t step_sequence() const noexcept;
    [[nodiscard]] RuntimeIdentity128 coordinator_nonce() const noexcept;

  private:
    friend class RuntimeEpisodeCoordinatorCandidate;
    friend class RuntimeHostCandidate;
    explicit RuntimeNativeEpisodeCapability(
        std::shared_ptr<RuntimeNativeEpisodeToken> token) noexcept;
    [[nodiscard]] RuntimeStateTransferStatus
    consume_for_host(const RuntimeIncarnationRef &expected_source);
    [[nodiscard]] RuntimeStateTransferStatus
    validate_for_host(const RuntimeIncarnationRef &expected_source) const;
    std::shared_ptr<RuntimeNativeEpisodeToken> token_;
};

struct RuntimeNativeEpisodeAdmission {
    RuntimeStateTransferStatus status;
    RuntimeNativeEpisodeCapability capability;
};

class RuntimeEpisodeBarrierCapability {
  public:
    RuntimeEpisodeBarrierCapability() = default;
    RuntimeEpisodeBarrierCapability(RuntimeEpisodeBarrierCapability &&) noexcept;
    RuntimeEpisodeBarrierCapability &operator=(RuntimeEpisodeBarrierCapability &&) noexcept;
    RuntimeEpisodeBarrierCapability(const RuntimeEpisodeBarrierCapability &) = delete;
    RuntimeEpisodeBarrierCapability &operator=(const RuntimeEpisodeBarrierCapability &) = delete;
    ~RuntimeEpisodeBarrierCapability();

    [[nodiscard]] bool valid() const noexcept;
    [[nodiscard]] RuntimeEpisodeCoordinatorSnapshot snapshot() const noexcept;
    [[nodiscard]] RuntimeIdentity128 coordinator_nonce() const noexcept;

  private:
    friend class RuntimeEpisodeCoordinatorCandidate;
    friend class RuntimeHostCandidate;
    friend class RuntimeStateTransferValidator;
    explicit RuntimeEpisodeBarrierCapability(
        std::shared_ptr<RuntimeEpisodeBarrierToken> token) noexcept;
    [[nodiscard]] RuntimeStateTransferStatus
    bind_for_host(const RuntimeIdentity128 &host_instance_nonce, std::uint64_t world_slot) noexcept;
    std::shared_ptr<RuntimeEpisodeBarrierToken> token_;
};

struct RuntimeEpisodeBarrierAdmission {
    RuntimeStateTransferStatus status;
    RuntimeEpisodeBarrierCapability capability;
};

struct RuntimeEpisodeCoordinatorCreateResult;

class RuntimeEpisodeCoordinatorCandidate {
  public:
    [[nodiscard]] static RuntimeEpisodeCoordinatorCreateResult
    create(const RuntimeEpisodeCoordinatorConfig &config);

    RuntimeEpisodeCoordinatorCandidate(const RuntimeEpisodeCoordinatorCandidate &) = delete;
    RuntimeEpisodeCoordinatorCandidate &
    operator=(const RuntimeEpisodeCoordinatorCandidate &) = delete;
    RuntimeEpisodeCoordinatorCandidate(RuntimeEpisodeCoordinatorCandidate &&) noexcept = default;
    RuntimeEpisodeCoordinatorCandidate &
    operator=(RuntimeEpisodeCoordinatorCandidate &&) noexcept = default;
    ~RuntimeEpisodeCoordinatorCandidate();

    [[nodiscard]] RuntimeEpisodeTransitionResult
    submit(const RuntimeEpisodeTransitionIntent &intent, RuntimeNativeEpisodeControl &control);
    [[nodiscard]] RuntimeStateTransferStatus
    acknowledge_receipt(const RuntimeEpisodeTransitionReceipt &receipt);
    [[nodiscard]] RuntimeEpisodeBarrierAdmission
    open_replacement_barrier(const RuntimeEpisodeRef &expected_episode,
                             std::uint64_t expected_step_sequence);
    [[nodiscard]] RuntimeNativeEpisodeAdmission issue_episode_capability();
    [[nodiscard]] RuntimeIdentity128 coordinator_nonce() const noexcept;
    [[nodiscard]] RuntimeStateTransferStatus
    abort_replacement_barrier(RuntimeEpisodeBarrierCapability &&capability);
    [[nodiscard]] RuntimeEpisodeCoordinatorSnapshot snapshot() const;

  private:
    explicit RuntimeEpisodeCoordinatorCandidate(
        std::shared_ptr<RuntimeEpisodeCoordinatorState> state) noexcept;
    std::shared_ptr<RuntimeEpisodeCoordinatorState> state_;
};

struct RuntimeEpisodeCoordinatorCreateResult {
    RuntimeStateTransferStatus status;
    std::unique_ptr<RuntimeEpisodeCoordinatorCandidate> coordinator;
};

struct RuntimeStateCensusRowPolicy {
    RuntimeStateCategory category = RuntimeStateCategory::CompositionProviderSystemGraph;
    RuntimeStateDisposition disposition = RuntimeStateDisposition::Reject;
    std::string owner_id;
    std::string schema_id;
    std::uint32_t minimum_schema_generation = 0;
    std::uint32_t maximum_schema_generation = 0;
    bool truth_affecting = false;
};

struct RuntimeStateTransferProfile {
    std::string profile_id;
    std::uint32_t profile_generation = 0;
    std::string source_plan_sha256;
    std::string target_plan_sha256;
    std::vector<RuntimeStateCensusRowPolicy> rows;
};

struct RuntimeStateCensusEntry {
    RuntimeStateCategory category = RuntimeStateCategory::CompositionProviderSystemGraph;
    RuntimeStateDisposition disposition = RuntimeStateDisposition::Reject;
    std::string owner_id;
    std::string schema_id;
    std::uint32_t schema_generation = 0;
    std::vector<std::uint8_t> canonical_payload;
    std::string canonical_payload_sha256;
    // Digest of the owner-decoded category state.  The canonical payload is a
    // fixed envelope over this digest and the typed counters below; category
    // owners must separately prove they decoded the exact schema bytes.
    std::string state_content_sha256;
    std::string semantic_evidence_sha256;
    bool contains_unknown_truth_fields = false;
    bool replay_idempotent = false;
    std::uint64_t item_count = 0;
    std::uint64_t settled_item_count = 0;
    std::uint64_t sequence_high_watermark = 0;
    std::uint64_t rng_draw_position = 0;
    std::uint64_t simulation_tick = 0;
    std::uint64_t step_sequence = 0;
    std::uint64_t barrier_sequence = 0;
};

struct RuntimeStateCensus {
    std::uint32_t contract_generation = kRuntimeStateTransferContractGeneration;
    std::string profile_id;
    std::uint32_t profile_generation = 0;
    RuntimeIncarnationRef source_slot;
    std::string source_plan_sha256;
    std::string target_plan_sha256;
    std::vector<RuntimeStateCensusEntry> entries;
};

struct RuntimeStateTransferEvidence {
    std::uint64_t source_final_mutation_fence_sequence = 0;
    bool production_authorized = false;
};

struct RuntimeStateOwnerObservation {
    RuntimeStateCategory category = RuntimeStateCategory::CompositionProviderSystemGraph;
    std::string owner_id;
    std::string schema_id;
    std::uint32_t schema_generation = 0;
    std::string source_entry_sha256;
    std::string candidate_entry_sha256;
    std::string source_artifact_payload_sha256;
    std::string candidate_artifact_payload_sha256;
    std::string semantic_replay_sha256;
    RuntimeIdentity128 candidate_resource_identity;
    std::uint64_t item_count = 0;
    std::uint64_t settled_item_count = 0;
    std::uint32_t source_schema_generation = 0;
    bool exact_schema_decoded = false;
    bool contains_unknown_truth_fields = false;
    bool contains_raw_process_handle = false;
};

class RuntimeStateOwnerImportTransaction {
  public:
    virtual ~RuntimeStateOwnerImportTransaction() = default;
    // The owner must make the candidate import durable only on commit and must
    // discard every provisional mutation on abort.  Both hooks are noexcept so
    // lifecycle cleanup can fail closed without unwinding through host code.
    virtual void commit() noexcept = 0;
    virtual void abort() noexcept = 0;
};

struct RuntimeStateOwnerImportReceipt {
    RuntimeStateTransferStatus status;
    RuntimeIdentity128 candidate_resource_identity;
    std::vector<RuntimeStateOwnerObservation> observations;
    std::shared_ptr<RuntimeStateOwnerImportTransaction> transaction;
};

// Typed owner bytes are carried separately from the census envelope.  The
// source owner is responsible for producing these exact schema bytes; the
// target owner receives the package and must decode the same bytes before it
// can return an import observation.
struct RuntimeStateOwnerArtifact {
    RuntimeStateCategory category = RuntimeStateCategory::CompositionProviderSystemGraph;
    std::string schema_id;
    std::uint32_t schema_generation = 0;
    std::vector<std::uint8_t> payload;
    std::string payload_sha256;
};

// A source export is produced by the resource owner itself.  It is kept
// separate from the caller-provided request census so the validator can reject
// a self-consistent DTO that was never read from the quiesced source.
struct RuntimeStateOwnerExport {
    RuntimeStateTransferStatus status;
    RuntimeIncarnationRef source_slot;
    RuntimeStateCensus census;
    std::vector<RuntimeStateOwnerArtifact> artifacts;
};

// P4-B requires a typed owner/import adapter.  The validator never accepts
// caller-authored aggregate hashes as evidence: it asks this registry to decode
// each exact schema from the quiesced source, import it into the bound candidate
// resource, and report both observed digests plus replay evidence.
class RuntimeStateTransferOwnerRegistry {
  public:
    virtual ~RuntimeStateTransferOwnerRegistry() = default;
    [[nodiscard]] virtual RuntimeStateOwnerExport
    export_source(const RuntimeStateTransferProfile &profile,
                  const RuntimeIncarnationRef &source_slot,
                  const RuntimeEpisodeCoordinatorSnapshot &barrier_snapshot) noexcept = 0;
    [[nodiscard]] virtual RuntimeStateOwnerImportReceipt
    import_and_observe(const RuntimeStateTransferProfile &profile,
                       const RuntimeStateOwnerExport &source_export,
                       const RuntimeIdentity128 &candidate_resource_identity) noexcept = 0;
};

struct RuntimeHostQuiescenceToken;

// Minted only by RuntimeHostCandidate after admission is closed, cancellation
// is acknowledged, and every truth-mutating lease has settled.  It binds a
// state export to one candidate transaction and one non-reusable host mutation
// fence; callers cannot synthesize the ordering proof from DTO fields.
class RuntimeHostQuiescenceCapability {
  public:
    RuntimeHostQuiescenceCapability() = default;
    RuntimeHostQuiescenceCapability(RuntimeHostQuiescenceCapability &&) noexcept;
    RuntimeHostQuiescenceCapability &operator=(RuntimeHostQuiescenceCapability &&) noexcept;
    RuntimeHostQuiescenceCapability(const RuntimeHostQuiescenceCapability &) = delete;
    RuntimeHostQuiescenceCapability &operator=(const RuntimeHostQuiescenceCapability &) = delete;
    ~RuntimeHostQuiescenceCapability();

    [[nodiscard]] bool valid() const noexcept;
    [[nodiscard]] RuntimeIncarnationRef source_slot() const noexcept;
    [[nodiscard]] std::uint64_t mutation_fence_sequence() const noexcept;
    [[nodiscard]] RuntimeIdentity128 candidate_resource_identity() const noexcept;

  private:
    friend class RuntimeHostCandidate;
    friend class RuntimeStateTransferValidator;
    explicit RuntimeHostQuiescenceCapability(
        std::shared_ptr<RuntimeHostQuiescenceToken> token) noexcept;
    [[nodiscard]] static RuntimeHostQuiescenceCapability
    mint_for_host(const RuntimeIncarnationRef &source_slot, std::string source_plan_sha256,
                  std::string target_plan_sha256, RuntimeIdentity128 candidate_resource_identity,
                  std::shared_ptr<RuntimeStateTransferOwnerRegistry> source_owner_registry,
                  std::shared_ptr<RuntimeStateTransferOwnerRegistry> target_owner_registry,
                  const RuntimeIdentity128 &host_instance_nonce,
                  std::function<bool()> host_revalidate, std::function<void()> host_rollback,
                  std::function<bool()> host_begin_transfer,
                  std::function<bool()> host_claim_transfer,
                  std::function<void()> host_end_transfer, std::uint64_t lifecycle_ticket,
                  std::uint64_t candidate_sequence, std::uint64_t mutation_fence_sequence);
    std::shared_ptr<RuntimeHostQuiescenceToken> token_;
};

struct RuntimeValidatedStateTransferState;

class RuntimeValidatedStateTransfer {
  public:
    RuntimeValidatedStateTransfer() = default;
    RuntimeValidatedStateTransfer(RuntimeValidatedStateTransfer &&) noexcept;
    RuntimeValidatedStateTransfer &operator=(RuntimeValidatedStateTransfer &&) noexcept;
    RuntimeValidatedStateTransfer(const RuntimeValidatedStateTransfer &) = delete;
    RuntimeValidatedStateTransfer &operator=(const RuntimeValidatedStateTransfer &) = delete;
    ~RuntimeValidatedStateTransfer();

    [[nodiscard]] bool valid() const noexcept;
    [[nodiscard]] RuntimeIncarnationRef source_slot() const noexcept;
    [[nodiscard]] std::string_view target_plan_sha256() const noexcept;
    [[nodiscard]] std::string_view state_bundle_sha256() const noexcept;
    [[nodiscard]] std::uint64_t transfer_fence_sequence() const noexcept;
    [[nodiscard]] std::uint64_t episode_barrier_sequence() const noexcept;
    [[nodiscard]] RuntimeEpisodeCoordinatorSnapshot source_barrier_snapshot() const noexcept;
    void abandon() noexcept;

  private:
    friend class RuntimeStateTransferValidator;
    friend class RuntimeHostCandidate;
    explicit RuntimeValidatedStateTransfer(
        std::shared_ptr<RuntimeValidatedStateTransferState> state) noexcept;

    [[nodiscard]] RuntimeStateTransferStatus prepare_for_host(
        const RuntimeIncarnationRef &expected_source, std::string_view expected_source_plan_sha256,
        std::string_view expected_target_plan_sha256,
        const RuntimeIdentity128 &expected_candidate_resource_identity,
        std::uint64_t expected_lifecycle_ticket, std::uint64_t expected_candidate_sequence,
        std::uint64_t expected_mutation_fence_sequence);
    void commit_for_host() noexcept;
    void abort_for_host() noexcept;

    std::shared_ptr<RuntimeValidatedStateTransferState> state_;
};

struct RuntimeStateTransferValidationRequest {
    RuntimeStateTransferProfile profile;
    RuntimeStateCensus census;
    RuntimeStateTransferEvidence evidence;
    RuntimeHostQuiescenceCapability host_quiescence;
    RuntimeEpisodeBarrierCapability episode_barrier;
};

struct RuntimeStateTransferValidationResult {
    RuntimeStateTransferStatus status;
    RuntimeValidatedStateTransfer transfer;
};

class RuntimeStateTransferValidator {
  public:
    [[nodiscard]] static RuntimeStateTransferValidationResult
    validate(RuntimeStateTransferValidationRequest &&request);
};

[[nodiscard]] std::string runtime_state_payload_sha256(const std::vector<std::uint8_t> &payload);
[[nodiscard]] std::vector<std::uint8_t>
runtime_state_canonical_payload(const RuntimeStateCensusEntry &entry);
[[nodiscard]] std::string runtime_state_census_entry_sha256(const RuntimeStateCensusEntry &entry);
[[nodiscard]] std::string
canonical_episode_transition_intent_bytes(const RuntimeEpisodeTransitionIntent &intent);
[[nodiscard]] std::string
canonical_episode_transition_receipt_bytes(const RuntimeEpisodeTransitionReceipt &receipt);
[[nodiscard]] std::string_view runtime_state_category_name(RuntimeStateCategory category) noexcept;
[[nodiscard]] std::string_view
runtime_state_disposition_name(RuntimeStateDisposition disposition) noexcept;
[[nodiscard]] std::string_view runtime_state_owner_id(RuntimeStateCategory category) noexcept;
[[nodiscard]] std::string_view runtime_state_schema_id(RuntimeStateCategory category) noexcept;

} // namespace runtime::host
