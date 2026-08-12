#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include "runtime/facade/internal/cuda_resident/cuda_world_store.h"

namespace runtime::cuda_resident::detail {

struct CudaWorldStoreDeviceAllocation;

struct CudaWorldStoreDeviceFaultInjection {
    bool fail_next_allocation = false;
    bool fail_next_reset_copy = false;
    bool fail_next_release = false;
    bool fail_next_state_transfer = false;
    bool fail_next_barrier_commit = false;
    bool fail_next_device_lease_allocation = false;
    bool fail_next_device_lease_event_record = false;
};

struct CudaWorldStoreDeviceSnapshot {
    std::vector<std::uint32_t> seeds;
    std::vector<std::uint64_t> reset_generations;
};

struct CudaWorldStoreDeviceAllocationResult {
    CudaWorldStoreDeviceAllocation *allocation = nullptr;
    std::size_t device_bytes = 0;
    std::size_t state_slot_bytes = 0;
    std::string error;
};

struct CudaWorldStoreDeviceConsumerRaw {
    void *values = nullptr;
    void *ids = nullptr;
    void *ready_event = nullptr;
    int device_ordinal = -1;
    std::size_t world_count = 0;
    // One for the smoke consumer, the packed observation field count for the
    // learner-equivalent consumer.
    std::size_t values_per_world = 0;
};

[[nodiscard]] bool cuda_world_store_runtime_available(std::string *error);
[[nodiscard]] CudaWorldStoreDeviceAllocationResult
allocate_cuda_world_store_metadata(std::size_t world_capacity,
                                   CudaWorldStoreDeviceFaultInjection *faults);
[[nodiscard]] bool reset_cuda_world_store_metadata(CudaWorldStoreDeviceAllocation *allocation,
                                                   const std::uint32_t *seeds,
                                                   std::size_t world_capacity,
                                                   std::uint64_t reset_generation,
                                                   CudaWorldStoreDeviceFaultInjection *faults,
                                                   std::string *error);
[[nodiscard]] bool read_cuda_world_store_metadata(const CudaWorldStoreDeviceAllocation *allocation,
                                                  std::size_t world_capacity,
                                                  CudaWorldStoreDeviceSnapshot *snapshot,
                                                  std::string *error);
[[nodiscard]] bool setup_cuda_world_store_fixed_air_fixture(
    CudaWorldStoreDeviceAllocation *allocation, const std::vector<CudaFixedAirWorldSetup> &setups,
    CudaWorldStoreDeviceFaultInjection *faults, std::string *error);
[[nodiscard]] bool inject_cuda_world_store_flight_controls(
    CudaWorldStoreDeviceAllocation *allocation,
    const std::vector<CudaWorldFlightControlAssignment> &assignments,
    CudaWorldStoreDeviceFaultInjection *faults, std::string *error);
[[nodiscard]] bool publish_cuda_world_store_stage(CudaWorldStoreDeviceAllocation *allocation,
                                                  CudaWorldStoreDeviceFaultInjection *faults,
                                                  std::string *error);
[[nodiscard]] bool commit_cuda_world_store_window(CudaWorldStoreDeviceAllocation *allocation,
                                                  CudaWorldStoreDeviceFaultInjection *faults,
                                                  std::string *error);
[[nodiscard]] bool
export_cuda_world_store_device_observation(const CudaWorldStoreDeviceAllocation *allocation,
                                           CudaWorldStoreDeviceObservationRaw *raw,
                                           std::string *error);
[[nodiscard]] bool acquire_cuda_world_store_device_observation_lease(
    const CudaWorldStoreDeviceAllocation *allocation, const device_consumer::LeaseEpoch &epoch,
    CudaWorldStoreDeviceObservationLeaseRaw *raw, CudaWorldStoreDeviceFaultInjection *faults,
    device_consumer::FailureCode *failure, std::string *error);
void release_cuda_world_store_device_observation(void *values, void *ids) noexcept;
void release_cuda_world_store_device_observation_lease(void *values, void *ids, void *ready_event,
                                                       int device_ordinal) noexcept;
[[nodiscard]] bool submit_cuda_world_store_device_observation_consumer(
    const CudaWorldStoreDeviceObservationLeaseRaw &lease, CudaWorldStoreDeviceConsumerRaw *raw,
    bool learner_equivalent, bool fail_allocation, bool fail_launch, bool fail_event_record,
    device_consumer::FailureCode *failure, std::string *error);
[[nodiscard]] bool
await_cuda_world_store_device_observation_consumer(const CudaWorldStoreDeviceConsumerRaw &raw,
                                                   bool fail_wait, std::string *error);
[[nodiscard]] bool materialize_cuda_world_store_device_observation_consumer(
    const CudaWorldStoreDeviceConsumerRaw &raw, std::vector<float> *values,
    std::vector<std::uint64_t> *ids, bool fail_materialize, std::string *error);
void release_cuda_world_store_device_consumer(void *values, void *ids, void *ready_event,
                                              int device_ordinal) noexcept;
[[nodiscard]] bool consume_cuda_world_store_device_observation(
    const void *values, const void *ids, std::size_t world_count, std::size_t values_per_world,
    std::vector<float> *first_values, std::vector<std::uint64_t> *ids_out, std::string *error);
[[nodiscard]] bool read_cuda_world_store_state(const CudaWorldStoreDeviceAllocation *allocation,
                                               CudaWorldStoreStateSnapshot *snapshot,
                                               std::string *error);
[[nodiscard]] bool
query_cuda_world_store_barrier_kernel_resources(CudaBarrierKernelResources *resources,
                                                std::string *error);
[[nodiscard]] bool
query_cuda_world_store_control_preparation_kernel_resources(CudaBarrierKernelResources *resources,
                                                            std::string *error);
[[nodiscard]] bool query_cuda_world_store_window_commit_body_kernel_resources(
    CudaBarrierKernelResources *resources, std::string *error);
[[nodiscard]] bool query_cuda_world_store_device_observation_pack_kernel_resources(
    CudaBarrierKernelResources *resources, std::string *error);
[[nodiscard]] bool query_cuda_world_store_device_observation_consumer_kernel_resources(
    CudaBarrierKernelResources *resources, std::string *error);
[[nodiscard]] bool query_cuda_world_store_learner_consumer_kernel_resources(
    CudaBarrierKernelResources *resources, std::string *error);
[[nodiscard]] bool
release_cuda_world_store_metadata(CudaWorldStoreDeviceAllocation *&allocation,
                                  CudaWorldStoreDeviceFaultInjection *faults) noexcept;

} // namespace runtime::cuda_resident::detail
