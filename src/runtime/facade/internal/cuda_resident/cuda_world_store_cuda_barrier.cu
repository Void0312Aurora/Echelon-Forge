#include "runtime/facade/internal/cuda_resident/cuda_world_store_cuda_internal.cuh"
#include <cuda_runtime_api.h>
namespace runtime::cuda_resident::detail {
namespace {
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
    const std::size_t dynamics_index =
        static_cast<std::size_t>(CudaResidentShard::dynamics) * world_capacity + world_index;
    const std::size_t episode_index =
        static_cast<std::size_t>(CudaResidentShard::episode) * world_capacity + world_index;
    const std::size_t instrument_index =
        static_cast<std::size_t>(CudaResidentShard::instrument) * world_capacity + world_index;
    const std::size_t observation_index =
        static_cast<std::size_t>(CudaResidentShard::observation) * world_capacity + world_index;
    const std::size_t reward_index =
        static_cast<std::size_t>(CudaResidentShard::reward) * world_capacity + world_index;
    const std::size_t termination_index =
        static_cast<std::size_t>(CudaResidentShard::termination) * world_capacity + world_index;
    const std::size_t events_index =
        static_cast<std::size_t>(CudaResidentShard::events) * world_capacity + world_index;
    if (barrier == CudaResidentBarrierCode::input_injection) {
        overflow = overflow || increment_would_overflow(shard_versions[identity_index]) ||
                   increment_would_overflow(shard_versions[controls_index]);
    } else if (barrier == CudaResidentBarrierCode::window_commit) {
        overflow = overflow || increment_would_overflow(shard_versions[identity_index]) ||
                   increment_would_overflow(shard_versions[clock_index]) ||
                   increment_would_overflow(shard_versions[snapshot_index]) ||
                   increment_would_overflow(shard_versions[kinematics_index]) ||
                   increment_would_overflow(shard_versions[dynamics_index]) ||
                   increment_would_overflow(shard_versions[episode_index]) ||
                   increment_would_overflow(shard_versions[instrument_index]) ||
                   increment_would_overflow(shard_versions[observation_index]) ||
                   increment_would_overflow(shard_versions[reward_index]) ||
                   increment_would_overflow(shard_versions[termination_index]) ||
                   increment_would_overflow(shard_versions[events_index]);
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
    ++shard_versions[dynamics_index];
    ++shard_versions[episode_index];
    ++shard_versions[instrument_index];
    ++shard_versions[observation_index];
    ++shard_versions[reward_index];
    ++shard_versions[termination_index];
    ++shard_versions[events_index];
}
} // namespace

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


} // namespace runtime::cuda_resident::detail
