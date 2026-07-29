#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

namespace runtime::cuda_resident {

namespace testing {
class CudaWorldStoreTestAccess;
}

enum class CudaWorldStoreState : std::uint8_t {
    unconfigured,
    ready,
    unavailable,
};

struct CudaWorldStoreDiagnostics {
    CudaWorldStoreState state = CudaWorldStoreState::unconfigured;
    bool compiled_with_cuda = false;
    bool runtime_available = false;
    std::size_t world_capacity = 0;
    std::size_t device_bytes = 0;
    std::uint64_t allocation_generation = 0;
    std::uint64_t reset_generation = 0;
    std::string last_error;
};

struct CudaWorldStoreLifecycleSnapshot {
    std::vector<std::uint32_t> seeds;
    std::vector<std::uint64_t> reset_generations;
};

// Instance-owned RB3 lifecycle store. It owns only device lifecycle metadata;
// simulation shards, entity state, barriers, and kernels start in later rows.
class CudaWorldStore final {
  public:
    CudaWorldStore();
    ~CudaWorldStore();

    CudaWorldStore(const CudaWorldStore &) = delete;
    CudaWorldStore &operator=(const CudaWorldStore &) = delete;
    CudaWorldStore(CudaWorldStore &&) = delete;
    CudaWorldStore &operator=(CudaWorldStore &&) = delete;

    [[nodiscard]] static bool compiled_with_cuda() noexcept;
    [[nodiscard]] bool configure(std::size_t world_capacity);
    [[nodiscard]] bool reset(const std::vector<std::uint32_t> &seeds);
    [[nodiscard]] bool teardown() noexcept;

    [[nodiscard]] CudaWorldStoreDiagnostics diagnostics() const;
    [[nodiscard]] std::size_t world_capacity() const noexcept;

  private:
    friend class testing::CudaWorldStoreTestAccess;

    struct Impl;
    std::unique_ptr<Impl> impl_;
};

namespace testing {

// Narrow, per-instance fault/readback seam for the RB3 CUDA lifecycle tests.
// It is not a runtime capability and is never surfaced by RuntimeFacade.
class CudaWorldStoreTestAccess final {
  public:
    static void fail_next_allocation(CudaWorldStore &store) noexcept;
    static void fail_next_reset_copy(CudaWorldStore &store) noexcept;
    static void fail_next_release(CudaWorldStore &store) noexcept;
    static void set_allocation_generation(CudaWorldStore &store, std::uint64_t generation) noexcept;
    static void set_reset_generation(CudaWorldStore &store, std::uint64_t generation) noexcept;
    [[nodiscard]] static CudaWorldStoreLifecycleSnapshot readback(const CudaWorldStore &store);
};

} // namespace testing

} // namespace runtime::cuda_resident
