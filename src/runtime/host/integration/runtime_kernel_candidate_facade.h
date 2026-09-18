#pragma once

#include "runtime_kernel_candidate.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace runtime::host::integration {

// P4-C shadow adapter for the existing world-batch/facade shape. It owns no
// kernel, host, or publication state: every operation delegates to the
// host-bound RuntimeKernelCandidate and therefore inherits its epoch fence.
class RuntimeKernelCandidateFacadeAdapter final {
  public:
    explicit RuntimeKernelCandidateFacadeAdapter(RuntimeKernelCandidate &candidate) noexcept
        : candidate_(&candidate) {}

    [[nodiscard]] RuntimeWorldRef world_ref() const noexcept;
    [[nodiscard]] RuntimeCandidateCompositionSnapshot composition_snapshot() const;
    [[nodiscard]] bool composition_immutable() const noexcept;

    [[nodiscard]] std::vector<RuntimeEntityRef>
    // Returns the successfully spawned prefix when a later request is
    // rejected; this candidate seam does not claim atomic batch rollback.
    apply_spawn_batch(const std::vector<WorldSpawnRequest> &requests);
    [[nodiscard]] bool step_batch(std::size_t world_count = 1);
    [[nodiscard]] bool set_time_step(double dt);
    [[nodiscard]] bool try_get_entity_kinematics(const RuntimeEntityRef &entity,
                                                 WorldEntityKinematics *state);
    [[nodiscard]] bool try_set_entity_kinematics(const RuntimeEntityRef &entity,
                                                 const WorldEntityKinematics &state);

  private:
    RuntimeKernelCandidate *candidate_ = nullptr;
};

} // namespace runtime::host::integration
