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

inline constexpr std::string_view kCudaResidentControlPreparationBackendId =
    // internal-code: compatibility -- backend identity emitted by stored snapshots
    "cuda_resident.rb5_phase_a";
inline constexpr std::string_view kCudaResidentFlightDynamicsBackendId =
    // internal-code: compatibility -- backend identity emitted by stored snapshots
    "cuda_resident.rb6_phase_b";
inline constexpr std::string_view kCudaResidentObservationProjectionBackendId =
    // internal-code: compatibility -- backend identity emitted by stored snapshots
    "cuda_resident.rb7_phase_d";

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
    CudaWorldDynamicsState dynamics{};
    CudaWorldObservationProjectionState observation_projection{};
    std::string source_barrier_id;
};

struct CudaResidentExportSnapshot {
    std::vector<CudaResidentWorldSnapshot> worlds;
    ExportEnvelopeContract envelope{};
    CudaResidentBarrierEvidence barrier{};
};

// The fixed-air resident shell keeps observation-projection values backend-private;
// they are exposed only through explicit host reconstruction or a lease-scoped device view.
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
    [[nodiscard]] CudaResidentDeviceObservationView
    export_device_observation_view(const std::string &request_id) const;
    [[nodiscard]] device_consumer::AcquireResult
    acquire_device_observation_lease(const std::string &request_id) const;

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
