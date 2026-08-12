#include "runtime/facade/internal/cuda_resident/cuda_world_store_cuda_internal.cuh"
#include <cuda_runtime_api.h>
namespace runtime::cuda_resident::detail {

bool commit_flight_dynamics_window(CudaWorldStoreDeviceAllocation *allocation,
                                   CudaWorldStoreDeviceFaultInjection *faults, std::string *error) {
    if (allocation == nullptr) {
        if (error != nullptr) *error = "CUDA flight-dynamics window requires an allocation";
        return false;
    }
    const std::uint8_t next_slot = allocation->active_state_slot ^ 1U;
    if (allocation->world_capacity == 0) {
        if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_barrier_commit)) {
            if (error != nullptr) *error = "injected CUDA world store barrier commit failure";
            return false;
        }
        allocation->active_state_slot = next_slot;
        if (error != nullptr) error->clear();
        return true;
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

    // CP-5 fused the six-launch window graph into one launch; CP-7b folded the
    // window_commit barrier into that launch as a per-world epilogue. This is
    // the only host synchronization in the window commit.
    status = launch_window_commit_body(allocation, next_slot);
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
    // The window commit is the host-side slot flip; the barrier-commit fault
    // hook keeps failing the window after a clean body, before the flip.
    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_barrier_commit)) {
        if (error != nullptr) *error = "injected CUDA world store barrier commit failure";
        return false;
    }
    allocation->active_state_slot = next_slot;
    if (error != nullptr) error->clear();
    return true;
}

bool commit_cuda_world_store_window(CudaWorldStoreDeviceAllocation *allocation,
                                    CudaWorldStoreDeviceFaultInjection *faults,
                                    std::string *error) {
    return commit_flight_dynamics_window(allocation, faults, error);
}

} // namespace runtime::cuda_resident::detail
