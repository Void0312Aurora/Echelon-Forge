#pragma once

#include "runtime/facade/internal/cuda_resident/cuda_world_store_device_api.h"

#include <cuda_runtime_api.h>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <memory>
#include <string>
#include <vector>

namespace runtime::cuda_resident::detail {

struct alignas(16) CudaWorldLifecycleRecord {
    std::uint64_t reset_generation = 0;
    std::uint32_t seed = 0;
    std::uint32_t reserved = 0;
};

struct alignas(16) HostStateBlock {
    std::byte bytes[16];
};

static_assert(sizeof(CudaWorldLifecycleRecord) == 16);
static_assert(sizeof(HostStateBlock) == 16);

inline constexpr std::size_t kKinematicsFieldCount = 9;
inline constexpr std::size_t kControlDoubleFieldCount = 5;
inline constexpr std::size_t kControlFloatFieldCount = 3;
inline constexpr std::size_t kControlFlagFieldCount = 3;
inline constexpr std::size_t kPreparedDoubleFieldCount = 4;
inline constexpr std::size_t kPreparedFlagFieldCount = 2;
inline constexpr std::size_t kDynamicsDoubleFieldCount = 20;
inline constexpr std::size_t kPhaseBForceFieldCount = 6;
inline constexpr std::size_t kPhaseDInstrumentFieldCount = 23;
inline constexpr std::size_t kPhaseDObservationFieldCount = 15;
inline constexpr std::size_t kPhaseDRewardFieldCount = 3;

struct CudaWorldStateSlotLayout {
    std::size_t setup_complete = 0;
    std::size_t entity_ids = 0;
    std::size_t entity_generations = 0;
    std::size_t time_steps = 0;
    std::size_t kinematics = 0;
    std::size_t dynamics = 0;
    std::size_t phase_b_forces = 0;
    std::size_t phase_d_instruments = 0;
    std::size_t phase_d_observations = 0;
    std::size_t phase_d_observation_ids = 0;
    std::size_t phase_d_rewards = 0;
    std::size_t phase_d_reward_versions = 0;
    std::size_t phase_d_termination_flags = 0;
    std::size_t phase_d_termination_codes = 0;
    std::size_t phase_d_event_empty = 0;
    std::size_t control_doubles = 0;
    std::size_t control_floats = 0;
    std::size_t control_flags = 0;
    std::size_t prepared_doubles = 0;
    std::size_t prepared_flags = 0;
    std::size_t phase_versions = 0;
    std::size_t clock_ticks = 0;
    std::size_t simulation_times = 0;
    std::size_t global_versions = 0;
    std::size_t barrier_sequences = 0;
    std::size_t barrier_codes = 0;
    std::size_t shard_versions = 0;
    std::size_t slot_bytes = 0;
};

enum PhaseBDynamicsField : std::size_t {
    kDynP = 0,
    kDynQ,
    kDynR,
    kDynElevatorPos,
    kDynAileronPos,
    kDynRudderPos,
    kDynThrottleState,
    kDynDryThrustState,
    kDynAbState,
    kDynCurrentThrust,
    kDynDynamicPressure,
    kDynAlpha,
    kDynAlphaRate,
    kDynPreviousAlpha,
    kDynBeta,
    kDynMach,
    kDynLiftCoefficient,
    kDynDragCoefficient,
    kDynStallProgress,
    kDynGearExtension,
};

enum PhaseBForceField : std::size_t {
    kForceX = 0,
    kForceY,
    kForceZ,
    kTorqueRoll,
    kTorquePitch,
    kTorqueYaw,
};

enum PhaseDInstrumentField : std::size_t {
    kInstAltBaro = 0,
    kInstAltRadar,
    kInstIas,
    kInstMach,
    kInstVvi,
    kInstPitch,
    kInstRoll,
    kInstHeading,
    kInstAoa,
    kInstBeta,
    kInstGNormal,
    kInstGAxial,
    kInstP,
    kInstQ,
    kInstR,
    kInstEngineRpm,
    kInstFuelFlow,
    kInstThrottle,
    kInstFuelInternal,
    kInstFuelExternal,
    kInstGear,
    kInstFlaps,
    kInstSpeedbrake,
};

enum PhaseDObservationField : std::size_t {
    kObsSimTime = 0,
    kObsX,
    kObsY,
    kObsZ,
    kObsVx,
    kObsVy,
    kObsVz,
    kObsHeading,
    kObsPitch,
    kObsRoll,
    kObsSpeed,
    kObsHealth,
    kObsGear,
    kObsThrottle,
    kObsTotalReward,
};

enum PhaseDRewardField : std::size_t {
    kRewardSurvival = 0,
    kRewardSpeed,
    kRewardTotal,
};

struct CudaWorldStoreDeviceAllocation {
    std::uint8_t *storage = nullptr;
    std::size_t storage_bytes = 0;
    CudaWorldLifecycleRecord *records = nullptr;
    std::uint8_t *state_slots[2] = {nullptr, nullptr};
    std::uint32_t *barrier_status = nullptr;
    CudaWorldStateSlotLayout state_layout{};
    std::size_t world_capacity = 0;
    std::uint8_t active_lifecycle_slot = 0;
    std::uint8_t active_state_slot = 0;
};

inline std::string cuda_error_message(const char *operation, cudaError_t status) {
    return std::string(operation) + ": " + cudaGetErrorString(status);
}

inline bool consume_fault(bool *fault) noexcept {
    if (fault == nullptr || !*fault) {
        return false;
    }
    *fault = false;
    return true;
}

template <typename T>
inline T *host_field(std::vector<HostStateBlock> &storage, std::size_t offset) {
    return reinterpret_cast<T *>(reinterpret_cast<std::byte *>(storage.data()) + offset);
}

template <typename T>
inline const T *host_field(const std::vector<HostStateBlock> &storage, std::size_t offset) {
    return reinterpret_cast<const T *>(reinterpret_cast<const std::byte *>(storage.data()) +
                                       offset);
}

inline std::vector<HostStateBlock> make_host_slot(std::size_t slot_bytes) {
    return std::vector<HostStateBlock>((slot_bytes + sizeof(HostStateBlock) - 1) /
                                       sizeof(HostStateBlock));
}

template <typename T>
inline T *device_field(std::uint8_t *slot_base, std::size_t offset) noexcept {
    return reinterpret_cast<T *>(slot_base + offset);
}

template <typename T>
inline const T *device_field(const std::uint8_t *slot_base, std::size_t offset) noexcept {
    return reinterpret_cast<const T *>(slot_base + offset);
}

__device__ inline bool increment_would_overflow(std::uint64_t value) {
    return value == ~std::uint64_t{0};
}

[[nodiscard]] bool build_state_layout(std::size_t world_capacity,
                                      CudaWorldStateSlotLayout *layout) noexcept;

[[nodiscard]] bool finalize_staged_barrier(CudaWorldStoreDeviceAllocation *allocation,
                                           std::uint8_t next_slot,
                                           CudaResidentBarrierCode barrier,
                                           CudaWorldStoreDeviceFaultInjection *faults,
                                           std::string *error);
[[nodiscard]] bool commit_barrier(CudaWorldStoreDeviceAllocation *allocation,
                                  CudaResidentBarrierCode barrier,
                                  CudaWorldStoreDeviceFaultInjection *faults,
                                  std::string *error);
[[nodiscard]] bool commit_phase_a_stage(CudaWorldStoreDeviceAllocation *allocation,
                                        CudaWorldStoreDeviceFaultInjection *faults,
                                        std::string *error);
[[nodiscard]] bool commit_phase_b_window(CudaWorldStoreDeviceAllocation *allocation,
                                         CudaWorldStoreDeviceFaultInjection *faults,
                                         std::string *error);

[[nodiscard]] cudaError_t launch_phase_b_forces(CudaWorldStoreDeviceAllocation *allocation,
                                                std::uint8_t slot) noexcept;
[[nodiscard]] cudaError_t launch_phase_b_aerodynamics(
    CudaWorldStoreDeviceAllocation *allocation, std::uint8_t slot) noexcept;
[[nodiscard]] cudaError_t launch_phase_b_integrate(CudaWorldStoreDeviceAllocation *allocation,
                                                   std::uint8_t slot) noexcept;
[[nodiscard]] cudaError_t launch_phase_d_instruments(
    CudaWorldStoreDeviceAllocation *allocation, std::uint8_t slot) noexcept;
[[nodiscard]] cudaError_t launch_phase_d_configuration(
    CudaWorldStoreDeviceAllocation *allocation, std::uint8_t slot) noexcept;
[[nodiscard]] cudaError_t launch_phase_d_episode(CudaWorldStoreDeviceAllocation *allocation,
                                                 std::uint8_t slot) noexcept;

template <typename Kernel>
bool query_phase_b_kernel_resources(Kernel kernel, const char *name,
                                    CudaBarrierKernelResources *resources, std::string *error) {
    if (resources == nullptr) {
        if (error != nullptr)
            *error = std::string("CUDA ") + name + " resource query requires an output";
        return false;
    }
    cudaFuncAttributes attributes{};
    cudaError_t status = cudaFuncGetAttributes(&attributes, kernel);
    if (status != cudaSuccess) {
        if (error != nullptr) *error = cuda_error_message(name, status);
        return false;
    }
    constexpr int threads_per_block = 128;
    int active_blocks = 0;
    status =
        cudaOccupancyMaxActiveBlocksPerMultiprocessor(&active_blocks, kernel, threads_per_block, 0);
    if (status != cudaSuccess) {
        if (error != nullptr) *error = cuda_error_message("query Phase B active blocks", status);
        return false;
    }
    int device = 0;
    cudaDeviceProp properties{};
    status = cudaGetDevice(&device);
    if (status == cudaSuccess) status = cudaGetDeviceProperties(&properties, device);
    if (status != cudaSuccess || properties.warpSize <= 0 ||
        properties.maxThreadsPerMultiProcessor <= 0) {
        if (error != nullptr) {
            *error = status == cudaSuccess
                         ? "CUDA device returned invalid Phase B occupancy properties"
                         : cuda_error_message("query CUDA Phase B occupancy properties", status);
        }
        return false;
    }
    *resources = CudaBarrierKernelResources{
        .registers_per_thread = attributes.numRegs,
        .local_bytes_per_thread = attributes.localSizeBytes,
        .static_shared_bytes = attributes.sharedSizeBytes,
        .threads_per_block = threads_per_block,
        .active_blocks_per_multiprocessor = active_blocks,
        .active_warps_per_multiprocessor =
            active_blocks * (threads_per_block / properties.warpSize),
        .theoretical_occupancy = static_cast<double>(active_blocks * threads_per_block) /
                                 static_cast<double>(properties.maxThreadsPerMultiProcessor),
    };
    if (error != nullptr) error->clear();
    return true;
}

} // namespace runtime::cuda_resident::detail
