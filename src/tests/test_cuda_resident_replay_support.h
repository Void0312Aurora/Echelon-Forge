#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

#include "runtime/contracts/cuda_resident_replay_contract.h"
#include "runtime/facade/internal/cuda_resident/cuda_resident_backend.h"

namespace runtime::cuda_resident::replay::test_support {

struct ProjectedWorld {
    WorldEntityRef ref{};
    DeviceClockContract clock{};
    SnapshotIdentityContract snapshot{};
    runtime::backend::EntityKinematics kinematics{};
    InstrumentState instrument{};
    AgentObservation observation{};
    double survival_reward = 0.0;
    double speed_reward = 0.0;
    double total_reward = 0.0;
    std::uint64_t reward_snapshot_version = 0;
    bool terminated = false;
    bool truncated = false;
    std::string termination_reason;
    std::string termination_reason_source;
    std::uint64_t termination_snapshot_version = 0;
    ExportEnvelopeContract envelope{};
};

[[nodiscard]] ReplayLaneFrame make_input_frame(const ReplayTrace &trace, std::size_t window,
                                               const std::vector<std::uint64_t> &entity_ids);

[[nodiscard]] ReplayLaneFrame make_projection_frame(const ReplayTrace &trace, std::size_t window,
                                                    std::string_view barrier_id,
                                                    const std::vector<ProjectedWorld> &worlds);

[[nodiscard]] ProjectedWorld project_cuda_state(const CudaWorldResidentState &state,
                                                std::size_t window, std::string_view barrier_id,
                                                std::string_view request_id);

[[nodiscard]] ProjectedWorld project_cuda_snapshot(const CudaResidentWorldSnapshot &snapshot,
                                                   const ExportEnvelopeContract &envelope,
                                                   std::size_t window, std::string_view request_id);

[[nodiscard]] ProjectedWorld project_cpu_oracle(const ReplayTrace &trace, std::size_t world,
                                                std::uint64_t entity_id, std::size_t window,
                                                std::string_view barrier_id,
                                                std::string_view request_id);

[[nodiscard]] ReplayLaneResult run_cpu_reference(const ReplayTrace &trace);
[[nodiscard]] ReplayLaneResult run_cuda_resident(const ReplayTrace &trace);
[[nodiscard]] ReplayTrace make_trace();

} // namespace runtime::cuda_resident::replay::test_support
