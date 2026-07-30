#include "runtime/facade/internal/cuda_resident/cuda_resident_backend.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <string>
#include <vector>

#include "runtime/contracts/cuda_resident_phase_d_fixture_contract.h"
#include "runtime/contracts/parity_budget_contracts.h"

namespace {

constexpr double kPi = 3.1415926535897932384626433832795;

std::vector<WorldSpawnRequest> make_spawns() {
    std::vector<WorldSpawnRequest> spawns;
    for (std::size_t world = 0; world < 2; ++world) {
        WorldSpawnRequest spawn{};
        spawn.world_index = world;
        spawn.type_name = std::string(runtime::cuda_resident::kFixedAirFixtureTypeName);
        spawn.entity_name = "RB7PhaseD" + std::to_string(world);
        spawn.is_agent = true;
        spawn.x = 1000.0 + static_cast<double>(world) * 100.0;
        spawn.z = 1500.0;
        spawn.vx = 200.0 + static_cast<double>(world);
        spawn.heading = 90.0;
        spawns.push_back(spawn);
    }
    return spawns;
}

std::vector<WorldPilotActionAssignment> make_actions(const std::vector<std::uint64_t> &ids) {
    std::vector<WorldPilotActionAssignment> actions(ids.size());
    for (std::size_t world = 0; world < ids.size(); ++world) {
        actions[world].world_index = world;
        actions[world].entity_id = ids[world];
        actions[world].action.active = true;
        actions[world].action.stick_roll = -0.20 + static_cast<double>(world) * 0.05;
        actions[world].action.stick_pitch = 0.10 + static_cast<double>(world) * 0.05;
        actions[world].action.rudder = 0.03;
        actions[world].action.throttle = 0.65;
    }
    return actions;
}

void check_resource(const runtime::cuda_resident::CudaBarrierKernelResources &resource) {
    CHECK(resource.registers_per_thread > 0);
    CHECK(resource.local_bytes_per_thread >= 0);
    CHECK(resource.threads_per_block == 128);
    CHECK(resource.active_blocks_per_multiprocessor > 0);
    CHECK(resource.theoretical_occupancy > 0.0);
    CHECK(resource.theoretical_occupancy <= 1.0);
}

} // namespace

TEST_CASE("RB7 Phase D projects host export and a lease-scoped device view") {
    using namespace runtime::cuda_resident;
    if (!CudaWorldStore::compiled_with_cuda()) {
        CHECK(true);
        return;
    }

    CudaResidentBackend backend;
    backend.configure({.world_count = 2});
    check_resource(testing::CudaWorldStoreTestAccess::phase_d_instruments_kernel_resources());
    check_resource(testing::CudaWorldStoreTestAccess::phase_d_configuration_kernel_resources());
    check_resource(testing::CudaWorldStoreTestAccess::phase_d_projection_kernel_resources());

    const std::vector<std::uint32_t> seeds = {101, 202};
    const std::vector<WorldSpawnRequest> spawns = make_spawns();
    const std::vector<double> time_steps = {0.05, 0.125};
    const auto setup = backend.setup({
        .kind = runtime::backend::SetupKind::Batch,
        .seeds = seeds,
        .spawn_requests = spawns,
        .time_steps = time_steps,
    });
    const auto actions = make_actions(setup.entity_ids);
    backend.inject({.pilot_actions = actions});
    backend.publish_stage();
    backend.advance({.kind = runtime::backend::AdvanceKind::WorldBatch});

    CudaWorldStore &store = testing::CudaResidentBackendTestAccess::world_store(backend);
    const auto state = testing::CudaWorldStoreTestAccess::read_state(store);
    REQUIRE(state.worlds.size() == 2);
    for (std::size_t world = 0; world < state.worlds.size(); ++world) {
        const auto &phase_d = state.worlds[world].phase_d;
        const auto &resident = state.worlds[world];
        CHECK(phase_d.instrument.alt_baro_m == doctest::Approx(state.worlds[world].kinematics.z));
        CHECK(phase_d.instrument.alt_radar_m == doctest::Approx(phase_d.instrument.alt_baro_m));
        CHECK(phase_d.instrument.ias_mps == doctest::Approx(std::sqrt(
            2.0 * resident.dynamics.dynamic_pressure / kPhaseBSeaLevelDensityKgM3)));
        CHECK(phase_d.instrument.mach == doctest::Approx(resident.dynamics.mach_number));
        CHECK(phase_d.instrument.vvi_mps == doctest::Approx(resident.kinematics.vz));
        CHECK(phase_d.instrument.pitch_deg == doctest::Approx(resident.kinematics.pitch));
        CHECK(phase_d.instrument.roll_deg == doctest::Approx(resident.kinematics.roll));
        CHECK(phase_d.instrument.heading_deg == doctest::Approx(resident.kinematics.heading));
        CHECK(phase_d.instrument.aoa_deg == doctest::Approx(resident.dynamics.angle_of_attack));
        CHECK(phase_d.instrument.beta_deg == doctest::Approx(resident.dynamics.sideslip_angle));
        CHECK(phase_d.instrument.p_deg_s == doctest::Approx(resident.dynamics.p * 180.0 / kPi));
        CHECK(phase_d.instrument.q_deg_s == doctest::Approx(resident.dynamics.q * 180.0 / kPi));
        CHECK(phase_d.instrument.r_deg_s == doctest::Approx(resident.dynamics.r * 180.0 / kPi));
        CHECK(phase_d.instrument.engine_rpm_pct == doctest::Approx(
            resident.dynamics.throttle_state * 100.0 + resident.dynamics.ab_state * 10.0));
        CHECK(phase_d.instrument.fuel_flow_kg_h == doctest::Approx(
            resident.dynamics.current_thrust_n * kPhaseDFuelFlowTsfcNhPerN));
        CHECK(phase_d.instrument.throttle_pos == doctest::Approx(actions[world].action.throttle));
        CHECK(phase_d.instrument.fuel_internal_kg == doctest::Approx(kPhaseBFuelMassKg));
        CHECK(phase_d.instrument.fuel_external_kg == doctest::Approx(0.0));
        CHECK(phase_d.instrument.flaps_pos == doctest::Approx(actions[world].action.flaps));
        CHECK(phase_d.instrument.speedbrake_pos ==
              doctest::Approx(actions[world].action.speedbrake));
        CHECK(phase_d.instrument.gear_pos > 0.0);
        CHECK(phase_d.instrument.gear_pos <= 1.0);
        CHECK(phase_d.observation.id == setup.entity_ids[world]);
        CHECK(phase_d.observation.sim_time ==
              doctest::Approx(std::vector<double>{0.05, 0.125}[world]));
        CHECK(phase_d.observation.x == doctest::Approx(resident.kinematics.x));
        CHECK(phase_d.observation.y == doctest::Approx(resident.kinematics.y));
        CHECK(phase_d.observation.z == doctest::Approx(resident.kinematics.z));
        CHECK(phase_d.observation.vx == doctest::Approx(resident.kinematics.vx));
        CHECK(phase_d.observation.vy == doctest::Approx(resident.kinematics.vy));
        CHECK(phase_d.observation.vz == doctest::Approx(resident.kinematics.vz));
        CHECK(phase_d.observation.heading == doctest::Approx(resident.kinematics.heading));
        CHECK(phase_d.observation.pitch == doctest::Approx(resident.kinematics.pitch));
        CHECK(phase_d.observation.roll == doctest::Approx(resident.kinematics.roll));
        CHECK(phase_d.observation.speed == doctest::Approx(std::sqrt(
            resident.kinematics.vx * resident.kinematics.vx +
            resident.kinematics.vy * resident.kinematics.vy +
            resident.kinematics.vz * resident.kinematics.vz)));
        CHECK(phase_d.observation.health == doctest::Approx(kPhaseDHealth));
        CHECK(phase_d.observation.gear_state == doctest::Approx(phase_d.instrument.gear_pos));
        CHECK(phase_d.observation.throttle == doctest::Approx(actions[world].action.throttle));
        CHECK(phase_d.observation.total_reward ==
              doctest::Approx(phase_d.reward.total_reward));
        CHECK(phase_d.reward.survival_term == doctest::Approx(kPhaseDSurvivalReward));
        CHECK(phase_d.reward.speed_term == doctest::Approx(0.0));
        CHECK(phase_d.reward.total_reward == doctest::Approx(kPhaseDSurvivalReward));
        CHECK_FALSE(phase_d.termination.terminated);
        CHECK(phase_d.termination.reason_code == CudaResidentTerminationCode::running);
        CHECK(phase_d.events_empty);
        CHECK(state.worlds[world].shard_versions[static_cast<std::size_t>(CudaResidentShard::instrument)] ==
              1);
        CHECK(state.worlds[world].shard_versions[static_cast<std::size_t>(CudaResidentShard::observation)] ==
              1);
    }

    const auto snapshot = backend.export_snapshot("rb7.phase_d");
    REQUIRE(snapshot.worlds.size() == 2);
    CHECK(snapshot.barrier.contract_satisfied);
    CHECK(snapshot.barrier.comparison_eligible);
    CHECK(snapshot.barrier.host_truth_available);
    CHECK(snapshot.barrier.materialized_shards ==
          std::vector<std::string>{"identity", "clock", "snapshot", "kinematics", "dynamics",
                                   "instrument", "observation", "reward", "termination", "events",
                                   "export_envelope"});
    CHECK(snapshot.envelope.schema_version == std::string(kCudaResidentPhaseDSnapshotSchemaV3));
    CHECK(snapshot.envelope.provenance == std::string(kCudaResidentPhaseDSnapshotProvenance));
    CHECK(snapshot.worlds[0].identity.lineage.source_backend_id ==
          std::string(kCudaResidentRb7BackendId));
    CHECK(snapshot.worlds[0].phase_d.observation.id == setup.entity_ids[0]);

    const std::vector<WorldEntityRef> refs = {
        {.world_index = 0, .entity_id = setup.entity_ids[0]},
    };
    const auto host_export = backend.export_state({
        .refs = refs,
        .include_agent_observations = true,
        .include_instrument_states = true,
    });
    REQUIRE(host_export.agent_observations.size() == 1);
    REQUIRE(host_export.instrument_states.size() == 1);
    CHECK(host_export.agent_observations[0].id == setup.entity_ids[0]);
    CHECK(host_export.agent_observations[0].total_reward == doctest::Approx(kPhaseDSurvivalReward));
    CHECK(host_export.instrument_states[0].ias_mps ==
          doctest::Approx(snapshot.worlds[0].phase_d.instrument.ias_mps));

    const auto view = backend.export_device_observation_view("rb7.device_view");
    REQUIRE(view.valid());
    CHECK(view.descriptor.output_shape == std::vector<std::uint64_t>{2, kPhaseDObservationValueCount});
    CHECK(view.descriptor.element_count == 2 * kPhaseDObservationValueCount);
    CHECK(view.descriptor.source_snapshot == snapshot.envelope.source_snapshot_version);
    CHECK(view.descriptor.dtype == "float32");
    CHECK(std::find(view.descriptor.consumer_constraints.begin(),
                    view.descriptor.consumer_constraints.end(), "ownership_copy_d2d") !=
          view.descriptor.consumer_constraints.end());
    CHECK(std::find(view.descriptor.consumer_constraints.begin(),
                    view.descriptor.consumer_constraints.end(), "not_zero_copy") !=
          view.descriptor.consumer_constraints.end());

    std::vector<float> first_values;
    std::vector<std::uint64_t> ids;
    REQUIRE(testing::CudaWorldStoreTestAccess::consume_device_observation_view(
        view, &first_values, &ids));
    REQUIRE(first_values.size() == 2);
    CHECK(first_values[0] == doctest::Approx(0.05F));
    CHECK(first_values[1] == doctest::Approx(0.125F));
    CHECK(ids == setup.entity_ids);

    const auto copied_view = view;
    backend.reset({.seeds = seeds});
    std::vector<float> copied_values;
    std::vector<std::uint64_t> copied_ids;
    CHECK(testing::CudaWorldStoreTestAccess::consume_device_observation_view(
        copied_view, &copied_values, &copied_ids));
    CHECK(copied_ids == setup.entity_ids);
}
