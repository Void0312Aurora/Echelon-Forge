#pragma once

#include "runtime_state_transfer_candidate.h"

#include <memory>
#include <functional>
#include <string>

class SimulationKernel;

namespace runtime::host::integration {

struct SimulationKernelStateOwnerRegistryConfig {
    SimulationKernel *kernel = nullptr;
    std::shared_ptr<RuntimeStateTransferJournal> journal;
    std::string transaction_namespace;
    // Host resource identity is the immutable binding between this registry
    // and the control/slot that owns the kernel.  The owner pointer is also
    // retained as an opaque provenance token so two registries cannot be
    // paired for source/target transfer when they capture the same kernel.
    RuntimeIdentity128 bound_resource_identity;
    // Owner callbacks are sampled after commit/abort to enforce the host's
    // logical deadline.  A missing sampler remains compatible with fixture
    // probes but cannot provide a bounded real-runtime commit.
    std::function<std::uint64_t()> sample_tick;
    // Optional target-side bridge invoked only after native owner truth has
    // been imported.  The callback is responsible for calling the Python
    // rederive hook with the target native state; it is never given source
    // Python objects as authority.
    std::function<bool()> rederive_python_caches;
    // Capture an opaque target-side rollback image before rederive.  The bytes
    // are persisted in the owner WAL; they are not source authority and must
    // be sufficient for the matching rollback/recovery callbacks after reopen.
    std::function<std::vector<std::uint8_t>()> snapshot_python_caches;
    // Matching rollback and recovery probes make the Python mirror owner a
    // real participant in the durable composite transaction. Host-bound
    // registries must provide all three callbacks; fixture registries may use
    // the in-memory staged fallback.
    std::function<bool(const std::vector<std::uint8_t> &)> rollback_python_caches;
    std::function<RuntimeStateOwnerImportTransactionPhase(const std::vector<std::uint8_t> &)>
        recover_python_caches;
};

class SimulationKernelStateOwnerBridge {
  public:
    [[nodiscard]] static std::shared_ptr<RuntimeStateTransferOwnerRegistry>
    create_registry(SimulationKernelStateOwnerRegistryConfig config);

    // Owner-layer implementation hooks. They are public only so the adapter's
    // category callbacks can remain small value-capturing functions; callers
    // should construct a registry instead of invoking them directly.
    [[nodiscard]] static std::string serialize_world(SimulationKernel &kernel);
    [[nodiscard]] static bool restore_world(SimulationKernel &kernel,
                                            const std::vector<std::uint8_t> &payload);
    [[nodiscard]] static std::string serialize_rng(SimulationKernel &kernel);
    [[nodiscard]] static bool restore_rng(SimulationKernel &kernel,
                                          const std::vector<std::uint8_t> &payload);
    [[nodiscard]] static std::string serialize_clock(SimulationKernel &kernel,
                                                     std::uint64_t step_sequence,
                                                     std::uint64_t barrier_sequence);
    [[nodiscard]] static bool restore_clock(SimulationKernel &kernel,
                                            const std::vector<std::uint8_t> &payload);
    [[nodiscard]] static std::string
    serialize_episode_barrier(const RuntimeEpisodeCoordinatorSnapshot &barrier);
    [[nodiscard]] static std::string serialize_composition(SimulationKernel &kernel);
};

} // namespace runtime::host::integration
