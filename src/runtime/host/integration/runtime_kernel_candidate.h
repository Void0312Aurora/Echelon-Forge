#pragma once

#include "core/engine/world_batch_runtime.h"
#include "runtime/host/runtime_host_candidate.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <optional>
#include <string>
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

    RuntimeKernelCandidateConfig config_;
    std::shared_ptr<SimulationKernel> kernel_;
    std::shared_ptr<RuntimeStateTransferJournal> journal_;
    std::shared_ptr<Control> control_;
    std::shared_ptr<RuntimeStateTransferOwnerRegistry> registry_;
    RuntimeHostCandidate host_;
    RuntimeCandidateCompositionSnapshot sealed_composition_;
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
