#pragma once

#include <string>

#include "runtime/contracts/cuda_resident_full_window_contract.h"
#include "runtime/facade/internal/world_batch_backend.h"

namespace runtime::cuda_resident::full_window {

struct RunnerConfig {
    replay::ReplayLaneKind lane = replay::ReplayLaneKind::cpu_reference;
    std::string backend_id;
};

// Synchronous, non-owning orchestration over the backend-neutral SPI. The
// backend and all request storage belong to the caller; no device pointer or
// borrowed trace view escapes run().
class Runner final {
  public:
    Runner(IWorldBatchBackend &backend, RunnerConfig config);

    [[nodiscard]] RunResult run(const replay::ReplayTrace &trace);

  private:
    IWorldBatchBackend *backend_;
    RunnerConfig config_;
    bool poisoned_ = false;
};

} // namespace runtime::cuda_resident::full_window
