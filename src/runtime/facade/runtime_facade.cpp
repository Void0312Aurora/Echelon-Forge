#include "runtime/facade/runtime_facade_internal.h"

#include "runtime/facade/internal/world_batch_backend_provider.h"

#include <cstddef>
#include <memory>
#include <stdexcept>
#include <utility>

RuntimeFacade::RuntimeFacade(std::size_t world_count)
    : identity_(std::make_shared<RuntimeFacadeIdentity>()) {
    runtime::backend_provider::WorldBatchBackendProviderMaterialization materialized =
        runtime::backend_provider::materialize_default_world_batch_backend(world_count);
    if (!materialized) {
        throw std::runtime_error(materialized.error.code + "@" + materialized.error.subject + ": " +
                                 materialized.error.detail);
    }
    identity_->backend_identity = std::move(materialized.identity);
    runtime_ = std::move(materialized.backend);
}

RuntimeFacade::RuntimeFacade(const RuntimeBatchConfig &config) : RuntimeFacade(config.world_count) {
    configure_batch(config);
}

// Out-of-line so std::unique_ptr<IWorldBatchBackend> can stay incomplete at
// the public header boundary.
RuntimeFacade::RuntimeFacade(RuntimeFacade &&) noexcept = default;
RuntimeFacade &RuntimeFacade::operator=(RuntimeFacade &&) noexcept = default;
RuntimeFacade::~RuntimeFacade() = default;
