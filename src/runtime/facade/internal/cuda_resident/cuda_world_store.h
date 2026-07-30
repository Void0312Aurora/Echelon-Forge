#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "runtime/contracts/cuda_resident_fixed_air_fixture_contract.h"
#include "runtime/contracts/cuda_resident_phase_b_fixture_contract.h"

namespace runtime::cuda_resident {

class CudaResidentBackend;

namespace testing {
class CudaWorldStoreTestAccess;
}

enum class CudaWorldStoreState : std::uint8_t {
    unconfigured,
    ready,
    unavailable,
};

struct CudaWorldStoreDiagnostics {
    CudaWorldStoreState state = CudaWorldStoreState::unconfigured;
    bool compiled_with_cuda = false;
    bool runtime_available = false;
    std::size_t world_capacity = 0;
    std::size_t device_bytes = 0;
    std::uint64_t allocation_generation = 0;
    std::uint64_t reset_generation = 0;
    std::string last_error;
};

struct CudaWorldStoreLifecycleSnapshot {
    std::vector<std::uint32_t> seeds;
    std::vector<std::uint64_t> reset_generations;
};

struct CudaWorldKinematicsState {
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    double vx = 0.0;
    double vy = 0.0;
    double vz = 0.0;
    double heading = 0.0;
    double pitch = 0.0;
    double roll = 0.0;
};

struct CudaWorldFlightControls {
    double stick_pitch = 0.0;
    double stick_roll = 0.0;
    double rudder = 0.0;
    double throttle = 0.0;
    double brake = 0.0;
    float gear_handle = 0.0F;
    float flaps = 0.0F;
    float speedbrake = 0.0F;
    bool brake_left = false;
    bool brake_right = false;
    bool active = false;
};

struct CudaFixedAirWorldSetup {
    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
    std::uint32_t entity_generation = 0;
    double time_step_s = 0.0;
    CudaWorldKinematicsState kinematics{};
};

struct CudaWorldFlightControlAssignment {
    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
    CudaWorldFlightControls controls{};
};

struct CudaWorldPreparedControls {
    double stick_roll_filt = 0.0;
    double stick_pitch_filt = 0.0;
    double stick_yaw_filt = 0.0;
    double stick_yaw_cmd = 0.0;
    bool valid = false;
    bool manual_takeover = false;
    std::uint64_t phase_version = 0;
};

struct CudaWorldDynamicsState {
    // Body angular rates and realized control-surface positions.
    double p = 0.0;
    double q = 0.0;
    double r = 0.0;
    double elevator_pos = 0.0;
    double aileron_pos = 0.0;
    double rudder_pos = 0.0;
    // Propulsion spool state.
    double throttle_state = 0.0;
    double dry_thrust_state_n = 0.0;
    double ab_state = 0.0;
    double current_thrust_n = 0.0;
    // Cached aerodynamic state used by the next control pass.
    double dynamic_pressure = 0.0;
    double angle_of_attack = 0.0;
    double angle_of_attack_rate_dps = 0.0;
    double previous_angle_of_attack = 0.0;
    double sideslip_angle = 0.0;
    double mach_number = 0.0;
    double lift_coefficient = 0.0;
    double drag_coefficient = 0.0;
    double stall_progress = 0.0;
    double gear_extension = 1.0;
};

struct CudaWorldResidentState {
    std::uint64_t world_index = 0;
    std::uint32_t seed = 0;
    std::uint64_t reset_generation = 0;
    bool setup_complete = false;
    std::uint64_t entity_id = 0;
    std::uint32_t entity_generation = 0;
    double time_step_s = 0.0;
    CudaWorldKinematicsState kinematics{};
    CudaWorldDynamicsState dynamics{};
    CudaWorldFlightControls controls{};
    CudaWorldPreparedControls prepared_controls{};
    std::uint64_t clock_tick = 0;
    double simulation_time_s = 0.0;
    std::uint64_t global_version = 0;
    std::uint64_t barrier_sequence = 0;
    CudaResidentBarrierCode barrier = CudaResidentBarrierCode::none;
    std::array<std::uint64_t, kCudaResidentShardCount> shard_versions{};
};

struct CudaWorldStoreStateSnapshot {
    std::vector<CudaWorldResidentState> worlds;
};

struct CudaBarrierKernelResources {
    int registers_per_thread = 0;
    std::size_t local_bytes_per_thread = 0;
    std::size_t static_shared_bytes = 0;
    int threads_per_block = 0;
    int active_blocks_per_multiprocessor = 0;
    int active_warps_per_multiprocessor = 0;
    double theoretical_occupancy = 0.0;
};

// Instance-owned lifecycle plus the bounded RB5/RB6 fixed-air resident store.
// Phase D remains absent until its owning iteration.
class CudaWorldStore final {
  public:
    CudaWorldStore();
    ~CudaWorldStore();

    CudaWorldStore(const CudaWorldStore &) = delete;
    CudaWorldStore &operator=(const CudaWorldStore &) = delete;
    CudaWorldStore(CudaWorldStore &&) = delete;
    CudaWorldStore &operator=(CudaWorldStore &&) = delete;

    [[nodiscard]] static bool compiled_with_cuda() noexcept;
    [[nodiscard]] bool configure(std::size_t world_capacity);
    [[nodiscard]] bool reset(const std::vector<std::uint32_t> &seeds);
    [[nodiscard]] bool setup_fixed_air_fixture(std::vector<CudaFixedAirWorldSetup> *setups);
    [[nodiscard]] bool
    inject_flight_controls(const std::vector<CudaWorldFlightControlAssignment> &assignments);
    [[nodiscard]] bool publish_stage();
    [[nodiscard]] bool partial_sync_commit();
    [[nodiscard]] bool commit_window();
    [[nodiscard]] bool teardown() noexcept;

    [[nodiscard]] CudaWorldStoreDiagnostics diagnostics() const;
    [[nodiscard]] std::size_t world_capacity() const noexcept;

  private:
    friend class CudaResidentBackend;
    friend class testing::CudaWorldStoreTestAccess;

    [[nodiscard]] CudaWorldStoreStateSnapshot state_snapshot() const;

    struct Impl;
    std::unique_ptr<Impl> impl_;
};

namespace testing {

// Narrow, per-instance fault/readback seam for RB3-RB6 CUDA tests.
// It is not a runtime capability and is never surfaced by RuntimeFacade.
class CudaWorldStoreTestAccess final {
  public:
    static void fail_next_allocation(CudaWorldStore &store) noexcept;
    static void fail_next_reset_copy(CudaWorldStore &store) noexcept;
    static void fail_next_release(CudaWorldStore &store) noexcept;
    static void fail_next_state_transfer(CudaWorldStore &store) noexcept;
    static void fail_next_barrier_commit(CudaWorldStore &store) noexcept;
    static void set_allocation_generation(CudaWorldStore &store, std::uint64_t generation) noexcept;
    static void set_reset_generation(CudaWorldStore &store, std::uint64_t generation) noexcept;
    [[nodiscard]] static CudaWorldStoreLifecycleSnapshot readback(const CudaWorldStore &store);
    [[nodiscard]] static CudaWorldStoreStateSnapshot read_state(const CudaWorldStore &store);
    [[nodiscard]] static CudaBarrierKernelResources barrier_kernel_resources();
    [[nodiscard]] static CudaBarrierKernelResources phase_a_kernel_resources();
    [[nodiscard]] static CudaBarrierKernelResources phase_b_forces_kernel_resources();
    [[nodiscard]] static CudaBarrierKernelResources phase_b_aerodynamics_kernel_resources();
    [[nodiscard]] static CudaBarrierKernelResources phase_b_integrate_kernel_resources();
};

} // namespace testing

} // namespace runtime::cuda_resident
