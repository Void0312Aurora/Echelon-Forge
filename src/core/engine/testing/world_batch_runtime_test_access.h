#pragma once

#include "core/engine/world_batch_runtime.h"

#include <utility>

// Deterministic fault injection for native qualification tests only. This is
// absent from facade/binding APIs and must be changed only while the batch is idle.
class WorldBatchRuntimeTestAccess {
  public:
    static void set_mutation_hook(WorldBatchRuntime &runtime, std::function<void()> hook) {
        (void)runtime;
        WorldBatchRuntime::mutation_hook_for_test_ = std::move(hook);
    }
};
