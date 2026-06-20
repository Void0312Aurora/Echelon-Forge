#include "core/engine/world_batch_runtime.h"

#include <doctest/doctest.h>

#include <stdexcept>

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

    TEST_CASE("world index guards fail closed for out of range batch access") {
        WorldBatchRuntime runtime(1);

        CHECK_NOTHROW(runtime.step_worlds({}));
        CHECK_THROWS_AS(runtime.world_raw_quarantine(1), std::out_of_range);
        CHECK_THROWS_AS(runtime.world_time_step(1), std::out_of_range);
        CHECK_THROWS_AS(runtime.step_worlds({1}), std::out_of_range);
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

} // TEST_SUITE("world_batch_runtime")
