#pragma once

#include <cstddef>

#include "runtime/facade/internal/world_batch_backend.h"
#include "runtime/facade/internal/world_batch_compatibility_port.h"
#include "runtime/facade/runtime_facade_internal.h"

// CPU reference adapter. Composition preserves WorldBatchRuntime's existing
// layout/compatibility ABI and makes all translation into the semantic backend
// contract explicit at one internal boundary.
class FlecsCpuBackend final : public IWorldBatchBackend, public IWorldBatchCompatibilityPort {
  public:
    explicit FlecsCpuBackend(std::size_t world_count = 0);

    runtime::backend::Configuration configuration() const noexcept override;
    void configure(const runtime::backend::ConfigureRequest &request) override;
    runtime::backend::ContentResult
    load_content(const runtime::backend::ContentRequest &request) override;
    void reset(const runtime::backend::ResetRequest &request) override;
    runtime::backend::SetupResult setup(const runtime::backend::SetupRequest &request) override;
    runtime::backend::InputResult inject(const runtime::backend::InputBatch &input) override;
    runtime::backend::EvaluationResult
    evaluate(const runtime::backend::EvaluationRequest &request) const override;
    runtime::backend::AdvanceResult
    advance(const runtime::backend::AdvanceRequest &request) override;
    runtime::backend::ExportResult
    export_state(const runtime::backend::ExportRequest &request) const override;
    runtime::backend::Diagnostics diagnostics() const override;

    const IWorldBatchCompatibilityPort *compatibility_port() const noexcept override {
        return this;
    }

    std::vector<std::vector<std::uint64_t>>
    get_sensor_candidate_ids_batch(const std::vector<WorldEntityRef> &refs,
                                   bool use_gpu) const override;
    std::vector<std::vector<std::uint64_t>>
    get_visual_candidate_ids_batch(const std::vector<WorldEntityRef> &refs, double range_m,
                                   bool use_gpu) const override;
    std::vector<std::vector<std::uint64_t>>
    get_comm_candidate_ids_batch(const std::vector<WorldEntityRef> &refs,
                                 bool use_gpu) const override;
    std::vector<WorldBatchVisualBindingCompatibilityScene>
    collect_visual_binding_compatibility_scenes_from_candidate_ids_batch(
        const std::vector<WorldEntityRef> &refs, int downsample,
        const std::vector<std::vector<std::uint64_t>> &candidate_ids_batch) const override;

  private:
    WorldBatchRuntime runtime_;
};
