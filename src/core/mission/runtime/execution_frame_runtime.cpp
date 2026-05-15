#include "core/mission/runtime/execution_frame_runtime.h"

#include <algorithm>
#include <exception>
#include <mutex>
#include <thread>

namespace {

size_t hardware_thread_count() noexcept {
    const unsigned int hc = std::thread::hardware_concurrency();
    return hc == 0U ? 1U : static_cast<size_t>(hc);
}

template <typename Fn>
void parallel_for_index(size_t task_count, Fn&& fn) {
    if (task_count == 0) {
        return;
    }
    // Keep small batches on one thread to avoid scheduling overhead.
    if (task_count < 64) {
        for (size_t i = 0; i < task_count; ++i) {
            fn(i);
        }
        return;
    }

    const size_t thread_count = std::min(task_count, hardware_thread_count());
    if (thread_count <= 1) {
        for (size_t i = 0; i < task_count; ++i) {
            fn(i);
        }
        return;
    }

    const size_t chunk_size = (task_count + thread_count - 1) / thread_count;
    std::vector<std::thread> workers;
    workers.reserve(thread_count - 1);

    std::exception_ptr first_exception;
    std::mutex exception_mutex;

    auto run_range = [&](size_t begin, size_t end) {
        for (size_t i = begin; i < end; ++i) {
            try {
                fn(i);
            } catch (...) {
                std::lock_guard<std::mutex> lock(exception_mutex);
                if (first_exception == nullptr) {
                    first_exception = std::current_exception();
                }
                break;
            }
        }
    };

    size_t begin = 0;
    for (size_t worker_idx = 1; worker_idx < thread_count; ++worker_idx) {
        const size_t end = std::min(task_count, begin + chunk_size);
        workers.emplace_back(run_range, begin, end);
        begin = end;
    }
    run_range(begin, task_count);
    for (auto& worker : workers) {
        worker.join();
    }
    if (first_exception != nullptr) {
        std::rethrow_exception(first_exception);
    }
}

}  // namespace

ExecutionFrameRuntimeProducts compute_execution_frame_runtime(const ExecutionFrameRuntimeInputs& inputs) {
    ExecutionFrameRuntimeProducts out{};
    out.valid = true;

    if (inputs.has_mission_observation) {
        out.mission_observation_evaluated = true;
        out.mission_observation = compute_mission_observation(inputs.mission_observation);
    }

    if (inputs.has_step_info) {
        out.step_info_evaluated = true;
        out.step_info = compute_step_info_runtime(inputs.step_info);
    }

    if (inputs.has_execution_step) {
        out.execution_step_evaluated = true;
        out.execution_step = compute_execution_step_runtime(inputs.execution_step);
    }

    if (inputs.has_flight_shaping) {
        out.flight_shaping_evaluated = true;
        out.flight_shaping = compute_flight_shaping_terms(inputs.flight_shaping);
    }

    return out;
}

std::vector<ExecutionFrameRuntimeProducts> compute_execution_frame_runtime_batch(
    const std::vector<ExecutionFrameRuntimeInputs>& inputs_batch
) {
    std::vector<ExecutionFrameRuntimeProducts> out(inputs_batch.size());
    parallel_for_index(inputs_batch.size(), [&](size_t i) {
        out[i] = compute_execution_frame_runtime(inputs_batch[i]);
    });
    return out;
}
