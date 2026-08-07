#include "runtime/facade/internal/cuda_resident/cuda_resident_backend.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "runtime/contracts/parity_budget_contracts.h"

namespace {

struct FixedAirFixtureInputs {
    std::vector<std::uint32_t> seeds = {101, 202};
    std::vector<WorldSpawnRequest> spawns;
    std::vector<double> time_steps = {0.05, 0.125};

    FixedAirFixtureInputs() {
        for (std::size_t world = 0; world < seeds.size(); ++world) {
            WorldSpawnRequest spawn{};
            spawn.world_index = world;
            spawn.type_name = std::string(runtime::cuda_resident::kFixedAirFixtureTypeName);
            spawn.entity_name = "RB4Lead" + std::to_string(world);
            spawn.is_agent = true;
            spawn.x = 1000.0 + static_cast<double>(world) * 100.0;
            spawn.y = -50.0 * static_cast<double>(world);
            spawn.z = 1500.0 + static_cast<double>(world) * 10.0;
            spawn.vx = 200.0 + static_cast<double>(world);
            spawn.vy = 2.0 * static_cast<double>(world);
            spawn.vz = -1.0;
            spawn.heading = 90.0 - static_cast<double>(world) * 5.0;
            spawn.pitch = 2.0;
            spawn.roll = -3.0;
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

std::vector<WorldPilotActionAssignment> make_actions(const std::vector<std::uint64_t> &entity_ids,
                                                     double throttle_offset = 0.0) {
    std::vector<WorldPilotActionAssignment> actions;
    for (std::size_t world = 0; world < entity_ids.size(); ++world) {
        WorldPilotActionAssignment assignment{};
        assignment.world_index = world;
        assignment.entity_id = entity_ids[world];
        assignment.action.stick_pitch = 0.1 + static_cast<double>(world) * 0.05;
        assignment.action.stick_roll = -0.2 + static_cast<double>(world) * 0.05;
        assignment.action.rudder = 0.03;
        assignment.action.throttle = 0.6 + throttle_offset + static_cast<double>(world) * 0.05;
        assignment.action.gear_handle = 0.0F;
        assignment.action.flaps = 0.1F;
        assignment.action.speedbrake = 0.0F;
        assignment.action.brake = 0.0;
        assignment.action.active = true;
        actions.push_back(assignment);
    }
    return actions;
}

const runtime::parity::ParityBudgetBarrierRule &required_barrier_rule(std::string_view id) {
    const auto &rules = runtime::parity::resident_candidate_barrier_contract();
    const auto found = std::find_if(rules.begin(), rules.end(),
                                    [id](const auto &rule) { return rule.barrier_id == id; });
    if (found == rules.end()) {
        throw std::logic_error("missing RB2 barrier rule");
    }
    return *found;
}

} // namespace

TEST_CASE("RB4 fixed-air setup input barriers and export reconstruct exact device state") {
    using namespace runtime::cuda_resident;

    CudaResidentBackend backend;
    if (!CudaWorldStore::compiled_with_cuda()) {
        CHECK_THROWS_AS(backend.configure({.world_count = 2}), std::runtime_error);
        return;
    }

    backend.configure({.world_count = 2, .worker_threads = 4});
    const CudaBarrierKernelResources resources =
        testing::CudaWorldStoreTestAccess::barrier_kernel_resources();
    CHECK(resources.registers_per_thread > 0);
    CHECK(resources.local_bytes_per_thread == 0);
    CHECK(resources.static_shared_bytes == 0);
    CHECK(resources.threads_per_block == 128);
    CHECK(resources.active_blocks_per_multiprocessor > 0);
    CHECK(resources.active_warps_per_multiprocessor > 0);
    CHECK(resources.theoretical_occupancy > 0.0);
    CHECK(resources.theoretical_occupancy <= 1.0);
    FixedAirFixtureInputs fixture;
    const runtime::backend::SetupResult setup = backend.setup(fixture.request());
    REQUIRE(setup.entity_ids.size() == 2);
    CHECK(setup.entity_ids[0] == fixed_air_fixture_entity_id(0));
    CHECK(setup.entity_ids[1] == fixed_air_fixture_entity_id(0));

    CudaResidentExportSnapshot snapshot = backend.export_snapshot("rb4.setup");
    REQUIRE(snapshot.worlds.size() == 2);
    const auto &export_rule = required_barrier_rule("export");
    CHECK(snapshot.barrier.barrier_id == export_rule.barrier_id);
    CHECK(snapshot.barrier.required_visible_shards == export_rule.visible_shards);
    CHECK(snapshot.barrier.materialized_shards ==
          std::vector<std::string>{"identity", "clock", "snapshot", "kinematics", "dynamics",
                                   "export_envelope"});
    CHECK(snapshot.barrier.enabled == export_rule.enabled);
    CHECK_FALSE(snapshot.barrier.contract_satisfied);
    CHECK_FALSE(snapshot.barrier.comparison_eligible);
    CHECK_FALSE(snapshot.barrier.host_truth_available);
    CHECK(snapshot.envelope.schema_version ==
          std::string(kCudaResidentFlightDynamicsSnapshotSchemaV2));
    CHECK(snapshot.envelope.visibility_label == "export");
    CHECK(snapshot.envelope.provenance ==
          std::string(kCudaResidentFlightDynamicsSnapshotProvenance));
    CHECK(snapshot.envelope.source_snapshot_version == 1);
    CHECK(snapshot.envelope.field_set ==
          std::vector<std::string>{"entity_ref", "seed", "reset_generation", "clock", "snapshot",
                                   "kinematics", "dynamics", "source_barrier_id"});

    for (std::size_t world = 0; world < snapshot.worlds.size(); ++world) {
        const CudaResidentWorldSnapshot &state = snapshot.worlds[world];
        CHECK(state.entity_ref.world_index == world);
        CHECK(state.entity_ref.entity_id == fixed_air_fixture_entity_id(0));
        CHECK(state.seed == fixture.seeds[world]);
        CHECK(state.reset_generation == 1);
        CHECK(state.clock.tick == 0);
        CHECK(state.clock.simulation_time_s == doctest::Approx(0.0));
        CHECK(state.identity.world_id == world);
        CHECK(state.identity.global_version == 1);
        CHECK(state.identity.barrier_id == "export");
        CHECK(state.identity.barrier_sequence == 2);
        CHECK(state.identity.shard_versions.size() == kCudaResidentShardCount);
        CHECK(state.identity.shard_versions[static_cast<std::size_t>(CudaResidentShard::instrument)]
                  .version == 0);
        CHECK(state.identity
                  .shard_versions[static_cast<std::size_t>(CudaResidentShard::export_envelope)]
                  .version == 1);
        CHECK(state.identity.lineage.source_snapshot_version == 1);
        CHECK(state.identity.lineage.source_backend_id ==
              std::string(kCudaResidentFlightDynamicsBackendId));
        CHECK(state.identity.lineage.source_request_id == "rb4.setup");
        CHECK(state.source_barrier_id == "input_injection");
        CHECK(state.kinematics.x == doctest::Approx(fixture.spawns[world].x));
        CHECK(state.kinematics.heading == doctest::Approx(fixture.spawns[world].heading));
    }

    CudaWorldStore &store = testing::CudaResidentBackendTestAccess::world_store(backend);
    std::vector<WorldPilotActionAssignment> changed_actions = make_actions(setup.entity_ids, 0.1);
    testing::CudaWorldStoreTestAccess::fail_next_state_transfer(store);
    CHECK_THROWS_AS(backend.inject({.pilot_actions = changed_actions}), std::runtime_error);
    snapshot = backend.export_snapshot("rb4.after_transfer_failure");
    CudaWorldStoreStateSnapshot resident_state =
        testing::CudaWorldStoreTestAccess::read_state(store);
    CHECK(snapshot.worlds[0].identity.global_version == 1);
    CHECK(resident_state.worlds[0].controls.throttle == doctest::Approx(0.0));

    testing::CudaWorldStoreTestAccess::fail_next_barrier_commit(store);
    CHECK_THROWS_AS(backend.inject({.pilot_actions = changed_actions}), std::runtime_error);
    snapshot = backend.export_snapshot("rb4.after_barrier_failure");
    resident_state = testing::CudaWorldStoreTestAccess::read_state(store);
    CHECK(snapshot.worlds[0].identity.global_version == 1);
    CHECK(resident_state.worlds[0].controls.throttle == doctest::Approx(0.0));

    std::vector<WorldPilotActionAssignment> actions = make_actions(setup.entity_ids);
    backend.inject({.pilot_actions = actions});
    CHECK_THROWS_AS(backend.inject({.pilot_actions = changed_actions}), std::runtime_error);
    snapshot = backend.export_snapshot("rb4.input");
    resident_state = testing::CudaWorldStoreTestAccess::read_state(store);
    for (std::size_t world = 0; world < snapshot.worlds.size(); ++world) {
        const auto &state = snapshot.worlds[world];
        CHECK(state.identity.global_version == 2);
        CHECK(state.identity.barrier_sequence == 3);
        CHECK(state.source_barrier_id == "input_injection");
        CHECK(resident_state.worlds[world].controls.throttle ==
              doctest::Approx(actions[world].action.throttle));
        CHECK(resident_state.worlds[world].controls.active);
        CHECK(state.identity.shard_versions[static_cast<std::size_t>(CudaResidentShard::identity)]
                  .version == 2);
        CHECK(
            state.identity
                .shard_versions[static_cast<std::size_t>(CudaResidentShard::pilot_flight_controls)]
                .version == 2);
    }

    backend.publish_stage();
    snapshot = backend.export_snapshot("rb4.stage");
    CHECK(snapshot.worlds[0].identity.global_version == 2);
    CHECK(snapshot.worlds[0].identity.barrier_sequence == 4);
    CHECK(snapshot.worlds[0].source_barrier_id == "stage_publish");
    CHECK(snapshot.worlds[0]
              .identity.shard_versions[static_cast<std::size_t>(CudaResidentShard::identity)]
              .version == 2);
    CHECK(snapshot.worlds[0]
              .identity
              .shard_versions[static_cast<std::size_t>(CudaResidentShard::pilot_flight_controls)]
              .version == 2);
    const auto before_partial_sync = snapshot.worlds[0].identity;
    CHECK_FALSE(backend.partial_sync_commit());
    snapshot = backend.export_snapshot("rb4.partial_disabled");
    CHECK(snapshot.worlds[0].identity.global_version == before_partial_sync.global_version);
    CHECK(snapshot.worlds[0].identity.barrier_sequence == before_partial_sync.barrier_sequence);
    CHECK(required_barrier_rule("partial_sync_commit").enabled == false);

    backend.advance({.kind = runtime::backend::AdvanceKind::WorldBatch});
    snapshot = backend.export_snapshot("rb4.window");
    resident_state = testing::CudaWorldStoreTestAccess::read_state(store);
    for (std::size_t world = 0; world < snapshot.worlds.size(); ++world) {
        const auto &state = snapshot.worlds[world];
        CHECK(state.clock.tick == 1);
        CHECK(state.clock.simulation_time_s == doctest::Approx(fixture.time_steps[world]));
        CHECK(state.identity.global_version == 3);
        CHECK(state.identity.barrier_sequence == 5);
        CHECK(state.source_barrier_id == "window_commit");
        CHECK(state.identity.shard_versions[static_cast<std::size_t>(CudaResidentShard::clock)]
                  .version == 2);
        CHECK(state.identity.shard_versions[static_cast<std::size_t>(CudaResidentShard::snapshot)]
                  .version == 2);
        CHECK(state.identity.shard_versions[static_cast<std::size_t>(CudaResidentShard::kinematics)]
                  .version == 2);
        CHECK(state.identity.shard_versions[static_cast<std::size_t>(CudaResidentShard::identity)]
                  .version == 3);
        CHECK(state.identity.shard_versions[static_cast<std::size_t>(CudaResidentShard::dynamics)]
                  .version == 2);
        CHECK(state.identity.shard_versions[static_cast<std::size_t>(CudaResidentShard::episode)]
                  .version == 2);
        CHECK(
            state.identity
                .shard_versions[static_cast<std::size_t>(CudaResidentShard::pilot_flight_controls)]
                .version == 2);
    }

    WorldEntityRef ref{.world_index = 1, .entity_id = setup.entity_ids[1]};
    const runtime::backend::ExportResult semantic_export = backend.export_state({
        .kinematics_ref = &ref,
        .world_index = 1,
        .include_kinematics = true,
        .include_world_time_step = true,
    });
    REQUIRE(semantic_export.kinematics.size() == 1);
    CHECK(semantic_export.kinematics[0].found);
    CHECK(semantic_export.kinematics[0].state.x ==
          doctest::Approx(resident_state.worlds[1].kinematics.x));
    CHECK(semantic_export.world_time_step == doctest::Approx(fixture.time_steps[1]));

    const runtime::backend::SetupResult repeated = backend.setup(fixture.request());
    CHECK(repeated.entity_ids == std::vector<std::uint64_t>{fixed_air_fixture_entity_id(1),
                                                            fixed_air_fixture_entity_id(1)});
    snapshot = backend.export_snapshot("rb4.repeated_setup");
    CHECK(snapshot.worlds[0].reset_generation == 2);
    CHECK(snapshot.worlds[0].clock.tick == 0);
    CHECK(snapshot.worlds[0].identity.global_version == 1);
}

TEST_CASE("RB4 fixed-air boundary rejects undeclared setup input advance and export features") {
    using namespace runtime::cuda_resident;

    if (!CudaWorldStore::compiled_with_cuda()) {
        CHECK(true);
        return;
    }
    CudaResidentBackend backend;
    backend.configure({.world_count = 2});
    FixedAirFixtureInputs fixture;

    CHECK_THROWS_AS(backend.publish_stage(), std::runtime_error);
    CHECK_THROWS_AS(backend.export_state({.world_index = 0, .include_world_time_step = true}),
                    std::logic_error);
    CHECK_THROWS_AS((void)backend.export_snapshot("rb4.before_reset"), std::logic_error);

    backend.reset({.seeds = fixture.seeds});
    CHECK_THROWS_AS(backend.export_state({.world_index = 0, .include_world_time_step = true}),
                    std::logic_error);
    CHECK_THROWS_AS((void)backend.export_snapshot("rb4.after_reset"), std::logic_error);

    CudaWorldStore &store = testing::CudaResidentBackendTestAccess::world_store(backend);
    testing::CudaWorldStoreTestAccess::fail_next_state_transfer(store);
    CHECK_THROWS_AS(backend.setup(fixture.request()), std::runtime_error);
    CHECK_THROWS_AS(backend.export_state({.world_index = 0, .include_world_time_step = true}),
                    std::logic_error);
    CHECK_THROWS_AS((void)backend.export_snapshot("rb4.after_failed_setup"), std::logic_error);

    std::vector<WorldTerrainAssignment> terrain(1);
    terrain[0].world_index = 0;
    terrain[0].terrain_type = "flat";
    runtime::backend::SetupRequest unsupported_setup = fixture.request();
    unsupported_setup.terrain_assignments = terrain;
    CHECK_THROWS_AS(backend.setup(unsupported_setup), std::invalid_argument);

    FixedAirFixtureInputs outside_flight_dynamics_envelope;
    outside_flight_dynamics_envelope.spawns[0].z = 50.0;
    CHECK_THROWS_AS(backend.setup(outside_flight_dynamics_envelope.request()),
                    std::invalid_argument);

    const auto setup = backend.setup(fixture.request());
    auto unsupported_actions = make_actions(setup.entity_ids);
    unsupported_actions[0].action.fire_weapon = true;
    CHECK_THROWS_AS(backend.inject({.pilot_actions = unsupported_actions}), std::invalid_argument);
    unsupported_actions[0].action.fire_weapon = false;
    unsupported_actions[0].action.radar_active = true;
    CHECK_THROWS_AS(backend.inject({.pilot_actions = unsupported_actions}), std::invalid_argument);
    CHECK_THROWS_AS(backend.advance({.kind = runtime::backend::AdvanceKind::StepExecutionResults}),
                    std::logic_error);
    CHECK_THROWS_AS(backend.export_state(
                        {.include_agent_observations = true, .include_instrument_states = true}),
                    std::logic_error);
    CHECK_THROWS_AS((void)backend.export_snapshot(""), std::invalid_argument);
    CHECK(backend.compatibility_port() == nullptr);
}
