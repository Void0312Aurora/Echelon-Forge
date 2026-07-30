#pragma once

#include <cstddef>
#include <string>
#include <string_view>
#include <vector>

#include "runtime/contracts/cuda_resident_selected_slice_contract.h"
#include "runtime/facade/internal/cuda_resident/cuda_world_store.h"
#include "runtime/facade/internal/world_batch_backend.h"

namespace runtime::cuda_resident {

namespace testing {
class CudaResidentBackendTestAccess;
}

inline constexpr std::string_view kCudaResidentRb4BackendId = "cuda_resident.rb4_state_shell";

struct CudaResidentBarrierEvidence {
    std::string barrier_id;
    std::vector<std::string> required_visible_shards;
    std::vector<std::string> materialized_shards;
    bool enabled = false;
    bool contract_satisfied = false;
    bool comparison_eligible = false;
    bool host_truth_available = false;
};

struct CudaResidentWorldSnapshot {
    WorldEntityRef entity_ref{};
    std::uint32_t seed = 0;
    std::uint64_t reset_generation = 0;
    DeviceClockContract clock{};
    SnapshotIdentityContract identity{};
    CudaWorldKinematicsState kinematics{};
    std::string source_barrier_id;
};

struct CudaResidentExportSnapshot {
    std::vector<CudaResidentWorldSnapshot> worlds;
    ExportEnvelopeContract envelope{};
    CudaResidentBarrierEvidence barrier{};
};

// RB4 fixed-air state/barrier shell. Only setup, selected pilot input, clock
// commit, and explicit minimal reconstruction are implemented; later phase
// semantics remain fail-closed until their owning iterations.
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
    void publish_stage();
    [[nodiscard]] bool partial_sync_commit();
    [[nodiscard]] CudaResidentExportSnapshot export_snapshot(const std::string &request_id) const;

  private:
    friend class testing::CudaResidentBackendTestAccess;

    [[noreturn]] static void reject_unimplemented_operation(const char *operation);

    CudaWorldStore store_;
    std::size_t worker_threads_ = 1;
};

namespace testing {

class CudaResidentBackendTestAccess final {
  public:
    [[nodiscard]] static CudaWorldStore &world_store(CudaResidentBackend &backend) noexcept;
};

} // namespace testing

} // namespace runtime::cuda_resident
