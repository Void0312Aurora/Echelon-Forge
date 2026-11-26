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
RuntimeFacade &RuntimeFacade::operator=(RuntimeFacade &&other) noexcept {
    if (this == &other) return *this;
    if (identity_ && identity_->run_recorder) {
        try {
            fail_recorded_run("recorded run replaced before explicit finish");
            finish_recorded_run();
        } catch (...) {
        }
    }
    runtime_ = std::move(other.runtime_);
    identity_ = std::move(other.identity_);
    return *this;
}
RuntimeFacade::~RuntimeFacade() {
    if (identity_ && identity_->run_recorder) {
        try {
            fail_recorded_run("recorded run abandoned before explicit finish");
            finish_recorded_run();
        } catch (...) {
            // A failed terminal write never becomes a completion claim.
        }
    }
}

RuntimeNativeSnapshotFacts RuntimeFacade::native_snapshot_facts(std::size_t world_index) const {
    return runtime_->native_snapshot_facts(world_index);
}

std::unique_ptr<RuntimeFacadeNativeBranch>
RuntimeFacade::fork_native_branch(std::size_t world_index, std::string intervention_digest,
                                  std::uint64_t horizon) {
    return runtime_->fork_native_branch(world_index, std::move(intervention_digest), horizon);
}
