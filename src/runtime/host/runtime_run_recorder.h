#pragma once

#include <cstdint>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace runtime::host {

class RuntimeFileArtifactLedgerStore;

// Opaque in-process proof that a RunRecorder admitted and owns a journal.
// Callers cannot construct this type; production stores may only receive it
// through the recorder-authorized operation hooks below.
class RuntimeRunAdmissionCapability final {
  public:
    RuntimeRunAdmissionCapability(const RuntimeRunAdmissionCapability &) = default;
    RuntimeRunAdmissionCapability &operator=(const RuntimeRunAdmissionCapability &) = default;

  private:
    friend class RuntimeRunRecorder;
    friend class RuntimeFileArtifactLedgerStore;
    explicit RuntimeRunAdmissionCapability(std::string token) : token_(std::move(token)) {}

    [[nodiscard]] bool valid() const noexcept { return !token_.empty(); }
    [[nodiscard]] std::string_view token() const noexcept { return token_; }

    std::string token_;
};

enum class RuntimeRunRecorderState : std::uint8_t {
    New,
    Admitted,
    Finalized,
    Rejected,
};

struct RuntimeRunRecorderStatus {
    bool accepted = false;
    std::string code;
    std::string detail;

    [[nodiscard]] explicit operator bool() const noexcept { return accepted; }
};

struct RuntimeRunRecorderAppendAck {
    bool durable = false;
    std::uint64_t sequence = 0;
    std::string payload_sha256;
    std::string record_sha256;
};

struct RuntimeRunRecorderFinalizeAck {
    bool durable = false;
    std::string receipt_sha256;
};

struct RuntimeRunRecorderCheckpointAck {
    bool durable = false;
    std::string checkpoint_sha256;
    std::string validation_sha256;
    std::string state_schema_generation;
};

struct RuntimeRunRecorderCommittedCheckpoint {
    std::string checkpoint_id;
    std::string checkpoint_sha256;
    std::string validation_sha256;
    std::string state_schema_generation;
};

struct RuntimeRunRecorderCommittedArtifact {
    std::string name;
    std::string digest;
    std::string media_type;
    std::uint64_t size = 0;
    std::string retention_class;
    std::string retrieval_location;
};

struct RuntimeRunRecorderRecoveryState {
    std::vector<RuntimeRunRecorderCommittedCheckpoint> committed_checkpoints;
    std::vector<std::string> lifecycle_events;
    std::string admitted_at;
    std::string host_boot_id;
    std::string incarnation_epoch;
    std::string execution_scope_json;
    std::string existing_receipt_json;
};

struct RuntimeExecutionArtifactSource {
    std::string identity;
    std::string path;
};

// Native host-owned facts which are not allowed to come from a receipt
// template. The build owner supplies only facts which cannot be measured from
// the running process. Request/input identities come from the canonical P5-A
// request and plan sources below.
struct RuntimeExecutionOwnerFacts {
    std::string build_mode;
    bool build_dirty = false;
    std::string linker;
    std::string cxx_abi;
    std::string python_abi;
    std::string node_abi;
};

struct RuntimeExecutionProvenanceSources {
    // The native collector validates the complete P5-A plan and its canonical
    // request source. Executable/native-module observations are always
    // discovered from the current process.
    std::string resolved_execution_plan_path;
    std::string request_path;
    std::string package_path;
    std::string wheel_path;
    RuntimeExecutionOwnerFacts owner_facts;
};

// Shared native RunReceipt contract gate used by both the recorder owner and
// the production file adapter. This prevents direct adapter calls from
// persisting a weaker receipt than the recorder would accept.
[[nodiscard]] bool validate_runtime_run_receipt_json(std::string_view receipt_json,
                                                     std::string &detail);
[[nodiscard]] bool validate_runtime_run_header_json(std::string_view run_id,
                                                    std::string_view header_json,
                                                    std::string &detail);
// Rebuild the byte- and host-backed receipt sections from owner-controlled
// paths. The supplied binding template contributes only semantic identities;
// every digest and platform field is replaced by an observation.
[[nodiscard]] bool collect_runtime_execution_bindings_json(
    const RuntimeExecutionProvenanceSources &sources, std::string_view binding_template_json,
    std::string &observed_bindings_json, std::string &detail,
    std::string *verified_request_json = nullptr);
// Return the exact validated P5-A plan bytes which SimulationKernel must
// consume. This deliberately returns the complete plan, rather than a caller-
// selected resolved-manifest projection, so native admission remains the only
// extraction boundary.
[[nodiscard]] bool load_runtime_execution_plan_json(
    const RuntimeExecutionProvenanceSources &sources, std::string_view receipt_bindings_json,
    std::string &execution_plan_json, std::string &detail);

// The native host owns this interface.  A production adapter supplies the
// durable ArtifactLedger implementation; tests use a deterministic fake.  No
// world or external side-effect hook is exposed before commit_header returns.
class RuntimeRunRecorderStore {
  public:
    virtual ~RuntimeRunRecorderStore() = default;
    [[nodiscard]] virtual bool acquire_fence(std::string_view stream_id, std::string_view writer_id,
                                             std::uint64_t &generation, std::string &detail) = 0;
    [[nodiscard]] virtual bool commit_header(std::string_view journal_id, std::uint64_t generation,
                                             std::string_view writer_id,
                                             std::string_view header_json, std::string &detail) = 0;
    [[nodiscard]] virtual bool commit_header_authorized(
        std::string_view journal_id, std::uint64_t generation, std::string_view writer_id,
        std::string_view header_json, const RuntimeRunAdmissionCapability &capability,
        std::string &detail) {
        (void)capability;
        return commit_header(journal_id, generation, writer_id, header_json, detail);
    }
    // Re-open an existing admitted journal after a process restart. The store
    // must validate the immutable header and the complete frame chain before
    // returning the durable tail; a fresh writer fence is supplied by the
    // recorder and stale frames remain read-only history.
    [[nodiscard]] virtual bool resume_journal(std::string_view journal_id, std::uint64_t generation,
                                              std::string_view writer_id,
                                              std::string_view header_json,
                                              std::uint64_t &next_sequence,
                                              std::string &last_record_sha256,
                                              std::string &detail) {
        (void)journal_id;
        (void)generation;
        (void)writer_id;
        (void)header_json;
        (void)next_sequence;
        (void)last_record_sha256;
        detail = "store does not support journal resume";
        return false;
    }
    [[nodiscard]] virtual bool resume_journal_authorized(
        std::string_view journal_id, std::uint64_t generation, std::string_view writer_id,
        std::string_view header_json, const RuntimeRunAdmissionCapability &capability,
        std::uint64_t &next_sequence, std::string &last_record_sha256,
        std::string &detail) {
        (void)capability;
        return resume_journal(journal_id, generation, writer_id, header_json, next_sequence,
                              last_record_sha256, detail);
    }
    [[nodiscard]] virtual bool append_record(std::string_view journal_id, std::uint64_t generation,
                                             std::string_view writer_id, std::uint64_t sequence,
                                             std::string_view payload,
                                             RuntimeRunRecorderAppendAck &ack,
                                             std::string &detail) = 0;
    [[nodiscard]] virtual bool append_record_authorized(
        std::string_view journal_id, std::uint64_t generation, std::string_view writer_id,
        std::uint64_t sequence, std::string_view payload,
        const RuntimeRunAdmissionCapability &capability, RuntimeRunRecorderAppendAck &ack,
        std::string &detail) {
        (void)capability;
        return append_record(journal_id, generation, writer_id, sequence, payload, ack, detail);
    }
    [[nodiscard]] virtual bool finalize_receipt(std::string_view journal_id,
                                                std::uint64_t generation,
                                                std::string_view writer_id,
                                                std::string_view receipt_json,
                                                RuntimeRunRecorderFinalizeAck &ack,
                                                std::string &detail) = 0;
    [[nodiscard]] virtual bool finalize_receipt_authorized(
        std::string_view journal_id, std::uint64_t generation, std::string_view writer_id,
        std::string_view receipt_json, const RuntimeRunAdmissionCapability &capability,
        RuntimeRunRecorderFinalizeAck &ack, std::string &detail) {
        (void)capability;
        return finalize_receipt(journal_id, generation, writer_id, receipt_json, ack, detail);
    }
    [[nodiscard]] virtual bool
    commit_checkpoint(std::string_view journal_id, std::uint64_t generation,
                      std::string_view writer_id,
                      std::string_view checkpoint_json, std::string_view validation_json,
                      RuntimeRunRecorderCheckpointAck &ack, std::string &detail) = 0;
    [[nodiscard]] virtual bool commit_checkpoint_authorized(
        std::string_view journal_id, std::uint64_t generation, std::string_view writer_id,
        std::string_view checkpoint_json, std::string_view validation_json,
        const RuntimeRunAdmissionCapability &capability, RuntimeRunRecorderCheckpointAck &ack,
        std::string &detail) {
        (void)capability;
        return commit_checkpoint(journal_id, generation, writer_id, checkpoint_json,
                                 validation_json, ack, detail);
    }
    [[nodiscard]] virtual bool rehydrate_state_authorized(
        std::string_view journal_id, const RuntimeRunAdmissionCapability &capability,
        RuntimeRunRecorderRecoveryState &state, std::string &detail) {
        (void)journal_id;
        (void)capability;
        (void)detail;
        state = {};
        return true;
    }

    // Completed receipts may bind only content-addressed durable artifacts.
    // Backends that do not expose artifact storage remain useful for recorder
    // unit tests, but cannot author a production completion on their own.
    [[nodiscard]] virtual bool put_artifact(std::string_view bytes, std::string_view media_type,
                                            std::string_view retention_class,
                                            std::string &digest, std::string &retrieval_location,
                                            std::string &detail) {
        (void)bytes;
        (void)media_type;
        (void)retention_class;
        (void)digest;
        (void)retrieval_location;
        detail = "store does not support content-addressed artifacts";
        return false;
    }
};

class RuntimeRunRecorder final {
  public:
    RuntimeRunRecorder(RuntimeRunRecorderStore &store, std::string run_id, std::string writer_id);

    [[nodiscard]] RuntimeRunRecorderStatus admit(std::string_view header_json);
    // Lifecycle state is owned by the admitted recorder.  Callers may only
    // report a monotonic phase boundary; timestamps and durable sequence
    // claims are generated by the recorder at finalization.
    [[nodiscard]] RuntimeRunRecorderStatus note_lifecycle(std::string_view event);
    [[nodiscard]] RuntimeRunRecorderStatus bind_runtime_identity(
        std::string_view host_boot_id, std::string_view incarnation_epoch,
        std::string_view world_id, std::string_view world_epoch,
        std::string_view episode_id, std::string_view episode_epoch,
        std::string_view request_id);
    [[nodiscard]] RuntimeRunRecorderStatus observe_entity(std::string_view entity_id,
                                                          std::string_view entity_epoch);
    [[nodiscard]] RuntimeRunRecorderStatus append(std::uint64_t sequence, std::string_view payload);
    [[nodiscard]] RuntimeRunRecorderStatus persist_checkpoint(std::string_view checkpoint_json,
                                                              std::string_view validation_json);
    [[nodiscard]] RuntimeRunRecorderStatus put_artifact(std::string_view name,
                                                        std::string_view bytes,
                                                        std::string_view media_type,
                                                        std::string_view retention_class,
                                                        std::string &digest,
                                                        std::string &retrieval_location);
    [[nodiscard]] RuntimeRunRecorderStatus record_native_result(
        std::string_view result_digest, std::string_view validation_evidence_sha256);
    [[nodiscard]] RuntimeRunRecorderStatus finalize(std::string_view receipt_json);
    [[nodiscard]] RuntimeRunRecorderStatus finalize_observed(std::string_view receipt_template_json,
                                                             std::string_view terminal_state,
                                                             std::string_view terminal_reason);

    [[nodiscard]] RuntimeRunRecorderState state() const noexcept { return state_; }
    [[nodiscard]] std::uint64_t fence_generation() const noexcept { return fence_generation_; }
    [[nodiscard]] std::uint64_t next_sequence() const noexcept { return next_sequence_; }
    [[nodiscard]] bool admitted() const noexcept {
        return state_ == RuntimeRunRecorderState::Admitted;
    }
    [[nodiscard]] bool terminalizable() const noexcept { return terminalizable_; }
    // Canonical static execution bindings admitted before the runtime host is
    // constructed. An empty value denotes the legacy unit-test-only header.
    [[nodiscard]] std::string admission_bindings_json() const;

  private:
    [[nodiscard]] static RuntimeRunAdmissionCapability make_admission_capability(
        std::string_view run_id, std::string_view writer_id);
    [[nodiscard]] RuntimeRunRecorderStatus reject(std::string code, std::string detail);
    [[nodiscard]] RuntimeRunRecorderStatus reject_after_admission(std::string code,
                                                                  std::string detail);

    RuntimeRunRecorderStore &store_;
    std::string run_id_;
    std::string writer_id_;
    RuntimeRunAdmissionCapability admission_capability_;
    RuntimeRunRecorderState state_ = RuntimeRunRecorderState::New;
    std::uint64_t fence_generation_ = 0;
    std::uint64_t next_sequence_ = 0;
    std::string last_record_sha256_;
    std::vector<RuntimeRunRecorderCommittedCheckpoint> committed_checkpoints_;
    std::vector<RuntimeRunRecorderCommittedArtifact> committed_artifacts_;
    std::string admission_bindings_json_;
    std::string admission_binding_sha256_;
    std::string admission_measurement_sha256_;
    std::string admitted_at_;
    std::string receipt_id_;
    std::string attempt_id_;
    std::string host_boot_id_ = "boot-unpublished";
    std::string incarnation_epoch_ = "0";
    std::string execution_scope_json_;
    std::string native_result_digest_;
    std::string native_validation_evidence_sha256_;
    // Exact receipt bytes retained for an idempotent retry after a durable
    // receipt write succeeded but its outcome audit acknowledgement failed.
    std::string pending_receipt_json_;
    std::string owner_projected_receipt_json_;
    std::vector<std::string> lifecycle_events_;
    bool terminalizable_ = false;
};

} // namespace runtime::host
