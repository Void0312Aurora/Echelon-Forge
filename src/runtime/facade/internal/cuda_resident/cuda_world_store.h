#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "runtime/contracts/cuda_resident_fixed_air_fixture_contract.h"
#include "runtime/contracts/cuda_resident_phase_b_fixture_contract.h"
#include "runtime/contracts/cuda_resident_phase_d_fixture_contract.h"

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
    std::size_t state_slot_bytes = 0;
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

// RB7 keeps the Phase-D projection in backend-private value types. The public
// InstrumentState/AgentObservation/RewardReport DTOs remain facade surfaces and
// are not copied into the resident device layout.
struct CudaWorldInstrumentState {
    double alt_baro_m = 0.0;
    double alt_radar_m = 0.0;
    double ias_mps = 0.0;
    double mach = 0.0;
    double vvi_mps = 0.0;
    double pitch_deg = 0.0;
    double roll_deg = 0.0;
    double heading_deg = 0.0;
    double aoa_deg = 0.0;
    double beta_deg = 0.0;
    double g_load_normal = 0.0;
    double g_load_axial = 0.0;
    double p_deg_s = 0.0;
    double q_deg_s = 0.0;
    double r_deg_s = 0.0;
    double engine_rpm_pct = 0.0;
    double fuel_flow_kg_h = 0.0;
    double throttle_pos = 0.0;
    double fuel_internal_kg = 0.0;
    double fuel_external_kg = 0.0;
    double gear_pos = 0.0;
    double flaps_pos = 0.0;
    double speedbrake_pos = 0.0;
};

struct CudaWorldObservationState {
    std::uint64_t id = 0;
    double sim_time = 0.0;
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    double vx = 0.0;
    double vy = 0.0;
    double vz = 0.0;
    double heading = 0.0;
    double pitch = 0.0;
    double roll = 0.0;
    double speed = 0.0;
    double health = 0.0;
    double gear_state = 0.0;
    double throttle = 0.0;
    double total_reward = 0.0;
};

struct CudaWorldRewardState {
    double survival_term = 0.0;
    double speed_term = 0.0;
    double total_reward = 0.0;
    std::uint64_t fact_snapshot_version = 0;
};

enum class CudaResidentTerminationCode : std::uint8_t {
    running = 0,
    nan_guard = 1,
    envelope_violation = 2,
};

struct CudaWorldTerminationState {
    bool terminated = false;
    bool truncated = false;
    CudaResidentTerminationCode reason_code = CudaResidentTerminationCode::running;
    std::uint64_t snapshot_version = 0;
};

struct CudaWorldPhaseDState {
    CudaWorldInstrumentState instrument{};
    CudaWorldObservationState observation{};
    CudaWorldRewardState reward{};
    CudaWorldTerminationState termination{};
    bool events_empty = true;
};

struct CudaWorldStoreDeviceObservationRaw {
    void *values = nullptr;
    void *ids = nullptr;
    std::size_t world_count = 0;
    std::size_t values_per_world = 0;
    std::uint64_t source_snapshot = 0;
};

struct CudaResidentDeviceObservationDescriptor {
    std::vector<std::uint64_t> output_shape;
    std::string dtype = "float32";
    std::size_t element_count = 0;
    std::uint64_t source_snapshot = 0;
    std::string sync_or_export_barrier = "export";
    std::string host_visible_availability = "host_snapshot_available";
    std::string diagnostics_label = "resident_phase_d";
    std::vector<std::string> consumer_constraints;
};

// The view owns an explicit D2D staging allocation through `lifetime`. A
// consumer must retain this value for its complete device call; raw pointers
// are never published through RuntimeCapabilities or host packets.
struct CudaResidentDeviceObservationView {
    std::shared_ptr<void> lifetime;
    const float *values = nullptr;
    const std::uint64_t *ids = nullptr;
    CudaResidentDeviceObservationDescriptor descriptor{};

    [[nodiscard]] bool valid() const noexcept {
        return lifetime != nullptr && values != nullptr && ids != nullptr &&
               descriptor.element_count != 0;
    }
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
    CudaWorldPhaseDState phase_d{};
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

// Instance-owned lifecycle plus the bounded RB5-RB7 fixed-air resident store.
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
    [[nodiscard]] bool export_device_observation_raw(CudaWorldStoreDeviceObservationRaw *raw,
                                                     std::string *error) const;
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

// Narrow, per-instance fault/readback seam for RB3-RB7 CUDA tests.
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
    [[nodiscard]] static CudaBarrierKernelResources phase_d_instruments_kernel_resources();
    [[nodiscard]] static CudaBarrierKernelResources phase_d_configuration_kernel_resources();
    [[nodiscard]] static CudaBarrierKernelResources phase_d_projection_kernel_resources();
    [[nodiscard]] static CudaBarrierKernelResources phase_d_pack_kernel_resources();
    [[nodiscard]] static CudaBarrierKernelResources phase_d_consumer_kernel_resources();
    [[nodiscard]] static bool
    consume_device_observation_view(const CudaResidentDeviceObservationView &view,
                                    std::vector<float> *first_values,
                                    std::vector<std::uint64_t> *ids);
};

} // namespace testing

} // namespace runtime::cuda_resident
