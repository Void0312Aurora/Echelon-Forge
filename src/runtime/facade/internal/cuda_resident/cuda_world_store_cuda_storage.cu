#include "runtime/facade/internal/cuda_resident/cuda_world_store_cuda_internal.cuh"
#include "runtime/contracts/cuda_resident_phase_a_fixture_contract.h"
#include "runtime/contracts/cuda_resident_phase_b_fixture_contract.h"

#include <algorithm>
#include <limits>
#include <memory>
#include <new>
#include <utility>
#include <vector>
namespace runtime::cuda_resident::detail {
bool checked_product(std::size_t left, std::size_t right, std::size_t *result) noexcept {
    if (result == nullptr ||
        (right != 0 && left > std::numeric_limits<std::size_t>::max() / right)) {
        return false;
    }
    *result = left * right;
    return true;
}

bool checked_add(std::size_t left, std::size_t right, std::size_t *result) noexcept {
    if (result == nullptr || left > std::numeric_limits<std::size_t>::max() - right) {
        return false;
    }
    *result = left + right;
    return true;
}

bool checked_align(std::size_t value, std::size_t alignment, std::size_t *result) noexcept {
    const std::size_t remainder = value % alignment;
    const std::size_t padding = remainder == 0 ? 0 : alignment - remainder;
    return checked_add(value, padding, result);
}

template <typename T>
bool append_array(std::size_t count, std::size_t *cursor, std::size_t *offset) noexcept {
    if (cursor == nullptr || offset == nullptr || !checked_align(*cursor, alignof(T), offset)) {
        return false;
    }
    std::size_t bytes = 0;
    return checked_product(count, sizeof(T), &bytes) && checked_add(*offset, bytes, cursor);
}

bool build_state_layout(std::size_t world_capacity, CudaWorldStateSlotLayout *layout) noexcept {
    if (layout == nullptr) {
        return false;
    }
    std::size_t cursor = 0;
    std::size_t kinematics_count = 0;
    std::size_t control_double_count = 0;
    std::size_t control_float_count = 0;
    std::size_t control_flag_count = 0;
    std::size_t prepared_double_count = 0;
    std::size_t prepared_flag_count = 0;
    std::size_t dynamics_count = 0;
    std::size_t phase_b_force_count = 0;
    std::size_t phase_d_instrument_count = 0;
    std::size_t phase_d_observation_count = 0;
    std::size_t phase_d_reward_count = 0;
    std::size_t shard_version_count = 0;
    if (!checked_product(world_capacity, kKinematicsFieldCount, &kinematics_count) ||
        !checked_product(world_capacity, kControlDoubleFieldCount, &control_double_count) ||
        !checked_product(world_capacity, kControlFloatFieldCount, &control_float_count) ||
        !checked_product(world_capacity, kControlFlagFieldCount, &control_flag_count) ||
        !checked_product(world_capacity, kPreparedDoubleFieldCount, &prepared_double_count) ||
        !checked_product(world_capacity, kPreparedFlagFieldCount, &prepared_flag_count) ||
        !checked_product(world_capacity, kDynamicsDoubleFieldCount, &dynamics_count) ||
        !checked_product(world_capacity, kPhaseBForceFieldCount, &phase_b_force_count) ||
        !checked_product(world_capacity, kPhaseDInstrumentFieldCount, &phase_d_instrument_count) ||
        !checked_product(world_capacity, kPhaseDObservationFieldCount, &phase_d_observation_count) ||
        !checked_product(world_capacity, kPhaseDRewardFieldCount, &phase_d_reward_count) ||
        !checked_product(world_capacity, kCudaResidentShardCount, &shard_version_count)) {
        return false;
    }
    if (!append_array<std::uint8_t>(world_capacity, &cursor, &layout->setup_complete) ||
        !append_array<std::uint64_t>(world_capacity, &cursor, &layout->entity_ids) ||
        !append_array<std::uint32_t>(world_capacity, &cursor, &layout->entity_generations) ||
        !append_array<double>(world_capacity, &cursor, &layout->time_steps) ||
        !append_array<double>(kinematics_count, &cursor, &layout->kinematics) ||
        !append_array<double>(dynamics_count, &cursor, &layout->dynamics) ||
        !append_array<double>(phase_b_force_count, &cursor, &layout->phase_b_forces) ||
        !append_array<double>(phase_d_instrument_count, &cursor, &layout->phase_d_instruments) ||
        !append_array<double>(phase_d_observation_count, &cursor, &layout->phase_d_observations) ||
        !append_array<std::uint64_t>(world_capacity, &cursor, &layout->phase_d_observation_ids) ||
        !append_array<double>(phase_d_reward_count, &cursor, &layout->phase_d_rewards) ||
        !append_array<std::uint64_t>(world_capacity, &cursor, &layout->phase_d_reward_versions) ||
        !append_array<std::uint8_t>(world_capacity, &cursor, &layout->phase_d_termination_flags) ||
        !append_array<std::uint8_t>(world_capacity, &cursor, &layout->phase_d_termination_codes) ||
        !append_array<std::uint8_t>(world_capacity, &cursor, &layout->phase_d_event_empty) ||
        !append_array<double>(control_double_count, &cursor, &layout->control_doubles) ||
        !append_array<float>(control_float_count, &cursor, &layout->control_floats) ||
        !append_array<std::uint8_t>(control_flag_count, &cursor, &layout->control_flags) ||
        !append_array<double>(prepared_double_count, &cursor, &layout->prepared_doubles) ||
        !append_array<std::uint8_t>(prepared_flag_count, &cursor, &layout->prepared_flags) ||
        !append_array<std::uint64_t>(world_capacity, &cursor, &layout->phase_versions) ||
        !append_array<std::uint64_t>(world_capacity, &cursor, &layout->clock_ticks) ||
        !append_array<double>(world_capacity, &cursor, &layout->simulation_times) ||
        !append_array<std::uint64_t>(world_capacity, &cursor, &layout->global_versions) ||
        !append_array<std::uint64_t>(world_capacity, &cursor, &layout->barrier_sequences) ||
        !append_array<std::uint8_t>(world_capacity, &cursor, &layout->barrier_codes) ||
        !append_array<std::uint64_t>(shard_version_count, &cursor, &layout->shard_versions) ||
        !checked_align(cursor, alignof(HostStateBlock), &layout->slot_bytes)) {
        return false;
    }
    return true;
}

bool cuda_world_store_runtime_available(std::string *error) {
    int device_count = 0;
    const cudaError_t status = cudaGetDeviceCount(&device_count);
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("cudaGetDeviceCount", status);
        }
        return false;
    }
    if (device_count <= 0) {
        if (error != nullptr) {
            *error = "cudaGetDeviceCount returned no CUDA devices";
        }
        return false;
    }
    if (error != nullptr) {
        error->clear();
    }
    return true;
}

CudaWorldStoreDeviceAllocationResult
allocate_cuda_world_store_metadata(std::size_t world_capacity,
                                   CudaWorldStoreDeviceFaultInjection *faults) {
    CudaWorldStoreDeviceAllocationResult result{};
    std::unique_ptr<CudaWorldStoreDeviceAllocation> allocation(
        new (std::nothrow) CudaWorldStoreDeviceAllocation{});
    if (!allocation) {
        result.error = "failed to allocate CUDA world store host owner";
        return result;
    }
    allocation->world_capacity = world_capacity;

    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_allocation)) {
        result.error = "injected CUDA world store allocation failure";
        return result;
    }
    if (!build_state_layout(world_capacity, &allocation->state_layout)) {
        result.error = "CUDA world store state layout size overflow";
        return result;
    }
    if (world_capacity == 0) {
        result.allocation = allocation.release();
        return result;
    }

    std::size_t lifecycle_count = 0;
    std::size_t lifecycle_bytes = 0;
    std::size_t state_base = 0;
    std::size_t state_bytes = 0;
    std::size_t status_offset = 0;
    std::size_t total_bytes = 0;
    if (!checked_product(world_capacity, 2, &lifecycle_count) ||
        !checked_product(lifecycle_count, sizeof(CudaWorldLifecycleRecord), &lifecycle_bytes) ||
        !checked_align(lifecycle_bytes, alignof(HostStateBlock), &state_base) ||
        !checked_product(allocation->state_layout.slot_bytes, 2, &state_bytes) ||
        !checked_add(state_base, state_bytes, &status_offset) ||
        !checked_align(status_offset, alignof(std::uint32_t), &status_offset) ||
        !checked_add(status_offset, sizeof(std::uint32_t), &total_bytes)) {
        result.error = "CUDA world store allocation byte total overflow";
        return result;
    }

    const cudaError_t status =
        cudaMalloc(reinterpret_cast<void **>(&allocation->storage), total_bytes);
    if (status != cudaSuccess) {
        result.error = cuda_error_message("cudaMalloc(resident_world_store)", status);
        return result;
    }
    allocation->storage_bytes = total_bytes;
    allocation->records = reinterpret_cast<CudaWorldLifecycleRecord *>(allocation->storage);
    allocation->state_slots[0] = allocation->storage + state_base;
    allocation->state_slots[1] = allocation->state_slots[0] + allocation->state_layout.slot_bytes;
    allocation->barrier_status =
        reinterpret_cast<std::uint32_t *>(allocation->storage + status_offset);
    result.device_bytes = total_bytes;
    result.state_slot_bytes = allocation->state_layout.slot_bytes;

    // No potentially-throwing operation follows the successful cudaMalloc;
    // ownership transfers directly into the opaque result.
    result.allocation = allocation.release();
    return result;
}

bool reset_cuda_world_store_metadata(CudaWorldStoreDeviceAllocation *allocation,
                                     const std::uint32_t *seeds, std::size_t world_capacity,
                                     std::uint64_t reset_generation,
                                     CudaWorldStoreDeviceFaultInjection *faults,
                                     std::string *error) {
    if (allocation == nullptr || allocation->world_capacity != world_capacity) {
        if (error != nullptr) {
            *error = "CUDA world store reset allocation/capacity mismatch";
        }
        return false;
    }
    if (world_capacity == 0) {
        allocation->active_lifecycle_slot ^= 1U;
        allocation->active_state_slot ^= 1U;
        if (error != nullptr) {
            error->clear();
        }
        return true;
    }

    std::vector<CudaWorldLifecycleRecord> next_records;
    try {
        next_records.resize(world_capacity);
    } catch (const std::bad_alloc &) {
        if (error != nullptr) {
            *error = "failed to allocate CUDA world store reset staging metadata";
        }
        return false;
    }
    for (std::size_t index = 0; index < world_capacity; ++index) {
        next_records[index].reset_generation = reset_generation;
        next_records[index].seed = seeds == nullptr ? 0 : seeds[index];
    }
    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_reset_copy)) {
        if (error != nullptr) {
            *error = "injected CUDA world store reset metadata copy failure";
        }
        return false;
    }

    const std::uint8_t next_lifecycle_slot = allocation->active_lifecycle_slot ^ 1U;
    const std::uint8_t next_state_slot = allocation->active_state_slot ^ 1U;
    CudaWorldLifecycleRecord *destination =
        allocation->records + (static_cast<std::size_t>(next_lifecycle_slot) * world_capacity);
    cudaError_t status =
        cudaMemcpy(destination, next_records.data(),
                   world_capacity * sizeof(CudaWorldLifecycleRecord), cudaMemcpyHostToDevice);
    if (status == cudaSuccess) {
        status = cudaMemset(allocation->state_slots[next_state_slot], 0,
                            allocation->state_layout.slot_bytes);
    }
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("reset resident world state", status);
        }
        return false;
    }

    allocation->active_lifecycle_slot = next_lifecycle_slot;
    allocation->active_state_slot = next_state_slot;
    if (error != nullptr) {
        error->clear();
    }
    return true;
}

bool read_cuda_world_store_metadata(const CudaWorldStoreDeviceAllocation *allocation,
                                    std::size_t world_capacity,
                                    CudaWorldStoreDeviceSnapshot *snapshot, std::string *error) {
    if (allocation == nullptr || allocation->world_capacity != world_capacity ||
        snapshot == nullptr) {
        if (error != nullptr) {
            *error = "CUDA world store readback allocation/capacity mismatch";
        }
        return false;
    }

    std::vector<CudaWorldLifecycleRecord> records(world_capacity);
    if (world_capacity != 0) {
        const CudaWorldLifecycleRecord *source =
            allocation->records +
            (static_cast<std::size_t>(allocation->active_lifecycle_slot) * world_capacity);
        const cudaError_t status =
            cudaMemcpy(records.data(), source, world_capacity * sizeof(CudaWorldLifecycleRecord),
                       cudaMemcpyDeviceToHost);
        if (status != cudaSuccess) {
            if (error != nullptr) {
                *error = cuda_error_message("read lifecycle metadata", status);
            }
            return false;
        }
    }

    CudaWorldStoreDeviceSnapshot next_snapshot;
    next_snapshot.seeds.reserve(world_capacity);
    next_snapshot.reset_generations.reserve(world_capacity);
    for (const CudaWorldLifecycleRecord &record : records) {
        next_snapshot.seeds.push_back(record.seed);
        next_snapshot.reset_generations.push_back(record.reset_generation);
    }
    *snapshot = std::move(next_snapshot);
    if (error != nullptr) {
        error->clear();
    }
    return true;
}

bool setup_cuda_world_store_fixed_air_fixture(CudaWorldStoreDeviceAllocation *allocation,
                                              const std::vector<CudaFixedAirWorldSetup> &setups,
                                              CudaWorldStoreDeviceFaultInjection *faults,
                                              std::string *error) {
    if (allocation == nullptr || setups.size() != allocation->world_capacity) {
        if (error != nullptr) {
            *error = "CUDA fixed-air setup count must equal world capacity";
        }
        return false;
    }
    for (std::size_t index = 0; index < setups.size(); ++index) {
        if (setups[index].world_index != index) {
            if (error != nullptr) {
                *error = "CUDA fixed-air setup worlds must be canonical and contiguous";
            }
            return false;
        }
    }
    if (allocation->world_capacity == 0) {
        allocation->active_state_slot ^= 1U;
        if (error != nullptr) {
            error->clear();
        }
        return true;
    }

    std::vector<HostStateBlock> host_slot = make_host_slot(allocation->state_layout.slot_bytes);
    auto *setup_complete =
        host_field<std::uint8_t>(host_slot, allocation->state_layout.setup_complete);
    auto *entity_ids = host_field<std::uint64_t>(host_slot, allocation->state_layout.entity_ids);
    auto *entity_generations =
        host_field<std::uint32_t>(host_slot, allocation->state_layout.entity_generations);
    auto *time_steps = host_field<double>(host_slot, allocation->state_layout.time_steps);
    auto *kinematics = host_field<double>(host_slot, allocation->state_layout.kinematics);
    auto *dynamics = host_field<double>(host_slot, allocation->state_layout.dynamics);
    auto *phase_b_forces = host_field<double>(host_slot, allocation->state_layout.phase_b_forces);
    auto *phase_d_instruments =
        host_field<double>(host_slot, allocation->state_layout.phase_d_instruments);
    auto *phase_d_observations =
        host_field<double>(host_slot, allocation->state_layout.phase_d_observations);
    auto *phase_d_observation_ids =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.phase_d_observation_ids);
    auto *phase_d_rewards = host_field<double>(host_slot, allocation->state_layout.phase_d_rewards);
    auto *phase_d_reward_versions =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.phase_d_reward_versions);
    auto *phase_d_termination_flags =
        host_field<std::uint8_t>(host_slot, allocation->state_layout.phase_d_termination_flags);
    auto *phase_d_termination_codes =
        host_field<std::uint8_t>(host_slot, allocation->state_layout.phase_d_termination_codes);
    auto *phase_d_event_empty =
        host_field<std::uint8_t>(host_slot, allocation->state_layout.phase_d_event_empty);
    auto *global_versions =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.global_versions);
    auto *barrier_sequences =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.barrier_sequences);
    auto *barrier_codes =
        host_field<std::uint8_t>(host_slot, allocation->state_layout.barrier_codes);
    auto *shard_versions =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.shard_versions);

    for (std::size_t world = 0; world < setups.size(); ++world) {
        const CudaFixedAirWorldSetup &setup = setups[world];
        setup_complete[world] = 1;
        entity_ids[world] = setup.entity_id;
        entity_generations[world] = setup.entity_generation;
        time_steps[world] = setup.time_step_s;
        const double values[kKinematicsFieldCount] = {
            setup.kinematics.x,       setup.kinematics.y,     setup.kinematics.z,
            setup.kinematics.vx,      setup.kinematics.vy,    setup.kinematics.vz,
            setup.kinematics.heading, setup.kinematics.pitch, setup.kinematics.roll,
        };
        for (std::size_t field = 0; field < kKinematicsFieldCount; ++field) {
            kinematics[field * setups.size() + world] = values[field];
        }
        for (std::size_t field = 0; field < kDynamicsDoubleFieldCount; ++field) {
            dynamics[field * setups.size() + world] = 0.0;
        }
        dynamics[kDynGearExtension * setups.size() + world] = 1.0;
        for (std::size_t field = 0; field < kPhaseBForceFieldCount; ++field) {
            phase_b_forces[field * setups.size() + world] = 0.0;
        }
        for (std::size_t field = 0; field < kPhaseDInstrumentFieldCount; ++field) {
            phase_d_instruments[field * setups.size() + world] = 0.0;
        }
        for (std::size_t field = 0; field < kPhaseDObservationFieldCount; ++field) {
            phase_d_observations[field * setups.size() + world] = 0.0;
        }
        phase_d_observation_ids[world] = setup.entity_id;
        for (std::size_t field = 0; field < kPhaseDRewardFieldCount; ++field) {
            phase_d_rewards[field * setups.size() + world] = 0.0;
        }
        phase_d_reward_versions[world] = 0;
        phase_d_termination_flags[world] = 0;
        phase_d_termination_codes[world] =
            static_cast<std::uint8_t>(CudaResidentTerminationCode::running);
        phase_d_event_empty[world] = 1;
        global_versions[world] = 1;
        barrier_sequences[world] = 1;
        barrier_codes[world] = static_cast<std::uint8_t>(CudaResidentBarrierCode::input_injection);
        for (CudaResidentShard shard :
             {CudaResidentShard::identity, CudaResidentShard::pilot_flight_controls,
              CudaResidentShard::clock, CudaResidentShard::snapshot, CudaResidentShard::kinematics,
              CudaResidentShard::dynamics, CudaResidentShard::episode}) {
            shard_versions[static_cast<std::size_t>(shard) * setups.size() + world] = 1;
        }
    }

    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_state_transfer)) {
        if (error != nullptr) {
            *error = "injected CUDA fixed-air setup transfer failure";
        }
        return false;
    }
    const std::uint8_t next_slot = allocation->active_state_slot ^ 1U;
    const cudaError_t status =
        cudaMemcpy(allocation->state_slots[next_slot], host_slot.data(),
                   allocation->state_layout.slot_bytes, cudaMemcpyHostToDevice);
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("upload fixed-air setup state", status);
        }
        return false;
    }
    allocation->active_state_slot = next_slot;
    if (error != nullptr) {
        error->clear();
    }
    return true;
}

bool inject_cuda_world_store_flight_controls(
    CudaWorldStoreDeviceAllocation *allocation,
    const std::vector<CudaWorldFlightControlAssignment> &assignments,
    CudaWorldStoreDeviceFaultInjection *faults, std::string *error) {
    if (allocation == nullptr || assignments.size() != allocation->world_capacity) {
        if (error != nullptr) {
            *error = "CUDA flight-control assignment count must equal world capacity";
        }
        return false;
    }
    for (std::size_t index = 0; index < assignments.size(); ++index) {
        if (assignments[index].world_index != index) {
            if (error != nullptr) {
                *error = "CUDA flight-control worlds must be canonical and contiguous";
            }
            return false;
        }
    }
    if (allocation->world_capacity == 0) {
        return commit_barrier(allocation, CudaResidentBarrierCode::input_injection, faults, error);
    }
    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_state_transfer)) {
        if (error != nullptr) {
            *error = "injected CUDA flight-control state transfer failure";
        }
        return false;
    }

    const std::uint8_t next_slot = allocation->active_state_slot ^ 1U;
    cudaError_t status = cudaMemcpy(allocation->state_slots[next_slot],
                                    allocation->state_slots[allocation->active_state_slot],
                                    allocation->state_layout.slot_bytes, cudaMemcpyDeviceToDevice);
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("copy state for flight-control injection", status);
        }
        return false;
    }

    std::vector<double> control_doubles(kControlDoubleFieldCount * assignments.size());
    std::vector<float> control_floats(kControlFloatFieldCount * assignments.size());
    std::vector<std::uint8_t> control_flags(kControlFlagFieldCount * assignments.size());
    for (std::size_t world = 0; world < assignments.size(); ++world) {
        const CudaWorldFlightControls &controls = assignments[world].controls;
        const double double_values[kControlDoubleFieldCount] = {
            controls.stick_pitch, controls.stick_roll, controls.rudder,
            controls.throttle,    controls.brake,
        };
        const float float_values[kControlFloatFieldCount] = {
            controls.gear_handle,
            controls.flaps,
            controls.speedbrake,
        };
        const std::uint8_t flag_values[kControlFlagFieldCount] = {
            static_cast<std::uint8_t>(controls.brake_left),
            static_cast<std::uint8_t>(controls.brake_right),
            static_cast<std::uint8_t>(controls.active),
        };
        for (std::size_t field = 0; field < kControlDoubleFieldCount; ++field) {
            control_doubles[field * assignments.size() + world] = double_values[field];
        }
        for (std::size_t field = 0; field < kControlFloatFieldCount; ++field) {
            control_floats[field * assignments.size() + world] = float_values[field];
        }
        for (std::size_t field = 0; field < kControlFlagFieldCount; ++field) {
            control_flags[field * assignments.size() + world] = flag_values[field];
        }
    }

    std::uint8_t *slot = allocation->state_slots[next_slot];
    status = cudaMemcpy(device_field<double>(slot, allocation->state_layout.control_doubles),
                        control_doubles.data(), control_doubles.size() * sizeof(double),
                        cudaMemcpyHostToDevice);
    if (status == cudaSuccess) {
        status = cudaMemcpy(device_field<float>(slot, allocation->state_layout.control_floats),
                            control_floats.data(), control_floats.size() * sizeof(float),
                            cudaMemcpyHostToDevice);
    }
    if (status == cudaSuccess) {
        status =
            cudaMemcpy(device_field<std::uint8_t>(slot, allocation->state_layout.control_flags),
                       control_flags.data(), control_flags.size() * sizeof(std::uint8_t),
                       cudaMemcpyHostToDevice);
    }
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("upload flight-control shard", status);
        }
        return false;
    }

    return finalize_staged_barrier(allocation, next_slot, CudaResidentBarrierCode::input_injection,
                                   faults, error);
}

bool release_cuda_world_store_metadata(CudaWorldStoreDeviceAllocation *&allocation,
                                       CudaWorldStoreDeviceFaultInjection *faults) noexcept {
    if (allocation == nullptr) {
        return true;
    }
    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_release)) {
        return false;
    }
    if (allocation->storage != nullptr) {
        if (cudaDeviceSynchronize() != cudaSuccess) {
            return false;
        }
        if (cudaFree(allocation->storage) != cudaSuccess) {
            return false;
        }
        allocation->storage = nullptr;
    }
    delete allocation;
    allocation = nullptr;
    return true;
}


} // namespace runtime::cuda_resident::detail
