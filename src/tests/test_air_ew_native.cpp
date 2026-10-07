// Native Air EW owner tests: MAWS launch attribution, RWR row projection, and
// countermeasure release admission.  These pin the native semantics the
// scripted EW layer consumes; they do not exercise any Python decision model.

#include "core/engine/simulation_kernel.h"
#include "core/engine/state_transfer_component_reflection.h"

#include "components/basic/common.h"
#include "components/combat/common/weapon_common.h"
#include "components/command/pilot_action.h"
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

    TEST_CASE("rwr rows are ordered launch, then lock, then plain emitters") {
        SimulationKernel kernel;
        kernel.reset(14);
        auto owner = spawn_aircraft(kernel, Side::Blue, 0.0, 0.0, 0.0);
        auto launcher = spawn_aircraft(kernel, Side::Red, 0.0, 20000.0, 180.0);
        std::vector<flecs::entity> painters;
        for (int index = 0; index < 4; ++index) {
            painters.push_back(
                spawn_aircraft(kernel, Side::Red, 3000.0 * (index + 1), 9000.0, 180.0));
        }
        {
            auto lease = kernel.acquire_world_lease();
            place_missile(lease.world(), launcher.id(), owner.id(), 0.0, 6000.0);
        }
        REQUIRE(kernel.run_exact_stage_direct("MAWS_Update"));
        {
            // Four plain painters are detected before the launch fact is
            // merged, and the last painter also holds a lock.
            auto lease = kernel.acquire_world_lease();
            RWR *rwr = lease.world().entity(owner.id()).get_mut<RWR>();
            REQUIRE(rwr != nullptr);
            for (const auto &painter : painters) {
                rwr->detected_radar_ids.push_back(painter.id());
            }
            rwr->locking_radar_ids.push_back(painters.back().id());
        }

        const AgentObservation obs = kernel.get_agent_observation(owner.id());
        REQUIRE(obs.rwr_warnings.size() == 5);
        // A four-row consumer keeps the launch row and the lock row.
        CHECK(obs.rwr_warnings[0].is_launch);
        CHECK(obs.rwr_warnings[0].source_id == launcher.id());
        CHECK(obs.rwr_warnings[1].is_lock);
        CHECK(obs.rwr_warnings[1].source_id == painters.back().id());
        // Plain rows keep their detection order.
        CHECK(obs.rwr_warnings[2].source_id == painters[0].id());
        CHECK(obs.rwr_warnings[3].source_id == painters[1].id());
        CHECK(obs.rwr_warnings[4].source_id == painters[2].id());
    }

    TEST_CASE("reset clears warnings without independently producing launch facts") {
        SimulationKernel kernel;
        kernel.reset(15);
        auto owner = spawn_aircraft(kernel, Side::Blue, 0.0, 0.0, 0.0);
        {
            auto lease = kernel.acquire_world_lease();
            place_missile(lease.world(), 0, owner.id(), 0.0, 6000.0);
        }
        REQUIRE(kernel.run_exact_stage_direct("MAWS_Update"));
        CHECK_FALSE(kernel.get_agent_observation(owner.id()).rwr_warnings.empty());
        REQUIRE(kernel.run_exact_stage_direct("RWR_Reset"));
        CHECK(kernel.get_agent_observation(owner.id()).rwr_warnings.empty());
        auto lease = kernel.acquire_world_lease();
        const RWR *rwr = lease.world().entity(owner.id()).get<RWR>();
        REQUIRE(rwr != nullptr);
        CHECK_FALSE(rwr->is_missile_launch);
        CHECK(rwr->missile_approach_warnings.empty());
    }

    TEST_CASE("ESM-only guidance sorts ahead of locks and coalesces with radar evidence") {
        SimulationKernel kernel;
        kernel.reset(16);
        auto owner = spawn_aircraft(kernel, Side::Blue, 0.0, 0.0, 0.0);
        auto painter = spawn_aircraft(kernel, Side::Red, 9000.0, 0.0, 270.0);
        {
            auto lease = kernel.acquire_world_lease();
            auto entity = lease.world().entity(owner.id());
            entity.get_mut<RWR>()->detected_radar_ids.push_back(painter.id());
            EmitterDetection launch{};
            launch.source_id = 1001;
            launch.observed_time_s = 0.0;
            launch.classification_known = true;
            launch.is_missile_guidance = true;
            EmitterDetection lock = launch;
            lock.source_id = painter.id();
            lock.is_missile_guidance = false;
            lock.is_radar_lock = true;
            entity.get_mut<ESMReceiver>()->detections = {lock, launch};
        }
        const auto obs = kernel.get_agent_observation(owner.id());
        REQUIRE(obs.rwr_warnings.size() == 2);
        CHECK(obs.rwr_warnings[0].source_id == 1001);
        CHECK(obs.rwr_warnings[0].is_launch);
        CHECK(obs.rwr_warnings[1].source_id == painter.id());
        CHECK(obs.rwr_warnings[1].is_lock);
        CHECK_FALSE(obs.rwr_warnings[1].is_launch);
    }

    TEST_CASE("RWR reflection preserves launcher and approach warning vectors") {
        flecs::world world;
        register_state_transfer_component_reflection(world);
        RWR original{};
        original.missile_launch_source_ids = {1001, 1002};
        original.is_missile_launch = true;
        original.missile_approach_warnings = {{1001, 2001, -90.0}, {1002, 2002, 15.0}};
        const auto json = world.to_json(&original);
        RWR restored{};
        REQUIRE(world.from_json(&restored, json.c_str()) != nullptr);
        CHECK(restored.missile_launch_source_ids == original.missile_launch_source_ids);
        CHECK(restored.is_missile_launch);
        REQUIRE(restored.missile_approach_warnings.size() == 2);
        CHECK(restored.missile_approach_warnings[0].source_id == 1001);
        CHECK(restored.missile_approach_warnings[0].missile_id == 2001);
        CHECK(restored.missile_approach_warnings[0].bearing_deg == doctest::Approx(-90.0));
        CHECK(restored.missile_approach_warnings[1].source_id == 1002);
        CHECK(restored.missile_approach_warnings[1].missile_id == 2002);
        CHECK(restored.missile_approach_warnings[1].bearing_deg == doctest::Approx(15.0));
    }

    TEST_CASE("long-interval dispensers admit the first release at t zero but reject a repeat") {
        SimulationKernel kernel;
        kernel.reset(17);
        auto owner = spawn_aircraft(kernel, Side::Blue, 0.0, 0.0, 0.0);
        {
            auto lease = kernel.acquire_world_lease();
            Countermeasures cm{};
            cm.chaff_count = cm.flare_count = 2;
            cm.release_interval = 10.0;
            lease.world().entity(owner.id()).set<Countermeasures>(cm);
        }
        PilotAction action{};
        action.active = action.program_chaff = action.program_flare = true;
        kernel.set_pilot_action(owner.id(), action);
        for (int i = 0; i < 2; ++i) {
            REQUIRE(kernel.run_exact_stage_direct("EW_Release_Chaff"));
            REQUIRE(kernel.run_exact_stage_direct("EW_Release_Flare"));
            auto lease = kernel.acquire_world_lease();
            const auto *cm = lease.world().entity(owner.id()).get<Countermeasures>();
            REQUIRE(cm != nullptr);
            CHECK(cm->chaff_count == 1);
            CHECK(cm->flare_count == 1);
            CHECK(cm->last_chaff_release_time == doctest::Approx(0.0));
            CHECK(cm->last_flare_release_time == doctest::Approx(0.0));
        }
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
