#pragma once

#include <echelon_forge/runtime_contracts/runtime_identity.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <memory>
#include <mutex>
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
// MissionCommandGround gained reflected stance after the generation-4 producer;
// N=5 materializes Stand for admitted N-1 bytes before durable import. Readers accept only N and
// N-1 so a rolling replacement can bridge one producer generation without silently accepting an
// arbitrarily old state bundle.
inline constexpr std::uint32_t kRuntimeStateTransferContractGeneration = 5;
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

enum class RuntimeStateUnknownFieldPolicy : std::uint8_t {
    Reject,
    PreserveOpaque,
    IgnoreDerived,
};

enum class RuntimeStateReplayPolicy : std::uint8_t {
    Transfer,
    Rederive,
    Cancel,
    Drain,
    Reject,
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
    ImportTransactionStateInvalid,
    ImportTransactionDeadlineExceeded,
    ImportTransactionAmbiguous,
    ImportJournalUnavailable,
    ImportJournalCorrupt,
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

// The matrix is the candidate's single directional compatibility declaration:
// every category has one owner/schema pair, explicit N/N-1 generations,
// unknown-field behavior, replay disposition, migration digest, and rollback
// obligation.  It describes the required production adapter contract; it is
// not itself evidence that an adapter exists or that its bytes are durable.
struct RuntimeStateDecoderReplayRule {
    RuntimeStateCategory category = RuntimeStateCategory::CompositionProviderSystemGraph;
    RuntimeStateDisposition disposition = RuntimeStateDisposition::Reject;
    std::string_view owner_id;
    std::string_view schema_id;
    std::uint32_t current_schema_generation = kRuntimeStateTransferContractGeneration;
    std::uint32_t previous_schema_generation = kRuntimeStateTransferPreviousGeneration;
    RuntimeStateUnknownFieldPolicy unknown_field_policy = RuntimeStateUnknownFieldPolicy::Reject;
    RuntimeStateReplayPolicy replay_policy = RuntimeStateReplayPolicy::Reject;
    std::string_view migration_sha256;
    bool rollback_required = true;
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

// Import is a two-phase owner operation.  The legacy commit()/abort() hooks
// remain as a compatibility edge for existing shadow fixtures, but new owner
// adapters must override the statusful methods below.  A transaction is not
// durable merely because it returns Committed: durable=true requires an owner
// journal and a non-zero journal sequence that survive process interruption.
enum class RuntimeStateOwnerImportTransactionPhase : std::uint8_t {
    Prepared,
    Committing,
    Committed,
    Aborting,
    Aborted,
    Ambiguous,
};

struct RuntimeStateOwnerImportTransactionStatus {
    RuntimeStateOwnerImportTransactionPhase phase =
        RuntimeStateOwnerImportTransactionPhase::Prepared;
    RuntimeStateTransferError error = RuntimeStateTransferError::None;
    std::uint64_t journal_sequence = 0;
    bool durable = false;

    [[nodiscard]] explicit operator bool() const noexcept {
        return error == RuntimeStateTransferError::None;
    }
};

class RuntimeStateOwnerImportTransaction {
  public:
    virtual ~RuntimeStateOwnerImportTransaction() = default;
    // Legacy fixture compatibility hooks.  They are intentionally retained
    // only as a bridge while production owners migrate to the statusful API.
    virtual void commit() noexcept;
    virtual void abort() noexcept;

    // The owner must make the candidate import durable only on commit and must
    // discard every provisional mutation on abort.  Statusful methods carry a
    // bounded deadline and expose terminal outcome.  A deadline of zero means
    // that the caller has not supplied a clock for this dark/shadow probe.
    [[nodiscard]] virtual RuntimeStateOwnerImportTransactionStatus
    commit_with_deadline(std::uint64_t now_tick, std::uint64_t deadline_tick) noexcept;
    [[nodiscard]] virtual RuntimeStateOwnerImportTransactionStatus
    abort_with_deadline(std::uint64_t now_tick, std::uint64_t deadline_tick) noexcept;
    [[nodiscard]] virtual RuntimeStateOwnerImportTransactionStatus
    recover_with_deadline(std::uint64_t now_tick, std::uint64_t deadline_tick) noexcept;
    // Compensation hook for a composite import whose later child failed
    // after this transaction had already committed.  Owners that cannot
    // compensate must return false; the composite then remains Ambiguous and
    // the host must keep the candidate quarantined.
    [[nodiscard]] virtual bool rollback_committed() noexcept;
    [[nodiscard]] virtual RuntimeStateOwnerImportTransactionStatus status() const noexcept;
};

struct RuntimeStateTransferJournalRecord {
    std::uint64_t sequence = 0;
    std::string transaction_id;
    RuntimeStateOwnerImportTransactionPhase phase =
        RuntimeStateOwnerImportTransactionPhase::Prepared;
    std::string payload_sha256;
    // Digest of the owner pre-image captured before the first mutation.  An
    // empty value is retained only for legacy host-neutral fixtures; a
    // maintained owner transaction must persist this binding.
    std::string pre_mutation_sha256;
    std::vector<std::uint8_t> pre_mutation_payload;
};

struct RuntimeStateTransferJournalAppendResult {
    RuntimeStateTransferStatus status;
    std::uint64_t sequence = 0;
};

struct RuntimeStateTransferJournalReadResult {
    RuntimeStateTransferStatus status;
    std::optional<RuntimeStateTransferJournalRecord> record;
};

class RuntimeStateTransferJournal {
  public:
    virtual ~RuntimeStateTransferJournal() = default;
    [[nodiscard]] virtual RuntimeStateTransferJournalAppendResult
    append_and_sync(std::string_view transaction_id, RuntimeStateOwnerImportTransactionPhase phase,
                    std::string_view payload_sha256, std::string_view pre_mutation_sha256 = {},
                    const std::vector<std::uint8_t> &pre_mutation_payload = {}) noexcept = 0;
    [[nodiscard]] virtual RuntimeStateTransferJournalReadResult
    latest(std::string_view transaction_id) noexcept = 0;
};

// Append-only, checksummed, fsync/_commit-backed local WAL for the P4-B owner
// transaction.  This is not the production ArtifactLedger qualification owned
// by P5-B, but it provides the durable pre-mutation/terminal and restart
// recovery semantics required by the P4-B handoff.
class RuntimeStateTransferFileJournal final : public RuntimeStateTransferJournal {
  public:
    explicit RuntimeStateTransferFileJournal(std::string path);
    ~RuntimeStateTransferFileJournal() override;
    RuntimeStateTransferFileJournal(const RuntimeStateTransferFileJournal &) = delete;
    RuntimeStateTransferFileJournal &operator=(const RuntimeStateTransferFileJournal &) = delete;

    [[nodiscard]] RuntimeStateTransferJournalAppendResult
    append_and_sync(std::string_view transaction_id, RuntimeStateOwnerImportTransactionPhase phase,
                    std::string_view payload_sha256, std::string_view pre_mutation_sha256 = {},
                    const std::vector<std::uint8_t> &pre_mutation_payload = {}) noexcept override;
    [[nodiscard]] RuntimeStateTransferJournalReadResult
    latest(std::string_view transaction_id) noexcept override;

  private:
    struct State;
    std::unique_ptr<State> state_;
};

struct RuntimeStateOwnerImportRecoveryCallbacks {
    std::function<bool()> commit;
    std::function<bool()> abort;
    // Called only for a durable non-terminal record after interruption.  It
    // must inspect owner state and return Committed/Aborted, or Ambiguous when
    // the owner cannot prove the outcome.
    std::function<RuntimeStateOwnerImportTransactionPhase()> recover;
    // Optional compensation for a child that already reached Committed while
    // a composite transaction is still being assembled.
    std::function<bool()> compensate;
    // Optional phase-sensitive terminal-state verification used when reopening
    // a journal. Returning false forces recovery instead of trusting a stale
    // terminal WAL row; the owner must verify the exact expected phase.
    std::function<bool(RuntimeStateOwnerImportTransactionPhase)> verify;
    // Optional owner clock sampled after a callback returns.  If it crosses
    // the caller's deadline, the transaction remains ambiguous and requires
    // explicit recovery before publication.
    std::function<std::uint64_t()> sample_tick;
};

class RuntimeDurableOwnerImportTransaction final : public RuntimeStateOwnerImportTransaction {
  public:
    RuntimeDurableOwnerImportTransaction(
        std::string transaction_id, std::string payload_sha256,
        std::shared_ptr<RuntimeStateTransferJournal> journal,
        RuntimeStateOwnerImportRecoveryCallbacks callbacks, std::string pre_mutation_sha256 = {},
        std::vector<std::uint8_t> pre_mutation_payload = {}) noexcept;

    [[nodiscard]] RuntimeStateOwnerImportTransactionStatus
    commit_with_deadline(std::uint64_t now_tick, std::uint64_t deadline_tick) noexcept override;
    [[nodiscard]] RuntimeStateOwnerImportTransactionStatus
    abort_with_deadline(std::uint64_t now_tick, std::uint64_t deadline_tick) noexcept override;
    [[nodiscard]] RuntimeStateOwnerImportTransactionStatus
    recover_with_deadline(std::uint64_t now_tick, std::uint64_t deadline_tick) noexcept override;
    [[nodiscard]] bool rollback_committed() noexcept override;
    [[nodiscard]] RuntimeStateOwnerImportTransactionStatus status() const noexcept override;

  private:
    [[nodiscard]] RuntimeStateOwnerImportTransactionStatus
    append_terminal(RuntimeStateOwnerImportTransactionPhase phase) noexcept;

    mutable std::mutex mutex_;
    std::string transaction_id_;
    std::string payload_sha256_;
    std::string pre_mutation_sha256_;
    std::vector<std::uint8_t> pre_mutation_payload_;
    std::shared_ptr<RuntimeStateTransferJournal> journal_;
    RuntimeStateOwnerImportRecoveryCallbacks callbacks_;
    RuntimeStateOwnerImportTransactionStatus status_{};
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

// A registration is the narrow bridge between a maintained runtime owner and
// the host-neutral P4-B protocol.  The callbacks must read/write the owner
// they capture; they must not manufacture fixture bytes from the request.
struct RuntimeStateOwnerAdapterExport {
    RuntimeStateCensusEntry census_entry;
    RuntimeStateOwnerArtifact artifact;
};

// Host-minted settlement facts that are not owned by the episode snapshot.
// Admission is already closed when this context is captured, so the source
// registry can account for every late read-only result without transferring
// the request or its process-local lease to the target.
struct RuntimeStateOwnerExportContext {
    RuntimeEpisodeCoordinatorSnapshot barrier_snapshot;
    std::size_t source_read_only_result_leases = 0;
    bool cooperative_cancellation_acknowledged = false;
};

struct RuntimeStateOwnerAdapterImport {
    RuntimeStateOwnerObservation observation;
    std::shared_ptr<RuntimeStateOwnerImportTransaction> transaction;
};

struct RuntimeStateOwnerAdapterRegistration {
    RuntimeStateCategory category = RuntimeStateCategory::CompositionProviderSystemGraph;
    std::string owner_id;
    std::string schema_id;
    std::string migration_sha256;
    std::function<RuntimeStateOwnerAdapterExport(const RuntimeStateTransferProfile &,
                                                 const RuntimeIncarnationRef &,
                                                 const RuntimeStateOwnerExportContext &)>
        export_state;
    std::function<RuntimeStateOwnerArtifact(const RuntimeStateOwnerArtifact &)> migrate_previous;
    std::function<RuntimeStateOwnerAdapterImport(
        const RuntimeStateTransferProfile &, const RuntimeIncarnationRef &,
        const RuntimeStateCensusEntry &, const RuntimeStateOwnerArtifact &,
        const RuntimeStateOwnerArtifact &, const RuntimeIdentity128 &)>
        import_state;
};

// P4-B requires a typed owner/import adapter.  The validator never accepts
// caller-authored aggregate hashes as evidence: it asks this registry to decode
// each exact schema from the quiesced source, import it into the bound candidate
// resource, and report both observed digests plus replay evidence.
class RuntimeStateTransferOwnerRegistry {
  public:
    virtual ~RuntimeStateTransferOwnerRegistry() = default;
    // Optional immutable provenance supplied by a concrete owner registry.
    // Empty values retain compatibility with host-neutral fixtures; when
    // present, the validator binds the registry to the host resource and
    // rejects source/target registries backed by the same owner instance.
    [[nodiscard]] virtual RuntimeIdentity128 bound_resource_identity() const noexcept = 0;
    [[nodiscard]] virtual const void *owner_binding_token() const noexcept = 0;
    [[nodiscard]] virtual RuntimeStateOwnerExport
    export_source(const RuntimeStateTransferProfile &profile,
                  const RuntimeIncarnationRef &source_slot,
                  const RuntimeStateOwnerExportContext &context) noexcept = 0;
    [[nodiscard]] virtual RuntimeStateOwnerImportReceipt
    import_and_observe(const RuntimeStateTransferProfile &profile,
                       const RuntimeStateOwnerExport &source_export,
                       const RuntimeIdentity128 &candidate_resource_identity) noexcept = 0;
};

// Concrete registry used by production-facing integration code.  Requiring a
// fixed twelve-entry registration array makes omission and duplicate owner
// registration observable at construction; all callback failures are returned
// as fail-closed transfer status rather than being converted into defaults.
class RuntimeStateOwnerAdapterRegistry final : public RuntimeStateTransferOwnerRegistry {
  public:
    explicit RuntimeStateOwnerAdapterRegistry(
        std::array<RuntimeStateOwnerAdapterRegistration, kRuntimeStateCategoryCount> registrations,
        RuntimeIdentity128 bound_resource_identity = {}, const void *owner_binding_token = nullptr);

    [[nodiscard]] RuntimeStateTransferStatus registration_status() const noexcept;
    [[nodiscard]] RuntimeIdentity128 bound_resource_identity() const noexcept override {
        return bound_resource_identity_;
    }
    [[nodiscard]] const void *owner_binding_token() const noexcept override {
        return owner_binding_token_;
    }

    // Exposes the immutable registration selected by the fixed category
    // table. Integration tests use this to exercise a maintained owner codec
    // and its WAL transaction without weakening the all-twelve export gate.
    [[nodiscard]] const RuntimeStateOwnerAdapterRegistration *
    registration(RuntimeStateCategory category) const noexcept;

    [[nodiscard]] RuntimeStateOwnerExport
    export_source(const RuntimeStateTransferProfile &profile,
                  const RuntimeIncarnationRef &source_slot,
                  const RuntimeStateOwnerExportContext &context) noexcept override;

    [[nodiscard]] RuntimeStateOwnerImportReceipt
    import_and_observe(const RuntimeStateTransferProfile &profile,
                       const RuntimeStateOwnerExport &source_export,
                       const RuntimeIdentity128 &candidate_resource_identity) noexcept override;

  private:
    std::array<RuntimeStateOwnerAdapterRegistration, kRuntimeStateCategoryCount> registrations_;
    RuntimeStateTransferStatus registration_status_;
    RuntimeIdentity128 bound_resource_identity_;
    const void *owner_binding_token_ = nullptr;
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
    [[nodiscard]] static RuntimeHostQuiescenceCapability mint_for_host(
        const RuntimeIncarnationRef &source_slot, std::string source_plan_sha256,
        std::string target_plan_sha256, RuntimeIdentity128 source_resource_identity,
        RuntimeIdentity128 candidate_resource_identity,
        std::shared_ptr<RuntimeStateTransferOwnerRegistry> source_owner_registry,
        std::shared_ptr<RuntimeStateTransferOwnerRegistry> target_owner_registry,
        const RuntimeIdentity128 &host_instance_nonce, std::function<bool()> host_revalidate,
        std::function<void()> host_rollback, std::function<bool()> host_begin_transfer,
        std::function<bool()> host_claim_transfer, std::function<void()> host_end_transfer,
        std::uint64_t lifecycle_ticket, std::uint64_t candidate_sequence,
        std::uint64_t mutation_fence_sequence, std::size_t source_read_only_result_leases,
        bool cooperative_cancellation_acknowledged);
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
    [[nodiscard]] RuntimeStateTransferStatus
    commit_for_host(std::uint64_t now_tick = 0, std::uint64_t deadline_tick = 0) noexcept;
    [[nodiscard]] RuntimeStateTransferStatus
    recover_for_host(std::uint64_t now_tick = 0, std::uint64_t deadline_tick = 0) noexcept;
    void abort_for_host() noexcept;

    [[nodiscard]] bool committed() const noexcept;
    [[nodiscard]] bool aborted() const noexcept;
    [[nodiscard]] bool ambiguous() const noexcept;

    // Release the host publication fence only after the host has finalized
    // its authority/state transition.  Commit/recover deliberately keep this
    // callback armed so no mutator can observe a partially published target.
    void release_host_transfer_fence() noexcept;

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
[[nodiscard]] const std::array<RuntimeStateDecoderReplayRule, kRuntimeStateCategoryCount> &
runtime_state_decoder_replay_matrix() noexcept;
[[nodiscard]] const RuntimeStateDecoderReplayRule *
runtime_state_decoder_replay_rule(RuntimeStateCategory category) noexcept;

// Construct the canonical twelve-row profile from the maintained decoder /
// replay matrix.  Callers still supply the plan bindings and profile identity,
// but cannot accidentally rename an owner/schema or widen the N/N-1 window.
// This is a profile-construction guard; it does not claim that the production
// owner adapters or durable journal behind the rows already exist.
[[nodiscard]] RuntimeStateTransferProfile runtime_state_transfer_profile_from_decoder_matrix(
    std::string profile_id, std::uint32_t profile_generation, std::string source_plan_sha256,
    std::string target_plan_sha256);

} // namespace runtime::host
