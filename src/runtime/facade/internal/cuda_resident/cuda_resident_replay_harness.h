#pragma once

#include <functional>

#include "runtime/contracts/cuda_resident_replay_contract.h"

namespace runtime::cuda_resident::replay {

using ReplayLaneRunner = std::function<ReplayLaneResult(const ReplayTrace &)>;

// RB8 diagnostics-only replay/shadow comparator. Each runner receives the same
// immutable owned trace and returns a detached observation record. Comparison
// never calls either backend and cannot write a shadow value back into a lane.
class CudaResidentReplayHarness final {
  public:
    CudaResidentReplayHarness(ReplayLaneRunner reference_runner,
                              ReplayLaneRunner shadow_runner);

    [[nodiscard]] ReplayComparisonReport run(const ReplayTrace &trace) const;
    [[nodiscard]] ReplayComparisonReport
    rerun(const ReplayTrace &trace, const ReplayComparisonReport &prior) const;

    [[nodiscard]] static std::string trace_signature(const ReplayTrace &trace);

  private:
    ReplayLaneRunner reference_runner_;
    ReplayLaneRunner shadow_runner_;
};

} // namespace runtime::cuda_resident::replay
