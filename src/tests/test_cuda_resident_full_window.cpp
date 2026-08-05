#include "runtime/facade/internal/cuda_resident/cuda_resident_full_window_runner.h"

#include <ostream>

#include <doctest/doctest.h>

#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "runtime/contracts/cuda_resident_parity_release_contract.h"
#include "runtime/facade/internal/cuda_resident/cuda_resident_backend.h"
#include "runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.h"

namespace {

namespace full_window = runtime::cuda_resident::full_window;
namespace replay = runtime::cuda_resident::replay;
using full_window::FailureCode;
using full_window::Operation;

replay::ReplayTrace make_trace() {
    replay::ReplayTrace trace{
        .run_id = "cr2.full_window.fixed_air",
        .seeds = {101, 202},
        .spawns = {},
        .time_steps = {0.01, 0.02},
        .windows = {},
    };
    for (std::size_t world = 0; world < trace.seeds.size(); ++world) {
        WorldSpawnRequest spawn{};
        spawn.world_index = world;
        spawn.type_name = std::string(runtime::cuda_resident::kFixedAirFixtureTypeName);
        spawn.entity_name = "CR2FullWindow" + std::to_string(world);
        spawn.is_agent = true;
        spawn.x = 1000.0 + static_cast<double>(world) * 100.0;
        spawn.z = 1500.0;
        spawn.vx = 200.0 + static_cast<double>(world);
        spawn.heading = 90.0;
        trace.spawns.push_back(std::move(spawn));
    }
    for (std::size_t window = 0; window < 2; ++window) {
        replay::ReplayActionWindow actions{
            .actions = {},
            .request_id = "cr2.window." + std::to_string(window),
        };
        for (std::size_t world = 0; world < trace.seeds.size(); ++world) {
            PilotAction action{};
            action.stick_pitch = 0.01 * static_cast<double>(window + world + 1);
            action.stick_roll = -0.01 * static_cast<double>(world + 1);
            action.rudder = 0.005 * static_cast<double>(window + 1);
            action.throttle = 0.65 + 0.01 * static_cast<double>(world);
            action.active = true;
            actions.actions.push_back(action);
        }
        trace.windows.push_back(std::move(actions));
    }
    return trace;
}

std::vector<WorldPilotActionAssignment>
make_assignments(const replay::ReplayActionWindow &window,
                 const std::vector<std::uint64_t> &entity_ids) {
    std::vector<WorldPilotActionAssignment> assignments;
    assignments.reserve(entity_ids.size());
    for (std::size_t world = 0; world < entity_ids.size(); ++world) {
        assignments.push_back({
            .world_index = world,
            .entity_id = entity_ids[world],
            .action = window.actions[world],
        });
    }
    return assignments;
}

class FakeBackend final : public IWorldBatchBackend {
  public:
    explicit FakeBackend(Operation failure = Operation::setup, bool fail = false)
        : failure_(failure), fail_(fail) {}

    runtime::backend::Configuration configuration() const noexcept override {
        return {.world_count = world_count_};
    }

    void configure(const runtime::backend::ConfigureRequest &request) override {
        if (request.world_count.has_value()) world_count_ = *request.world_count;
    }

    runtime::backend::ContentResult
    load_content(const runtime::backend::ContentRequest &) override {
        return {.loaded = true};
    }

    void reset(const runtime::backend::ResetRequest &) override {}

    runtime::backend::SetupResult setup(const runtime::backend::SetupRequest &request) override {
        record(Operation::setup);
        world_count_ = request.seeds.get().size();
        runtime::backend::SetupResult result{};
        for (std::size_t world = 0; world < world_count_; ++world) {
            result.entity_ids.push_back(1000 + world);
        }
        return result;
    }

    runtime::backend::InputResult inject(const runtime::backend::InputBatch &) override {
        record(Operation::input_injection);
        return {};
    }

    runtime::backend::EvaluationResult
    evaluate(const runtime::backend::EvaluationRequest &) const override {
        record(Operation::evaluation);
        runtime::backend::EvaluationResult result{};
        if (unexpected_evaluation_) {
            result.execution_episode_products.emplace_back();
        }
        return result;
    }

    runtime::backend::AdvanceResult advance(const runtime::backend::AdvanceRequest &) override {
        record(Operation::advance);
        return {};
    }

    runtime::backend::ExportResult
    export_state(const runtime::backend::ExportRequest &request) const override {
        record(Operation::export_state);
        runtime::backend::ExportResult result{};
        const std::size_t count = bad_export_cardinality_ && !request.refs.get().empty()
                                      ? request.refs.get().size() - 1
                                      : request.refs.get().size();
        result.agent_observations.resize(count);
        result.instrument_states.resize(count);
        for (std::size_t world = 0; world < count; ++world) {
            result.agent_observations[world].id = request.refs.get()[world].entity_id;
        }
        if (bad_export_identity_ && !result.agent_observations.empty()) {
            ++result.agent_observations.front().id;
        }
        return result;
    }

    runtime::backend::Diagnostics diagnostics() const override {
        return {.backend_id = "fake_backend", .world_count = world_count_};
    }

    void set_unexpected_evaluation(bool value) noexcept { unexpected_evaluation_ = value; }

    void set_bad_export_cardinality(bool value) noexcept { bad_export_cardinality_ = value; }

    void set_bad_export_identity(bool value) noexcept { bad_export_identity_ = value; }

    [[nodiscard]] const std::vector<Operation> &calls() const noexcept { return calls_; }

  private:
    void record(Operation operation) const {
        calls_.push_back(operation);
        if (fail_ && failure_ == operation) {
            throw std::runtime_error("fake failure at " +
                                     std::string(full_window::operation_name(operation)));
        }
    }

    Operation failure_;
    bool fail_ = false;
    bool unexpected_evaluation_ = false;
    bool bad_export_cardinality_ = false;
    bool bad_export_identity_ = false;
    std::size_t world_count_ = 0;
    mutable std::vector<Operation> calls_;
};

struct FailureCase {
    Operation operation;
    FailureCode code;
    std::string last_barrier;
    std::size_t expected_calls;
};

runtime::backend::SetupResult setup_cuda(runtime::cuda_resident::CudaResidentBackend &backend,
                                         const replay::ReplayTrace &trace) {
    return backend.setup({
        .kind = runtime::backend::SetupKind::Batch,
        .seeds = trace.seeds,
        .spawn_requests = trace.spawns,
        .time_steps = trace.time_steps,
    });
}

} // namespace

TEST_CASE("CR2-2 full-window runner records one common multi-window SPI") {
    FakeBackend backend;
    full_window::Runner runner(backend, {.lane = replay::ReplayLaneKind::cpu_reference,
                                         .backend_id = "fake_cpu_reference"});
    const auto trace = make_trace();
    const auto result = runner.run(trace);

    REQUIRE(result.completed);
    CHECK_FALSE(result.failure.has_value());
    CHECK(result.surface_id == full_window::kSurfaceId);
    CHECK(result.backend_id == "fake_cpu_reference");
    CHECK(result.trace_signature == replay::CudaResidentReplayHarness::trace_signature(trace));
    REQUIRE(result.operations.size() == 9);
    REQUIRE(result.export_frames.size() == trace.windows.size());
    CHECK(result.operations[0].operation == Operation::setup);
    CHECK(result.operations[0].barrier_id.empty());
    for (std::size_t window = 0; window < trace.windows.size(); ++window) {
        const std::size_t offset = 1 + window * 4;
        CHECK(result.operations[offset].operation == Operation::input_injection);
        CHECK(result.operations[offset].barrier_id == full_window::kInputBarrier);
        CHECK(result.operations[offset + 1].operation == Operation::evaluation);
        CHECK(result.operations[offset + 1].barrier_id.empty());
        CHECK(result.operations[offset + 2].operation == Operation::advance);
        CHECK(result.operations[offset + 2].barrier_id == full_window::kWindowBarrier);
        CHECK(result.operations[offset + 3].operation == Operation::export_state);
        CHECK(result.operations[offset + 3].barrier_id == full_window::kExportBarrier);
        const auto &frame = result.export_frames[window];
        CHECK(frame.window_index == window);
        CHECK(frame.request_id == trace.windows[window].request_id);
        CHECK(frame.source_barrier == full_window::kWindowBarrier);
        CHECK(frame.capture_barrier == full_window::kExportBarrier);
        REQUIRE(frame.agent_observations.size() == trace.seeds.size());
        REQUIRE(frame.instrument_states.size() == trace.seeds.size());
        for (std::size_t world = 0; world < trace.seeds.size(); ++world) {
            CHECK(frame.agent_observations[world].id == 1000 + world);
        }
        for (std::size_t step = 0; step < 4; ++step) {
            CHECK(result.operations[offset + step].window_index == window);
            CHECK(result.operations[offset + step].request_id == trace.windows[window].request_id);
        }
    }
}

TEST_CASE("CR2-4b release contract partitions raw DTO fields and stays fail-closed") {
    namespace parity_release = runtime::cuda_resident::parity_release;
    CHECK(parity_release::partition_is_complete());
    CHECK(parity_release::kReleasedNumericFields.size() == 12);
    CHECK(parity_release::kIdentityDiagnosticFields.size() == 1);
    CHECK(parity_release::kExcludedFields.size() == 53);
    CHECK(parity_release::kRawObservationFields.size() +
              parity_release::kRawInstrumentFields.size() ==
          parity_release::kReleasedNumericFields.size() +
              parity_release::kIdentityDiagnosticFields.size() +
              parity_release::kExcludedFields.size());
    CHECK(parity_release::kCandidatePromotionBlocked);
    CHECK_FALSE(parity_release::kMaintainedClaimAllowed);
    CHECK_FALSE(parity_release::kPublicSupportEnabled);
    CHECK(parity_release::kMeasuredConsumerPathUnchanged);
}

TEST_CASE("CR2-2 full-window runner fails closed at each operation and poisons") {
    const std::vector<FailureCase> cases = {
        {Operation::setup, FailureCode::setup_failed, "", 1},
        {Operation::input_injection, FailureCode::input_failed, "", 2},
        {Operation::evaluation, FailureCode::evaluation_failed,
         std::string(full_window::kInputBarrier), 3},
        {Operation::advance, FailureCode::advance_failed, std::string(full_window::kInputBarrier),
         4},
        {Operation::export_state, FailureCode::export_failed,
         std::string(full_window::kWindowBarrier), 5},
    };
    for (const auto &failure : cases) {
        CAPTURE(full_window::operation_name(failure.operation));
        FakeBackend backend(failure.operation, true);
        full_window::Runner runner(backend, {.lane = replay::ReplayLaneKind::cpu_reference,
                                             .backend_id = "fake_cpu_reference"});
        const auto trace = make_trace();
        const auto result = runner.run(trace);
        REQUIRE_FALSE(result.completed);
        REQUIRE(result.failure.has_value());
        CHECK(result.failure->code == failure.code);
        CHECK(result.failure->operation == failure.operation);
        CHECK(result.failure->last_completed_barrier == failure.last_barrier);
        CHECK(backend.calls().size() == failure.expected_calls);
        CHECK(result.operations.size() == failure.expected_calls);
        CHECK_FALSE(result.operations.back().succeeded);

        const std::size_t calls_before_poison_check = backend.calls().size();
        const auto poisoned = runner.run(trace);
        REQUIRE(poisoned.failure.has_value());
        CHECK(poisoned.failure->code == FailureCode::session_poisoned);
        CHECK(backend.calls().size() == calls_before_poison_check);
    }
}

TEST_CASE("CR2-2 full-window runner rejects output shape drift before advance or completion") {
    const auto trace = make_trace();

    FakeBackend evaluation_backend;
    evaluation_backend.set_unexpected_evaluation(true);
    full_window::Runner evaluation_runner(
        evaluation_backend,
        {.lane = replay::ReplayLaneKind::cpu_reference, .backend_id = "fake_cpu_reference"});
    const auto unexpected = evaluation_runner.run(trace);
    REQUIRE(unexpected.failure.has_value());
    CHECK(unexpected.failure->code == FailureCode::unexpected_evaluation_output);
    CHECK(unexpected.failure->last_completed_barrier == full_window::kInputBarrier);
    CHECK(evaluation_backend.calls().size() == 3);

    FakeBackend export_backend;
    export_backend.set_bad_export_cardinality(true);
    full_window::Runner export_runner(
        export_backend,
        {.lane = replay::ReplayLaneKind::cuda_resident, .backend_id = "fake_cuda_resident"});
    const auto cardinality = export_runner.run(trace);
    REQUIRE(cardinality.failure.has_value());
    CHECK(cardinality.failure->code == FailureCode::export_cardinality_mismatch);
    CHECK(cardinality.failure->last_completed_barrier == full_window::kWindowBarrier);
    CHECK(export_backend.calls().size() == 5);

    FakeBackend identity_backend;
    identity_backend.set_bad_export_identity(true);
    full_window::Runner identity_runner(
        identity_backend,
        {.lane = replay::ReplayLaneKind::cuda_resident, .backend_id = "fake_cuda_resident"});
    const auto identity = identity_runner.run(trace);
    REQUIRE(identity.failure.has_value());
    CHECK(identity.failure->code == FailureCode::export_identity_mismatch);
    CHECK(identity.failure->last_completed_barrier == full_window::kWindowBarrier);
    CHECK(identity.export_frames.empty());
    CHECK(identity_backend.calls().size() == 5);
}

TEST_CASE("CR2-2 CUDA backend accepts empty evaluation and auto-advances the common SPI") {
    using namespace runtime::cuda_resident;
    CudaResidentBackend backend;
    if (!CudaWorldStore::compiled_with_cuda()) {
        CHECK_THROWS_AS(backend.configure({.world_count = 2}), std::runtime_error);
        return;
    }
    backend.configure({.world_count = 2});
    const auto trace = make_trace();

    CHECK(backend.evaluate({}).execution_episode_products.empty());
    const std::vector<WorldExecutionEpisodeStepRequest> nonempty_evaluation(1);
    CHECK_THROWS_AS((void)backend.evaluate({.execution_episode_requests = nonempty_evaluation}),
                    std::logic_error);

    full_window::Runner runner(backend, {.lane = replay::ReplayLaneKind::cuda_resident,
                                         .backend_id = std::string(kCudaResidentRb7BackendId)});
    const auto result = runner.run(trace);
    REQUIRE(result.completed);
    CHECK_FALSE(result.failure.has_value());
    CHECK(result.operations.size() == 9);

    const auto &store = testing::CudaResidentBackendTestAccess::world_store(backend);
    const auto state = testing::CudaWorldStoreTestAccess::read_state(store);
    REQUIRE(state.worlds.size() == trace.seeds.size());
    CHECK(state.worlds[0].clock_tick == trace.windows.size());
    CHECK(state.worlds[0].barrier == CudaResidentBarrierCode::window_commit);
}

TEST_CASE("CR2-2 CUDA window state rejects missing input and retries commit without republish") {
    using namespace runtime::cuda_resident;
    CudaResidentBackend backend;
    if (!CudaWorldStore::compiled_with_cuda()) {
        CHECK(true);
        return;
    }
    backend.configure({.world_count = 2});
    const auto trace = make_trace();
    const auto setup = setup_cuda(backend, trace);
    REQUIRE(setup.entity_ids.size() == trace.seeds.size());

    CHECK_THROWS_AS(backend.advance({.kind = runtime::backend::AdvanceKind::WorldBatch}),
                    std::runtime_error);
    const auto assignments = make_assignments(trace.windows.front(), setup.entity_ids);
    backend.inject({.pilot_actions = assignments});
    CHECK_THROWS_AS(backend.inject({.pilot_actions = assignments}), std::runtime_error);
    backend.publish_stage();

    auto &store = testing::CudaResidentBackendTestAccess::world_store(backend);
    const auto before_failure = testing::CudaWorldStoreTestAccess::read_state(store);
    testing::CudaWorldStoreTestAccess::fail_next_state_transfer(store);
    CHECK_THROWS_AS(backend.advance({.kind = runtime::backend::AdvanceKind::WorldBatch}),
                    std::runtime_error);
    const auto after_failure = testing::CudaWorldStoreTestAccess::read_state(store);
    REQUIRE(after_failure.worlds.size() == before_failure.worlds.size());
    CHECK(after_failure.worlds[0].barrier_sequence == before_failure.worlds[0].barrier_sequence);
    CHECK(after_failure.worlds[0].barrier == CudaResidentBarrierCode::stage_publish);

    CHECK_THROWS_AS(backend.inject({.pilot_actions = assignments}), std::runtime_error);
    backend.advance({.kind = runtime::backend::AdvanceKind::WorldBatch});
    const auto retried = testing::CudaWorldStoreTestAccess::read_state(store);
    CHECK(retried.worlds[0].barrier_sequence == before_failure.worlds[0].barrier_sequence + 1);
    CHECK(retried.worlds[0].clock_tick == before_failure.worlds[0].clock_tick + 1);
    CHECK(retried.worlds[0].barrier == CudaResidentBarrierCode::window_commit);
}
