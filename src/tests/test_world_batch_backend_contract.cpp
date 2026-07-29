#include "runtime/facade/internal/world_batch_backend.h"

#include <doctest/doctest.h>

#include <type_traits>

namespace {

// Compile-only substitute backend. This translation unit intentionally does
// not include WorldBatchRuntime or any engine/GPU helper header; completing the
// interface proves a second backend can own an independent state layout.
class IndependentBackendProbe final : public IWorldBatchBackend {
  public:
    runtime::backend::Configuration configuration() const noexcept override { return {}; }
    void configure(const runtime::backend::ConfigureRequest &) override {}
    runtime::backend::ContentResult
    load_content(const runtime::backend::ContentRequest &) override {
        return {};
    }
    void reset(const runtime::backend::ResetRequest &) override {}
    runtime::backend::SetupResult setup(const runtime::backend::SetupRequest &) override {
        return {};
    }
    runtime::backend::InputResult inject(const runtime::backend::InputBatch &) override {
        return {};
    }
    runtime::backend::EvaluationResult
    evaluate(const runtime::backend::EvaluationRequest &) const override {
        return {};
    }
    runtime::backend::AdvanceResult advance(const runtime::backend::AdvanceRequest &) override {
        return {};
    }
    runtime::backend::ExportResult
    export_state(const runtime::backend::ExportRequest &) const override {
        return {};
    }
    runtime::backend::Diagnostics diagnostics() const override { return {}; }
};

static_assert(!std::is_abstract_v<IndependentBackendProbe>);
static_assert(
    std::is_trivially_copyable_v<runtime::backend::VectorBatchView<WorldPilotActionAssignment>>);
static_assert(sizeof(runtime::backend::VectorBatchView<WorldPilotActionAssignment>) ==
              sizeof(const void *));
static_assert(
    !std::is_constructible_v<runtime::backend::VectorBatchView<WorldPilotActionAssignment>,
                             std::vector<WorldPilotActionAssignment> &&>);
static_assert(
    !std::is_constructible_v<runtime::backend::VectorBatchView<WorldPilotActionAssignment>,
                             const std::vector<WorldPilotActionAssignment> &&>);

} // namespace

TEST_CASE("backend batch view aliases the caller vector without ownership") {
    const std::vector<WorldPilotActionAssignment> source(1);
    const runtime::backend::VectorBatchView<WorldPilotActionAssignment> view(source);

    CHECK(&view.get() == &source);
}
