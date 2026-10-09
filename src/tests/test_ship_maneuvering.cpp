// Ship maneuvering law tests (CSG-S1-B).
//
// Expected values come from closed forms of the law or from the sourced trial
// figures, not from the implementation under test:
//   * steady straight-line speed under quadratic resistance: U = U_order;
//   * full-ahead from rest: U(t) = U_max tanh(t a0 / U_max);
//   * steady full-rudder turn: radius R = STD / 2 at any speed, and speed
//     sigma * U_order at an unchanged engine order;
//   * the critically damped heading loop never overshoots;
//   * damage: attainable speed U_max cap^(1/3), coasting to rest at a mobility
//     kill;
//   * DDG-51 Flight I trial figures (USNI Proceedings, June 2002): rest to
//     flank in 74 s / 820 yd, flank to stop in 66 s / 470 yd.
// The system tests step a ship through the registered ShipMotion system at the
// CSG scenarios' 0.5 s step.

#include "components/basic/common.h"
#include "components/basic/stable_identity.h"
#include "components/combat/common/damage_common.h"
#include "components/domains/naval/command/station_keeping.h"
#include "components/domains/naval/platform/ship_maneuvering.h"
#include "components/domains/naval/platform/ship_platform.h"
#include "components/physics/forces.h"
#include "systems/domains/naval/ship_motion_system.h"
#include "systems/domains/naval/submarine_motion_system.h"
#include "systems/combat/damage_system_naval.h"
#include "systems/physics/instrument_system.h"

#include <doctest/doctest.h>
#include <flecs.h>

#include <cmath>
#include <numbers>

namespace {

constexpr double kYard = 0.9144;
constexpr double kStep = 0.5;

// DDG-51 Flight I under the maneuvering law, values from the migrated record.
ShipPlatform ddg51_flight_i() {
    ShipPlatform ship{};
    ship.length_m = 153.8;
    ship.beam_m = 20.4;
    ship.draft_m = 9.3;
    ship.displacement_full_load_kg = 8362000.0;
    ship.max_speed_mps = 15.43;
    ship.economical_speed_mps = 10.29;
    ship.max_accel_mps2 = 0.3646;
    ship.max_decel_mps2 = 0.1436;
    ship.steady_turning_diameter_m = 491.0;
    ship.nomoto_time_constant = 1.0;
    ship.steady_turn_speed_ratio = 0.67;
    ship.steerageway_speed_mps = 1.0;
    return ship;
}

struct ShipRig {
    flecs::world world;
    flecs::entity ship;

    ShipRig(const ShipPlatform &platform, double heading_deg, double speed_mps) {
        register_ship_motion_system(world);
        const double rad = heading_deg * std::numbers::pi_v<double> / 180.0;
        Transform transform{};
        transform.heading = heading_deg;
        ship = world.entity()
                   .set<Transform>(transform)
                   .set<Velocity>({std::sin(rad) * speed_mps, std::cos(rad) * speed_mps, 0.0})
                   .set<AngularVelocity>({0.0, 0.0, 0.0})
                   .set<ShipPlatform>(platform)
                   .set<StableEntitySerial>({1});
    }

    void order(double heading_deg, double speed_mps) {
        NavalCommandIntent intent{};
        intent.active = true;
        intent.cmd_heading_deg = heading_deg;
        intent.cmd_speed_mps = speed_mps;
        ship.set<NavalCommandIntent>(intent);
    }

    void damage(double mobility_capability, bool mobility_kill) {
        PlatformDamageState state{};
        state.mobility_capability = mobility_capability;
        state.mobility_kill = mobility_kill;
        ship.set<PlatformDamageState>(state);
    }

    void step(int count = 1) {
        for (int i = 0; i < count; ++i) {
            world.progress(kStep);
        }
    }

    double speed() const {
        const Velocity *v = ship.get<Velocity>();
        return std::hypot(v->vx, v->vy);
    }
    double heading() const { return ship.get<Transform>()->heading; }
    double x() const { return ship.get<Transform>()->x; }
    double y() const { return ship.get<Transform>()->y; }
};

double heading_change_deg(double from_deg, double to_deg) {
    return std::remainder(to_deg - from_deg, 360.0);
}

} // namespace

TEST_SUITE("ship_maneuvering") {
    TEST_CASE("resistance balances full ahead at the maximum speed") {
        const auto env = ship_maneuvering::make_envelope(ddg51_flight_i());
        CHECK(env.resistance_per_m * env.max_speed_mps * env.max_speed_mps ==
              doctest::Approx(env.ahead_accel_mps2));
        const double hold = ship_maneuvering::propulsive_accel_mps2(env, env.max_speed_mps,
                                                                    env.max_speed_mps, 1.0, 1.0);
        CHECK(ship_maneuvering::step_speed_mps(env, env.max_speed_mps, hold, 1.0, kStep) ==
              doctest::Approx(env.max_speed_mps).epsilon(1.0e-12));
    }

    TEST_CASE("coasting decays monotonically and never reverses at any step") {
        const auto env = ship_maneuvering::make_envelope(ddg51_flight_i());
        for (const double h : {0.05, 0.5, 5.0, 60.0}) {
            double v = env.max_speed_mps;
            for (int i = 0; i < 200; ++i) {
                const double next = ship_maneuvering::step_speed_mps(env, v, 0.0, 1.0, h);
                CHECK(next >= 0.0);
                CHECK(next <= v);
                v = next;
            }
            // Quadratic drag alone approaches rest asymptotically. Its closed
            // form is U(t) = U0 / (1 + c U0 t), including at a large step.
            const double expected =
                env.max_speed_mps / (1.0 + env.resistance_per_m * env.max_speed_mps * 200.0 * h);
            CHECK(v == doctest::Approx(expected).epsilon(1.0e-12));
        }
    }

    TEST_CASE("backing reaches rest without reversing at any step") {
        const auto env = ship_maneuvering::make_envelope(ddg51_flight_i());
        for (const double h : {0.05, 0.5, 5.0, 60.0}) {
            double v = env.max_speed_mps;
            for (int i = 0; i < int(std::ceil(180.0 / h)); ++i) {
                const double next =
                    ship_maneuvering::step_speed_mps(env, v, -env.astern_accel_mps2, 1.0, h);
                CHECK(next >= 0.0);
                CHECK(next <= v);
                v = next;
            }
            CHECK(v == 0.0);
        }
    }

    TEST_CASE("full ahead from rest follows the tanh closed form") {
        const auto env = ship_maneuvering::make_envelope(ddg51_flight_i());
        const double h = 0.01;
        double v = 0.0;
        for (int i = 0; i < 3000; ++i) {
            v = ship_maneuvering::step_speed_mps(env, v, env.ahead_accel_mps2, 1.0, h);
        }
        const double t = 3000 * h;
        const double expected =
            env.max_speed_mps * std::tanh(t * env.ahead_accel_mps2 / env.max_speed_mps);
        CHECK(v == doctest::Approx(expected).epsilon(2.0e-3));
    }

    TEST_CASE("DDG-51 Flight I reproduces the sourced acceleration and stopping trials") {
        ShipRig rig(ddg51_flight_i(), 0.0, 0.0);
        rig.order(0.0, 15.43);
        double t = 0.0;
        while (rig.speed() < 0.946 * 15.43 && t < 600.0) {
            rig.step();
            t += kStep;
        }
        // Trial: 74 s / 820 yd to flank; the law's speed regulator reaches
        // the 94.6 % mark the fit used within 5 % of both.
        CHECK(t == doctest::Approx(74.0).epsilon(0.05));
        CHECK(rig.y() == doctest::Approx(820.0 * kYard).epsilon(0.05));

        ShipRig stop(ddg51_flight_i(), 0.0, 15.43);
        stop.order(0.0, 0.0);
        t = 0.0;
        while (stop.speed() > 0.05 && t < 600.0) {
            stop.step();
            t += kStep;
        }
        CHECK(t == doctest::Approx(66.0).epsilon(0.05));
        CHECK(stop.y() == doctest::Approx(470.0 * kYard).epsilon(0.07));
    }

    TEST_CASE("a steady full-rudder turn traces the declared circle at any speed") {
        const ShipPlatform platform = ddg51_flight_i();
        for (const double speed_kt : {12.0, 20.0, 30.0}) {
            const double u = speed_kt * 0.514444;
            ShipRig rig(platform, 0.0, u);
            PilotAction full_right{};
            full_right.active = true;
            full_right.rudder = 1.0;
            full_right.throttle = u / platform.max_speed_mps;
            rig.ship.set<PilotAction>(full_right);
            rig.step(int(std::round(600.0 / kStep)));
            const double r = rig.ship.get<AngularVelocity>()->r;
            const double v = rig.speed();
            CHECK(v / r ==
                  doctest::Approx(0.5 * platform.steady_turning_diameter_m).epsilon(1.0e-3));
            CHECK(v / u == doctest::Approx(platform.steady_turn_speed_ratio).epsilon(1.0e-2));
        }
    }

    TEST_CASE("course changes under the autopilot never overshoot") {
        for (const double change : {10.0, 45.0, 90.0, 180.0}) {
            ShipRig rig(ddg51_flight_i(), 0.0, 10.29);
            rig.order(change, 10.29);
            double furthest = 0.0;
            for (int i = 0; i < 1200; ++i) {
                rig.step();
                furthest = std::max(furthest, heading_change_deg(0.0, rig.heading()));
            }
            CHECK(furthest <= change + 1.0e-6);
            CHECK(heading_change_deg(0.0, rig.heading()) ==
                  doctest::Approx(change).epsilon(1.0e-3));
            CHECK(rig.speed() == doctest::Approx(10.29).epsilon(1.0e-3));
        }
    }

    TEST_CASE("below steerageway the rudder has no authority") {
        ShipRig rig(ddg51_flight_i(), 0.0, 0.0);
        rig.order(90.0, 0.0);
        rig.step(100);
        CHECK(rig.heading() == doctest::Approx(0.0));
    }

    TEST_CASE("damage limits speed through the mobility capability") {
        for (const double capability : {1.0, 0.5, 0.27}) {
            ShipRig rig(ddg51_flight_i(), 0.0, 15.43);
            rig.damage(capability, false);
            rig.order(0.0, 15.43);
            rig.step(int(std::round(900.0 / kStep)));
            CHECK(rig.speed() == doctest::Approx(15.43 * std::cbrt(capability)).epsilon(2.0e-3));
        }
    }

    TEST_CASE("a mobility kill leaves the ship coasting to rest") {
        ShipRig rig(ddg51_flight_i(), 0.0, 15.43);
        rig.damage(0.2, true);
        rig.order(0.0, 15.43);
        double previous = rig.speed();
        for (int i = 0; i < 4000; ++i) {
            rig.step();
            CHECK(rig.speed() <= previous + 1.0e-12);
            previous = rig.speed();
        }
        CHECK(rig.speed() < 0.5);
    }

    TEST_CASE("naval flooding response reduces propulsion through the live mobility state") {
        ShipRig damaged(ddg51_flight_i(), 0.0, 15.43);
        ShipRig pristine(ddg51_flight_i(), 0.0, 15.43);
        register_naval_damage_system(damaged.world);
        damaged.ship.set<Health>({100.0, 100.0});
        PlatformDamageState state{};
        state.flooding_severity = 0.4;
        state.ongoing_hull_breach = 0.3;
        damaged.ship.set<PlatformDamageState>(state);
        damaged.order(0.0, 15.43);
        pristine.order(0.0, 15.43);
        for (int tick = 0; tick < 400; ++tick) {
            const auto before = *damaged.ship.get<PlatformDamageState>();
            const double hp = damaged.ship.get<Health>()->current_hp;
            INFO("tick=" << tick << ", hp=" << hp << ", mobility=" << before.mobility_capability
                         << ", survivability=" << before.survivability_margin);
            damaged.step();
            REQUIRE(damaged.ship.is_alive());
        }
        pristine.step(400);
        REQUIRE(damaged.ship.is_alive());
        const auto *response = damaged.ship.get<PlatformDamageState>();
        REQUIRE(response != nullptr);
        CHECK(response->mobility_capability < 0.85);
        CHECK(response->mobility_capability > 0.5);
        CHECK(damaged.speed() < pristine.speed() - 0.5);
        CHECK(damaged.speed() > 0.0);
    }

    TEST_CASE("station keeping holds a moving station without residual error") {
        const auto on_station = naval_station_keeping::station_keeping_command(
            0.0, 0.0, 0.0, 10.0, 90.0, 5000.0, 5000.0, 0.0, 123.0);
        CHECK(on_station.speed_mps == doctest::Approx(10.0));
        CHECK(on_station.heading_deg == doctest::Approx(0.0));

        const auto far_astern = naval_station_keeping::station_keeping_command(
            0.0, 0.0, 0.0, 10.0, 0.0, 5000.0, 0.0, -10000.0, 0.0);
        CHECK(far_astern.speed_mps ==
              doctest::Approx(10.0 + naval_station_keeping::kMaxClosingSpeedMps));

        const auto at_rest = naval_station_keeping::station_keeping_command(
            0.0, 0.0, 0.0, 0.0, 0.0, 1000.0, 0.0, 1000.0, 77.0);
        CHECK(at_rest.speed_mps == doctest::Approx(0.0));
        CHECK(at_rest.heading_deg == doctest::Approx(77.0));
    }

    TEST_CASE("off-station closure stays steerable until the arrival window") {
        const auto off_station = naval_station_keeping::station_keeping_command(
            0.0, 0.0, 0.0, 0.0, 90.0, 1000.0, 900.0, 0.0, 0.0, 2.0);
        CHECK(off_station.heading_deg == doctest::Approx(90.0));
        CHECK(off_station.speed_mps == doctest::Approx(2.0));
        const auto arrived = naval_station_keeping::station_keeping_command(
            0.0, 0.0, 0.0, 0.0, 90.0, 1000.0, 990.0, 0.0, 90.0, 2.0);
        CHECK(arrived.speed_mps == 0.0);
        CHECK(arrived.heading_deg == 90.0);
    }
}

TEST_SUITE("submarine_motion") {
    TEST_CASE("vertical motion uses shared nose-up pitch and clamps at fifteen degrees") {
        for (const double depth_rate : {3.0, 10.0}) {
            for (const double target_depth : {20.0, 50.0, 80.0}) {
                flecs::world world;
                register_submarine_motion_system(world);
                SubmarinePlatform platform{};
                platform.max_speed_submerged_mps = 20.0;
                platform.max_depth_rate_mps = depth_rate;
                Transform initial{};
                initial.z = -50.0;
                auto unit = world.entity()
                                .set<Transform>(initial)
                                .set<Velocity>({0.0, 8.0, 0.0})
                                .set<SubmarinePlatform>(platform);
                NavalCommandIntent command{};
                command.active = true;
                command.cmd_speed_mps = 8.0;
                command.cmd_depth_m = target_depth;
                unit.set<NavalCommandIntent>(command);
                world.progress(0.1);
                const auto &position = *unit.get<Transform>();
                const auto &velocity = *unit.get<Velocity>();
                const double sign = target_depth < 50.0 ? 1.0 : target_depth > 50.0 ? -1.0 : 0.0;
                CHECK(velocity.vz == doctest::Approx(sign * depth_rate));
                CHECK(position.pitch == doctest::Approx(sign * (depth_rate == 3.0 ? 12.0 : 15.0)));
                CHECK(position.roll == 0.0);
                CHECK(velocity.vx == doctest::Approx(0.0));
                CHECK(velocity.vy == doctest::Approx(8.0));
                const auto forward = Math::body_to_world({1.0, 0.0, 0.0}, position);
                CHECK(forward.z * velocity.vz >= 0.0);
                if (sign == 0.0) CHECK(forward.z == doctest::Approx(0.0));
            }
        }
    }
    TEST_CASE("hull-forward geometry changes with attitude at fixed position and velocity") {
        Transform hull{100.0, 200.0, -50.0, 0.0, 10.0, 0.0};
        const auto up = Math::body_to_world({1.0, 0.0, 0.0}, hull);
        hull.pitch = -10.0;
        const auto down = Math::body_to_world({1.0, 0.0, 0.0}, hull);
        CHECK(up.z == doctest::Approx(std::sin(Math::to_radians(10.0))));
        CHECK(down.z == doctest::Approx(-up.z));
        CHECK(down.x == doctest::Approx(up.x));
        CHECK(down.y == doctest::Approx(up.y));
        CHECK(hull.z == -50.0);
    }
}

TEST_SUITE("naval_instruments") {
    TEST_CASE("ship and submarine instruments follow motion without aero components") {
        for (const bool submarine : {false, true}) {
            flecs::world world;
            register_ship_motion_system(world);
            register_submarine_motion_system(world);
            register_instrument_system(world);
            InstrumentState initial{};
            initial.jammer_snapshot_time_s = 123.0;
            initial.countermeasure_snapshot_time_s = 124.0;
            auto unit = world.entity().set<Transform>({0, 0, submarine ? -50.0 : 0.0, 0, 0, 0})
                            .set<Velocity>({0, 8, 0}).set<InstrumentState>(initial);
            if (submarine) unit.set<SubmarinePlatform>({});
            else unit.set<ShipPlatform>(ddg51_flight_i()).set<AngularVelocity>({});
            NavalCommandIntent command{};
            command.active = true;
            command.cmd_heading_deg = 90;
            command.cmd_speed_mps = 10;
            command.cmd_depth_m = 80;
            unit.set<NavalCommandIntent>(command);
            for (int step = 0; step < 10; ++step) world.progress(0.1);
            const auto &position = *unit.get<Transform>();
            const auto &velocity = *unit.get<Velocity>();
            const auto &inst = *unit.get<InstrumentState>();
            CHECK(position.heading > 0);
            CHECK(inst.heading_deg == doctest::Approx(position.heading));
            CHECK(inst.ground_speed_mps == doctest::Approx(std::hypot(velocity.vx, velocity.vy)));
            CHECK(inst.vn_mps == doctest::Approx(velocity.vy));
            CHECK(inst.ve_mps == doctest::Approx(velocity.vx));
            CHECK(inst.vd_mps == doctest::Approx(-velocity.vz));
            CHECK(inst.vvi_mps == doctest::Approx(velocity.vz));
            CHECK(inst.pitch_deg == doctest::Approx(position.pitch));
            CHECK(inst.cmd_heading_deg == 90);
            CHECK(inst.cmd_speed_mps == 10);
            CHECK(inst.cmd_alt_m == (submarine ? -80 : 0));
            CHECK(inst.jammer_snapshot_time_s == 123);
            CHECK(inst.countermeasure_snapshot_time_s == 124);
            CHECK_FALSE(unit.has<AeroState>());
            // Installed navigation reports remain authoritative even when
            // deliberately different from truth (e.g. an INS drift test).
            EGI egi{};
            egi.vn_mps = 3; egi.ve_mps = 4; egi.vd_mps = 2;
            egi.lat_deg = 30; egi.lon_deg = 120;
            egi.gps_available = true; egi.position_uncertainty_m = 5;
            unit.set<EGI>(egi);
            world.progress(0.1);
            const auto &reported = *unit.get<InstrumentState>();
            CHECK(reported.ground_speed_mps == 5);
            CHECK(reported.vn_mps == 3);
            CHECK(reported.ve_mps == 4);
            CHECK(reported.vd_mps == 2);
            CHECK(reported.lat_deg == 30);
            CHECK(reported.lon_deg == 120);
            CHECK(reported.gps_available);
        }
    }
}
