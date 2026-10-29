#include "runtime_branch_contract.h"

#include <doctest/doctest.h>

namespace {

runtime::host::RuntimeEpisodeCoordinatorSnapshot parent_snapshot() {
    return {
        .episode = {.world = {.incarnation = {.host = {.host_id = {.high = 1, .low = 2},
                                                       .boot_id = {.high = 3, .low = 4}},
                                              .incarnation_epoch = 5},
                              .world_slot = 0,
                              .world_generation = 1},
                    .episode_id = {.high = 11, .low = 12},
                    .episode_generation = 1},
        .phase = runtime::host::RuntimeEpisodePhase::Running,
        .step_sequence = 4,
        .barrier_sequence = 2,
        .snapshot_id = {.high = 5, .low = 6},
        .snapshot_sha256 = std::string(64, 'a'),
    };
}

} // namespace

TEST_SUITE("runtime_branch_contract") {

    TEST_CASE("fork request requires a running immutable parent and dark authority") {
        runtime::host::RuntimeBranchForkRequest request{
            .parent_snapshot = parent_snapshot(),
            .branch_id = {.high = 7, .low = 8},
            .parent_plan_sha256 = std::string(64, 'b'),
            .intervention_sha256 = std::string(64, 'c'),
            .horizon = 2,
        };
        CHECK(runtime::host::validate_runtime_branch_fork_request(request));

        request.require_parent_immutable = false;
        CHECK(runtime::host::validate_runtime_branch_fork_request(request).error ==
              runtime::host::RuntimeBranchError::ParentImmutabilityRequired);
    }

    TEST_CASE("fork request rejects terminal parent and production publication") {
        auto request = runtime::host::RuntimeBranchForkRequest{
            .parent_snapshot = parent_snapshot(),
            .branch_id = {.high = 7, .low = 8},
            .intervention_sha256 = std::string(64, 'c'),
            .horizon = 1,
        };
        request.parent_snapshot.phase = runtime::host::RuntimeEpisodePhase::Terminal;
        CHECK(runtime::host::validate_runtime_branch_fork_request(request).error ==
              runtime::host::RuntimeBranchError::ParentNotRunning);
        request.parent_snapshot.phase = runtime::host::RuntimeEpisodePhase::Running;
        request.production_authorized = true;
        CHECK(runtime::host::validate_runtime_branch_fork_request(request).error ==
              runtime::host::RuntimeBranchError::ProductionForbidden);
    }

    TEST_CASE("branch proof requires all isolation gates") {
        runtime::host::RuntimeBranchForkProof proof{
            .branch =
                {
                    .branch_id = {.high = 7, .low = 8},
                    .parent_snapshot_id = {.high = 5, .low = 6},
                    .child_resource_id = {.high = 9, .low = 10},
                    .parent_episode = parent_snapshot().episode,
                    .parent_step_sequence = 4,
                    .depth = 1,
                    .parent_snapshot_sha256 = std::string(64, 'a'),
                    .intervention_sha256 = std::string(64, 'c'),
                },
            .parent_barrier_sealed = true,
            .state_scope_complete = true,
            .sibling_isolated = true,
            .external_side_effects_quarantined = true,
        };
        CHECK(runtime::host::validate_runtime_branch_fork_proof(proof));
        proof.sibling_isolated = false;
        CHECK(runtime::host::validate_runtime_branch_fork_proof(proof).error ==
              runtime::host::RuntimeBranchError::IncompleteIsolationProof);
    }

    TEST_CASE("native coordinator keeps branch barrier separate from replacement") {
        const auto parent = parent_snapshot();
        auto created = runtime::host::RuntimeEpisodeCoordinatorCandidate::create({
            .initial_episode = parent.episode,
            .initial_phase = runtime::host::RuntimeEpisodePhase::Running,
            .initial_snapshot_id = parent.snapshot_id,
            .initial_snapshot_sha256 = parent.snapshot_sha256,
            .initial_step_sequence = parent.step_sequence,
            .initial_barrier_sequence = parent.barrier_sequence,
        });
        REQUIRE(created.status);
        REQUIRE(created.coordinator != nullptr);

        auto branch =
            created.coordinator->open_branch_barrier(parent.episode, parent.step_sequence);
        REQUIRE(branch.status);
        REQUIRE(branch.capability.valid());
        CHECK(branch.capability.kind() == runtime::host::RuntimeEpisodeBarrierKind::Branch);
        CHECK(branch.capability.snapshot().phase ==
              runtime::host::RuntimeEpisodePhase::BranchBarrier);
        CHECK_FALSE(created.coordinator->issue_episode_capability().status);

        REQUIRE(created.coordinator->abort_branch_barrier(std::move(branch.capability)));
        CHECK(created.coordinator->snapshot().phase == runtime::host::RuntimeEpisodePhase::Running);
        CHECK_FALSE(branch.capability.valid());
    }

} // TEST_SUITE("runtime_branch_contract")
