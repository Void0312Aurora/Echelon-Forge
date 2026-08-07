#include "runtime/facade/internal/cuda_resident/cuda_world_store_cuda_internal.cuh"
#include <cuda_runtime_api.h>
namespace runtime::cuda_resident::detail {

bool commit_phase_b_window(CudaWorldStoreDeviceAllocation *allocation,
                           CudaWorldStoreDeviceFaultInjection *faults, std::string *error) {
    if (allocation == nullptr) {
        if (error != nullptr) *error = "CUDA flight-dynamics window requires an allocation";
        return false;
    }
    const std::uint8_t next_slot = allocation->active_state_slot ^ 1U;
    if (allocation->world_capacity == 0) {
        return finalize_staged_barrier(allocation, next_slot,
                                       CudaResidentBarrierCode::window_commit, faults, error);
    }
    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_state_transfer)) {
        if (error != nullptr) *error = "injected CUDA flight-dynamics state transfer failure";
        return false;
    }
    cudaError_t status = cudaMemcpy(allocation->state_slots[next_slot],
                                    allocation->state_slots[allocation->active_state_slot],
                                    allocation->state_layout.slot_bytes, cudaMemcpyDeviceToDevice);
    if (status != cudaSuccess) {
        if (error != nullptr) *error = cuda_error_message("copy state for flight dynamics", status);
        return false;
    }
    status = cudaMemset(allocation->barrier_status, 0, sizeof(std::uint32_t));
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("clear flight-dynamics status", status);
        }
        return false;
    }

    status = launch_phase_b_forces(allocation, next_slot);
    if (status == cudaSuccess) status = launch_phase_b_aerodynamics(allocation, next_slot);
    if (status == cudaSuccess) status = launch_phase_b_integrate(allocation, next_slot);
    if (status == cudaSuccess) status = launch_phase_d_instruments(allocation, next_slot);
    if (status == cudaSuccess) status = launch_phase_d_configuration(allocation, next_slot);
    if (status == cudaSuccess) status = launch_phase_d_episode(allocation, next_slot);

    // The six Phase-B/D launches form one device graph. This is the only
    // host synchronization before the declared window barrier.
    if (status == cudaSuccess) status = cudaDeviceSynchronize();
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("run fixed-air flight dynamics", status);
        }
        return false;
    }
    std::uint32_t phase_status = 0;
    status = cudaMemcpy(&phase_status, allocation->barrier_status, sizeof(phase_status),
                        cudaMemcpyDeviceToHost);
    if (status != cudaSuccess || phase_status != 0) {
        if (error != nullptr) {
            *error = status == cudaSuccess
                         ? "CUDA flight dynamics produced overflow or non-finite state"
                         : cuda_error_message("read flight-dynamics status", status);
        }
        return false;
    }
    return finalize_staged_barrier(allocation, next_slot, CudaResidentBarrierCode::window_commit,
                                   faults, error);
}

bool commit_cuda_world_store_window(CudaWorldStoreDeviceAllocation *allocation,
                                    CudaWorldStoreDeviceFaultInjection *faults,
                                    std::string *error) {
    return commit_phase_b_window(allocation, faults, error);
}

} // namespace runtime::cuda_resident::detail
