#pragma once

#include "runtime_run_recorder.h"

#include <cstdint>
#include <cstddef>
#include <filesystem>
#include <mutex>
#include <string>
#include <string_view>
#include <unordered_map>

namespace runtime::host {

enum class RuntimeArtifactLedgerRole : std::uint8_t {
    RuntimeHost,
    CrashReconciler,
    PlanCompiler,
    ReleaseArtifactPipeline,
    BackupOperator,
    ReadOnlyAuditor,
};

struct RuntimeArtifactLedgerAccessContext {
    RuntimeArtifactLedgerRole role = RuntimeArtifactLedgerRole::ReadOnlyAuditor;
    std::string audit_identity;
};

// Native local-filesystem ArtifactLedger adapter for the admitted in-process
// topology. A root lock excludes competing handles/processes, every mutation
// is flushed before atomic replacement, and journal frames are persisted with
// their hash-chain metadata. Unsupported multi-process failover remains
// fail-closed until the P1-C security provider is admitted.
class RuntimeFileArtifactLedgerStore final : public RuntimeRunRecorderStore {
  public:
    RuntimeFileArtifactLedgerStore(std::filesystem::path root,
                                   RuntimeArtifactLedgerAccessContext access);
    ~RuntimeFileArtifactLedgerStore() override;

    RuntimeFileArtifactLedgerStore(const RuntimeFileArtifactLedgerStore &) = delete;
    RuntimeFileArtifactLedgerStore &operator=(const RuntimeFileArtifactLedgerStore &) = delete;

    [[nodiscard]] bool acquire_fence(std::string_view stream_id, std::string_view writer_id,
                                     std::uint64_t &generation, std::string &detail) override;
    [[nodiscard]] bool commit_header(std::string_view journal_id, std::uint64_t generation,
                                     std::string_view writer_id, std::string_view header_json,
                                     std::string &detail) override;
    [[nodiscard]] bool commit_header_authorized(std::string_view journal_id,
                                                std::uint64_t generation,
                                                std::string_view writer_id,
                                                std::string_view header_json,
                                                const RuntimeRunAdmissionCapability &capability,
                                                std::string &detail) override;
    [[nodiscard]] bool append_record_authorized(std::string_view journal_id,
                                                std::uint64_t generation,
                                                std::string_view writer_id, std::uint64_t sequence,
                                                std::string_view payload,
                                                const RuntimeRunAdmissionCapability &capability,
                                                RuntimeRunRecorderAppendAck &ack,
                                                std::string &detail) override;
    [[nodiscard]] bool resume_journal(std::string_view journal_id, std::uint64_t generation,
                                      std::string_view writer_id, std::string_view header_json,
                                      std::uint64_t &next_sequence, std::string &last_record_sha256,
                                      std::string &detail) override;
    [[nodiscard]] bool
    resume_journal_authorized(std::string_view journal_id, std::uint64_t generation,
                              std::string_view writer_id, std::string_view header_json,
                              const RuntimeRunAdmissionCapability &capability,
                              std::uint64_t &next_sequence, std::string &last_record_sha256,
                              std::string &detail) override;
    [[nodiscard]] bool append_record(std::string_view journal_id, std::uint64_t generation,
                                     std::string_view writer_id, std::uint64_t sequence,
                                     std::string_view payload, RuntimeRunRecorderAppendAck &ack,
                                     std::string &detail) override;
    [[nodiscard]] bool finalize_receipt(std::string_view journal_id, std::uint64_t generation,
                                        std::string_view writer_id, std::string_view receipt_json,
                                        RuntimeRunRecorderFinalizeAck &ack,
                                        std::string &detail) override;
    [[nodiscard]] bool
    finalize_receipt_authorized(std::string_view journal_id, std::uint64_t generation,
                                std::string_view writer_id, std::string_view receipt_json,
                                const RuntimeRunAdmissionCapability &capability,
                                RuntimeRunRecorderFinalizeAck &ack, std::string &detail) override;
    [[nodiscard]] bool commit_checkpoint(std::string_view journal_id, std::uint64_t generation,
                                         std::string_view writer_id,
                                         std::string_view checkpoint_json,
                                         std::string_view validation_json,
                                         RuntimeRunRecorderCheckpointAck &ack,
                                         std::string &detail) override;
    [[nodiscard]] bool commit_checkpoint_authorized(
        std::string_view journal_id, std::uint64_t generation, std::string_view writer_id,
        std::string_view checkpoint_json, std::string_view validation_json,
        const RuntimeRunAdmissionCapability &capability, RuntimeRunRecorderCheckpointAck &ack,
        std::string &detail) override;
    [[nodiscard]] bool rehydrate_state_authorized(std::string_view journal_id,
                                                  const RuntimeRunAdmissionCapability &capability,
                                                  RuntimeRunRecorderRecoveryState &state,
                                                  std::string &detail) override;
    [[nodiscard]] bool put_artifact(std::string_view bytes, std::string_view media_type,
                                    std::string_view retention_class, std::string &digest,
                                    std::string &retrieval_location, std::string &detail) override;

    [[nodiscard]] bool read_receipt(std::string_view journal_id, std::string &receipt_json,
                                    std::string &detail) const;
    [[nodiscard]] bool read_checkpoint(std::string_view checkpoint_id, std::string &bundle_json,
                                       std::string &detail) const;
    [[nodiscard]] bool backup_to(const std::filesystem::path &target, std::string &detail) const;
    [[nodiscard]] static bool restore_from(const std::filesystem::path &source,
                                           const std::filesystem::path &target,
                                           const RuntimeArtifactLedgerAccessContext &access,
                                           std::string &detail);
    [[nodiscard]] bool availability_report(std::string &report_json, std::string &detail) const;

    [[nodiscard]] const std::filesystem::path &root() const noexcept { return root_; }

  private:
    [[nodiscard]] std::filesystem::path stream_path(std::string_view stream_id) const;
    [[nodiscard]] std::filesystem::path fence_path(std::string_view stream_id) const;
    [[nodiscard]] std::filesystem::path fence_history_path(std::string_view stream_id,
                                                           std::uint64_t generation) const;
    [[nodiscard]] bool active_fence(std::string_view stream_id, std::uint64_t generation,
                                    std::string_view writer_id, std::string &detail) const;
    [[nodiscard]] bool durable_write(const std::filesystem::path &path, std::string_view bytes,
                                     std::string &detail) const;
    [[nodiscard]] bool scan_journal(const std::filesystem::path &directory,
                                    std::string_view journal_id, std::uint64_t expected_generation,
                                    std::uint64_t &next_sequence, std::string &last_record_sha256,
                                    std::string &detail) const;
    [[nodiscard]] bool verify_artifact(std::string_view digest, std::size_t size,
                                       std::string_view media_type,
                                       std::string_view retention_class, std::string &detail) const;
    [[nodiscard]] bool verify_admission_artifacts_unlocked(std::string_view receipt_payload_json,
                                                           std::string &detail) const;
    [[nodiscard]] bool read_checkpoint_unlocked(std::string_view checkpoint_id,
                                                std::string &bundle_json,
                                                std::string &detail) const;
    [[nodiscard]] bool verify_checkpoint_commit_intent_unlocked(const std::string &checkpoint_json,
                                                                const std::string &validation_json,
                                                                std::string &detail) const;
    [[nodiscard]] bool
    validate_checkpoint_reference_unlocked(const std::string &reference_json,
                                           const std::string &receipt_payload_json, bool created,
                                           std::string &detail) const;
    [[nodiscard]] bool
    validate_receipt_checkpoints_unlocked(const std::string &receipt_payload_json,
                                          std::uint64_t writer_generation,
                                          std::string &detail) const;
    [[nodiscard]] bool finalize_receipt_impl(std::string_view journal_id, std::uint64_t generation,
                                             std::string_view writer_id,
                                             std::string_view receipt_json,
                                             const RuntimeRunAdmissionCapability *capability,
                                             RuntimeRunRecorderFinalizeAck &ack,
                                             std::string &detail);
    [[nodiscard]] bool commit_header_impl(std::string_view journal_id, std::uint64_t generation,
                                          std::string_view writer_id, std::string_view header_json,
                                          std::string &detail);
    [[nodiscard]] bool resume_journal_impl(std::string_view journal_id, std::uint64_t generation,
                                           std::string_view writer_id, std::string_view header_json,
                                           std::uint64_t &next_sequence,
                                           std::string &last_record_sha256, std::string &detail);
    [[nodiscard]] bool append_record_impl(std::string_view journal_id, std::uint64_t generation,
                                          std::string_view writer_id, std::uint64_t sequence,
                                          std::string_view payload,
                                          const RuntimeRunAdmissionCapability *capability,
                                          RuntimeRunRecorderAppendAck &ack, std::string &detail);
    [[nodiscard]] bool commit_checkpoint_impl(std::string_view journal_id, std::uint64_t generation,
                                              std::string_view writer_id,
                                              std::string_view checkpoint_json,
                                              std::string_view validation_json,
                                              const RuntimeRunAdmissionCapability *capability,
                                              RuntimeRunRecorderCheckpointAck &ack,
                                              std::string &detail);
    [[nodiscard]] bool authorize(std::string_view operation, std::string &detail) const;
    [[nodiscard]] bool record_audit(std::string_view operation, std::string_view resource,
                                    std::string_view outcome_sha256, std::string &detail) const;
    [[nodiscard]] bool verify_audit_chain(std::size_t &event_count, std::string &last_event_sha256,
                                          std::string &detail) const;
    [[nodiscard]] bool secure_root_permissions(std::string &detail) const;
    void release_root_lock() noexcept;

    std::filesystem::path root_;
    RuntimeArtifactLedgerAccessContext access_;
    mutable std::mutex mutex_;
    std::unordered_map<std::string, std::string> admission_capabilities_;
    int root_lock_fd_ = -1;
};

} // namespace runtime::host
