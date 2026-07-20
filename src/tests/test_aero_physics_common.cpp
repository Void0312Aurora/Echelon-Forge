#include <doctest/doctest.h>

#include "components/physics/dynamics.h"
#include "components/systems/logistics.h"
#include "components/systems/sensor.h"
#include "core/engine/simulation_kernel.h"
#include "models/physics/aerodynamics_common.h"

TEST_SUITE("aero_physics_common") {

    TEST_CASE("lookup_1d_or keeps aircraft-style fallback semantics") {
        CHECK(aero_physics::lookup_1d_or({}, {}, 0.5, 42.0) == doctest::Approx(42.0));

        const std::vector<double> breakpoints{0.0, 1.0, 2.0};
        const std::vector<double> values{10.0, 20.0, 30.0};
        CHECK(aero_physics::lookup_1d_or(breakpoints, values, -1.0, 42.0) == doctest::Approx(10.0));
        CHECK(aero_physics::lookup_1d_or(breakpoints, values, 1.5, 42.0) == doctest::Approx(25.0));
        CHECK(aero_physics::lookup_1d_or(breakpoints, values, 3.0, 42.0) == doctest::Approx(30.0));
    }

    TEST_CASE("positive strict lookup validates missile Mach tables") {
        const aero_physics::LookupTableValidation strict =
            aero_physics::positive_strict_lookup_validation();

        const std::vector<double> breakpoints{0.0, 1.0, 2.0};
        const std::vector<double> values{0.2, 0.6, 0.4};
        REQUIRE(aero_physics::lookup_1d_optional(breakpoints, values, 0.5, strict).has_value());
        CHECK(*aero_physics::lookup_1d_optional(breakpoints, values, 0.5, strict) ==
              doctest::Approx(0.4));

        CHECK_FALSE(
            aero_physics::lookup_1d_optional({0.0, 0.8, 0.8}, values, 0.5, strict).has_value());
        CHECK_FALSE(aero_physics::lookup_1d_optional(breakpoints, {0.2, -0.1, 0.4}, 0.5, strict)
                        .has_value());
    }

    TEST_CASE("air-relative flow shares atmosphere, Mach, and qbar calculation") {
        Transform transform{0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
        Velocity velocity{340.29, 0.0, 0.0};

        const aero_physics::AirRelativeFlow flow =
            aero_physics::compute_air_relative_flow(transform, velocity, nullptr);

        CHECK(flow.atmosphere.air_density ==
              doctest::Approx(aero_physics::kSeaLevelDensityKgM3).epsilon(0.001));
        CHECK(flow.dynamic_pressure_pa ==
              doctest::Approx(0.5 * flow.atmosphere.air_density * 340.29 * 340.29));
        CHECK(flow.mach == doctest::Approx(1.0).epsilon(0.001));
    }

} // TEST_SUITE("aero_physics_common")

TEST_SUITE("missile_guidance_cadence") {

    TEST_CASE("guidance delay does not pause propulsion drag fuel or velocity dynamics") {
        SimulationKernel kernel;
        kernel.reset(42);
        kernel.set_time_step(0.05);
        auto &world = kernel.get_world();

        auto target = world.entity()
                          .set<Transform>({12000.0, 0.0, 3000.0, 180.0, 0.0, 0.0})
                          .set<Velocity>({-200.0, 0.0, 0.0})
                          .set<Alliance>({Side::Red});

        Missile missile{};
        missile.target_id = target.id();
        missile.max_speed = 900.0;
        missile.turn_rate = 35.0;
        missile.seeker_fov_deg = 180.0;
        missile.seeker_lock_range = 100000.0;
        missile.guidance_delay_s = 1.0;
        missile.guidance_update_period_s = 0.2;
        missile.last_guidance_time = -1.0;
        missile.launch_time = 0.0;
        missile.max_flight_time_s = 20.0;
        missile.nav_gain = 3.0;
        missile.active = true;

        auto entity = world.entity()
                          .set<Transform>({0.0, 0.0, 3000.0, 0.0, 0.0, 0.0})
                          .set<Velocity>({250.0, 0.0, 0.0})
                          .set<Alliance>({Side::Blue})
                          .set<Missile>(missile)
                          .set<Mass>({60.0, 20.0, 0.0})
                          .set<MassProperties>({60.0, 80.0, 0.0, 0.0, 0.02});

        kernel.step();

        const Velocity *velocity = entity.get<Velocity>();
        const Missile *runtime = entity.get<Missile>();
        const Mass *mass = entity.get<Mass>();
        REQUIRE(velocity != nullptr);
        REQUIRE(runtime != nullptr);
        REQUIRE(mass != nullptr);
        CHECK(runtime->last_guidance_time == doctest::Approx(-1.0));
        CHECK(mass->fuel_mass_kg < 20.0);
        CHECK(velocity->vx > 250.0);
    }

    TEST_CASE("held guidance command drives autopilot and propulsion between updates") {
        SimulationKernel kernel;
        kernel.reset(42);
        kernel.set_time_step(0.05);
        auto &world = kernel.get_world();

        auto target = world.entity()
                          .set<Transform>({12000.0, 0.0, 3000.0, 180.0, 0.0, 0.0})
                          .set<Velocity>({-200.0, 0.0, 0.0})
                          .set<Alliance>({Side::Red});

        Missile missile{};
        missile.target_id = target.id();
        missile.max_speed = 900.0;
        missile.turn_rate = 35.0;
        missile.seeker_fov_deg = 180.0;
        missile.seeker_lock_range = 100000.0;
        missile.guidance_delay_s = 0.0;
        missile.guidance_update_period_s = 0.5;
        missile.last_guidance_time = -1.0;
        missile.launch_time = 0.001;
        missile.max_flight_time_s = 20.0;
        missile.nav_gain = 3.0;
        missile.active = true;

        Detection track{};
        track.target_id = target.id();
        track.range = 12000.0;
        track.bearing = 20.0;
        track.elevation = 0.0;
        track.closing_speed = 400.0;
        track.signal_strength = 1.0;
        track.local_sensor_hit = true;

        auto entity = world.entity()
                          .set<Transform>({0.0, 0.0, 3000.0, 0.0, 0.0, 0.0})
                          .set<Velocity>({250.0, 0.0, 0.0})
                          .set<Alliance>({Side::Blue})
                          .set<Missile>(missile)
                          .set<ContactList>({{track}})
                          .set<Mass>({60.0, 20.0, 0.0})
                          .set<MassProperties>({60.0, 80.0, 0.0, 0.0, 0.02});

        kernel.step();

        const Missile *runtime = entity.get<Missile>();
        REQUIRE(runtime != nullptr);
        const double first_guidance_time = runtime->last_guidance_time;
        const double first_achieved_accel = runtime->achieved_lateral_accel_mps2;
        const double first_fuel = entity.get<Mass>()->fuel_mass_kg;
        REQUIRE(first_guidance_time >= 0.0);
        REQUIRE(runtime->commanded_lateral_accel_mps2 > 0.0);
        REQUIRE(first_achieved_accel > 0.0);

        kernel.step();
        runtime = entity.get<Missile>();
        REQUIRE(runtime != nullptr);

        CHECK(runtime->last_guidance_time == doctest::Approx(first_guidance_time));
        CHECK(runtime->achieved_lateral_accel_mps2 > first_achieved_accel);
        CHECK(entity.get<Mass>()->fuel_mass_kg < first_fuel);
    }

} // TEST_SUITE("missile_guidance_cadence")
