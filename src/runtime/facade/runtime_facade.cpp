#include "runtime/facade/runtime_facade_internal.h"

#include <cstdint>
#include <memory>
#include <utility>

RuntimeFacade::RuntimeFacade(std::size_t world_count)
    : runtime_(std::make_unique<WorldBatchRuntime>(world_count)),
      counterfactual_worldlines_(std::make_unique<CounterfactualWorldlineRegistry>()) {}

RuntimeFacade::RuntimeFacade(const RuntimeBatchConfig &config)
    : runtime_(std::make_unique<WorldBatchRuntime>(config.world_count)),
      counterfactual_worldlines_(std::make_unique<CounterfactualWorldlineRegistry>()) {
    configure_batch(config);
}

// I54-R: the move operations are user-defined (not defaulted) because the
// uint64 evidence cursors would otherwise be *copied* on move, letting a
// moved-from facade silently mint ids that duplicate (or, via move
// assignment, rewind) the destination's run. Each operation transfers every
// member of RuntimeFacade -- runtime_, counterfactual_worldlines_,
// next_run_snapshot_version_, next_trace_id_ -- and leaves the source's
// cursors at kInvalidatedEvidenceCursor so the producer methods fail fast.
// The tripwire below fires if the member set changes without this file
// being revisited.
static_assert(sizeof(RuntimeFacade) == 2 * sizeof(std::unique_ptr<WorldBatchRuntime>) +
                                           2 * sizeof(std::uint64_t),
              "RuntimeFacade member set changed: update the user-defined move constructor and "
              "move assignment in runtime_facade.cpp to transfer every member");

RuntimeFacade::RuntimeFacade(RuntimeFacade &&other) noexcept
    : runtime_(std::move(other.runtime_)),
      counterfactual_worldlines_(std::move(other.counterfactual_worldlines_)),
      next_run_snapshot_version_(
          std::exchange(other.next_run_snapshot_version_, kInvalidatedEvidenceCursor)),
      next_trace_id_(std::exchange(other.next_trace_id_, kInvalidatedEvidenceCursor)) {}

RuntimeFacade &RuntimeFacade::operator=(RuntimeFacade &&other) noexcept {
    if (this != &other) {
        runtime_ = std::move(other.runtime_);
        counterfactual_worldlines_ = std::move(other.counterfactual_worldlines_);
        next_run_snapshot_version_ =
            std::exchange(other.next_run_snapshot_version_, kInvalidatedEvidenceCursor);
        next_trace_id_ = std::exchange(other.next_trace_id_, kInvalidatedEvidenceCursor);
    }
    return *this;
}

RuntimeFacade::~RuntimeFacade() = default;
