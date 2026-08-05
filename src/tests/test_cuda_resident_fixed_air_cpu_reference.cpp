#include "runtime/facade/internal/flecs_cpu_backend.h"

#include <doctest/doctest.h>

#include <cstdint>
#include <string>
#include <utility>
#include <vector>

#include "runtime/contracts/cuda_resident_fixed_air_fixture_contract.h"

TEST_CASE("RB4 CPU reference independently pins fixed-air identity and reset parity") {
    using namespace runtime::cuda_resident;

    FlecsCpuBackend backend(2);
    const std::string database_path = "examples/config/database";
    const runtime::backend::ContentResult loaded = backend.load_content({
        .kind = runtime::backend::ContentKind::Database,
        .path = &database_path,
    });
    REQUIRE(loaded.loaded);

    const std::vector<std::uint32_t> seeds = {101, 202};
    std::vector<WorldSpawnRequest> spawns;
    for (std::size_t world = 0; world < seeds.size(); ++world) {
        WorldSpawnRequest spawn{};
        spawn.world_index = world;
        spawn.type_name = std::string(kFixedAirFixtureTypeName);
        spawn.entity_name = "RB4CpuLead" + std::to_string(world);
        spawn.is_agent = true;
        spawn.x = 1000.0 + static_cast<double>(world) * 100.0;
        spawn.z = 1500.0;
        spawn.vx = 200.0;
        spawn.heading = 90.0;
        spawns.push_back(std::move(spawn));
    }
    const std::vector<double> time_steps = {0.05, 0.125};
    const runtime::backend::SetupRequest request{
        .kind = runtime::backend::SetupKind::Batch,
        .seeds = seeds,
        .spawn_requests = spawns,
        .time_steps = time_steps,
    };

    const runtime::backend::SetupResult first = backend.setup(request);
    REQUIRE(first.entity_ids.size() == 2);
    CHECK(first.entity_ids == std::vector<std::uint64_t>{fixed_air_fixture_entity_id(0),
                                                         fixed_air_fixture_entity_id(0)});
    for (std::size_t world = 0; world < first.entity_ids.size(); ++world) {
        WorldEntityRef ref{.world_index = world, .entity_id = first.entity_ids[world]};
        const runtime::backend::ExportResult exported = backend.export_state({
            .kinematics_ref = &ref,
            .world_index = world,
            .include_kinematics = true,
            .include_world_time_step = true,
        });
        REQUIRE(exported.kinematics.size() == 1);
        CHECK(exported.kinematics[0].found);
        CHECK(exported.kinematics[0].state.x == doctest::Approx(spawns[world].x));
        CHECK(exported.kinematics[0].state.z == doctest::Approx(spawns[world].z));
        CHECK(exported.world_time_step == doctest::Approx(time_steps[world]));
    }

    const runtime::backend::SetupResult second = backend.setup(request);
    CHECK(second.entity_ids == std::vector<std::uint64_t>{fixed_air_fixture_entity_id(1),
                                                          fixed_air_fixture_entity_id(1)});
}
