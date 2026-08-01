#include <cstddef>
#include <exception>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <nlohmann/json.hpp>

#include "runtime/facade/internal/cuda_resident/cuda_resident_full_window_runner.h"

#if defined(EF_CR2_FULL_WINDOW_CPU_PROBE) && defined(EF_CR2_FULL_WINDOW_CUDA_PROBE)
#error "CR2 full-window probe must select exactly one lane"
#elif defined(EF_CR2_FULL_WINDOW_CPU_PROBE)
#include "runtime/facade/internal/flecs_cpu_backend.h"
#include <spdlog/spdlog.h>
#elif defined(EF_CR2_FULL_WINDOW_CUDA_PROBE)
#include "runtime/facade/internal/cuda_resident/cuda_resident_backend.h"
#else
#error "CR2 full-window probe lane is not configured"
#endif

namespace {

namespace full_window = runtime::cuda_resident::full_window;
namespace replay = runtime::cuda_resident::replay;
using full_window::Operation;

inline constexpr std::string_view kProbeSchema =
    "cuda_resident.full_window_probe.v1";

replay::ReplayTrace make_trace() {
    replay::ReplayTrace trace{
        .run_id = "cr2.full_window.fixed_air",
        .seeds = {101, 202},
        .time_steps = {0.01, 0.02},
    };
    for (std::size_t world = 0; world < trace.seeds.size(); ++world) {
        WorldSpawnRequest spawn{};
        spawn.world_index = world;
        spawn.type_name =
            std::string(runtime::cuda_resident::kFixedAirFixtureTypeName);
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

std::string database_path_from_args(int argc, char **argv) {
    std::string database_path = "examples/config/database";
    for (int index = 1; index < argc; ++index) {
        const std::string_view argument(argv[index]);
        if (argument == "--database" && index + 1 < argc) {
            database_path = argv[++index];
        } else {
            throw std::invalid_argument(
                "usage: full-window probe [--database <path>]");
        }
    }
    return database_path;
}

void verify_common_sequence(const full_window::RunResult &result,
                            std::size_t window_count) {
    const std::vector<Operation> per_window{
        Operation::input_injection,
        Operation::evaluation,
        Operation::advance,
        Operation::export_state,
    };
    if (!result.completed || result.operations.size() != 1 + per_window.size() * window_count ||
        result.operations.front().operation != Operation::setup) {
        throw std::runtime_error("full-window probe did not complete the common operation sequence");
    }
    for (std::size_t window = 0; window < window_count; ++window) {
        for (std::size_t operation = 0; operation < per_window.size(); ++operation) {
            const auto &record = result.operations[1 + window * per_window.size() + operation];
            if (!record.succeeded || record.window_index != window ||
                record.operation != per_window[operation]) {
                throw std::runtime_error("full-window probe operation order diverged");
            }
        }
    }
}

nlohmann::json to_json(const full_window::RunResult &result) {
    nlohmann::json operations = nlohmann::json::array();
    for (const auto &record : result.operations) {
        operations.push_back({
            {"window_index", record.window_index},
            {"request_id", record.request_id},
            {"operation", full_window::operation_name(record.operation)},
            {"succeeded", record.succeeded},
            {"barrier_id", record.barrier_id},
        });
    }
    nlohmann::json output{
        {"schema_version", kProbeSchema},
        {"surface_id", result.surface_id},
        {"lane", replay::replay_lane_name(result.lane)},
        {"backend_id", result.backend_id},
        {"trace_signature", result.trace_signature},
        {"completed", result.completed},
        {"operations", std::move(operations)},
    };
    if (result.failure.has_value()) {
        output["failure"] = {
            {"code", full_window::failure_code_name(result.failure->code)},
            {"operation", full_window::operation_name(result.failure->operation)},
            {"window_index", result.failure->window_index},
            {"last_completed_barrier", result.failure->last_completed_barrier},
            {"detail", result.failure->detail},
        };
    } else {
        output["failure"] = nullptr;
    }
    return output;
}

} // namespace

int main(int argc, char **argv) {
    try {
        const std::string database_path = database_path_from_args(argc, argv);
        const replay::ReplayTrace trace = make_trace();
#if defined(EF_CR2_FULL_WINDOW_CPU_PROBE)
        spdlog::set_level(spdlog::level::warn);
        FlecsCpuBackend backend;
        backend.configure({.world_count = trace.seeds.size(), .worker_threads = 0});
        const auto content = backend.load_content({
            .kind = runtime::backend::ContentKind::Database,
            .path = &database_path,
        });
        if (!content.loaded) {
            throw std::runtime_error("CR2 CPU database load failed before runner entry");
        }
        full_window::Runner runner(
            backend, {.lane = replay::ReplayLaneKind::cpu_reference});
#else
        (void)database_path;
        if (!runtime::cuda_resident::CudaWorldStore::compiled_with_cuda()) {
            throw std::runtime_error("CR2 CUDA full-window probe was built without CUDA");
        }
        runtime::cuda_resident::CudaResidentBackend backend;
        backend.configure({.world_count = trace.seeds.size()});
        full_window::Runner runner(
            backend, {.lane = replay::ReplayLaneKind::cuda_resident});
#endif
        const full_window::RunResult result = runner.run(trace);
        verify_common_sequence(result, trace.windows.size());
        std::cout << to_json(result).dump(2) << '\n';
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "CR2 full-window probe failed: " << error.what() << '\n';
        return 2;
    }
}
