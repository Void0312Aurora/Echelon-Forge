#include "tests/test_cuda_resident_replay_support.h"

#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "runtime/contracts/cuda_resident_phase_d_fixture_contract.h"
#include "runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.h"

namespace runtime::cuda_resident::replay::test_support {

namespace {

std::vector<WorldPilotActionAssignment>
make_assignments(const ReplayTrace &trace, std::size_t window,
                 const std::vector<std::uint64_t> &entity_ids) {
    std::vector<WorldPilotActionAssignment> assignments;
    assignments.reserve(entity_ids.size());
    for (std::size_t world = 0; world < entity_ids.size(); ++world) {
        assignments.push_back({
            .world_index = world,
            .entity_id = entity_ids[world],
            .action = trace.windows[window].actions[world],
        });
    }
    return assignments;
}

} // namespace

ReplayLaneResult run_cpu_reference(const ReplayTrace &trace) {
    using namespace runtime::cuda_resident;
    using namespace runtime::cuda_resident::replay;
    if (trace.windows.size() != 1 || trace.seeds.size() != kCudaResidentPhaseBFirstExpected.size()) {
        throw std::invalid_argument("RB8 fixed CPU oracle owns exactly one two-world window");
    }
    const std::vector<std::uint64_t> entity_ids(trace.seeds.size(), fixed_air_fixture_entity_id(0));

    ReplayLaneResult result{
        .lane = ReplayLaneKind::cpu_reference,
        .backend_id = "fixed_air_cpu_fixture_oracle",
        .trace_signature = CudaResidentReplayHarness::trace_signature(trace),
        .completed = false,
    };
    for (std::size_t window = 0; window < trace.windows.size(); ++window) {
        result.frames.push_back(make_input_frame(trace, window, entity_ids));
        std::vector<ProjectedWorld> window_worlds;
        std::vector<ProjectedWorld> export_worlds;
        window_worlds.reserve(entity_ids.size());
        export_worlds.reserve(entity_ids.size());
        for (std::size_t world = 0; world < entity_ids.size(); ++world) {
            window_worlds.push_back(project_cpu_oracle(
                trace, world, entity_ids[world], window, "window_commit",
                trace.windows[window].request_id));
            export_worlds.push_back(project_cpu_oracle(
                trace, world, entity_ids[world], window, "export",
                trace.windows[window].request_id));
        }
        result.frames.push_back(
            make_projection_frame(trace, window, "window_commit", window_worlds));
        result.frames.push_back(make_projection_frame(trace, window, "export", export_worlds));
    }
    result.completed = true;
    return result;
}

ReplayLaneResult run_cuda_resident(const ReplayTrace &trace) {
    using namespace runtime::cuda_resident;
    using namespace runtime::cuda_resident::replay;
    if (!CudaWorldStore::compiled_with_cuda()) {
        return {
            .lane = ReplayLaneKind::cuda_resident,
            .backend_id = std::string(kCudaResidentRb7BackendId),
            .trace_signature = CudaResidentReplayHarness::trace_signature(trace),
            .completed = false,
            .failure_code = "cuda_not_compiled",
        };
    }
    CudaResidentBackend backend;
    backend.configure({.world_count = trace.seeds.size()});
    const auto setup = backend.setup({
        .kind = runtime::backend::SetupKind::Batch,
        .seeds = trace.seeds,
        .spawn_requests = trace.spawns,
        .time_steps = trace.time_steps,
    });
    if (setup.entity_ids.size() != trace.seeds.size()) {
        throw std::runtime_error("RB8 CUDA setup cardinality mismatch");
    }

    ReplayLaneResult result{
        .lane = ReplayLaneKind::cuda_resident,
        .backend_id = std::string(kCudaResidentRb7BackendId),
        .trace_signature = CudaResidentReplayHarness::trace_signature(trace),
        .completed = false,
    };
    for (std::size_t window = 0; window < trace.windows.size(); ++window) {
        const auto assignments = make_assignments(trace, window, setup.entity_ids);
        backend.inject({.pilot_actions = assignments});
        result.frames.push_back(make_input_frame(trace, window, setup.entity_ids));
        backend.publish_stage();
        backend.advance({.kind = runtime::backend::AdvanceKind::WorldBatch});

        const auto &store = testing::CudaResidentBackendTestAccess::world_store(backend);
        const auto resident = testing::CudaWorldStoreTestAccess::read_state(store);
        std::vector<ProjectedWorld> window_worlds;
        window_worlds.reserve(resident.worlds.size());
        for (const auto &state : resident.worlds) {
            window_worlds.push_back(project_cuda_state(
                state, window, "window_commit", trace.windows[window].request_id));
        }
        result.frames.push_back(
            make_projection_frame(trace, window, "window_commit", window_worlds));

        const auto snapshot = backend.export_snapshot(trace.windows[window].request_id);
        std::vector<ProjectedWorld> export_worlds;
        export_worlds.reserve(snapshot.worlds.size());
        for (const auto &world : snapshot.worlds) {
            export_worlds.push_back(
                project_cuda_snapshot(world, window, trace.windows[window].request_id));
        }
        result.frames.push_back(make_projection_frame(trace, window, "export", export_worlds));
    }
    result.completed = true;
    return result;
}

ReplayTrace make_trace() {
    using namespace runtime::cuda_resident;
    ReplayTrace trace{
        .run_id = "rb8.fixed_air.replay.001",
        .seeds = {101, 202},
        .time_steps = {0.05, 0.125},
    };
    for (std::size_t world = 0; world < trace.seeds.size(); ++world) {
        trace.spawns.push_back({
            .world_index = world,
            .type_name = std::string(kFixedAirFixtureTypeName),
            .entity_name = "RB8Replay" + std::to_string(world),
            .is_agent = true,
            .x = 1000.0 + static_cast<double>(world) * 100.0,
            .y = -50.0 * static_cast<double>(world),
            .z = 1500.0 + static_cast<double>(world) * 10.0,
            .heading = 90.0 - static_cast<double>(world) * 5.0,
            .pitch = 2.0,
            .roll = -3.0,
            .vx = 200.0 + static_cast<double>(world),
            .vy = 2.0 * static_cast<double>(world),
            .vz = -1.0,
        });
    }
    for (std::size_t window = 0; window < 1; ++window) {
        runtime::cuda_resident::replay::ReplayActionWindow actions{
            .request_id = "rb8.window." + std::to_string(window),
        };
        for (std::size_t world = 0; world < trace.seeds.size(); ++world) {
            PilotAction action{};
            action.stick_pitch = kCudaResidentPhaseBFirstInputs[world].stick_pitch;
            action.stick_roll = kCudaResidentPhaseBFirstInputs[world].stick_roll;
            action.rudder = kCudaResidentPhaseBFirstInputs[world].rudder;
            action.throttle = kCudaResidentPhaseBFirstInputs[world].throttle;
            action.gear_handle = 0.0F;
            action.flaps = 0.1F;
            action.speedbrake = 0.0F;
            action.brake = 0.0;
            action.active = true;
            actions.actions.push_back(action);
        }
        trace.windows.push_back(std::move(actions));
    }
    return trace;
}

} // namespace runtime::cuda_resident::replay::test_support
