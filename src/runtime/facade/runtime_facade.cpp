#include "runtime/facade/runtime_facade_internal.h"

#include <memory>

RuntimeFacade::RuntimeFacade(std::size_t world_count)
    : runtime_(std::make_unique<WorldBatchRuntime>(world_count)),
      counterfactual_worldlines_(std::make_unique<CounterfactualWorldlineRegistry>()) {}

RuntimeFacade::RuntimeFacade(const RuntimeBatchConfig &config)
    : runtime_(std::make_unique<WorldBatchRuntime>(config.world_count)),
      counterfactual_worldlines_(std::make_unique<CounterfactualWorldlineRegistry>()) {
    configure_batch(config);
}

RuntimeFacade::RuntimeFacade(RuntimeFacade &&) noexcept = default;

RuntimeFacade &RuntimeFacade::operator=(RuntimeFacade &&) noexcept = default;

RuntimeFacade::~RuntimeFacade() = default;
