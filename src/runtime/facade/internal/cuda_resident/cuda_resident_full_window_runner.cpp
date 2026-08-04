#include "runtime/facade/internal/cuda_resident/cuda_resident_full_window_runner.h"

#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.h"

namespace runtime::cuda_resident::full_window {

namespace {

using replay::ReplayTrace;

void validate_trace(const ReplayTrace &trace) {
    if (trace.run_id.empty() || trace.seeds.empty() ||
        trace.seeds.size() != trace.spawns.size() ||
        trace.seeds.size() != trace.time_steps.size() || trace.windows.empty()) {
        throw std::invalid_argument("full-window trace setup/window cardinalities are invalid");
    }
    for (const auto &window : trace.windows) {
        if (window.request_id.empty() || window.actions.size() != trace.seeds.size()) {
            throw std::invalid_argument("full-window trace action window is incomplete");
        }
    }
}

std::string exception_detail() {
    return "backend operation failed without a standard exception detail";
}

template <typename Exception>
std::string exception_detail(const Exception &error) {
    return error.what();
}

std::vector<WorldEntityRef> make_refs(const std::vector<std::uint64_t> &entity_ids) {
    std::vector<WorldEntityRef> refs;
    refs.reserve(entity_ids.size());
    for (std::size_t world = 0; world < entity_ids.size(); ++world) {
        refs.push_back({.world_index = world, .entity_id = entity_ids[world]});
    }
    return refs;
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

} // namespace

Runner::Runner(IWorldBatchBackend &backend, RunnerConfig config)
    : backend_(&backend), config_(std::move(config)) {
    if (config_.backend_id.empty()) {
        config_.backend_id = backend_->diagnostics().backend_id;
    }
}

RunResult Runner::run(const ReplayTrace &trace) {
    RunResult result{
        .surface_id = std::string(kSurfaceId),
        .lane = config_.lane,
        .backend_id = config_.backend_id,
        .trace_signature = replay::CudaResidentReplayHarness::trace_signature(trace),
    };
    if (poisoned_) {
        result.failure = FailureRecord{
            .code = FailureCode::session_poisoned,
            .operation = Operation::setup,
            .detail = "runner session is poisoned; construct a new runner",
        };
        return result;
    }

    const auto fail = [&](Operation operation, std::size_t window_index,
                         FailureCode code, std::string_view last_barrier,
                         std::string detail, std::string request_id = std::string{}) {
        result.operations.push_back({
            .window_index = window_index,
            .request_id = std::move(request_id),
            .operation = operation,
            .succeeded = false,
            .barrier_id = {},
        });
        result.failure = FailureRecord{
            .code = code,
            .operation = operation,
            .window_index = window_index,
            .last_completed_barrier = std::string(last_barrier),
            .detail = std::move(detail),
        };
        poisoned_ = true;
        return result;
    };

    try {
        validate_trace(trace);
    } catch (const std::exception &error) {
        return fail(Operation::setup, 0, FailureCode::invalid_trace, {},
                    exception_detail(error), trace.run_id);
    } catch (...) {
        return fail(Operation::setup, 0, FailureCode::invalid_trace, {},
                    exception_detail(), trace.run_id);
    }

    std::vector<std::uint64_t> entity_ids;
    try {
        const auto setup = backend_->setup({
            .kind = runtime::backend::SetupKind::Batch,
            .seeds = trace.seeds,
            .spawn_requests = trace.spawns,
            .time_steps = trace.time_steps,
        });
        if (setup.entity_ids.size() != trace.seeds.size()) {
            throw std::runtime_error("full-window setup returned invalid entity cardinality");
        }
        entity_ids = setup.entity_ids;
        result.operations.push_back({
            .window_index = 0,
            .request_id = trace.run_id,
            .operation = Operation::setup,
            .succeeded = true,
            .barrier_id = {},
        });
    } catch (const std::exception &error) {
        return fail(Operation::setup, 0, FailureCode::setup_failed, {},
                    exception_detail(error), trace.run_id);
    } catch (...) {
        return fail(Operation::setup, 0, FailureCode::setup_failed, {},
                    exception_detail(), trace.run_id);
    }

    const std::vector<WorldEntityRef> refs = make_refs(entity_ids);
    std::string last_barrier;
    for (std::size_t window_index = 0; window_index < trace.windows.size(); ++window_index) {
        const auto &window = trace.windows[window_index];
        const std::string request_id = window.request_id;
        const auto assignments = make_assignments(window, entity_ids);

        try {
            backend_->inject({.pilot_actions = assignments});
            result.operations.push_back({
                .window_index = window_index,
                .request_id = request_id,
                .operation = Operation::input_injection,
                .succeeded = true,
                .barrier_id = std::string(kInputBarrier),
            });
            last_barrier = std::string(kInputBarrier);
        } catch (const std::exception &error) {
            return fail(Operation::input_injection, window_index, FailureCode::input_failed,
                        last_barrier, exception_detail(error), request_id);
        } catch (...) {
            return fail(Operation::input_injection, window_index, FailureCode::input_failed,
                        last_barrier, exception_detail(), request_id);
        }

        try {
            const auto evaluation = backend_->evaluate({});
            if (!evaluation.execution_episode_products.empty()) {
                return fail(Operation::evaluation, window_index,
                            FailureCode::unexpected_evaluation_output, last_barrier,
                            "full-window evaluation must return an empty result", request_id);
            }
            result.operations.push_back({
                .window_index = window_index,
                .request_id = request_id,
                .operation = Operation::evaluation,
                .succeeded = true,
                .barrier_id = {},
            });
        } catch (const std::exception &error) {
            return fail(Operation::evaluation, window_index, FailureCode::evaluation_failed,
                        last_barrier, exception_detail(error), request_id);
        } catch (...) {
            return fail(Operation::evaluation, window_index, FailureCode::evaluation_failed,
                        last_barrier, exception_detail(), request_id);
        }

        try {
            backend_->advance({.kind = runtime::backend::AdvanceKind::WorldBatch});
            result.operations.push_back({
                .window_index = window_index,
                .request_id = request_id,
                .operation = Operation::advance,
                .succeeded = true,
                .barrier_id = std::string(kWindowBarrier),
            });
            last_barrier = std::string(kWindowBarrier);
        } catch (const std::exception &error) {
            return fail(Operation::advance, window_index, FailureCode::advance_failed, last_barrier,
                        exception_detail(error), request_id);
        } catch (...) {
            return fail(Operation::advance, window_index, FailureCode::advance_failed, last_barrier,
                        exception_detail(), request_id);
        }

        try {
            auto exported = backend_->export_state({
                .refs = refs,
                .include_agent_observations = true,
                .include_instrument_states = true,
            });
            if (exported.agent_observations.size() != refs.size() ||
                exported.instrument_states.size() != refs.size()) {
                return fail(Operation::export_state, window_index,
                            FailureCode::export_cardinality_mismatch, last_barrier,
                            "full-window export cardinality does not match setup", request_id);
            }
            for (std::size_t world = 0; world < refs.size(); ++world) {
                if (exported.agent_observations[world].id != refs[world].entity_id) {
                    return fail(Operation::export_state, window_index,
                                FailureCode::export_identity_mismatch, last_barrier,
                                "full-window observation identity does not match setup", request_id);
                }
            }
            result.export_frames.push_back({
                .window_index = window_index,
                .request_id = request_id,
                .source_barrier = std::string(kWindowBarrier),
                .capture_barrier = std::string(kExportBarrier),
                .agent_observations = std::move(exported.agent_observations),
                .instrument_states = std::move(exported.instrument_states),
            });
            result.operations.push_back({
                .window_index = window_index,
                .request_id = request_id,
                .operation = Operation::export_state,
                .succeeded = true,
                .barrier_id = std::string(kExportBarrier),
            });
            last_barrier = std::string(kExportBarrier);
        } catch (const std::exception &error) {
            return fail(Operation::export_state, window_index, FailureCode::export_failed,
                        last_barrier, exception_detail(error), request_id);
        } catch (...) {
            return fail(Operation::export_state, window_index, FailureCode::export_failed,
                        last_barrier, exception_detail(), request_id);
        }
    }
    result.completed = true;
    return result;
}

} // namespace runtime::cuda_resident::full_window
