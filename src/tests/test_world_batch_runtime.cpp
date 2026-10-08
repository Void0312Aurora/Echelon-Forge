#include "core/engine/world_batch_runtime.h"
#include "core/engine/world_batch_visual_binding_compatibility_helper.h"
#include "runtime/facade/runtime_facade.h"

#include <doctest/doctest.h>

#include <cmath>
#include <stdexcept>
#include <limits>
#include <type_traits>

static_assert(!std::is_polymorphic_v<WorldBatchRuntime>,
              "WorldBatchRuntime compatibility ABI must remain non-polymorphic");

TEST_SUITE("world_batch_runtime") {

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
            world_batch_visual_binding_compatibility::render_scenes_batch(scenes, false);
        CHECK(before_shutdown.batch_size == 1);

        world.shutdown();
        WorldBatchVisualObservationCompatibilityExport rendered{};
        CHECK_NOTHROW(rendered = world_batch_visual_binding_compatibility::render_scenes_batch(
                          scenes, false));
        CHECK(rendered.batch_size == 1);
        CHECK(rendered.flat.size() == rendered.frame_size);
        CHECK(rendered.flat == before_shutdown.flat);
    }

} // TEST_SUITE("world_batch_runtime")
