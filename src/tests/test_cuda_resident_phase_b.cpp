#include "runtime/facade/internal/cuda_resident/cuda_resident_backend.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <stdexcept>
#include <string>
#include <vector>

#include "runtime/contracts/cuda_resident_phase_b_fixture_contract.h"

namespace {

bool within_rb2_kinematics_budget(double actual, double expected) {
    return std::abs(actual - expected) <=
           std::max(1.0e-9, 1.0e-12 * std::max(std::abs(actual), std::abs(expected)));
}

void check_kernel_resources(const runtime::cuda_resident::CudaBarrierKernelResources &resources) {
    CAPTURE(resources.registers_per_thread);
    CAPTURE(resources.local_bytes_per_thread);
    CAPTURE(resources.static_shared_bytes);
    CAPTURE(resources.active_blocks_per_multiprocessor);
    CAPTURE(resources.active_warps_per_multiprocessor);
    CAPTURE(resources.theoretical_occupancy);
    CHECK(resources.registers_per_thread > 0);
    CHECK(resources.threads_per_block == 128);
    CHECK(resources.active_blocks_per_multiprocessor > 0);
    CHECK(resources.active_warps_per_multiprocessor > 0);
    CHECK(resources.theoretical_occupancy > 0.0);
    CHECK(resources.theoretical_occupancy <= 1.0);
}

} // namespace

TEST_CASE("RB6 Phase B commits CPU-parity airframe dynamics from resident state") {
    using namespace runtime::cuda_resident;
    if (!CudaWorldStore::compiled_with_cuda()) {
        CHECK(true);
        return;
    }
    CudaResidentBackend backend;
    backend.configure({.world_count = 2});
    check_kernel_resources(testing::CudaWorldStoreTestAccess::phase_b_forces_kernel_resources());
    check_kernel_resources(
        testing::CudaWorldStoreTestAccess::phase_b_aerodynamics_kernel_resources());
    check_kernel_resources(testing::CudaWorldStoreTestAccess::phase_b_integrate_kernel_resources());
    const std::vector<std::uint32_t> seeds = {101, 202};
    std::vector<WorldSpawnRequest> spawns;
    for (std::size_t world = 0; world < seeds.size(); ++world) {
        WorldSpawnRequest spawn{};
        spawn.world_index = world;
        spawn.type_name = std::string(kFixedAirFixtureTypeName);
        spawn.entity_name = "RB6PhaseB" + std::to_string(world);
        spawn.is_agent = true;
        spawn.x = 1000.0 + static_cast<double>(world) * 100.0;
        spawn.z = 1500.0;
        spawn.vx = 200.0 + static_cast<double>(world);
        spawn.heading = 90.0;
        spawns.push_back(spawn);
    }
    const std::vector<double> time_steps(kCudaResidentPhaseBFixtureTimeSteps.begin(),
                                         kCudaResidentPhaseBFixtureTimeSteps.end());
    const auto setup = backend.setup({
        .kind = runtime::backend::SetupKind::Batch,
        .seeds = seeds,
        .spawn_requests = spawns,
        .time_steps = time_steps,
    });
    std::vector<WorldPilotActionAssignment> actions;
    for (std::size_t world = 0; world < seeds.size(); ++world) {
        WorldPilotActionAssignment action{};
        action.world_index = world;
        action.entity_id = setup.entity_ids[world];
        action.action.active = true;
        action.action.stick_roll = kCudaResidentPhaseBFirstInputs[world].stick_roll;
        action.action.stick_pitch = kCudaResidentPhaseBFirstInputs[world].stick_pitch;
        action.action.rudder = kCudaResidentPhaseBFirstInputs[world].rudder;
        action.action.throttle = kCudaResidentPhaseBFirstInputs[world].throttle;
        actions.push_back(action);
    }
    backend.inject({.pilot_actions = actions});
    backend.publish_stage();
    backend.advance({.kind = runtime::backend::AdvanceKind::WorldBatch});
    auto &store = testing::CudaResidentBackendTestAccess::world_store(backend);
    const auto state = testing::CudaWorldStoreTestAccess::read_state(store);
    REQUIRE(state.worlds.size() == 2);
    for (std::size_t world = 0; world < state.worlds.size(); ++world) {
        const auto &actual = state.worlds[world];
        const std::array<double, 9> kinematics = {
            actual.kinematics.x,       actual.kinematics.y,     actual.kinematics.z,
            actual.kinematics.vx,      actual.kinematics.vy,    actual.kinematics.vz,
            actual.kinematics.heading, actual.kinematics.pitch, actual.kinematics.roll,
        };
        const std::array<double, 11> dynamics = {
            actual.dynamics.p,
            actual.dynamics.q,
            actual.dynamics.r,
            actual.dynamics.elevator_pos,
            actual.dynamics.aileron_pos,
            actual.dynamics.rudder_pos,
            actual.dynamics.dynamic_pressure,
            actual.dynamics.angle_of_attack,
            actual.dynamics.sideslip_angle,
            actual.dynamics.mach_number,
            actual.dynamics.drag_coefficient,
        };
        for (std::size_t field = 0; field < kinematics.size(); ++field) {
            CAPTURE(world);
            CAPTURE(field);
            CAPTURE(kinematics[field]);
            CAPTURE(kCudaResidentPhaseBFirstExpected[world].kinematics[field]);
            CHECK(within_rb2_kinematics_budget(
                kinematics[field], kCudaResidentPhaseBFirstExpected[world].kinematics[field]));
        }
        for (std::size_t field = 0; field < dynamics.size(); ++field) {
            CAPTURE(world);
            CAPTURE(field);
            CAPTURE(dynamics[field]);
            CAPTURE(kCudaResidentPhaseBFirstExpected[world].dynamics[field]);
            CHECK(within_rb2_kinematics_budget(
                dynamics[field], kCudaResidentPhaseBFirstExpected[world].dynamics[field]));
        }
        CHECK(actual.clock_tick == 1);
        CHECK(actual.shard_versions[static_cast<std::size_t>(CudaResidentShard::dynamics)] == 2);
        CHECK(actual.shard_versions[static_cast<std::size_t>(CudaResidentShard::episode)] == 2);
    }

    backend.inject({.pilot_actions = actions});
    backend.publish_stage();
    const auto before_failed_window = testing::CudaWorldStoreTestAccess::read_state(store);
    testing::CudaWorldStoreTestAccess::fail_next_state_transfer(store);
    CHECK_THROWS_AS(backend.advance({.kind = runtime::backend::AdvanceKind::WorldBatch}),
                    std::runtime_error);
    const auto after_failed_window = testing::CudaWorldStoreTestAccess::read_state(store);
    REQUIRE(after_failed_window.worlds.size() == before_failed_window.worlds.size());
    for (std::size_t world = 0; world < after_failed_window.worlds.size(); ++world) {
        CHECK(after_failed_window.worlds[world].clock_tick ==
              before_failed_window.worlds[world].clock_tick);
        CHECK(after_failed_window.worlds[world].global_version ==
              before_failed_window.worlds[world].global_version);
        CHECK(after_failed_window.worlds[world].kinematics.x ==
              before_failed_window.worlds[world].kinematics.x);
        CHECK(after_failed_window.worlds[world].dynamics.q ==
              before_failed_window.worlds[world].dynamics.q);
    }
    // A failed inactive-slot transaction does not consume the successfully
    // published Phase A input; retry commits that exact window.
    backend.advance({.kind = runtime::backend::AdvanceKind::WorldBatch});
    const auto retried_window = testing::CudaWorldStoreTestAccess::read_state(store);
    CHECK(retried_window.worlds[0].clock_tick == 2);
}
