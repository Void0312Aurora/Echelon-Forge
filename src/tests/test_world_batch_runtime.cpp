#include "core/engine/world_batch_runtime.h"
#include "core/engine/world_batch_visual_binding_compatibility_helper.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

static_assert(!std::is_polymorphic_v<WorldBatchRuntime>,
              "WorldBatchRuntime compatibility ABI must remain non-polymorphic");

namespace {

std::string resolve_world_batch_database_path() {
    const std::filesystem::path source_relative{"examples/config/database"};
    if (std::filesystem::exists(source_relative)) {
        return source_relative.string();
    }
    const std::filesystem::path build_relative = std::filesystem::path{".."} / source_relative;
    if (std::filesystem::exists(build_relative)) {
        return build_relative.string();
    }
    return source_relative.string();
}

// Two opposing fighters per world, offset per world so worlds differ.
std::vector<uint64_t> spawn_air_pairs(WorldBatchRuntime &runtime) {
    std::vector<WorldSpawnRequest> requests;
    for (size_t world = 0; world < runtime.world_count(); ++world) {
        for (int unit = 0; unit < 2; ++unit) {
            WorldSpawnRequest request{};
            request.world_index = world;
            request.side = unit == 0 ? Side::Blue : Side::Red;
            request.type_name = "F-16C_Block50";
            request.x = 3000.0 * unit + 100.0 * static_cast<double>(world);
            request.y = 20000.0 * unit;
            request.z = 5000.0;
            request.heading = unit == 0 ? 0.0 : 180.0;
            request.vx = 200.0;
            requests.push_back(request);
        }
    }
    return runtime.spawn_units_batch(requests);
}

std::vector<WorldEntityKinematics> run_air_batch(size_t worker_threads, int steps) {
    WorldBatchRuntime runtime(6);
    runtime.set_worker_threads(worker_threads);
    REQUIRE(runtime.load_database(resolve_world_batch_database_path()));
    runtime.set_time_step(0.05);
    runtime.reset_batch({11});
    const auto ids = spawn_air_pairs(runtime);
    for (int step = 0; step < steps; ++step) {
        runtime.step_batch();
    }
    std::vector<WorldEntityKinematics> out;
    for (size_t i = 0; i < ids.size(); ++i) {
        WorldEntityRef ref{};
        ref.world_index = i / 2;
        ref.entity_id = ids[i];
        WorldEntityKinematics state{};
        REQUIRE(runtime.try_get_entity_kinematics(ref, &state));
        out.push_back(state);
    }
    return out;
}

} // namespace

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

    TEST_CASE("persistent worker pool keeps batch results identical to serial execution") {
        const auto serial = run_air_batch(1, 40);
        const auto pooled = run_air_batch(4, 40);
        const auto oversubscribed = run_air_batch(16, 40);
        REQUIRE(serial.size() == pooled.size());
        REQUIRE(serial.size() == oversubscribed.size());
        for (size_t i = 0; i < serial.size(); ++i) {
            CHECK(pooled[i].x == serial[i].x);
            CHECK(pooled[i].y == serial[i].y);
            CHECK(pooled[i].z == serial[i].z);
            CHECK(pooled[i].heading == serial[i].heading);
            CHECK(oversubscribed[i].x == serial[i].x);
            CHECK(oversubscribed[i].vz == serial[i].vz);
        }
    }

    TEST_CASE("persistent worker pool accounts occupancy and survives thread-count changes") {
        WorldBatchRuntime runtime(8);
        runtime.set_worker_threads(1);
        runtime.step_batch();
        auto stats = runtime.worker_pool_stats();
        CHECK(stats.dispatch_count == 1);
        CHECK(stats.serial_dispatch_count == 1);
        CHECK(stats.task_count == 8);
        CHECK(stats.pool_threads == 0);
        CHECK(stats.busy_ns == stats.thread_wall_ns);

        runtime.reset_worker_pool_stats();
        runtime.set_worker_threads(4);
        for (int i = 0; i < 3; ++i) {
            runtime.step_batch();
        }
        stats = runtime.worker_pool_stats();
        CHECK(stats.dispatch_count == 3);
        CHECK(stats.serial_dispatch_count == 0);
        CHECK(stats.task_count == 24);
        CHECK(stats.pool_threads == 3);
        CHECK(stats.thread_wall_ns == 4 * stats.wall_ns);
        CHECK(stats.busy_ns > 0);
        CHECK(stats.busy_ns <= stats.thread_wall_ns);

        // Shrinking reuses a subset of the existing workers; growing adds more.
        runtime.set_worker_threads(2);
        runtime.step_batch();
        CHECK(runtime.worker_pool_stats().pool_threads == 3);
        runtime.set_worker_threads(8);
        runtime.step_batch();
        CHECK(runtime.worker_pool_stats().pool_threads == 7);

        // Moving the runtime moves the pool with it.
        WorldBatchRuntime moved(std::move(runtime));
        moved.step_batch();
        CHECK(moved.worker_pool_stats().pool_threads == 7);
    }

    TEST_CASE("persistent worker pool propagates the first task exception and stays usable") {
        WorldBatchRuntime runtime(4);
        runtime.set_worker_threads(4);
        runtime.world_raw_quarantine(2).shutdown();
        CHECK_THROWS_AS(runtime.step_batch(), std::logic_error);
        // The failed dispatch must not wedge the pool for the healthy worlds.
        CHECK_NOTHROW(runtime.step_worlds({0, 1, 3}));
        CHECK_THROWS_AS(runtime.step_worlds({2}), std::logic_error);
    }

    TEST_CASE("system timing reports per-world Flecs system time only while enabled") {
        WorldBatchRuntime runtime(2);
        runtime.set_worker_threads(2);
        REQUIRE(runtime.load_database(resolve_world_batch_database_path()));
        runtime.reset_batch({5});
        spawn_air_pairs(runtime);
        CHECK_FALSE(runtime.system_timing_enabled());

        runtime.set_system_timing_enabled(true);
        CHECK(runtime.system_timing_enabled());
        for (int i = 0; i < 5; ++i) {
            runtime.step_batch();
        }
        const auto timings = runtime.system_timings();
        REQUIRE_FALSE(timings.empty());
        double total_s = 0.0;
        bool saw_damage_system = false;
        for (const auto &timing : timings) {
            CHECK(timing.world_index < 2);
            CHECK(timing.time_spent_s >= 0.0);
            total_s += timing.time_spent_s;
            saw_damage_system =
                saw_damage_system || timing.system_name == "AircraftDamageStateUpdate";
        }
        CHECK(total_s > 0.0);
        CHECK(saw_damage_system);

        // Re-enabling restarts the measurement window from zero.
        runtime.set_system_timing_enabled(false);
        runtime.set_system_timing_enabled(true);
        double restarted_s = 0.0;
        for (const auto &timing : runtime.system_timings()) {
            restarted_s += timing.time_spent_s;
        }
        CHECK(restarted_s == 0.0);
    }

} // TEST_SUITE("world_batch_runtime")
