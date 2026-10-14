#include "core/engine/world_batch_runtime.h"
#include "core/engine/parallel_for_index.h"
#include "core/engine/testing/world_batch_runtime_test_access.h"
#include "components/basic/common.h"
#include "components/basic/stable_identity.h"
#include "components/command/common/mission_command_control_state.h"
#include "components/visual/visual_sensor.h"
#include "gpu/gpu_world_batch_visual_binding_compatibility.h"
#include "runtime/facade/runtime_facade.h"

#include <doctest/doctest.h>

#include <atomic>
#include <cmath>
#include <functional>
#include <stdexcept>
#include <limits>
#include <type_traits>

static_assert(!std::is_polymorphic_v<WorldBatchRuntime>,
              "WorldBatchRuntime compatibility ABI must remain non-polymorphic");

TEST_SUITE("world_batch_runtime") {

    TEST_CASE("world batch applies gravity without an active command") {
        WorldBatchRuntime runtime(1);
        BatchWorldSetupRequest setup{};
        setup.seeds = {42};
        setup.time_steps = {0.05};
        WorldSpawnRequest spawn{};
        spawn.world_index = 0;
        spawn.side = Side::Blue;
        spawn.type_name = "Aircraft";
        spawn.entity_name = "GravityNoCommand";
        spawn.is_agent = false;
        spawn.z = 1000.0;
        setup.spawn_requests = {spawn};
        const auto entity_ids = runtime.apply_world_setup_batch(
            setup.seeds, {}, {{0, 0.0, 0.0, 0.0}}, {}, setup.spawn_requests, setup.time_steps);
        REQUIRE(entity_ids.size() == 1);

        // Use the quarantine seam only to prepare the missing-input fixture;
        // WorldBatchRuntime remains the execution and observation owner.
        auto &kernel = runtime.world_raw_quarantine(0);
        {
            auto lease = kernel.acquire_world_lease();
            const auto entity = lease.world().entity(entity_ids.front());
            REQUIRE(entity.is_valid());
            auto *control = entity.get_mut<MissionCommandControlState>();
            REQUIRE(control != nullptr);
            *control = MissionCommandControlState{};
        }
        constexpr double gravity = 9.80665;
        constexpr double dt = 0.05;
        runtime.step_batch();
        const auto observations = runtime.get_agent_observations_batch({{0, entity_ids.front()}});
        REQUIRE(observations.size() == 1);
        CHECK(observations.front().vz == doctest::Approx(-gravity * dt));
        CHECK(observations.front().z == doctest::Approx(1000.0 - 0.5 * gravity * dt * dt));
    }

    TEST_CASE("batch worker launch failure fences exports and failed recovery until reset") {
        for (const std::size_t world_count : {std::size_t{3}, std::size_t{4}}) {
            for (const std::size_t failed_launch : {std::size_t{0}, std::size_t{1}}) {
                WorldBatchRuntime batch(world_count);
                batch.set_worker_threads(world_count);
                std::atomic<std::size_t> launch_count{0};
                std::atomic<std::size_t> finished_count{0};
                auto clock = [&](std::size_t index) {
                    auto lease = batch.world_raw_quarantine(index).acquire_world_lease();
                    return ecs_get_world_info(lease.world().c_ptr())->world_time_total;
                };
                WorldBatchRuntimeTestAccess::set_worker_thread_factory(
                    batch, [&](std::function<void()> task) -> std::jthread {
                        if (launch_count.fetch_add(1) == failed_launch) {
                            throw std::runtime_error("injected batch worker launch failure");
                        }
                        return std::jthread([&, task = std::move(task)] {
                            task();
                            finished_count.fetch_add(1);
                        });
                    });
                CHECK_THROWS_WITH(batch.step_batch(), "injected batch worker launch failure");
                CHECK(launch_count.load() == failed_launch + 1);
                CHECK(finished_count.load() == failed_launch);
                CHECK_FALSE(batch.batch_healthy());
                CHECK(batch.batch_failure_reason() == "injected batch worker launch failure");
                CHECK((clock(0) > 0.0) == (failed_launch == 1));
                for (std::size_t index = 1; index < world_count; ++index) {
                    CHECK(clock(index) == 0.0);
                }
                // Clocks are diagnostics, never per-world commit/rollback evidence.
                CHECK_THROWS_AS(batch.step_batch(), std::logic_error);
                CHECK_THROWS_AS((void)batch.composition_diagnostics(), std::logic_error);
                CHECK_THROWS_AS(batch.get_agent_observations_batch({}), std::logic_error);
                CHECK(launch_count.load() == failed_launch + 1);
                // A recovery launch exception also leaves the generation fenced.
                WorldBatchRuntimeTestAccess::set_worker_thread_factory(
                    batch, [](std::function<void()>) -> std::jthread {
                        throw std::runtime_error("injected recovery launch failure");
                    });
                CHECK_THROWS_WITH(batch.reset_batch({31}), "injected recovery launch failure");
                CHECK_FALSE(batch.batch_healthy());
                CHECK_THROWS_AS(batch.step_batch(), std::logic_error);
                WorldBatchRuntimeTestAccess::set_worker_thread_factory(batch, {});
                REQUIRE_NOTHROW(batch.reset_batch({31}));
                CHECK(batch.batch_healthy());
                CHECK(batch.batch_failure_reason().empty());
                for (std::size_t index = 0; index < world_count; ++index) {
                    CHECK(clock(index) == 0.0);
                }
                CHECK_NOTHROW(batch.step_batch());
                CHECK_NOTHROW((void)batch.composition_diagnostics());
            }
        }
    }

    TEST_CASE("worker launch failure joins already started workers before propagating") {
        std::atomic<std::size_t> launch_count{0};
        std::atomic<bool> worker_finished{false};
        auto thread_factory = [&](std::function<void()> task) -> std::jthread {
            if (launch_count.fetch_add(1) == 1) {
                throw std::runtime_error("injected worker launch failure");
            }
            return std::jthread(std::move(task));
        };

        CHECK_THROWS_AS(
            runtime::detail::parallel_for_index(
                4, 4, [&](std::size_t) { worker_finished.store(true, std::memory_order_release); },
                thread_factory),
            std::runtime_error);
        CHECK(worker_finished.load(std::memory_order_acquire));
        CHECK(launch_count.load() == 2);
    }

    TEST_CASE("state-mutating batch failure is fail-closed until reset") {
        for (const std::size_t worker_threads : {std::size_t{1}, std::size_t{2}}) {
            WorldBatchRuntime runtime(2);
            runtime.set_worker_threads(worker_threads);
            runtime.world_raw_quarantine(1).begin_exact_stage_trace_frame();

            CHECK(runtime.batch_healthy());
            CHECK_THROWS_AS(runtime.step_batch(), std::logic_error);
            CHECK_FALSE(runtime.batch_healthy());
            CHECK(runtime.batch_failure_reason().find("exact-stage trace frame") !=
                  std::string::npos);

            // The failed batch cannot be retried as if all worlds had advanced.
            CHECK_THROWS_AS(runtime.step_batch(), std::logic_error);

            runtime.world_raw_quarantine(1).end_exact_stage_trace_frame();
            CHECK_NOTHROW(runtime.reset_batch({11, 17}));
            CHECK(runtime.batch_healthy());
            CHECK(runtime.batch_failure_reason().empty());
            CHECK_NOTHROW(runtime.step_batch());
        }
    }

    TEST_CASE("mixed world advancement remains diagnostic until explicit generation reset") {
        for (const std::size_t world_count : {std::size_t{3}, std::size_t{4}}) {
            for (const std::size_t worker_threads : {std::size_t{1}, std::size_t{2}, world_count}) {
                WorldBatchRuntime runtime(world_count);
                runtime.set_worker_threads(worker_threads);
                auto clock = [&](std::size_t index) {
                    auto lease = runtime.world_raw_quarantine(index).acquire_world_lease();
                    return ecs_get_world_info(lease.world().c_ptr())->world_time_total;
                };
                runtime.world_raw_quarantine(1).begin_exact_stage_trace_frame();
                // The trace probe opens a Flecs frame and advances its clock.
                // Isolate that probe mutation from the subsequent batch call.
                const double fault_world_clock_before_step = clock(1);
                CHECK_THROWS_AS(runtime.step_batch(), std::logic_error);
                CHECK_FALSE(runtime.batch_healthy());
                // The first chunk advances world 0 before world 1 throws. Other
                // chunks finish in parallel; serial execution leaves 2+ skipped.
                CHECK(clock(0) > 0.0);
                CHECK(clock(1) == fault_world_clock_before_step);
                for (std::size_t index = 2; index < world_count; ++index) {
                    CHECK((clock(index) > 0.0) == (worker_threads > 1));
                }
                // None of these clock observations proves effect commit or
                // rollback. Maintained exports must not publish a valid batch.
                CHECK_THROWS_AS((void)runtime.composition_diagnostics(), std::logic_error);
                CHECK_THROWS_AS(runtime.get_agent_observations_batch({}), std::logic_error);
                CHECK_THROWS_AS(runtime.resize(world_count + 1), std::logic_error);
                CHECK(runtime.world_count() == world_count);
                CHECK_THROWS_AS(runtime.reset_batch({11, 17}), std::invalid_argument);
                CHECK_FALSE(runtime.batch_healthy());
                runtime.world_raw_quarantine(1).end_exact_stage_trace_frame();
                REQUIRE_NOTHROW(runtime.reset_batch({23}));
                CHECK(runtime.batch_healthy());
                for (std::size_t index = 0; index < world_count; ++index) {
                    CHECK(clock(index) == 0.0);
                }
                CHECK_NOTHROW(runtime.step_batch());
            }
        }
    }

    TEST_CASE("batch reset and setup resolve documented effective seeds") {
        WorldBatchRuntime runtime(4);
        auto effective_seed = [&](std::size_t index) {
            auto lease = runtime.world_raw_quarantine(index).acquire_world_lease();
            const auto *state = lease.world().get<StableIdentityState>();
            REQUIRE(state != nullptr);
            return state->episode_seed;
        };
        const std::vector<std::vector<std::uint32_t>> modes{
            {}, {11}, {11, 22, 33, 44}, {UINT32_MAX}};
        const std::vector<std::vector<std::uint32_t>> expected{
            {42, 43, 44, 45}, {11, 12, 13, 14}, {11, 22, 33, 44}, {UINT32_MAX, 0, 1, 2}};
        for (std::size_t mode = 0; mode < modes.size(); ++mode) {
            runtime.reset_batch(modes[mode]);
            for (std::size_t i = 0; i < 4; ++i)
                CHECK(effective_seed(i) == expected[mode][i]);
            runtime.apply_world_setup_batch(modes[mode], {}, {}, {}, {});
            for (std::size_t i = 0; i < 4; ++i)
                CHECK(effective_seed(i) == expected[mode][i]);
        }
    }

    TEST_CASE("unsupported seed counts reject reset and setup before any mutation") {
        WorldBatchRuntime runtime(4);
        runtime.set_worker_threads(4);
        runtime.reset_batch({11, 22, 33, 44});
        std::vector<flecs::entity> entities;
        for (std::size_t i = 0; i < 4; ++i) {
            auto &world = runtime.world_raw_quarantine(i);
            world.set_time_step(0.2);
            entities.push_back(
                world.spawn_unit(Side::Blue, "Aircraft", 0, 0, 1000, 0, 0, 0, 0, 0, 0));
        }
        for (const auto &invalid : std::vector<std::vector<std::uint32_t>>{
                 {11, 22}, {11, 22, 33}, {11, 22, 33, 44, 55}}) {
            CHECK_THROWS_AS(runtime.reset_batch(invalid), std::invalid_argument);
            CHECK_THROWS_AS(runtime.apply_world_setup_batch(invalid, {}, {}, {}, {}, {0.1}),
                            std::invalid_argument);
            for (std::size_t i = 0; i < 4; ++i) {
                auto lease = runtime.world_raw_quarantine(i).acquire_world_lease();
                CHECK(lease.world().get<StableIdentityState>()->episode_seed == (i + 1) * 11);
                CHECK(entities[i].is_alive());
                CHECK(runtime.world_time_step(i) == 0.2);
            }
        }
        WorldBatchRuntime single(1);
        CHECK_THROWS_AS(single.reset_batch({11, 22}), std::invalid_argument);
        WorldBatchRuntime empty(0);
        CHECK_NOTHROW(empty.reset_batch({}));
        CHECK_NOTHROW(empty.reset_batch({11}));
        CHECK_THROWS_AS(empty.reset_batch({11, 22}), std::invalid_argument);
    }

    TEST_CASE("full setup restores canonical timestep for absent native values") {
        WorldBatchRuntime runtime(2);
        const double default_dt = SimulationKernel::kDefaultTimeStepS;
        CHECK(runtime.world_time_step(0) == default_dt);
        for (const auto &values :
             std::vector<std::vector<double>>{{0.2, 0.3}, {}, {0.0}, {0.2, 0.3}}) {
            runtime.apply_world_setup_batch({11, 17}, {}, {}, {}, {}, values);
            for (std::size_t i = 0; i < 2; ++i) {
                CHECK(runtime.world_time_step(i) == (values.size() == 2 ? values[i] : default_dt));
            }
        }
        runtime.apply_world_layout(0, 17, "flat", 0, 0, 0, false, 0, 0, 8, {}, {});
        CHECK(runtime.world_time_step(0) == default_dt);
        CHECK(runtime.world_time_step(1) == 0.3);
    }

    TEST_CASE("invalid setup timesteps reject before changing or resetting any world") {
        WorldBatchRuntime runtime(2);
        runtime.apply_world_setup_batch({11, 17}, {}, {}, {}, {}, {0.2, 0.3});
        auto &world = runtime.world_raw_quarantine(0);
        const auto entity = world.spawn_unit(Side::Blue, "Aircraft", 0, 0, 1000, 0, 0, 0, 0, 0, 0);
        REQUIRE(entity.is_alive());
        for (double invalid : {-0.1, std::numeric_limits<double>::quiet_NaN(),
                               std::numeric_limits<double>::infinity()}) {
            CHECK_THROWS_AS(
                runtime.apply_world_setup_batch({11, 17}, {}, {}, {}, {}, {0.1, invalid}),
                std::invalid_argument);
            CHECK_THROWS_AS(runtime.apply_world_layout(0, 17, "flat", 0, 0, 0, false, 0, 0, 8, {},
                                                       {}, {invalid}),
                            std::invalid_argument);
            CHECK(runtime.world_time_step(0) == 0.2);
            CHECK(runtime.world_time_step(1) == 0.3);
            CHECK(entity.is_alive());
        }
        CHECK_THROWS_AS(runtime.apply_world_setup_batch({}, {}, {}, {}, {}, {0.1, 0.2, 0.3}),
                        std::invalid_argument);
        CHECK(entity.is_alive());
    }

    TEST_CASE("layout failure after timestep mutation fail-closes the batch") {
        WorldBatchRuntime runtime(1);
        runtime.apply_world_setup_batch({11}, {}, {}, {}, {}, {0.2});

        CHECK_THROWS_AS(runtime.apply_world_layout(0, 17, "not-a-terrain", 0.0, 0.0, 0.0, false,
                                                   0.0, 0.0, 8.0, {}, {}, {0.1}),
                        std::invalid_argument);
        CHECK_FALSE(runtime.batch_healthy());
        CHECK(runtime.batch_failure_reason().find("Unknown terrain_type") != std::string::npos);
        CHECK(runtime.world_raw_quarantine(0).get_time_step() == 0.1);
        CHECK_THROWS_AS(runtime.step_batch(), std::logic_error);

        runtime.reset_batch({23});
        CHECK(runtime.batch_healthy());
        CHECK_NOTHROW(runtime.step_batch());
    }

    TEST_CASE("invalid layout world index preserves healthy batch") {
        WorldBatchRuntime runtime(1);
        runtime.apply_world_setup_batch({11}, {}, {}, {}, {}, {0.2});

        CHECK_THROWS_AS(runtime.apply_world_layout(99, 17, "flat", 0.0, 0.0, 0.0, false, 0.0, 0.0,
                                                   8.0, {}, {}, {0.1}),
                        std::out_of_range);
        CHECK(runtime.batch_healthy());
        CHECK(runtime.batch_failure_reason().empty());
        CHECK(runtime.world_time_step(0) == 0.2);
        CHECK_NOTHROW(runtime.step_batch());
    }

    TEST_CASE("batch setup applies maritime overrides and clears absent worlds") {
        WorldBatchRuntime runtime(2);
        const std::vector<WorldMaritimeAssignment> assignments{{0, true, 3.0, 45.0, 7.0},
                                                               {1, true, 6.0, 90.0, 9.0}};
        runtime.apply_world_setup_batch({11, 17}, {}, {}, {}, {}, {}, {}, {}, assignments);
        WorldBatchRuntime single(1);
        single.apply_world_layout(0, 17, "flat", 0.0, 0.0, 0.0, true, 6.0, 90.0, 9.0, {}, {});
        const auto single_state = single.world_raw_quarantine(0).get_maritime_state();
        const auto batch_state = runtime.world_raw_quarantine(1).get_maritime_state();
        CHECK(batch_state.configured == single_state.configured);
        CHECK(batch_state.sea_state == single_state.sea_state);
        CHECK(batch_state.wave_heading_deg == single_state.wave_heading_deg);
        CHECK(batch_state.wave_period_s == single_state.wave_period_s);
        for (std::size_t i = 0; i < 2; ++i) {
            const auto state = runtime.world_raw_quarantine(i).get_maritime_state();
            CHECK(state.configured);
            CHECK(state.sea_state == doctest::Approx(assignments[i].sea_state));
            CHECK(state.wave_heading_deg == doctest::Approx(assignments[i].wave_heading_deg));
            CHECK(state.wave_period_s == doctest::Approx(assignments[i].wave_period_s));
        }
        runtime.apply_world_setup_batch({11, 17}, {}, {}, {}, {}, {}, {}, {}, {{0, false}});
        CHECK_FALSE(runtime.world_raw_quarantine(0).get_maritime_state().configured);
        CHECK_FALSE(runtime.world_raw_quarantine(1).get_maritime_state().configured);
        runtime.apply_world_setup_batch({11, 17}, {}, {}, {}, {}, {}, {}, {}, assignments);
        CHECK(runtime.world_raw_quarantine(1).get_maritime_state().sea_state == 6.0);
        runtime.apply_world_setup_batch({11, 17}, {}, {}, {}, {});
        CHECK_FALSE(runtime.world_raw_quarantine(1).get_maritime_state().configured);
    }

    TEST_CASE("invalid maritime assignment rejects before resetting any world") {
        WorldBatchRuntime runtime(2);
        runtime.world_raw_quarantine(0).set_maritime_state(3.0);
        CHECK_THROWS_AS(runtime.apply_world_setup_batch({1, 2}, {}, {}, {}, {}, {}, {}, {},
                                                        {{0, true}, {0, true}}),
                        std::invalid_argument);
        CHECK_THROWS_AS(
            runtime.apply_world_setup_batch({1, 2}, {}, {}, {}, {}, {}, {}, {}, {{2, true}}),
            std::out_of_range);
        CHECK_THROWS_AS(
            runtime.apply_world_setup_batch({1, 2}, {}, {}, {}, {}, {}, {}, {},
                                            {{1, true, std::numeric_limits<double>::quiet_NaN()}}),
            std::invalid_argument);
        CHECK(runtime.world_raw_quarantine(0).get_maritime_state().sea_state == 3.0);
    }

    TEST_CASE("typed facade setup preserves maritime truth in CPU environment snapshots") {
        RuntimeFacade facade(2);
        BatchWorldSetupRequest request{};
        request.seeds = {11, 17};
        request.maritime_assignments = {{0, true, 3.0, 45.0, 7.0}, {1, true, 6.0, 90.0, 9.0}};
        for (std::uint64_t i = 0; i < 2; ++i) {
            WorldSpawnRequest spawn{};
            spawn.world_index = i;
            spawn.type_name = "Aircraft";
            spawn.z = 1000.0;
            request.spawn_requests.push_back(spawn);
        }
        auto result = facade.apply_world_setup(request);
        REQUIRE(result.entity_ids.size() == 2);
        auto scenes = facade.collect_visual_binding_compatibility_scenes_batch(
            {{0, result.entity_ids[0]}, {1, result.entity_ids[1]}}, 4, false);
        REQUIRE(scenes.size() == 2);
        for (std::size_t i = 0; i < 2; ++i) {
            CHECK(scenes[i].environment_snapshot.maritime_state_configured);
            CHECK(scenes[i].environment_snapshot.sea_state ==
                  request.maritime_assignments[i].sea_state);
            CHECK(scenes[i].environment_snapshot.wave_heading_deg ==
                  request.maritime_assignments[i].wave_heading_deg);
            CHECK(scenes[i].environment_snapshot.wave_period_s ==
                  request.maritime_assignments[i].wave_period_s);
        }
        request.maritime_assignments.clear();
        result = facade.apply_world_setup(request);
        scenes = facade.collect_visual_binding_compatibility_scenes_batch(
            {{0, result.entity_ids[0]}, {1, result.entity_ids[1]}}, 4, false);
        REQUIRE(scenes.size() == 2);
        CHECK_FALSE(scenes[0].environment_snapshot.maritime_state_configured);
        CHECK_FALSE(scenes[1].environment_snapshot.maritime_state_configured);
    }

    TEST_CASE("worker thread controls clamp to available batch work") {
        WorldBatchRuntime runtime(3);

        CHECK(runtime.world_count() == 3);
        CHECK(runtime.worker_threads() == 1);
        CHECK(runtime.effective_worker_threads() == 1);

        runtime.set_worker_threads(8);
        CHECK(runtime.worker_threads() == 8);
        CHECK(runtime.effective_worker_threads() == 3);

        runtime.resize(0);
        CHECK(runtime.world_count() == 0);
        CHECK(runtime.effective_worker_threads() == 1);
    }

    TEST_CASE("resize preserves existing world references") {
        WorldBatchRuntime runtime(1);
        SimulationKernel *world0 = &runtime.world_raw_quarantine(0);

        runtime.resize(1);
        CHECK(&runtime.world_raw_quarantine(0) == world0);

        runtime.resize(3);
        CHECK(runtime.world_count() == 3);
        CHECK(&runtime.world_raw_quarantine(0) == world0);

        SimulationKernel *world1 = &runtime.world_raw_quarantine(1);
        runtime.resize(2);
        CHECK(runtime.world_count() == 2);
        CHECK(&runtime.world_raw_quarantine(0) == world0);
        CHECK(&runtime.world_raw_quarantine(1) == world1);
        CHECK_THROWS_AS(runtime.world_raw_quarantine(2), std::out_of_range);
    }

    TEST_CASE("world index guards fail closed for out of range batch access") {
        WorldBatchRuntime runtime(1);

        CHECK_NOTHROW(runtime.step_worlds({}));
        CHECK_THROWS_AS(runtime.world_raw_quarantine(1), std::out_of_range);
        CHECK_THROWS_AS(runtime.world_time_step(1), std::out_of_range);
        CHECK_THROWS_AS(runtime.step_worlds({1}), std::out_of_range);
        CHECK_THROWS_AS(runtime.step_worlds({0, 0}), std::invalid_argument);
        CHECK_THROWS_AS(runtime.clear_zones_batch({0, 0}), std::invalid_argument);
        CHECK_THROWS_AS(runtime.apply_world_layout(0, 1, "flat", 0.0, 0.0, 0.0, false, 0.0, 0.0,
                                                   8.0, {}, {}, {0.1, 0.2}),
                        std::invalid_argument);
    }

    TEST_CASE("kinematics helpers reject null output and missing entities without mutation") {
        WorldBatchRuntime runtime(1);
        WorldEntityRef missing_ref{};
        missing_ref.world_index = 0;
        missing_ref.entity_id = 999999;
        WorldEntityKinematics state{};
        state.x = 12.0;

        CHECK_FALSE(runtime.try_get_entity_kinematics(missing_ref, nullptr));
        CHECK_FALSE(runtime.try_get_entity_kinematics(missing_ref, &state));
        CHECK_FALSE(runtime.try_set_entity_kinematics(missing_ref, state));
        CHECK(state.x == doctest::Approx(12.0));

        WorldEntityRef bad_world_ref = missing_ref;
        bad_world_ref.world_index = 3;
        CHECK_THROWS_AS(runtime.try_get_entity_kinematics(bad_world_ref, &state),
                        std::out_of_range);
        CHECK_THROWS_AS(runtime.try_set_entity_kinematics(bad_world_ref, state), std::out_of_range);
    }

    TEST_CASE("mutation callback failure poisons the batch after a partial kinematics write") {
        WorldBatchRuntime runtime(1);
        WorldSpawnRequest spawn{};
        spawn.world_index = 0;
        spawn.side = Side::Blue;
        spawn.type_name = "Aircraft";
        spawn.z = 1000.0;
        const auto entity_ids = runtime.apply_world_setup_batch({}, {}, {}, {}, {spawn});
        REQUIRE(entity_ids.size() == 1);

        {
            auto world_lease = runtime.world_raw_quarantine(0).acquire_world_lease();
            bool callback_entered = false;
            auto throwing_observer =
                world_lease.world()
                    .observer<Velocity>()
                    .event(flecs::OnSet)
                    .each([&](flecs::entity, Velocity &) {
                        callback_entered = true;
                        throw std::runtime_error("injected velocity callback failure");
                    });

            WorldEntityKinematics state{};
            state.x = 17.0;
            state.vx = 3.0;
            const WorldEntityRef ref{0, entity_ids.front()};
            CHECK_THROWS_AS(runtime.try_set_entity_kinematics(ref, state), std::runtime_error);
            CHECK(callback_entered);
            CHECK_FALSE(runtime.batch_healthy());
            CHECK(runtime.batch_failure_reason().find("injected velocity callback failure") !=
                  std::string::npos);
            CHECK_THROWS_AS(runtime.step_batch(), std::logic_error);
            throwing_observer.destruct();
            if (world_lease.world().is_deferred()) {
                world_lease.world().defer_end();
            }
        }
        CHECK_NOTHROW(runtime.reset_batch());
        CHECK(runtime.batch_healthy());
    }

    TEST_CASE("direct native spawn callback failure poisons the batch") {
        WorldBatchRuntime runtime(1);
        auto world_lease = runtime.world_raw_quarantine(0).acquire_world_lease();
        bool callback_entered = false;
        auto throwing_observer =
            world_lease.world()
                .observer<Transform>()
                .event(flecs::OnSet)
                .each([&](flecs::entity, Transform &) {
                    callback_entered = true;
                    throw std::runtime_error("injected direct spawn callback failure");
                });

        TypedPlatformSpawnRequest request{};
        request.world_index = 0;
        request.side = Side::Blue;
        request.request_id = "direct-spawn-failure";
        request.source_type_name = "Aircraft";
        request.entity_name = "DirectSpawnFailure";
        request.z = 1000.0;
        CHECK_THROWS_AS(runtime.spawn_typed_platform_unit(request), std::runtime_error);
        CHECK(callback_entered);
        CHECK_FALSE(runtime.batch_healthy());
        CHECK(runtime.batch_failure_reason().find("injected direct spawn callback failure") !=
              std::string::npos);
        CHECK_THROWS_AS(runtime.step_batch(), std::logic_error);
        throwing_observer.destruct();
        if (world_lease.world().is_deferred()) {
            world_lease.world().defer_end();
        }
    }

    TEST_CASE("complete world setup with missing wind resets calm") {
        WorldBatchRuntime runtime(1);
        auto &world = runtime.world_raw_quarantine(0);
        world.set_wind(25.0, 270.0, 5.0);

        auto world_lease = world.acquire_world_lease();
        const auto *env_ref = world_lease.world().get<EnvironmentModelRef>();
        REQUIRE(env_ref != nullptr);
        REQUIRE(env_ref->model != nullptr);
        const auto windy = env_ref->model->get_atmosphere_at(0.0, 0.0, 1000.0);
        CHECK(std::hypot(windy.wind_velocity.x, windy.wind_velocity.y) > 1.0);

        runtime.apply_world_setup_batch({123}, {}, {}, {}, {});

        const auto calm = env_ref->model->get_atmosphere_at(0.0, 0.0, 1000.0);
        CHECK(calm.wind_velocity.x == doctest::Approx(0.0));
        CHECK(calm.wind_velocity.y == doctest::Approx(0.0));
        CHECK(calm.wind_velocity.z == doctest::Approx(0.0));
    }

    TEST_CASE("world setup applies a per-world geodetic anchor and resets undeclared worlds") {
        WorldBatchRuntime runtime(2);
        WorldGeodeticAnchorAssignment south_china_sea{};
        south_china_sea.world_index = 1;
        south_china_sea.latitude_deg = 18.2;
        south_china_sea.longitude_deg = 109.5;
        runtime.apply_world_setup_batch({1, 2}, {}, {}, {}, {}, {}, {}, {south_china_sea});

        const auto world0 = runtime.world_raw_quarantine(0).get_geodetic_anchor();
        const auto world1 = runtime.world_raw_quarantine(1).get_geodetic_anchor();
        CHECK(world0.latitude_deg == doctest::Approx(geodesy::kDefaultGeodeticAnchor.latitude_deg));
        CHECK(world1.latitude_deg == doctest::Approx(18.2));
        CHECK(world1.longitude_deg == doctest::Approx(109.5));

        // A re-setup without an anchor returns every world to the default.
        runtime.apply_world_setup_batch({3, 4}, {}, {}, {}, {});
        CHECK(runtime.world_raw_quarantine(1).get_geodetic_anchor().latitude_deg ==
              doctest::Approx(geodesy::kDefaultGeodeticAnchor.latitude_deg));

        // A non-finite anchor fails closed instead of producing NaN positions.
        WorldGeodeticAnchorAssignment polar{};
        polar.latitude_deg = 90.0;
        CHECK_THROWS_AS(runtime.apply_world_setup_batch({5, 6}, {}, {}, {}, {}, {}, {}, {polar}),
                        std::invalid_argument);
    }

    TEST_CASE("visual compatibility scenes own snapshots across world shutdown") {
        WorldBatchRuntime runtime(1);
        auto &world = runtime.world_raw_quarantine(0);
        const auto camera = world.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, 1000.0, 0.0, 0.0,
                                             0.0, 0.0, 0.0, 0.0);
        REQUIRE(camera.is_valid());

        WorldEntityRef ref{};
        ref.world_index = 0;
        ref.entity_id = camera.id();
        auto scenes = runtime.collect_visual_binding_compatibility_scenes_batch({ref}, 4, false);
        REQUIRE(scenes.size() == 1);
        CHECK(scenes.front().environment == nullptr);
        CHECK(scenes.front().environment_snapshot.valid);
        CHECK(scenes.front().environment_snapshot.raster.width == 200);
        CHECK(scenes.front().environment_snapshot.raster.height == 200);
        CHECK(scenes.front().environment_snapshot.raster.surface_codes.size() == 40000);
        CHECK(scenes.front().request.out_height == arb::ARB_HEIGHT / 4);
        CHECK(scenes.front().request.out_width == arb::ARB_WIDTH / 4);

        const auto before_shutdown =
            gpu::render_world_batch_visual_binding_compatibility(scenes, false);
        CHECK(before_shutdown.batch_size == 1);

        world.shutdown();
        WorldBatchVisualObservationCompatibilityExport rendered{};
        CHECK_NOTHROW(rendered =
                          gpu::render_world_batch_visual_binding_compatibility(scenes, false));
        CHECK(rendered.batch_size == 1);
        CHECK(rendered.flat.size() == rendered.frame_size);
        CHECK(rendered.flat == before_shutdown.flat);
    }

} // TEST_SUITE("world_batch_runtime")
