#include "runtime/facade/internal/cuda_resident/cuda_world_store_cuda_internal.cuh"
#include "runtime/contracts/cuda_resident_control_preparation_fixture_contract.h"

#include <cmath>
namespace runtime::cuda_resident::detail {
namespace {
__global__ void control_preparation_kernel(std::size_t world_capacity, const double *time_steps,
                                           const double *control_doubles,
                                           const std::uint8_t *control_flags,
                                           double *prepared_doubles, std::uint8_t *prepared_flags,
                                           std::uint64_t *prepared_control_versions,
                                           std::uint64_t *barrier_sequences,
                                           std::uint8_t *barrier_codes, std::uint32_t *status) {
    const std::size_t world_index = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (world_index >= world_capacity) {
        return;
    }

    // Match the maintained CPU FlightControl stage's ecs_ftime_t=float boundary.
    const double dt = static_cast<double>(static_cast<float>(time_steps[world_index]));
    const double tau = kCudaResidentControlPreparationStickTauS;
    const double alpha = dt / (tau + dt);
    const bool active = control_flags[2 * world_capacity + world_index] != 0;
    // The frozen flight-control SoA preserves the maintained CPU component order:
    // pitch, roll, rudder, throttle, brake. Prepared controls use semantic order.
    const double raw_pitch = control_doubles[world_index];
    const double raw_roll = control_doubles[world_capacity + world_index];
    const double raw_rudder = control_doubles[2 * world_capacity + world_index];
    const bool manual_takeover =
        active && (fabs(raw_roll) > kCudaResidentControlPreparationManualDeadband ||
                   fabs(raw_pitch) > kCudaResidentControlPreparationManualDeadband ||
                   fabs(raw_rudder) > kCudaResidentControlPreparationManualDeadband);
    const double target_roll = manual_takeover ? raw_roll : 0.0;
    const double target_pitch = manual_takeover ? raw_pitch : 0.0;
    const double target_yaw = manual_takeover ? -raw_rudder : 0.0;
    const std::size_t roll_index = world_index;
    const std::size_t pitch_index = world_capacity + world_index;
    const std::size_t yaw_index = 2 * world_capacity + world_index;
    const std::size_t yaw_cmd_index = 3 * world_capacity + world_index;

    bool invalid = !isfinite(dt) || !(dt > 0.0) || !isfinite(alpha) ||
                   increment_would_overflow(prepared_control_versions[world_index]);
    const double next_roll =
        prepared_doubles[roll_index] + alpha * (target_roll - prepared_doubles[roll_index]);
    const double next_pitch =
        prepared_doubles[pitch_index] + alpha * (target_pitch - prepared_doubles[pitch_index]);
    const double next_yaw =
        prepared_doubles[yaw_index] + alpha * (target_yaw - prepared_doubles[yaw_index]);
    invalid = invalid || !isfinite(next_roll) || !isfinite(next_pitch) || !isfinite(next_yaw);
    if (invalid) {
        atomicExch(status, 1U);
        return;
    }

    prepared_doubles[roll_index] = next_roll;
    prepared_doubles[pitch_index] = next_pitch;
    prepared_doubles[yaw_index] = next_yaw;
    prepared_doubles[yaw_cmd_index] = next_yaw;
    prepared_flags[world_index] = 1;
    prepared_flags[world_capacity + world_index] = static_cast<std::uint8_t>(manual_takeover);
    ++prepared_control_versions[world_index];

    // CP-7b: the stage_publish barrier is a per-world epilogue instead of a
    // separate launch. It mirrors apply_barrier_kernel's stage_publish branch
    // exactly: the barrier sequence is the only overflow surface, and a
    // stage-publish barrier does not mutate snapshot state.
    if (increment_would_overflow(barrier_sequences[world_index])) {
        atomicExch(status, 1U);
        return;
    }
    ++barrier_sequences[world_index];
    barrier_codes[world_index] = static_cast<std::uint8_t>(CudaResidentBarrierCode::stage_publish);
}
} // namespace

bool commit_control_preparation_stage(CudaWorldStoreDeviceAllocation *allocation,
                                      CudaWorldStoreDeviceFaultInjection *faults,
                                      std::string *error) {
    if (allocation == nullptr) {
        if (error != nullptr) {
            *error = "CUDA control-preparation stage requires an allocation";
        }
        return false;
    }
    const std::uint8_t next_slot = allocation->active_state_slot ^ 1U;
    if (allocation->world_capacity == 0) {
        if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_barrier_commit)) {
            if (error != nullptr) {
                *error = "injected CUDA world store barrier commit failure";
            }
            return false;
        }
        allocation->active_state_slot = next_slot;
        if (error != nullptr) error->clear();
        return true;
    }
    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_state_transfer)) {
        if (error != nullptr) {
            *error = "injected CUDA control-preparation state transfer failure";
        }
        return false;
    }

    cudaError_t status = cudaMemcpy(allocation->state_slots[next_slot],
                                    allocation->state_slots[allocation->active_state_slot],
                                    allocation->state_layout.slot_bytes, cudaMemcpyDeviceToDevice);
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("copy state for control preparation", status);
        }
        return false;
    }
    status = cudaMemset(allocation->barrier_status, 0, sizeof(std::uint32_t));
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("clear control-preparation status", status);
        }
        return false;
    }
    constexpr unsigned int threads = 128;
    const unsigned int blocks =
        static_cast<unsigned int>((allocation->world_capacity + threads - 1) / threads);
    std::uint8_t *slot = allocation->state_slots[next_slot];
    control_preparation_kernel<<<blocks, threads>>>(
        allocation->world_capacity, device_field<double>(slot, allocation->state_layout.time_steps),
        device_field<double>(slot, allocation->state_layout.control_doubles),
        device_field<std::uint8_t>(slot, allocation->state_layout.control_flags),
        device_field<double>(slot, allocation->state_layout.prepared_doubles),
        device_field<std::uint8_t>(slot, allocation->state_layout.prepared_flags),
        device_field<std::uint64_t>(slot, allocation->state_layout.prepared_control_versions),
        device_field<std::uint64_t>(slot, allocation->state_layout.barrier_sequences),
        device_field<std::uint8_t>(slot, allocation->state_layout.barrier_codes),
        allocation->barrier_status);
    status = cudaGetLastError();
    if (status == cudaSuccess) {
        status = cudaDeviceSynchronize();
    }
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("run control preparation", status);
        }
        return false;
    }
    std::uint32_t phase_status = 0;
    status = cudaMemcpy(&phase_status, allocation->barrier_status, sizeof(phase_status),
                        cudaMemcpyDeviceToHost);
    if (status != cudaSuccess || phase_status != 0) {
        if (error != nullptr) {
            *error = status == cudaSuccess
                         ? "CUDA control preparation overflow or non-finite state"
                         : cuda_error_message("read control-preparation status", status);
        }
        return false;
    }
    // CP-7b: the stage_publish barrier ran as the kernel's per-world epilogue,
    // so the stage commit is the host-side slot flip. The barrier-commit fault
    // hook keeps its observable contract: the stage fails after a clean phase
    // and the staged slot never becomes active.
    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_barrier_commit)) {
        if (error != nullptr) {
            *error = "injected CUDA world store barrier commit failure";
        }
        return false;
    }
    allocation->active_state_slot = next_slot;
    if (error != nullptr) error->clear();
    return true;
}
bool publish_cuda_world_store_stage(CudaWorldStoreDeviceAllocation *allocation,
                                    CudaWorldStoreDeviceFaultInjection *faults,
                                    std::string *error) {
    return commit_control_preparation_stage(allocation, faults, error);
}
bool query_cuda_world_store_control_preparation_kernel_resources(
    CudaBarrierKernelResources *resources, std::string *error) {
    if (resources == nullptr) {
        if (error != nullptr) {
            *error = "CUDA control-preparation kernel resource query requires an output";
        }
        return false;
    }
    cudaFuncAttributes attributes{};
    cudaError_t status = cudaFuncGetAttributes(&attributes, control_preparation_kernel);
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error =
                cuda_error_message("cudaFuncGetAttributes(control_preparation_kernel)", status);
        }
        return false;
    }
    constexpr int threads_per_block = 128;
    int active_blocks = 0;
    status = cudaOccupancyMaxActiveBlocksPerMultiprocessor(
        &active_blocks, control_preparation_kernel, threads_per_block, 0);
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message(
                "cudaOccupancyMaxActiveBlocksPerMultiprocessor(control preparation)", status);
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
            *error =
                cuda_error_message("query CUDA control-preparation occupancy properties", status);
        }
        return false;
    }
    if (properties.warpSize <= 0 || properties.maxThreadsPerMultiProcessor <= 0) {
        if (error != nullptr) {
            *error = "CUDA device returned invalid control-preparation occupancy properties";
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
