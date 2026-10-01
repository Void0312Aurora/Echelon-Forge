// Native Air EW owner tests: MAWS launch attribution, RWR row projection, and
// countermeasure release admission.  These pin the native semantics the
// scripted EW layer consumes; they do not exercise any Python decision model.

#include "core/engine/simulation_kernel.h"

#include "components/basic/common.h"
#include "components/combat/common/weapon_common.h"
#include "components/systems/ew.h"

#include <doctest/doctest.h>
#include <flecs.h>

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>

namespace {

flecs::entity spawn_aircraft(SimulationKernel &kernel, Side side, double x, double y,
                             double heading_deg) {
    return kernel.spawn_unit(side, "Aircraft", x, y, 3000.0, heading_deg, 0.0, 0.0, 0.0, 0.0, 0.0);
}

// Places an inert-guidance missile entity so MAWS_Update can observe it
// without running the weapon-release service.
flecs::entity place_missile(flecs::world &world, std::uint64_t attacker_id, std::uint64_t target_id,
                            double x, double y, bool active = true) {
    Missile missile{};
    missile.attacker_id = attacker_id;
    missile.target_id = target_id;
    missile.active = active;
    return world.entity().set<Missile>(missile).set<Transform>({x, y, 3000.0, 0.0, 0.0, 0.0});
}

std::vector<RWREvent> launch_rows(const AgentObservation &obs) {
    std::vector<RWREvent> rows;
    std::copy_if(obs.rwr_warnings.begin(), obs.rwr_warnings.end(), std::back_inserter(rows),
                 [](const RWREvent &event) { return event.is_launch; });
    return rows;
}

} // namespace

TEST_SUITE("air_ew_native") {
    TEST_CASE("maws keeps scanning past an out-of-envelope missile") {
        SimulationKernel kernel;
        kernel.reset(11);
        auto owner = spawn_aircraft(kernel, Side::Blue, 0.0, 0.0, 0.0);
        auto far_launcher = spawn_aircraft(kernel, Side::Red, 0.0, 300000.0, 180.0);
        auto near_launcher = spawn_aircraft(kernel, Side::Red, 0.0, 9000.0, 180.0);
        REQUIRE(owner.is_valid());
        REQUIRE(far_launcher.is_valid());
        REQUIRE(near_launcher.is_valid());
        {
            auto lease = kernel.acquire_world_lease();
            flecs::world &world = lease.world();
            // Missile order matters: the out-of-envelope missile is created
            // first so a pass-terminating early return would hide the second.
            place_missile(world, far_launcher.id(), owner.id(), 0.0, 290000.0);
            place_missile(world, near_launcher.id(), owner.id(), 0.0, 6000.0);
        }
        REQUIRE(kernel.run_exact_stage_direct("MAWS_Update"));

        auto lease = kernel.acquire_world_lease();
        const RWR *rwr = lease.world().entity(owner.id()).get<RWR>();
        REQUIRE(rwr != nullptr);
        CHECK(rwr->is_missile_launch);
        REQUIRE(rwr->missile_launch_source_ids.size() == 1);
        CHECK(rwr->missile_launch_source_ids.front() == near_launcher.id());
        REQUIRE(rwr->missile_approach_warnings.size() == 1);
        CHECK(rwr->missile_approach_warnings.front().source_id == near_launcher.id());
        // The missile is due north of a north-facing owner.
        CHECK(rwr->missile_approach_warnings.front().bearing_deg == doctest::Approx(0.0));
    }

    TEST_CASE("maws ignores inactive missiles and missiles aimed at others") {
        SimulationKernel kernel;
        kernel.reset(12);
        auto owner = spawn_aircraft(kernel, Side::Blue, 0.0, 0.0, 0.0);
        auto bystander = spawn_aircraft(kernel, Side::Blue, 5000.0, 0.0, 0.0);
        auto launcher = spawn_aircraft(kernel, Side::Red, 0.0, 9000.0, 180.0);
        {
            auto lease = kernel.acquire_world_lease();
            flecs::world &world = lease.world();
            place_missile(world, launcher.id(), owner.id(), 0.0, 6000.0, false);
            place_missile(world, launcher.id(), bystander.id(), 5000.0, 6000.0);
        }
        REQUIRE(kernel.run_exact_stage_direct("MAWS_Update"));

        auto lease = kernel.acquire_world_lease();
        const RWR *owner_rwr = lease.world().entity(owner.id()).get<RWR>();
        const RWR *bystander_rwr = lease.world().entity(bystander.id()).get<RWR>();
        REQUIRE(owner_rwr != nullptr);
        REQUIRE(bystander_rwr != nullptr);
        CHECK_FALSE(owner_rwr->is_missile_launch);
        CHECK(owner_rwr->missile_launch_source_ids.empty());
        CHECK(owner_rwr->missile_approach_warnings.empty());
        CHECK(bystander_rwr->is_missile_launch);
        REQUIRE(bystander_rwr->missile_approach_warnings.size() == 1);
        // Bystander at (5000, 0) facing north sees the missile at (5000, 6000)
        // dead ahead.
        CHECK(bystander_rwr->missile_approach_warnings.front().bearing_deg == doctest::Approx(0.0));
    }

    TEST_CASE("rwr rows carry launch evidence only for the attributed source") {
        SimulationKernel kernel;
        kernel.reset(13);
        auto owner = spawn_aircraft(kernel, Side::Blue, 0.0, 0.0, 90.0);
        auto launcher = spawn_aircraft(kernel, Side::Red, 0.0, 9000.0, 180.0);
        auto painter = spawn_aircraft(kernel, Side::Red, 9000.0, 0.0, 270.0);
        {
            auto lease = kernel.acquire_world_lease();
            flecs::world &world = lease.world();
            place_missile(world, launcher.id(), owner.id(), 0.0, 6000.0);
        }
        REQUIRE(kernel.run_exact_stage_direct("MAWS_Update"));
        {
            // A painting radar that has not launched: the RWR row must not be
            // marked as a launch just because some other missile is inbound.
            auto lease = kernel.acquire_world_lease();
            RWR *rwr = lease.world().entity(owner.id()).get_mut<RWR>();
            REQUIRE(rwr != nullptr);
            rwr->detected_radar_ids.push_back(painter.id());
        }

        const AgentObservation obs = kernel.get_agent_observation(owner.id());
        const auto painter_row =
            std::find_if(obs.rwr_warnings.begin(), obs.rwr_warnings.end(),
                         [&](const RWREvent &event) { return event.source_id == painter.id(); });
        REQUIRE(painter_row != obs.rwr_warnings.end());
        CHECK_FALSE(painter_row->is_launch);

        const auto launches = launch_rows(obs);
        REQUIRE(launches.size() == 1);
        CHECK(launches.front().source_id == launcher.id());
        // Owner faces east; the missile is due north, i.e. 90 deg to the left.
        CHECK(launches.front().bearing == doctest::Approx(-90.0));
    }

    TEST_CASE("countermeasure release admission treats a negative stamp as never released") {
        CHECK(countermeasure_release_ready(-1.0, 0.5, 0.0));
        CHECK(countermeasure_release_ready(-1.0, 0.5, 0.05));
        CHECK_FALSE(countermeasure_release_ready(0.05, 0.5, 0.30));
        CHECK(countermeasure_release_ready(0.05, 0.5, 0.55));
        // A stamp of exactly zero is a real release at t=0, not "never".
        CHECK_FALSE(countermeasure_release_ready(0.0, 0.5, 0.25));
    }
}
