#pragma once

#include <cstddef>

#include "runtime/facade/internal/cuda_resident/cuda_world_store.h"
#include "runtime/facade/internal/world_batch_backend.h"

namespace runtime::cuda_resident {

// RB3 lifecycle shell. Semantic operations remain fail-closed until their
// owning iterations implement the complete bounded manifest.
class CudaResidentBackend final : public IWorldBatchBackend {
  public:
    CudaResidentBackend() = default;
    ~CudaResidentBackend() override = default;

    CudaResidentBackend(const CudaResidentBackend &) = delete;
    CudaResidentBackend &operator=(const CudaResidentBackend &) = delete;
    CudaResidentBackend(CudaResidentBackend &&) = delete;
    CudaResidentBackend &operator=(CudaResidentBackend &&) = delete;

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

    [[nodiscard]] CudaWorldStoreDiagnostics store_diagnostics() const;

  private:
    [[noreturn]] static void reject_unimplemented_operation(const char *operation);

    CudaWorldStore store_;
    std::size_t worker_threads_ = 1;
};

} // namespace runtime::cuda_resident
