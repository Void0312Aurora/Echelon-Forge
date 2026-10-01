// Native Air EW owner tests: MAWS launch attribution, RWR row projection, and
// countermeasure release admission.  These pin the native semantics the
// scripted EW layer consumes; they do not exercise any Python decision model.

#include "core/engine/simulation_kernel.h"

#include "components/basic/common.h"
#include "components/command/pilot_action.h"
#include "components/physics/instruments.h"
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

    TEST_CASE("countermeasure release admission treats a negative stamp as never released") {
        CHECK(countermeasure_release_ready(-1.0, 0.5, 0.0));
        CHECK(countermeasure_release_ready(-1.0, 0.5, 0.05));
        CHECK_FALSE(countermeasure_release_ready(0.05, 0.5, 0.30));
        CHECK(countermeasure_release_ready(0.05, 0.5, 0.55));
        // A stamp of exactly zero is a real release at t=0, not "never".
        CHECK_FALSE(countermeasure_release_ready(0.0, 0.5, 0.25));
    }

    TEST_CASE("jammer command admission keys an installed pod and rejects bad requests") {
        Jammer pod{false, 1000.0, 2000.0, JammingType::NoiseBarrage, 60.0};
        CHECK(apply_jammer_command(pod, true, 1, 2.0));
        CHECK(pod.is_active);
        CHECK(pod.type == JammingType::NoiseSpot);
        CHECK(pod.transmit_start_time_s == doctest::Approx(2.0));
        // Holding the switch keeps the original transmit-start stamp.
        CHECK_FALSE(apply_jammer_command(pod, true, 1, 2.5));
        CHECK(pod.transmit_start_time_s == doctest::Approx(2.0));
        // An unknown technique code is rejected without touching state.
        CHECK_FALSE(apply_jammer_command(pod, true, 7, 3.0));
        CHECK(pod.type == JammingType::NoiseSpot);
        CHECK(apply_jammer_command(pod, false, 0, 4.0));
        CHECK_FALSE(pod.is_active);
        CHECK(pod.transmit_start_time_s < 0.0);

        Jammer absent{false, 0.0, 0.0, JammingType::NoiseBarrage, 0.0};
        CHECK_FALSE(apply_jammer_command(absent, true, 0, 1.0));
        CHECK_FALSE(absent.is_active);
    }

    TEST_CASE("cockpit jammer switch drives the native pod through EW_Jammer_Control") {
        SimulationKernel kernel;
        kernel.reset(15);
        auto owner = spawn_aircraft(kernel, Side::Blue, 0.0, 0.0, 0.0);
        REQUIRE(owner.is_valid());
        {
            auto lease = kernel.acquire_world_lease();
            Jammer *pod = lease.world().entity(owner.id()).get_mut<Jammer>();
            REQUIRE(pod != nullptr);
            // Install a pod on the generic airframe; the default suite has none.
            pod->power_watts = 1000.0;
            pod->bandwidth_mhz = 2000.0;
            pod->effective_angle = 60.0;
        }

        PilotAction action{};
        action.active = true;
        action.jammer_transmit = true;
        action.jammer_mode = 2;
        kernel.set_pilot_action(owner.id(), action);
        REQUIRE(kernel.run_exact_stage_direct("EW_Jammer_Control"));
        {
            auto lease = kernel.acquire_world_lease();
            auto entity = lease.world().entity(owner.id());
            const Jammer *pod = entity.get<Jammer>();
            const InstrumentState *instrument = entity.get<InstrumentState>();
            REQUIRE(pod != nullptr);
            REQUIRE(instrument != nullptr);
            CHECK(pod->is_active);
            CHECK(pod->type == JammingType::DeceptionDRFM);
            CHECK(instrument->jammer_transmitting);
            CHECK(instrument->jammer_mode == static_cast<int>(JammingType::DeceptionDRFM));
        }

        action.jammer_transmit = false;
        kernel.set_pilot_action(owner.id(), action);
        REQUIRE(kernel.run_exact_stage_direct("EW_Jammer_Control"));
        auto lease = kernel.acquire_world_lease();
        auto entity = lease.world().entity(owner.id());
        CHECK_FALSE(entity.get<Jammer>()->is_active);
        CHECK_FALSE(entity.get<InstrumentState>()->jammer_transmitting);
    }

    TEST_CASE("an uninstalled pod ignores the cockpit switch and reports no jammer") {
        SimulationKernel kernel;
        kernel.reset(16);
        auto owner = spawn_aircraft(kernel, Side::Blue, 0.0, 0.0, 0.0);
        PilotAction action{};
        action.active = true;
        action.jammer_transmit = true;
        kernel.set_pilot_action(owner.id(), action);
        REQUIRE(kernel.run_exact_stage_direct("EW_Jammer_Control"));
        auto lease = kernel.acquire_world_lease();
        auto entity = lease.world().entity(owner.id());
        CHECK_FALSE(entity.get<Jammer>()->is_active);
        CHECK_FALSE(entity.get<InstrumentState>()->jammer_transmitting);
        CHECK(entity.get<InstrumentState>()->jammer_mode == -1);
    }
}
