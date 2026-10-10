#pragma once

#include <algorithm>
#include <cstddef>
#include <exception>
#include <functional>
#include <mutex>
#include <thread>
#include <utility>
#include <vector>

namespace runtime::detail {

inline std::size_t hardware_thread_count() noexcept {
    const unsigned int hc = std::thread::hardware_concurrency();
    return hc == 0U ? 1U : static_cast<std::size_t>(hc);
}

// The worker factory is injectable so failure-path tests can deterministically
// throw while starting a later worker. The production overload uses jthread:
// if a later launch fails, already-started workers are joined during vector
// unwinding before the exception reaches the caller.
template <typename Fn, typename ThreadFactory>
void parallel_for_index(std::size_t task_count, std::size_t requested_threads, Fn &&fn,
                        ThreadFactory &&thread_factory) {
    if (task_count == 0) {
        return;
    }
    const std::size_t thread_count =
        std::min(task_count, requested_threads == 0 ? hardware_thread_count()
                                                    : std::max<std::size_t>(1, requested_threads));
    if (thread_count <= 1) {
        for (std::size_t i = 0; i < task_count; ++i) {
            fn(i);
        }
        return;
    }

    const std::size_t chunk_size = (task_count + thread_count - 1) / thread_count;

    // Keep these declarations in this order. jthread destruction must happen
    // before the mutex and exception state it protects are destroyed when a
    // worker launch throws during stack unwinding.
    std::exception_ptr first_exception;
    std::mutex exception_mutex;
    std::vector<std::jthread> workers;
    workers.reserve(thread_count - 1);

    auto run_range = [&](std::size_t begin, std::size_t end) {
        for (std::size_t i = begin; i < end; ++i) {
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

    std::size_t begin = 0;
    for (std::size_t worker_idx = 1; worker_idx < thread_count; ++worker_idx) {
        const std::size_t end = std::min(task_count, begin + chunk_size);
        workers.emplace_back(
            thread_factory(std::function<void()>([&, begin, end] { run_range(begin, end); })));
        begin = end;
    }
    run_range(begin, task_count);
    for (auto &worker : workers) {
        worker.join();
    }
    if (first_exception != nullptr) {
        std::rethrow_exception(first_exception);
    }
}

template <typename Fn>
void parallel_for_index(std::size_t task_count, std::size_t requested_threads, Fn &&fn) {
    parallel_for_index(task_count, requested_threads, std::forward<Fn>(fn),
                       [](std::function<void()> task) { return std::jthread(std::move(task)); });
}

} // namespace runtime::detail
