#include "runtime/host/integration/runtime_kernel_candidate.h"
#include "runtime/host/integration/runtime_kernel_candidate_facade.h"

#include <doctest/doctest.h>

using runtime::host::RuntimeHostState;
using runtime::host::integration::RuntimeKernelCandidate;

TEST_SUITE("runtime_kernel_candidate") {

TEST_CASE("P4-C candidate publishes only a fenced internal kernel") {
    RuntimeKernelCandidate candidate({
        .host_id = {.high = 0x5044432D484F5354ULL, .low = 1},
        .mode = runtime::host::RuntimeHostMode::Dark,
        .lifecycle_deadline_tick = 100,
    });

    REQUIRE(candidate.start());
    const auto snapshot = candidate.host_snapshot();
    REQUIRE(snapshot.state == RuntimeHostState::Active);
    REQUIRE(snapshot.active.has_value());
    CHECK_FALSE(snapshot.production_authorized);
    CHECK(candidate.composition_immutable());
    CHECK(candidate.composition_snapshot().resolved_manifest_sha256.size() == 64);

    const auto world = candidate.world_ref();
    REQUIRE(world.well_formed());
    WorldSpawnRequest request{};
    request.world_index = 0;
    request.side = Side::Blue;
    request.type_name = "Aircraft";
    request.x = 10.0;
    request.y = 20.0;
    request.z = 3000.0;
    const auto entity = candidate.spawn_unit(world, request);
    REQUIRE(entity.has_value());
    REQUIRE(entity->well_formed());

    WorldEntityKinematics before{};
    REQUIRE(candidate.try_get_entity_kinematics(*entity, &before));
    before.x = 99.0;
    REQUIRE(candidate.try_set_entity_kinematics(*entity, before));
    WorldEntityKinematics after{};
    REQUIRE(candidate.try_get_entity_kinematics(*entity, &after));
    CHECK(after.x == doctest::Approx(99.0));

    REQUIRE(candidate.step(world));
    CHECK(candidate.composition_immutable());

    auto stale_world = world;
    ++stale_world.world_generation;
    CHECK_FALSE(candidate.step(stale_world));
    auto stale_entity = *entity;
    ++stale_entity.entity_generation;
    CHECK_FALSE(candidate.try_get_entity_kinematics(stale_entity, &after));

    const auto running_episode = candidate.episode_ref();
    REQUIRE(running_episode.well_formed());
    candidate.arm_terminal_receipt_for_test();
    runtime::host::RuntimeEpisodeTransitionReceipt terminal_receipt{};
    REQUIRE(candidate.submit_episode(
        running_episode, runtime::host::RuntimeEpisodeIntentKind::Action,
        {.high = 0x4550432D5445524DULL, .low = 1}, std::string(64, 'c'),
        &terminal_receipt));
    REQUIRE(terminal_receipt.terminal);
    CHECK(candidate.episode_ref() == terminal_receipt.episode_after);
    WorldSpawnRequest terminal_spawn = request;
    terminal_spawn.x = 123.0;
    CHECK_FALSE(candidate.spawn_unit(candidate.world_ref(), terminal_spawn).has_value());
    CHECK_FALSE(candidate.try_set_entity_kinematics(*entity, before));
    runtime::host::RuntimeEpisodeTransitionReceipt reset_receipt{};
    REQUIRE(candidate.submit_episode(
        terminal_receipt.episode_after, runtime::host::RuntimeEpisodeIntentKind::Reset,
        {.high = 0x4550432D52455345ULL, .low = 1}, std::string(64, 'b'),
        &reset_receipt));
    REQUIRE(reset_receipt.reset_applied);
    CHECK(reset_receipt.episode_after.world.world_generation == world.world_generation + 1);
    CHECK_FALSE(candidate.try_get_entity_kinematics(*entity, &after));
    REQUIRE(candidate.step(candidate.world_ref()));

    const auto shutdown = candidate.shutdown(10, 100);
    REQUIRE(shutdown.status);
    CHECK(shutdown.state == RuntimeHostState::Stopped);
    CHECK(candidate.host_snapshot().state == RuntimeHostState::Stopped);
}

TEST_CASE("P4-C candidate rejects a plan hash that is not the sealed composition") {
    RuntimeKernelCandidate candidate({
        .host_id = {.high = 0x5044432D504C414EULL, .low = 3},
        .plan = {.plan_id = "p4c.kernel-candidate.v1", .plan_sha256 = std::string(64, 'f')},
    });
    CHECK_FALSE(candidate.start());

    RuntimeKernelCandidate partial({
        .host_id = {.high = 0x5044432D50415254ULL, .low = 4},
        .plan = {.plan_id = "p4c.kernel-candidate.v1"},
    });
    CHECK_FALSE(partial.start());
}

TEST_CASE("P4-C facade adapter keeps batch operations on epoch-bearing refs") {
    RuntimeKernelCandidate candidate({
        .host_id = {.high = 0x5044432D42415443ULL, .low = 2},
        .mode = runtime::host::RuntimeHostMode::Shadow,
        .lifecycle_deadline_tick = 100,
    });
    REQUIRE(candidate.start());
    runtime::host::integration::RuntimeKernelCandidateFacadeAdapter facade(candidate);

    WorldSpawnRequest first{};
    first.side = Side::Blue;
    first.type_name = "Aircraft";
    WorldSpawnRequest second = first;
    second.side = Side::Red;
    second.x = 100.0;
    const auto entities = facade.apply_spawn_batch({first, second});
    REQUIRE(entities.size() == 2);
    CHECK(entities.front().world == facade.world_ref());
    CHECK(entities.back().world == facade.world_ref());
    CHECK(facade.composition_immutable());
    CHECK(facade.step_batch());

    WorldSpawnRequest invalid = first;
    invalid.type_name.clear();
    const auto partial = facade.apply_spawn_batch({first, invalid});
    REQUIRE(partial.size() == 1);
    WorldEntityKinematics state{};
    CHECK(facade.try_get_entity_kinematics(partial.front(), &state));

    auto stale = entities.front();
    ++stale.world.incarnation.incarnation_epoch;
    CHECK_FALSE(facade.try_get_entity_kinematics(stale, &state));
    REQUIRE(candidate.shutdown(10, 100).status);
    CHECK_FALSE(facade.step_batch());
}

} // TEST_SUITE("runtime_kernel_candidate")
