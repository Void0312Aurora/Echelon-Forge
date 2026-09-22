#pragma once

#include "core/engine/world_batch_runtime.h"
#include "runtime/host/runtime_host_candidate.h"
#include "runtime_file_artifact_ledger_store.h"
#include "runtime_run_recorder.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

// P4-C internal-only adapter.  This header is intentionally under src/ and is
// not installed or exposed through the maintained facade/binding surfaces.
// RuntimeHostCandidate remains the only publication authority; this adapter
// supplies a kernel-backed shadow resource and epoch-bearing references for
// native/Python probes.
namespace runtime::host::integration {

using echelon_forge::runtime_contracts::v1::RuntimeEntityRef;
using echelon_forge::runtime_contracts::v1::RuntimeWorldRef;

struct RuntimeKernelCandidateConfig {
    RuntimeIdentity128 host_id;
    RuntimeHostMode mode = RuntimeHostMode::Dark;
    RuntimePlanBinding plan;
    std::string resolved_manifest_json;
    std::uint64_t lifecycle_deadline_tick = 100;
    std::string journal_path;
    RuntimeRunRecorderStore *run_recorder_store = nullptr;
    std::string run_ledger_path;
    std::string run_audit_identity;
    std::string run_id;
    std::string run_writer_id;
    std::string run_header_json;
    // Any configured P5-B recorder is admitted before SimulationKernel exists.
    // Native callers provide a fully versioned, run-specific receipt template.
    // The recorder treats it only as a static contract shell and replaces all
    // observed/terminal facts from recorder-owned state.
    std::string run_receipt_template_json;
    RuntimeExecutionProvenanceSources run_execution_sources;
};

struct RuntimeCandidateCompositionSnapshot {
    std::string requested_manifest_sha256;
    std::string resolved_manifest_sha256;
    std::string executable_graph_sha256;
    std::array<std::uint64_t, 5> scope_generations{};

    bool operator==(const RuntimeCandidateCompositionSnapshot &) const = default;
};

class RuntimeKernelCandidate final {
  public:
    explicit RuntimeKernelCandidate(RuntimeKernelCandidateConfig config);
    RuntimeKernelCandidate(const RuntimeKernelCandidate &) = delete;
    RuntimeKernelCandidate &operator=(const RuntimeKernelCandidate &) = delete;
    ~RuntimeKernelCandidate();

    [[nodiscard]] RuntimeHostStatus start();
    // Candidate-only native fact injection used by the focused terminal/reset
    // receipt test. It is not a production caller or an episode payload claim.
    void arm_terminal_receipt_for_test() noexcept;
    [[nodiscard]] RuntimeShutdownResult shutdown(std::uint64_t now_tick = 0,
                                                 std::uint64_t deadline_tick = 0);
    [[nodiscard]] RuntimeRunRecorderStatus finalize_run(std::string_view receipt_json);
    [[nodiscard]] RuntimeRunRecorderStatus persist_checkpoint(std::string_view checkpoint_json,
                                                              std::string_view validation_json);

    [[nodiscard]] RuntimeHostSnapshot host_snapshot() const;
    [[nodiscard]] RuntimeCandidateCompositionSnapshot composition_snapshot() const;
    [[nodiscard]] bool composition_immutable() const noexcept;
    [[nodiscard]] RuntimeIncarnationRef incarnation() const noexcept;
    [[nodiscard]] RuntimeWorldRef world_ref() const noexcept;
    [[nodiscard]] RuntimeEpisodeRef episode_ref() noexcept;
    [[nodiscard]] std::optional<RuntimeEntityRef> entity_ref(std::uint64_t entity_id) const;

    // Every operation accepts the public epoch-bearing reference.  Conversion
    // to the legacy WorldEntityRef is private to this adapter and occurs only
    // after the host/world/entity fences have been checked.
    [[nodiscard]] std::optional<RuntimeEntityRef> spawn_unit(const RuntimeWorldRef &world,
                                                             const WorldSpawnRequest &request);
    [[nodiscard]] bool step(const RuntimeWorldRef &world);
    [[nodiscard]] bool set_time_step(const RuntimeWorldRef &world, double dt);
    [[nodiscard]] bool submit_episode(const RuntimeEpisodeRef &expected_episode,
                                      RuntimeEpisodeIntentKind kind,
                                      RuntimeIdentity128 idempotency_key,
                                      std::string payload_sha256,
                                      RuntimeEpisodeTransitionReceipt *receipt = nullptr);
    [[nodiscard]] bool try_get_entity_kinematics(const RuntimeEntityRef &entity,
                                                 WorldEntityKinematics *state);
    [[nodiscard]] bool try_set_entity_kinematics(const RuntimeEntityRef &entity,
                                                 const WorldEntityKinematics &state);

  private:
    class Control;

    [[nodiscard]] bool validate_world(const RuntimeWorldRef &world) const noexcept;
    [[nodiscard]] bool validate_entity(const RuntimeEntityRef &entity) const noexcept;
    [[nodiscard]] RuntimeEpisodeRef current_episode() noexcept;
    [[nodiscard]] RuntimeHostStatus initialize_candidate();
    [[nodiscard]] std::optional<std::vector<std::uint8_t>> observed_state_bytes() const;
    [[nodiscard]] std::optional<std::string> observed_state_sha256() const;
    [[nodiscard]] bool record_mutation(std::string_view operation,
                                       std::string_view arguments_json = "{}");
    [[nodiscard]] bool record_outcome(std::string_view operation, bool success,
                                      std::string_view result_json = "{}");
    [[nodiscard]] RuntimeRunRecorderStatus finalize_observed(
        std::string_view receipt_template_json, std::string_view terminal_state,
        std::string_view terminal_reason);
    void terminalize_evidence_failure(std::string_view reason) noexcept;

    RuntimeKernelCandidateConfig config_;
    std::shared_ptr<SimulationKernel> kernel_;
    std::shared_ptr<RuntimeStateTransferJournal> journal_;
    std::shared_ptr<Control> control_;
    std::shared_ptr<RuntimeStateTransferOwnerRegistry> registry_;
    RuntimeHostCandidate host_;
    std::unique_ptr<RuntimeRunRecorder> run_recorder_;
    std::unique_ptr<RuntimeFileArtifactLedgerStore> owned_run_store_;
    RuntimeCandidateCompositionSnapshot sealed_composition_;
    std::string admitted_execution_plan_sha256_;
    std::string admitted_resolved_manifest_sha256_;
    std::optional<std::uint32_t> admitted_seed_;
    std::optional<std::uint64_t> admitted_time_step_ns_;
    std::optional<std::vector<std::uint8_t>> terminal_state_bytes_;
    std::optional<std::string> terminal_state_sha256_;
    std::string journal_path_;
    RuntimeIncarnationRef incarnation_;
    std::uint64_t world_generation_ = 1;
    std::uint64_t episode_step_sequence_ = 0;
    std::uint64_t next_action_idempotency_sequence_ = 1;
    std::uint64_t next_entity_generation_ = 1;
    bool owns_journal_path_ = false;
    bool started_ = false;
    bool stopped_ = false;
};

} // namespace runtime::host::integration
