#include "core/engine/world_batch_runtime.h"
#include "core/engine/world_batch_visual_binding_compatibility_helper.h"

#include <doctest/doctest.h>

#include <cmath>
#include <stdexcept>
#include <type_traits>

static_assert(!std::is_polymorphic_v<WorldBatchRuntime>,
              "WorldBatchRuntime compatibility ABI must remain non-polymorphic");

TEST_SUITE("world_batch_runtime") {

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

    TEST_CASE("resize preserves existing world references and controller prefixes") {
        WorldBatchRuntime runtime(1);
        SimulationKernel *world0 = &runtime.world_raw_quarantine(0);

        WorldEntityRef ref0{};
        ref0.world_index = 0;
        ref0.entity_id = 77;
        ExecutionEpisodeState state0{};
        state0.agent_id = ref0.entity_id;
        runtime.prime_execution_episode_controller_batch({ref0}, {state0});

        runtime.resize(1);
        CHECK(&runtime.world_raw_quarantine(0) == world0);
        CHECK(runtime.execution_episode_controller_ready(0));

        runtime.resize(3);
        CHECK(runtime.world_count() == 3);
        CHECK(&runtime.world_raw_quarantine(0) == world0);
        CHECK(runtime.execution_episode_controller_ready(0));
        CHECK_FALSE(runtime.execution_episode_controller_ready(1));
        CHECK_FALSE(runtime.execution_episode_controller_ready(2));

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

    TEST_CASE("complete world setup clears episode controller and missing wind resets calm") {
        WorldBatchRuntime runtime(1);
        auto &world = runtime.world_raw_quarantine(0);
        world.set_wind(25.0, 270.0, 5.0);

        auto world_lease = world.acquire_world_lease();
        const auto *env_ref = world_lease.world().get<EnvironmentModelRef>();
        REQUIRE(env_ref != nullptr);
        REQUIRE(env_ref->model != nullptr);
        const auto windy = env_ref->model->get_atmosphere_at(0.0, 0.0, 1000.0);
        CHECK(std::hypot(windy.wind_velocity.x, windy.wind_velocity.y) > 1.0);

        WorldEntityRef ref{};
        ref.world_index = 0;
        ref.entity_id = 77;
        ExecutionEpisodeState state{};
        state.agent_id = ref.entity_id;
        runtime.prime_execution_episode_controller_batch({ref}, {state});
        REQUIRE(runtime.execution_episode_controller_ready(0));

        runtime.apply_world_setup_batch({123}, {}, {}, {}, {});

        CHECK_FALSE(runtime.execution_episode_controller_ready(0));
        const auto calm = env_ref->model->get_atmosphere_at(0.0, 0.0, 1000.0);
        CHECK(calm.wind_velocity.x == doctest::Approx(0.0));
        CHECK(calm.wind_velocity.y == doctest::Approx(0.0));
        CHECK(calm.wind_velocity.z == doctest::Approx(0.0));

        runtime.prime_execution_episode_controller_batch({ref}, {state});
        REQUIRE(runtime.execution_episode_controller_ready(0));
        runtime.apply_world_layout(0, 456, "flat", 0.0, 0.0, 0.0, false, 0.0, 0.0, 8.0, {}, {});
        CHECK_FALSE(runtime.execution_episode_controller_ready(0));
    }

    TEST_CASE("visual compatibility scenes own snapshots across world shutdown") {
        WorldBatchRuntime runtime(1);
        auto &world = runtime.world_raw_quarantine(0);
        const auto camera = world.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, 1000.0, 0.0,
                                             0.0, 0.0, 0.0, 0.0, 0.0);
        REQUIRE(camera.is_valid());

        WorldEntityRef ref{};
        ref.world_index = 0;
        ref.entity_id = camera.id();
        auto scenes = runtime.collect_visual_binding_compatibility_scenes_batch({ref}, 4, false);
        REQUIRE(scenes.size() == 1);
        CHECK(scenes.front().environment_snapshot.valid);
        CHECK(scenes.front().environment_snapshot.raster.width == 200);
        CHECK(scenes.front().environment_snapshot.raster.height == 200);
        CHECK(scenes.front().environment_snapshot.raster.surface_codes.size() == 40000);
        CHECK(scenes.front().request.out_height == arb::ARB_HEIGHT / 4);
        CHECK(scenes.front().request.out_width == arb::ARB_WIDTH / 4);

        const auto before_shutdown =
            world_batch_visual_binding_compatibility::render_scenes_batch(scenes, false);
        CHECK(before_shutdown.batch_size == 1);

        world.shutdown();
        WorldBatchVisualObservationCompatibilityExport rendered{};
        CHECK_NOTHROW(rendered = world_batch_visual_binding_compatibility::render_scenes_batch(
                          scenes, false));
        CHECK(rendered.batch_size == 1);
        CHECK(rendered.flat.size() == rendered.frame_size);
    }

} // TEST_SUITE("world_batch_runtime")
