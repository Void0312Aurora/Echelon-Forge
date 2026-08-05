#include <doctest/doctest.h>

#include <ostream>
#include <string>

#include "runtime/contracts/cuda_resident_performance_contract.h"
#include "runtime/facade/internal/cuda_resident/cuda_resident_backend.h"

TEST_CASE("RB9 performance contract freezes the private-window operation ledger") {
    using namespace runtime::cuda_resident::performance;
    CHECK(kCudaResidentPerformanceProfileId == "resident_state.unmaintained_candidate");
    CHECK(kCudaResidentPerformanceInvocationSurface == "backend_private_phase_sequence");

    constexpr std::size_t worlds = 4;
    constexpr std::size_t slot_bytes = 1000;
    const WindowTransferLedger resident = modeled_window_ledger(worlds, slot_bytes, false, false);
    CHECK(resident.h2d_copy_count == 3);
    CHECK(resident.h2d_bytes == worlds * 55);
    CHECK(resident.d2h_copy_count == 5);
    CHECK(resident.d2h_bytes == 20);
    CHECK(resident.d2d_copy_count == 3);
    CHECK(resident.d2d_bytes == 3 * slot_bytes);
    CHECK(resident.kernel_launch_count == 10);
    CHECK(resident.synchronization_count == 5);

    const WindowTransferLedger host = modeled_window_ledger(worlds, slot_bytes, true, false);
    CHECK(host.d2h_copy_count == 7);
    CHECK(host.d2h_bytes == 20 + slot_bytes + worlds * 16);
    CHECK(host.host_snapshot_includes_full_state_d2h);

    const WindowTransferLedger device = modeled_window_ledger(worlds, slot_bytes, false, true);
    CHECK(device.kernel_launch_count == 12);
    CHECK(device.synchronization_count == 7);
    CHECK(device.d2h_copy_count == 10);
    CHECK(device.device_observation_pack_bytes ==
          worlds * (15 * sizeof(float) + sizeof(std::uint64_t)));
    CHECK(device.device_observation_consumer_bytes ==
          worlds * (sizeof(float) + sizeof(std::uint64_t)));
    CHECK(device.device_consumer_includes_host_validation_d2h);

    const WindowTransferLedger both = modeled_window_ledger(worlds, slot_bytes, true, true);
    CHECK(both.d2h_copy_count == 12);
    CHECK(both.d2h_bytes == device.d2h_bytes + slot_bytes + worlds * 16);
}

TEST_CASE("RB9 CUDA resource inventory includes pack and consumer kernels") {
    using namespace runtime::cuda_resident;
    if (!CudaWorldStore::compiled_with_cuda()) {
        CHECK(true);
        return;
    }
    const auto pack = testing::CudaWorldStoreTestAccess::phase_d_pack_kernel_resources();
    const auto consumer = testing::CudaWorldStoreTestAccess::phase_d_consumer_kernel_resources();
    CHECK(pack.registers_per_thread > 0);
    CHECK(pack.threads_per_block == 128);
    CHECK(pack.theoretical_occupancy > 0.0);
    CHECK(consumer.registers_per_thread > 0);
    CHECK(consumer.threads_per_block == 128);
    CHECK(consumer.theoretical_occupancy > 0.0);
}

TEST_CASE("RB9 diagnostics expose exact resident state-slot bytes") {
    using namespace runtime::cuda_resident;
    if (!CudaWorldStore::compiled_with_cuda()) {
        CHECK(true);
        return;
    }
    CudaResidentBackend backend;
    backend.configure({.world_count = 4});
    const auto diagnostics = backend.store_diagnostics();
    CHECK(diagnostics.device_bytes > 0);
    CHECK(diagnostics.state_slot_bytes > 0);
    CHECK(diagnostics.device_bytes > diagnostics.state_slot_bytes * 2);
}
