#pragma once

#include "runtime/facade/internal/flecs_cpu_backend.h"
#include "runtime/facade/runtime_facade.h"

#include <stdexcept>

namespace runtime::facade::testing {

// Native qualification only: permits controlled ECS fault injection behind
// the maintained facade without adding a production binding or runtime hook.
class RuntimeFacadeTestAccess final {
  public:
    static WorldBatchRuntime &world_batch_runtime(RuntimeFacade &facade) {
        auto *backend = dynamic_cast<FlecsCpuBackend *>(facade.runtime_.get());
        if (backend == nullptr) {
            throw std::logic_error("RuntimeFacade test access requires the CPU backend");
        }
        return backend->runtime_;
    }
};

} // namespace runtime::facade::testing
