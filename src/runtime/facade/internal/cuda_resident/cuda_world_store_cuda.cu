#include "runtime/facade/internal/cuda_resident/cuda_world_store_device_api.h"

#include <cuda_runtime_api.h>

#include <cmath>
#include <cstddef>
#include <limits>
#include <memory>
#include <new>
#include <utility>
#include <vector>

namespace runtime::cuda_resident::detail {

namespace {

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

struct CudaWorldStateSlotLayout {
    std::size_t setup_complete = 0;
    std::size_t entity_ids = 0;
    std::size_t entity_generations = 0;
    std::size_t time_steps = 0;
    std::size_t kinematics = 0;
    std::size_t control_doubles = 0;
    std::size_t control_floats = 0;
    std::size_t control_flags = 0;
    std::size_t clock_ticks = 0;
    std::size_t simulation_times = 0;
    std::size_t global_versions = 0;
    std::size_t barrier_sequences = 0;
    std::size_t barrier_codes = 0;
    std::size_t shard_versions = 0;
    std::size_t slot_bytes = 0;
};

std::string cuda_error_message(const char *operation, cudaError_t status) {
    return std::string(operation) + ": " + cudaGetErrorString(status);
}

bool consume_fault(bool *fault) noexcept {
    if (fault == nullptr || !*fault) {
        return false;
    }
    *fault = false;
    return true;
}

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
    std::size_t shard_version_count = 0;
    if (!checked_product(world_capacity, kKinematicsFieldCount, &kinematics_count) ||
        !checked_product(world_capacity, kControlDoubleFieldCount, &control_double_count) ||
        !checked_product(world_capacity, kControlFloatFieldCount, &control_float_count) ||
        !checked_product(world_capacity, kControlFlagFieldCount, &control_flag_count) ||
        !checked_product(world_capacity, kCudaResidentShardCount, &shard_version_count)) {
        return false;
    }
    if (!append_array<std::uint8_t>(world_capacity, &cursor, &layout->setup_complete) ||
        !append_array<std::uint64_t>(world_capacity, &cursor, &layout->entity_ids) ||
        !append_array<std::uint32_t>(world_capacity, &cursor, &layout->entity_generations) ||
        !append_array<double>(world_capacity, &cursor, &layout->time_steps) ||
        !append_array<double>(kinematics_count, &cursor, &layout->kinematics) ||
        !append_array<double>(control_double_count, &cursor, &layout->control_doubles) ||
        !append_array<float>(control_float_count, &cursor, &layout->control_floats) ||
        !append_array<std::uint8_t>(control_flag_count, &cursor, &layout->control_flags) ||
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

template <typename T> T *host_field(std::vector<HostStateBlock> &storage, std::size_t offset) {
    return reinterpret_cast<T *>(reinterpret_cast<std::byte *>(storage.data()) + offset);
}

template <typename T>
const T *host_field(const std::vector<HostStateBlock> &storage, std::size_t offset) {
    return reinterpret_cast<const T *>(reinterpret_cast<const std::byte *>(storage.data()) +
                                       offset);
}

std::vector<HostStateBlock> make_host_slot(std::size_t slot_bytes) {
    return std::vector<HostStateBlock>((slot_bytes + sizeof(HostStateBlock) - 1) /
                                       sizeof(HostStateBlock));
}

template <typename T> T *device_field(std::uint8_t *slot_base, std::size_t offset) noexcept {
    return reinterpret_cast<T *>(slot_base + offset);
}

template <typename T>
const T *device_field(const std::uint8_t *slot_base, std::size_t offset) noexcept {
    return reinterpret_cast<const T *>(slot_base + offset);
}

__device__ bool increment_would_overflow(std::uint64_t value) {
    return value == ~std::uint64_t{0};
}

__global__ void apply_barrier_kernel(std::size_t world_capacity, CudaResidentBarrierCode barrier,
                                     double *simulation_times, const double *time_steps,
                                     std::uint64_t *clock_ticks, std::uint64_t *global_versions,
                                     std::uint64_t *barrier_sequences, std::uint8_t *barrier_codes,
                                     std::uint64_t *shard_versions, std::uint32_t *status) {
    const std::size_t world_index = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (world_index >= world_capacity) {
        return;
    }

    const bool mutates_snapshot = barrier != CudaResidentBarrierCode::stage_publish;
    bool overflow = increment_would_overflow(barrier_sequences[world_index]);
    if (mutates_snapshot) {
        overflow = overflow || increment_would_overflow(global_versions[world_index]);
    }
    if (barrier == CudaResidentBarrierCode::window_commit) {
        overflow = overflow || increment_would_overflow(clock_ticks[world_index]) ||
                   !isfinite(simulation_times[world_index] + time_steps[world_index]);
    }

    const std::size_t identity_index =
        static_cast<std::size_t>(CudaResidentShard::identity) * world_capacity + world_index;
    const std::size_t controls_index =
        static_cast<std::size_t>(CudaResidentShard::pilot_flight_controls) * world_capacity +
        world_index;
    const std::size_t clock_index =
        static_cast<std::size_t>(CudaResidentShard::clock) * world_capacity + world_index;
    const std::size_t snapshot_index =
        static_cast<std::size_t>(CudaResidentShard::snapshot) * world_capacity + world_index;
    const std::size_t kinematics_index =
        static_cast<std::size_t>(CudaResidentShard::kinematics) * world_capacity + world_index;
    if (barrier == CudaResidentBarrierCode::input_injection) {
        overflow = overflow || increment_would_overflow(shard_versions[identity_index]) ||
                   increment_would_overflow(shard_versions[controls_index]);
    } else if (barrier == CudaResidentBarrierCode::window_commit) {
        overflow = overflow || increment_would_overflow(shard_versions[identity_index]) ||
                   increment_would_overflow(shard_versions[clock_index]) ||
                   increment_would_overflow(shard_versions[snapshot_index]) ||
                   increment_would_overflow(shard_versions[kinematics_index]);
    }
    if (overflow) {
        atomicExch(status, 1U);
        return;
    }

    ++barrier_sequences[world_index];
    barrier_codes[world_index] = static_cast<std::uint8_t>(barrier);
    if (!mutates_snapshot) {
        return;
    }
    ++global_versions[world_index];
    if (barrier == CudaResidentBarrierCode::input_injection) {
        ++shard_versions[identity_index];
        ++shard_versions[controls_index];
        return;
    }

    ++clock_ticks[world_index];
    simulation_times[world_index] += time_steps[world_index];
    ++shard_versions[identity_index];
    ++shard_versions[clock_index];
    ++shard_versions[snapshot_index];
    ++shard_versions[kinematics_index];
}

} // namespace

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

namespace {

bool finalize_staged_barrier(CudaWorldStoreDeviceAllocation *allocation, std::uint8_t next_slot,
                             CudaResidentBarrierCode barrier,
                             CudaWorldStoreDeviceFaultInjection *faults, std::string *error) {
    if (allocation == nullptr) {
        if (error != nullptr) {
            *error = "CUDA world store barrier requires an allocation";
        }
        return false;
    }
    if (allocation->world_capacity == 0) {
        allocation->active_state_slot = next_slot;
        if (error != nullptr) {
            error->clear();
        }
        return true;
    }
    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_barrier_commit)) {
        if (error != nullptr) {
            *error = "injected CUDA world store barrier commit failure";
        }
        return false;
    }

    cudaError_t status = cudaMemset(allocation->barrier_status, 0, sizeof(std::uint32_t));
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("clear resident barrier status", status);
        }
        return false;
    }
    constexpr unsigned int threads = 128;
    const unsigned int blocks =
        static_cast<unsigned int>((allocation->world_capacity + threads - 1) / threads);
    std::uint8_t *slot = allocation->state_slots[next_slot];
    apply_barrier_kernel<<<blocks, threads>>>(
        allocation->world_capacity, barrier,
        device_field<double>(slot, allocation->state_layout.simulation_times),
        device_field<double>(slot, allocation->state_layout.time_steps),
        device_field<std::uint64_t>(slot, allocation->state_layout.clock_ticks),
        device_field<std::uint64_t>(slot, allocation->state_layout.global_versions),
        device_field<std::uint64_t>(slot, allocation->state_layout.barrier_sequences),
        device_field<std::uint8_t>(slot, allocation->state_layout.barrier_codes),
        device_field<std::uint64_t>(slot, allocation->state_layout.shard_versions),
        allocation->barrier_status);
    status = cudaGetLastError();
    if (status == cudaSuccess) {
        status = cudaDeviceSynchronize();
    }
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("commit resident barrier", status);
        }
        return false;
    }
    std::uint32_t barrier_status = 0;
    status = cudaMemcpy(&barrier_status, allocation->barrier_status, sizeof(barrier_status),
                        cudaMemcpyDeviceToHost);
    if (status != cudaSuccess || barrier_status != 0) {
        if (error != nullptr) {
            *error = status == cudaSuccess
                         ? "CUDA world store barrier version/clock overflow"
                         : cuda_error_message("read resident barrier status", status);
        }
        return false;
    }

    allocation->active_state_slot = next_slot;
    if (error != nullptr) {
        error->clear();
    }
    return true;
}

bool commit_barrier(CudaWorldStoreDeviceAllocation *allocation, CudaResidentBarrierCode barrier,
                    CudaWorldStoreDeviceFaultInjection *faults, std::string *error) {
    if (allocation == nullptr) {
        if (error != nullptr) {
            *error = "CUDA world store barrier requires an allocation";
        }
        return false;
    }
    const std::uint8_t next_slot = allocation->active_state_slot ^ 1U;
    if (allocation->world_capacity == 0) {
        return finalize_staged_barrier(allocation, next_slot, barrier, faults, error);
    }
    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_state_transfer)) {
        if (error != nullptr) {
            *error = "injected CUDA world store state transfer failure";
        }
        return false;
    }
    const cudaError_t status = cudaMemcpy(
        allocation->state_slots[next_slot], allocation->state_slots[allocation->active_state_slot],
        allocation->state_layout.slot_bytes, cudaMemcpyDeviceToDevice);
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("copy resident state to inactive slot", status);
        }
        return false;
    }
    return finalize_staged_barrier(allocation, next_slot, barrier, faults, error);
}

} // namespace

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
        global_versions[world] = 1;
        barrier_sequences[world] = 1;
        barrier_codes[world] = static_cast<std::uint8_t>(CudaResidentBarrierCode::input_injection);
        for (CudaResidentShard shard :
             {CudaResidentShard::identity, CudaResidentShard::pilot_flight_controls,
              CudaResidentShard::clock, CudaResidentShard::snapshot,
              CudaResidentShard::kinematics}) {
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

bool publish_cuda_world_store_stage(CudaWorldStoreDeviceAllocation *allocation,
                                    CudaWorldStoreDeviceFaultInjection *faults,
                                    std::string *error) {
    return commit_barrier(allocation, CudaResidentBarrierCode::stage_publish, faults, error);
}

bool commit_cuda_world_store_window(CudaWorldStoreDeviceAllocation *allocation,
                                    CudaWorldStoreDeviceFaultInjection *faults,
                                    std::string *error) {
    return commit_barrier(allocation, CudaResidentBarrierCode::window_commit, faults, error);
}

bool read_cuda_world_store_state(const CudaWorldStoreDeviceAllocation *allocation,
                                 CudaWorldStoreStateSnapshot *snapshot, std::string *error) {
    if (allocation == nullptr || snapshot == nullptr) {
        if (error != nullptr) {
            *error = "CUDA world store state readback requires an allocation and output";
        }
        return false;
    }
    std::vector<HostStateBlock> host_slot = make_host_slot(allocation->state_layout.slot_bytes);
    if (allocation->world_capacity != 0) {
        const cudaError_t status =
            cudaMemcpy(host_slot.data(), allocation->state_slots[allocation->active_state_slot],
                       allocation->state_layout.slot_bytes, cudaMemcpyDeviceToHost);
        if (status != cudaSuccess) {
            if (error != nullptr) {
                *error = cuda_error_message("read resident world state", status);
            }
            return false;
        }
    }

    CudaWorldStoreDeviceSnapshot lifecycle;
    if (!read_cuda_world_store_metadata(allocation, allocation->world_capacity, &lifecycle,
                                        error)) {
        return false;
    }
    if (allocation->world_capacity == 0) {
        snapshot->worlds.clear();
        if (error != nullptr) {
            error->clear();
        }
        return true;
    }

    const auto *setup_complete =
        host_field<std::uint8_t>(host_slot, allocation->state_layout.setup_complete);
    const auto *entity_ids =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.entity_ids);
    const auto *entity_generations =
        host_field<std::uint32_t>(host_slot, allocation->state_layout.entity_generations);
    const auto *time_steps = host_field<double>(host_slot, allocation->state_layout.time_steps);
    const auto *kinematics = host_field<double>(host_slot, allocation->state_layout.kinematics);
    const auto *control_doubles =
        host_field<double>(host_slot, allocation->state_layout.control_doubles);
    const auto *control_floats =
        host_field<float>(host_slot, allocation->state_layout.control_floats);
    const auto *control_flags =
        host_field<std::uint8_t>(host_slot, allocation->state_layout.control_flags);
    const auto *clock_ticks =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.clock_ticks);
    const auto *simulation_times =
        host_field<double>(host_slot, allocation->state_layout.simulation_times);
    const auto *global_versions =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.global_versions);
    const auto *barrier_sequences =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.barrier_sequences);
    const auto *barrier_codes =
        host_field<std::uint8_t>(host_slot, allocation->state_layout.barrier_codes);
    const auto *shard_versions =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.shard_versions);

    CudaWorldStoreStateSnapshot next_snapshot;
    next_snapshot.worlds.reserve(allocation->world_capacity);
    for (std::size_t world = 0; world < allocation->world_capacity; ++world) {
        CudaWorldResidentState state{};
        state.world_index = world;
        state.seed = lifecycle.seeds[world];
        state.reset_generation = lifecycle.reset_generations[world];
        state.setup_complete = setup_complete[world] != 0;
        state.entity_id = entity_ids[world];
        state.entity_generation = entity_generations[world];
        state.time_step_s = time_steps[world];
        state.kinematics.x = kinematics[world];
        state.kinematics.y = kinematics[allocation->world_capacity + world];
        state.kinematics.z = kinematics[2 * allocation->world_capacity + world];
        state.kinematics.vx = kinematics[3 * allocation->world_capacity + world];
        state.kinematics.vy = kinematics[4 * allocation->world_capacity + world];
        state.kinematics.vz = kinematics[5 * allocation->world_capacity + world];
        state.kinematics.heading = kinematics[6 * allocation->world_capacity + world];
        state.kinematics.pitch = kinematics[7 * allocation->world_capacity + world];
        state.kinematics.roll = kinematics[8 * allocation->world_capacity + world];
        state.controls.stick_pitch = control_doubles[world];
        state.controls.stick_roll = control_doubles[allocation->world_capacity + world];
        state.controls.rudder = control_doubles[2 * allocation->world_capacity + world];
        state.controls.throttle = control_doubles[3 * allocation->world_capacity + world];
        state.controls.brake = control_doubles[4 * allocation->world_capacity + world];
        state.controls.gear_handle = control_floats[world];
        state.controls.flaps = control_floats[allocation->world_capacity + world];
        state.controls.speedbrake = control_floats[2 * allocation->world_capacity + world];
        state.controls.brake_left = control_flags[world] != 0;
        state.controls.brake_right = control_flags[allocation->world_capacity + world] != 0;
        state.controls.active = control_flags[2 * allocation->world_capacity + world] != 0;
        state.clock_tick = clock_ticks[world];
        state.simulation_time_s = simulation_times[world];
        state.global_version = global_versions[world];
        state.barrier_sequence = barrier_sequences[world];
        state.barrier = static_cast<CudaResidentBarrierCode>(barrier_codes[world]);
        for (std::size_t shard = 0; shard < kCudaResidentShardCount; ++shard) {
            state.shard_versions[shard] =
                shard_versions[shard * allocation->world_capacity + world];
        }
        next_snapshot.worlds.push_back(state);
    }
    *snapshot = std::move(next_snapshot);
    if (error != nullptr) {
        error->clear();
    }
    return true;
}

bool query_cuda_world_store_barrier_kernel_resources(CudaBarrierKernelResources *resources,
                                                     std::string *error) {
    if (resources == nullptr) {
        if (error != nullptr) {
            *error = "CUDA barrier kernel resource query requires an output";
        }
        return false;
    }
    cudaFuncAttributes attributes{};
    cudaError_t status = cudaFuncGetAttributes(&attributes, apply_barrier_kernel);
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("cudaFuncGetAttributes(apply_barrier_kernel)", status);
        }
        return false;
    }
    constexpr int threads_per_block = 128;
    int active_blocks = 0;
    status = cudaOccupancyMaxActiveBlocksPerMultiprocessor(&active_blocks, apply_barrier_kernel,
                                                           threads_per_block, 0);
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("cudaOccupancyMaxActiveBlocksPerMultiprocessor", status);
        }
        return false;
    }
    int device = 0;
    cudaDeviceProp properties{};
    status = cudaGetDevice(&device);
    if (status == cudaSuccess) {
        status = cudaGetDeviceProperties(&properties, device);
    }
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("query CUDA device occupancy properties", status);
        }
        return false;
    }
    if (properties.warpSize <= 0 || properties.maxThreadsPerMultiProcessor <= 0) {
        if (error != nullptr) {
            *error = "CUDA device returned invalid occupancy properties";
        }
        return false;
    }

    *resources = {
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
    if (error != nullptr) {
        error->clear();
    }
    return true;
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
