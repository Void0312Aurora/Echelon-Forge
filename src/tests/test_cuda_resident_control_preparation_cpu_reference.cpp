#include "components/physics/control_law.h"
#include "core/engine/world_batch_runtime.h"

#include <doctest/doctest.h>

#include <array>
#include <cstdint>
#include <string>
#include <utility>
#include <vector>

#include "runtime/contracts/cuda_resident_fixed_air_fixture_contract.h"
#include "runtime/contracts/cuda_resident_control_preparation_fixture_contract.h"

namespace {

std::vector<WorldSpawnRequest> make_spawns() {
    std::vector<WorldSpawnRequest> spawns;
    for (std::size_t world = 0; world < 2; ++world) {
        WorldSpawnRequest spawn{};
        spawn.world_index = world;
        spawn.type_name = std::string(runtime::cuda_resident::kFixedAirFixtureTypeName);
        spawn.entity_name = "CpuControlPreparation" + std::to_string(world);
        spawn.is_agent = true;
        spawn.x = 1000.0 + static_cast<double>(world) * 100.0;
        spawn.z = 1500.0;
        spawn.vx = 200.0 + static_cast<double>(world);
        spawn.heading = 90.0;
        spawns.push_back(std::move(spawn));
    }
    return spawns;
}

std::vector<WorldPilotActionAssignment>
make_actions(const std::vector<std::uint64_t> &entity_ids,
             const std::array<runtime::cuda_resident::CudaResidentControlPreparationFixtureInput, 2>
                 &inputs) {
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

void check_control_law_state(
    const WorldBatchRuntime &runtime, const std::vector<std::uint64_t> &entity_ids,
    const std::array<runtime::cuda_resident::CudaResidentControlPreparationFixtureExpected, 2>
        &expected) {
    for (std::size_t world = 0; world < entity_ids.size(); ++world) {
        const auto &kernel = runtime.world_raw_quarantine(world);
        auto world_lease = kernel.acquire_world_lease();
        const auto entity = world_lease.world().entity(entity_ids[world]);
        const auto *control = entity.get<ControlLawState>();
        REQUIRE(control != nullptr);
        CHECK(control->stick_roll_filt ==
              doctest::Approx(expected[world].stick_roll_filt).epsilon(1e-12));
        CHECK(control->stick_pitch_filt ==
              doctest::Approx(expected[world].stick_pitch_filt).epsilon(1e-12));
        CHECK(control->stick_yaw_filt ==
              doctest::Approx(expected[world].stick_yaw_filt).epsilon(1e-12));
        CHECK(control->stick_yaw_cmd ==
              doctest::Approx(expected[world].stick_yaw_cmd).epsilon(1e-12));
    }
}

} // namespace

TEST_CASE("CPU reference pins the direct-pilot control-preparation stage trace") {
    using namespace runtime::cuda_resident;
    WorldBatchRuntime runtime(2);
    REQUIRE(runtime.load_database("examples/config/database"));
    const std::vector<std::uint32_t> seeds = {101, 202};
    const std::vector<double> time_steps(kCudaResidentControlPreparationFixtureTimeSteps.begin(),
                                         kCudaResidentControlPreparationFixtureTimeSteps.end());
    const auto entity_ids =
        runtime.apply_world_setup_batch(seeds, {}, {}, {}, make_spawns(), time_steps, {});
    REQUIRE(entity_ids.size() == 2);
    CHECK(entity_ids[0] == fixed_air_fixture_entity_id(0));
    CHECK(entity_ids[1] == fixed_air_fixture_entity_id(0));

    runtime.set_pilot_actions_batch(
        make_actions(entity_ids, kCudaResidentControlPreparationFirstInputs));
    for (std::size_t world = 0; world < entity_ids.size(); ++world) {
        REQUIRE(runtime.world_raw_quarantine(world).run_exact_stage_direct("FlightControl"));
    }
    check_control_law_state(runtime, entity_ids, kCudaResidentControlPreparationFirstExpected);

    runtime.set_pilot_actions_batch(
        make_actions(entity_ids, kCudaResidentControlPreparationEdgeInputs));
    for (std::size_t world = 0; world < entity_ids.size(); ++world) {
        REQUIRE(runtime.world_raw_quarantine(world).run_exact_stage_direct("FlightControl"));
    }
    check_control_law_state(runtime, entity_ids, kCudaResidentControlPreparationEdgeExpected);
}
