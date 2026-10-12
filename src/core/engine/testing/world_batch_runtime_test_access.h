#pragma once

#include "core/engine/world_batch_runtime.h"

#include <utility>

// Deterministic fault injection for native qualification tests only. This is
// absent from facade/binding APIs and must be changed only while the batch is idle.
class WorldBatchRuntimeTestAccess {
  public:
    static void set_worker_thread_factory(
        WorldBatchRuntime &runtime,
        std::function<std::jthread(std::function<void()>)> factory) {
        (void)runtime;
        WorldBatchRuntime::worker_thread_factory_for_test_ = std::move(factory);
    }
};
