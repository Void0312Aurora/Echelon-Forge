#include "runtime/facade/internal/cuda_resident/cuda_resident_backend.h"

#include <doctest/doctest.h>

#include <array>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "runtime/contracts/cuda_resident_phase_a_fixture_contract.h"

namespace {

struct PhaseAFixture {
    std::vector<std::uint32_t> seeds = {101, 202};
    std::vector<WorldSpawnRequest> spawns;
    std::vector<double> time_steps =
        std::vector<double>(runtime::cuda_resident::kCudaResidentPhaseAFixtureTimeSteps.begin(),
                            runtime::cuda_resident::kCudaResidentPhaseAFixtureTimeSteps.end());

    PhaseAFixture() {
        for (std::size_t world = 0; world < seeds.size(); ++world) {
            WorldSpawnRequest spawn{};
            spawn.world_index = world;
            spawn.type_name = std::string(runtime::cuda_resident::kFixedAirFixtureTypeName);
            spawn.entity_name = "RB5PhaseA" + std::to_string(world);
            spawn.is_agent = true;
            spawn.x = 1000.0 + static_cast<double>(world) * 100.0;
            spawn.z = 1500.0;
            spawn.vx = 200.0 + static_cast<double>(world);
            spawn.heading = 90.0;
            spawns.push_back(std::move(spawn));
        }
    }

    runtime::backend::SetupRequest request() const {
        return {
            .kind = runtime::backend::SetupKind::Batch,
            .seeds = seeds,
            .spawn_requests = spawns,
            .time_steps = time_steps,
        };
    }
};

std::vector<WorldPilotActionAssignment>
make_actions(const std::vector<std::uint64_t> &entity_ids,
             const std::array<runtime::cuda_resident::CudaResidentPhaseAFixtureInput, 2> &inputs) {
    std::vector<WorldPilotActionAssignment> actions;
    actions.reserve(entity_ids.size());
    for (std::size_t world = 0; world < entity_ids.size(); ++world) {
        WorldPilotActionAssignment assignment{};
        assignment.world_index = world;
        assignment.entity_id = entity_ids[world];
        assignment.action.stick_roll = inputs[world].stick_roll;
        assignment.action.stick_pitch = inputs[world].stick_pitch;
        assignment.action.rudder = inputs[world].rudder;
        assignment.action.active = inputs[world].active;
        actions.push_back(assignment);
    }
    return actions;
}

void check_prepared(
    const runtime::cuda_resident::CudaWorldStoreStateSnapshot &state,
    const std::array<runtime::cuda_resident::CudaResidentPhaseAFixtureExpected, 2> &expected) {
    REQUIRE(state.worlds.size() == expected.size());
    for (std::size_t world = 0; world < expected.size(); ++world) {
        const auto &actual = state.worlds[world].prepared_controls;
        const auto &want = expected[world];
        CHECK(actual.valid);
        CHECK(actual.manual_takeover == want.manual_takeover);
        CHECK(actual.phase_version == want.phase_version);
        CHECK(actual.stick_roll_filt == doctest::Approx(want.stick_roll_filt).epsilon(1e-12));
        CHECK(actual.stick_pitch_filt == doctest::Approx(want.stick_pitch_filt).epsilon(1e-12));
        CHECK(actual.stick_yaw_filt == doctest::Approx(want.stick_yaw_filt).epsilon(1e-12));
        CHECK(actual.stick_yaw_cmd == doctest::Approx(want.stick_yaw_cmd).epsilon(1e-12));
    }
}

} // namespace

TEST_CASE("RB5 Phase A prepares direct pilot controls in a resident SoA") {
    using namespace runtime::cuda_resident;
    if (!CudaWorldStore::compiled_with_cuda()) {
        CHECK(true);
        return;
    }

    CudaResidentBackend backend;
    backend.configure({.world_count = 2});
    const CudaBarrierKernelResources resources =
        testing::CudaWorldStoreTestAccess::phase_a_kernel_resources();
    CAPTURE(resources.registers_per_thread);
    CAPTURE(resources.local_bytes_per_thread);
    CAPTURE(resources.static_shared_bytes);
    CAPTURE(resources.threads_per_block);
    CAPTURE(resources.active_blocks_per_multiprocessor);
    CAPTURE(resources.active_warps_per_multiprocessor);
    CAPTURE(resources.theoretical_occupancy);
    CHECK(resources.registers_per_thread > 0);
    CHECK(resources.local_bytes_per_thread == 0);
    CHECK(resources.static_shared_bytes == 0);
    CHECK(resources.threads_per_block == 128);
    CHECK(resources.active_blocks_per_multiprocessor > 0);
    CHECK(resources.active_warps_per_multiprocessor > 0);
    CHECK(resources.theoretical_occupancy > 0.0);
    CHECK(resources.theoretical_occupancy <= 1.0);

    PhaseAFixture fixture;
    const auto setup = backend.setup(fixture.request());
    CHECK_THROWS_AS(backend.advance({.kind = runtime::backend::AdvanceKind::WorldBatch}),
                    std::runtime_error);
    const auto first_actions = make_actions(setup.entity_ids, kCudaResidentPhaseAFirstInputs);
    backend.inject({.pilot_actions = first_actions});
    backend.publish_stage();
    CudaWorldStore &store = testing::CudaResidentBackendTestAccess::world_store(backend);
    check_prepared(testing::CudaWorldStoreTestAccess::read_state(store),
                   kCudaResidentPhaseAFirstExpected);
    backend.advance({.kind = runtime::backend::AdvanceKind::WorldBatch});

    const auto edge_actions = make_actions(setup.entity_ids, kCudaResidentPhaseAEdgeInputs);
    backend.inject({.pilot_actions = edge_actions});
    testing::CudaWorldStoreTestAccess::fail_next_state_transfer(store);
    CHECK_THROWS_AS(backend.publish_stage(), std::runtime_error);
    backend.publish_stage();
    const CudaWorldStoreStateSnapshot edge_state =
        testing::CudaWorldStoreTestAccess::read_state(store);
    check_prepared(edge_state, kCudaResidentPhaseAEdgeExpected);
    CHECK(edge_state.worlds[1].controls.active);
    backend.advance({.kind = runtime::backend::AdvanceKind::WorldBatch});
}
