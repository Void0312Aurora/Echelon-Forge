#include "runtime/facade/runtime_facade_internal.h"

#include "runtime/facade/internal/flecs_cpu_backend.h"

#include <cstddef>
#include <memory>

RuntimeFacade::RuntimeFacade(std::size_t world_count)
    : runtime_(std::make_unique<FlecsCpuBackend>(world_count)) {}

RuntimeFacade::RuntimeFacade(const RuntimeBatchConfig &config)
    : runtime_(std::make_unique<FlecsCpuBackend>(config.world_count)) {
    configure_batch(config);
}

// Out-of-line so std::unique_ptr<IWorldBatchBackend> can stay incomplete at
// the public header boundary.
RuntimeFacade::RuntimeFacade(RuntimeFacade &&) noexcept = default;
RuntimeFacade &RuntimeFacade::operator=(RuntimeFacade &&) noexcept = default;
RuntimeFacade::~RuntimeFacade() = default;
