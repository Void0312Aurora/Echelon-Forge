#include "runtime/facade/runtime_facade.h"
#include "runtime/host/integration/runtime_kernel_candidate.h"
#include "runtime/host/integration/runtime_kernel_candidate_facade.h"

#include <doctest/doctest.h>

#include <cmath>
#include <string>

using runtime::host::integration::RuntimeKernelCandidate;
using runtime::host::integration::RuntimeKernelCandidateFacadeAdapter;

namespace {

WorldSpawnRequest parity_request() {
    WorldSpawnRequest request{};
    request.world_index = 0;
    request.side = Side::Blue;
    request.type_name = "Aircraft";
    // Keep the workload on the common spawn/step surface. Agent-control
    // metadata is intentionally outside the candidate adapter's current seam.
    request.is_agent = false;
    request.x = 100.0;
    request.y = 200.0;
    request.z = 1500.0;
    request.vx = 200.0;
    request.heading = 90.0;
    return request;
}

void check_close(double lhs, double rhs) {
    CHECK(lhs == doctest::Approx(rhs).epsilon(1e-12));
}

} // namespace

TEST_SUITE("runtime_kernel_candidate_parity") {

TEST_CASE("candidate and maintained facade share the admitted native workload") {
    RuntimeFacade facade(RuntimeBatchConfig{.world_count = 1, .worker_threads = 1});
    BatchWorldSetupRequest setup{};
    setup.seeds = {42};
    setup.time_steps = {0.05};
    setup.spawn_requests = {parity_request()};
    const auto setup_result = facade.apply_world_setup(setup);
    REQUIRE(setup_result.entity_ids.size() == 1);

    const WorldEntityRef maintained_ref{.world_index = 0,
                                        .entity_id = setup_result.entity_ids.front()};
    const auto maintained_before = facade.get_agent_observations_batch({maintained_ref});
    REQUIRE(maintained_before.size() == 1);

    RuntimeKernelCandidate candidate({
        .host_id = {.high = 0x5044432D50415249ULL, .low = 7},
        .mode = runtime::host::RuntimeHostMode::Shadow,
        .lifecycle_deadline_tick = 100,
    });
    REQUIRE(candidate.start());
    RuntimeKernelCandidateFacadeAdapter candidate_facade(candidate);
    REQUIRE(candidate_facade.set_time_step(0.05));
    const auto candidate_entities = candidate_facade.apply_spawn_batch({parity_request()});
    REQUIRE(candidate_entities.size() == 1);

    WorldEntityKinematics candidate_before{};
    REQUIRE(candidate_facade.try_get_entity_kinematics(candidate_entities.front(),
                                                        &candidate_before));
    check_close(candidate_before.x, maintained_before.front().x);
    check_close(candidate_before.y, maintained_before.front().y);
    check_close(candidate_before.z, maintained_before.front().z);
    check_close(candidate_before.vx, maintained_before.front().vx);
    check_close(candidate_before.vy, maintained_before.front().vy);
    check_close(candidate_before.vz, maintained_before.front().vz);

    // The candidate seam currently exposes only the common spawn/kinematics
    // subset. Both paths must accept one step, but full post-step parity also
    // depends on maintained setup surfaces (wind/sun/zones/agent metadata)
    // that are intentionally not part of this internal adapter yet.
    REQUIRE(candidate_facade.step_batch());
    facade.step_batch();
    const auto maintained_after = facade.get_agent_observations_batch({maintained_ref});
    REQUIRE(maintained_after.size() == 1);
    WorldEntityKinematics candidate_after{};
    REQUIRE(candidate_facade.try_get_entity_kinematics(candidate_entities.front(),
                                                       &candidate_after));
    CHECK(std::isfinite(candidate_after.x));
    CHECK(std::isfinite(candidate_after.y));
    CHECK(std::isfinite(candidate_after.z));
    CHECK(std::isfinite(maintained_after.front().x));
    CHECK(std::isfinite(maintained_after.front().y));
    CHECK(std::isfinite(maintained_after.front().z));

    const auto composition = facade.export_composition_evidence();
    REQUIRE(composition.available);
    const auto candidate_composition = candidate.composition_snapshot();
    CHECK(candidate_composition.resolved_manifest_sha256 ==
          composition.evidence.resolved_manifest_sha256);
    CHECK(candidate_composition.executable_graph_sha256 ==
          composition.evidence.executable_graph_sha256);
    CHECK(candidate.composition_immutable());
    REQUIRE(candidate.shutdown(10, 100).status);
}

} // TEST_SUITE("runtime_kernel_candidate_parity")
