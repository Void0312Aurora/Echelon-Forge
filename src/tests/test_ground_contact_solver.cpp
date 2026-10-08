// Semi-implicit ground-contact tests.
//
// Expected values come from the continuous laws or closed forms, not from the
// implementation under test:
//   * static equilibrium of the gear spring: penetration = m g / k;
//   * Coulomb friction: a body at rest stays at rest while the applied force is
//     inside the friction set, and accelerates by (F - mu N) / m once outside;
//   * braking deceleration of a Coulomb law: (mu_brake * 0.8 + mu_roll) * g;
//   * the one-step KKT conditions of the per-wheel minimisation.
// The system tests step a single body under the kernel's integrator updates
// (the ones RotationalIntegrate and LeapfrogIntegrate apply) at the naval
// scenarios' 0.5 s step, which the previous explicit discretisation could not
// carry (natural period of the gear spring ~0.3-0.5 s).

#include "components/basic/common.h"
#include "components/physics/dynamics.h"
#include "components/physics/forces.h"
#include "components/physics/physics_input_policy.h"
#include "components/physics/performance.h"
#include "components/systems/logistics.h"
#include "core/interfaces/environment_model.h"
#include "systems/physics/ground_contact_solver.h"
#include "systems/physics/ground_contact_system.h"
#include "systems/physics/leapfrog_system.h"
#include "systems/physics/rotational_system.h"
#include "systems/system_contribution_registry.h"

#include <doctest/doctest.h>
#include <flecs.h>

#include <array>
#include <cmath>
#include <limits>
#include <string>

namespace {

constexpr double kG = 9.80665;

struct ContactTestEnvironment final : IEnvironmentModel {
    SurfaceType surface = SurfaceType::Concrete;

    AtmosphericData get_atmosphere_at(double, double, double) override {
        return {1.225, 340.0, 101325.0, 288.15, {0.0, 0.0, 0.0}};
    }
    double get_terrain_elevation(double, double) override { return 0.0; }
    bool check_line_of_sight(double, double, double, double, double, double) override {
        return true;
    }
    double get_weather_attenuation(double, double, double, double, double, double, int) override {
        return 0.0;
    }
    Vec3 get_sun_direction() override { return {0.0, 0.0, 1.0}; }
    TerrainCell get_terrain_at(double, double) override {
        return {0.0, surface, 1.0, 0.0, 0.0, 0.0};
    }
    void clear_zones() override {}
    void add_zone(const std::string &, double, double, double, double, double,
                  SurfaceType) override {}
};

// Constant external loads standing in for gravity, thrust, and aerodynamics.
struct ExternalLoad {
    double fx = 0.0, fy = 0.0, fz = 0.0;
    double torque_roll = 0.0, torque_pitch = 0.0, torque_yaw = 0.0;
};

struct ContactRig {
    flecs::world world;
    ContactTestEnvironment environment;
    flecs::entity body;

    ContactRig(double mass_kg, double gear_height_m, double z0_m, const Velocity &v0,
               const ExternalLoad &load, const PilotAction &pilot) {
        // Admitted components first, in registry order: flecs caches component ids per C++
        // type for the whole process, so a raw world must not claim ids in a local order
        // (see the raw-world fixture in test_structural_failure_system.cpp).
        runtime::systems::register_default_component_contributions(world);
        world.set<EnvironmentModelRef>({&environment});
        world.component<ExternalLoad>();
        world.system<ForceAccumulator>("ContactTestClearForces")
            .kind(flecs::OnUpdate)
            .each([](ForceAccumulator &f) { f.clear(); });
        world.system<ForceAccumulator, const ExternalLoad>("ContactTestExternalLoad")
            .kind(flecs::OnUpdate)
            .each([](ForceAccumulator &f, const ExternalLoad &l) {
                f.add_force(l.fx, l.fy, l.fz);
                f.add_torque(l.torque_roll, l.torque_pitch, l.torque_yaw);
            });
        register_ground_contact_system(world);
        register_rotational_integration_system(world);
        register_leapfrog_integration_system(world);

        LandingGear gear{};
        gear.contact_height_m = gear_height_m;
        gear.extension_state = 1.0;
        ExternalLoad with_gravity = load;
        with_gravity.fz -= mass_kg * kG;
        body = world.entity()
                   .set<ForceAccumulator>(ForceAccumulator{})
                   .set<ExternalLoad>(with_gravity)
                   .set<Transform>({0.0, 0.0, z0_m, 0.0, 0.0, 0.0})
                   .set<Velocity>(v0)
                   .set<Mass>({mass_kg, 0.0, 0.0})
                   .set<Inertia>({60000.0, 150000.0, 200000.0})
                   .set<AngularVelocity>({0.0, 0.0, 0.0})
                   .set<LandingGear>(gear)
                   .set<GearState>({true, 0.0, false, 0.0, true})
                   .set<GroundState>({false, 0.0})
                   .set<PilotAction>(pilot);
    }

    void step(double dt, int count) {
        for (int n = 0; n < count; ++n) {
            world.progress(static_cast<float>(dt));
        }
    }
    const Transform &transform() const { return *body.get<Transform>(); }
    const Velocity &velocity() const { return *body.get<Velocity>(); }
    const AngularVelocity &rates() const { return *body.get<AngularVelocity>(); }
};

PilotAction pilot_input(double throttle, double brake, double rudder = 0.0) {
    PilotAction p{};
    p.throttle = throttle;
    p.brake = brake;
    p.rudder = rudder;
    p.active = true;
    return p;
}

} // namespace

TEST_SUITE("ground_contact_solver") {

    TEST_CASE("frozen-force kick-drift-kick is exact for constant acceleration") {
        flecs::world world;
        runtime::systems::register_default_component_contributions(world);
        register_leapfrog_integration_system(world);

        const auto body = world.entity()
                              .set<Transform>({1.0, -2.0, 3.0, 0.0, 0.0, 0.0})
                              .set<Velocity>({3.0, -4.0, 0.5})
                              .set<ForceAccumulator>({4.0, -6.0, 2.0, 0.0, 0.0, 0.0})
                              .set<Mass>({2.0, 0.0, 0.0});

        world.progress(0.25f);

        const auto &position = *body.get<Transform>();
        const auto &velocity = *body.get<Velocity>();
        CHECK(position.x == doctest::Approx(1.8125));
        CHECK(position.y == doctest::Approx(-3.09375));
        CHECK(position.z == doctest::Approx(3.15625));
        CHECK(velocity.vx == doctest::Approx(3.5));
        CHECK(velocity.vy == doctest::Approx(-4.75));
        CHECK(velocity.vz == doctest::Approx(0.75));
    }

    TEST_CASE("angle wrapping leaves non-finite inputs unchanged") {
        const double infinity = std::numeric_limits<double>::infinity();
        const double nan = std::numeric_limits<double>::quiet_NaN();
        CHECK(std::isinf(integration_wrap_angle_360(infinity)));
        CHECK(std::isinf(integration_wrap_angle_360(-infinity)));
        CHECK(std::isnan(integration_wrap_angle_360(nan)));
        CHECK(integration_wrap_angle_360(-30.0) == doctest::Approx(330.0));
    }

    TEST_CASE("ground contact and downstream integrators share one dt policy") {
        CHECK(physics_runtime::resolve_integrator_dt(0.0) == doctest::Approx(0.05));
        CHECK(physics_runtime::resolve_integrator_dt(-1.0) == doctest::Approx(0.05));
        CHECK(physics_runtime::resolve_integrator_dt(0.01) == doctest::Approx(0.01));
        CHECK(physics_runtime::valid_mass(0.5));
        CHECK(physics_runtime::valid_reference_area(0.5));
    }
    TEST_CASE("normal contact settles to the static spring equilibrium in one step") {
        // Body resting at the undeflected gear height under gravity.
        for (double h : {0.05, 0.2, 0.5}) {
            ground_contact_solver::NormalContactInput in;
            in.mass_kg = 15000.0;
            in.dt_s = h;
            in.penetration_m = 0.0;
            in.vertical_speed_mps = 0.0;
            in.other_vertical_force_n = -in.mass_kg * kG;
            in.stiffness_n_per_m = 2.0e6;
            in.damping_n_s_per_m = 3.5e5;
            const auto out = ground_contact_solver::solve_normal_contact(in);
            REQUIRE(out.active);
            CHECK(out.force_n > 0.0);
            CHECK(out.force_n < in.mass_kg * kG);
            CHECK(out.end_penetration_m > 0.0);
            CHECK(out.end_penetration_m < in.mass_kg * kG / in.stiffness_n_per_m);
        }
    }

    TEST_CASE("normal contact is inactive when the free motion ends clear of the surface") {
        ground_contact_solver::NormalContactInput in;
        in.mass_kg = 10000.0;
        in.dt_s = 0.5;
        in.penetration_m = -0.5;
        in.vertical_speed_mps = 0.0;
        in.other_vertical_force_n = -in.mass_kg * kG; // falls 1.23 m in 0.5 s
        in.stiffness_n_per_m = 2.0e6;
        in.damping_n_s_per_m = 3.5e5;
        CHECK(ground_contact_solver::solve_normal_contact(in).active);
        in.penetration_m = -2.0;
        CHECK_FALSE(ground_contact_solver::solve_normal_contact(in).active);
    }

    TEST_CASE("normal contact never launches the body clear of the surface") {
        ground_contact_solver::NormalContactInput in;
        in.mass_kg = 7000.0;
        in.dt_s = 0.05;
        in.penetration_m = 0.02;
        in.vertical_speed_mps = -6.0;
        in.other_vertical_force_n = -in.mass_kg * kG;
        in.stiffness_n_per_m = 2.0e6;
        in.damping_n_s_per_m = 3.5e5;
        const auto out = ground_contact_solver::solve_normal_contact(in);
        REQUIRE(out.active);
        CHECK(out.end_penetration_m >= -1e-12);
    }

    TEST_CASE("wheel force minimiser satisfies the one-step optimality conditions") {
        using namespace ground_contact_solver;
        const Mat2 A{2.0e-5, 3.0e-6, 5.0e-5};
        const WheelForceSet sets[] = {
            {2000.0, 80000.0, 90000.0}, // braked
            {2000.0, 0.0, 90000.0},     // unbraked: box
            {0.0, 80000.0, 90000.0},    // no rolling resistance: pure ellipse
        };
        const Vec2 gs[] = {{0.0, 0.0},   {1.0, 0.0},   {-3.0, 0.5}, {0.2, -4.0},
                           {10.0, 10.0}, {0.01, 0.02}, {-0.5, 0.0}, {0.0, -0.3}};
        for (const WheelForceSet &s : sets) {
            for (const Vec2 &g : gs) {
                const Vec2 f = minimize_over_wheel_force_set(A, g, s);
                CHECK(in_wheel_force_set(f, s));
                // No admissible point on a fine grid does better (convex problem).
                const double best = quad_value(A, g, f);
                const double xr = s.rolling_n + s.brake_n;
                const double yr = s.lateral_n;
                for (int ix = -40; ix <= 40; ++ix) {
                    for (int iy = -40; iy <= 40; ++iy) {
                        const Vec2 z{xr * ix / 40.0, yr * iy / 40.0};
                        if (!in_wheel_force_set(z, s, 0.0)) continue;
                        CHECK(quad_value(A, g, z) >= best - 1e-9 * std::max(1.0, std::abs(best)));
                    }
                }
            }
        }
    }

    TEST_CASE("tangential solve holds a braked body at rest and releases it past the limit") {
        using namespace ground_contact_solver;
        const double m = 15000.0;
        const double Fn = m * kG;
        const PlanarBody body{m, 1.0 / 200000.0};
        auto wheels_for = [&](double brake) {
            std::array<Wheel, 2> w{};
            w[0].x_m = 4.0;
            w[0].force_set = {0.02 * 0.2 * Fn, 0.0, 0.8 * 0.2 * Fn};
            w[1].x_m = -2.0;
            w[1].force_set = {0.02 * 0.8 * Fn, brake * 0.8 * 0.8 * Fn, 0.8 * 0.8 * Fn};
            return w;
        };
        const double h = 0.5;
        // 3 kN idle thrust against a full brake: sticks.
        {
            const std::array<double, 3> u_free{h * 3000.0 / m, 0.0, 0.0};
            const auto out = solve_tangential_contact(body, h, u_free, wheels_for(1.0));
            CHECK(out.converged);
            CHECK(out.force_forward_n == doctest::Approx(-3000.0).epsilon(1e-9));
            CHECK(std::abs(out.force_left_n) < 1e-6);
        }
        // 6 kN thrust, no brake, rolling resistance cap 0.02 m g = 2942 N: rolls away.
        {
            const std::array<double, 3> u_free{h * 6000.0 / m, 0.0, 0.0};
            const auto out = solve_tangential_contact(body, h, u_free, wheels_for(0.0));
            CHECK(out.converged);
            CHECK(out.force_forward_n == doctest::Approx(-0.02 * Fn).epsilon(1e-9));
        }
    }
}

TEST_SUITE("ground_contact_system") {
    TEST_CASE("a parked aircraft stays put at the naval step size") {
        // S0-D measured an F/A-18E-class airframe placed at gear height being thrown
        // up by the first contact step at dt = 0.5 s under the explicit law.
        for (double mass : {7000.0, 15000.0, 25000.0}) {
            for (double h : {0.05, 0.2, 0.5}) {
                CAPTURE(mass);
                CAPTURE(h);
                ContactRig rig(mass, 1.6, 1.6, {0.0, 0.0, 0.0}, {}, pilot_input(0.0, 0.0));
                double z_max = rig.transform().z;
                double z_min = rig.transform().z;
                const int steps = static_cast<int>(std::lround(20.0 / h));
                for (int n = 0; n < steps; ++n) {
                    rig.step(h, 1);
                    z_max = std::max(z_max, rig.transform().z);
                    z_min = std::min(z_min, rig.transform().z);
                }
                const double static_deflection = mass * kG / 2.0e6;
                CHECK(z_max <= 1.6 + 1e-9);
                CHECK(z_min >= 1.6 - 1.5 * static_deflection);
                CHECK(rig.transform().z == doctest::Approx(1.6 - static_deflection).epsilon(1e-6));
                CHECK(std::abs(rig.velocity().vx) < 1e-9);
                CHECK(std::abs(rig.velocity().vy) < 1e-9);
                CHECK(std::abs(rig.velocity().vz) < 1e-6);
                CHECK(rig.body.get<GroundState>()->on_ground);
            }
        }
    }

    TEST_CASE("a dropped aircraft is caught in the step it arrives and does not bounce") {
        for (double h : {0.05, 0.5}) {
            CAPTURE(h);
            ContactRig rig(15000.0, 1.6, 3.0, {0.0, 0.0, -3.0}, {}, pilot_input(0.0, 0.0));
            double z_min = rig.transform().z;
            bool touched = false;
            double z_after_touch = -1e9;
            for (int n = 0; n < static_cast<int>(std::lround(10.0 / h)); ++n) {
                rig.step(h, 1);
                z_min = std::min(z_min, rig.transform().z);
                if (rig.body.get<GroundState>()->on_ground) touched = true;
                if (touched) z_after_touch = std::max(z_after_touch, rig.transform().z);
            }
            CHECK(touched);
            CHECK(z_min > 1.6 - 0.35);          // bounded gear stroke
            CHECK(z_after_touch <= 1.6 + 1e-9); // no rebound off the gear
        }
    }

    TEST_CASE("idle thrust against the parking brake does not creep") {
        for (double h : {0.05, 0.5}) {
            CAPTURE(h);
            ExternalLoad thrust{};
            thrust.fx = 3000.0; // idle-class thrust along +x (heading 0 is north, +y)
            thrust.fy = 3000.0;
            ContactRig rig(15000.0, 1.6, 1.6, {0.0, 0.0, 0.0}, thrust, pilot_input(0.0, 0.0));
            rig.step(h, static_cast<int>(std::lround(30.0 / h)));
            CHECK(std::hypot(rig.transform().x, rig.transform().y) < 1e-6);
            CHECK(std::hypot(rig.velocity().vx, rig.velocity().vy) < 1e-9);
            CHECK(std::abs(rig.rates().r) < 1e-9);
        }
    }

    TEST_CASE("full braking decelerates at the Coulomb rate and stops exactly") {
        // Main gear carries 0.8 of the load and brakes at mu 0.8; both gears roll at 0.02.
        const double decel = (0.8 * 0.8 + 0.02) * kG;
        for (double h : {0.05, 0.5}) {
            CAPTURE(h);
            ContactRig rig(15000.0, 1.6, 1.6 - 15000.0 * kG / 2.0e6, {0.0, 40.0, 0.0}, {},
                           pilot_input(0.0, 1.0));
            // Before the stop the speed follows v0 - decel t (within one step of lag at the
            // start while the normal load builds).
            rig.step(h, static_cast<int>(std::lround(2.0 / h)));
            CHECK(rig.velocity().vy == doctest::Approx(40.0 - decel * 2.0).epsilon(0.03));
            rig.step(h, static_cast<int>(std::lround(10.0 / h)));
            CHECK(std::abs(rig.velocity().vy) < 1e-9);
            CHECK(std::abs(rig.velocity().vx) < 1e-9);
            const double stop_distance = 40.0 * 40.0 / (2.0 * decel);
            CHECK(rig.transform().y == doctest::Approx(stop_distance).epsilon(0.05));
        }
    }

    TEST_CASE("thrust above rolling resistance accelerates at (T - mu_roll N) / m") {
        const double m = 15000.0;
        for (double h : {0.05, 0.5}) {
            CAPTURE(h);
            ExternalLoad thrust{};
            thrust.fy = 30000.0;
            ContactRig rig(m, 1.6, 1.6 - m * kG / 2.0e6, {0.0, 0.0, 0.0}, thrust,
                           pilot_input(0.5, 0.0));
            rig.step(h, static_cast<int>(std::lround(4.0 / h)));
            const double expected = (30000.0 - 0.02 * m * kG) / m * 4.0;
            CHECK(rig.velocity().vy == doctest::Approx(expected).epsilon(0.02));
            CHECK(std::abs(rig.velocity().vx) < 1e-6);
        }
    }

    TEST_CASE("gear attitude constraint holds pitch-up torque at the rotation limit") {
        // A steady nose-up torque beyond the free band: pitch settles at limit + torque / K.
        // The gear pitch spring-damper is light (zeta = D / (2 sqrt(K I)) = 0.18 for
        // Iyy = 1.5e5), so the continuous law itself overshoots to 16.8 deg (RK4, h = 1e-5 s);
        // the implicit step may only damp that, never exceed it.
        constexpr double kContinuousPeakDeg = 16.79;
        for (double h : {0.05, 0.5}) {
            CAPTURE(h);
            ExternalLoad load{};
            load.torque_pitch = 100000.0;
            ContactRig rig(15000.0, 1.6, 1.6 - 15000.0 * kG / 2.0e6, {0.0, 0.0, 0.0}, load,
                           pilot_input(0.0, 0.0));
            double pitch_max = 0.0;
            for (int n = 0; n < static_cast<int>(std::lround(20.0 / h)); ++n) {
                rig.step(h, 1);
                pitch_max = std::max(pitch_max, rig.transform().pitch);
            }
            const double settle_deg = 10.0 + Math::to_degrees(100000.0 / 2.0e6);
            CHECK(rig.transform().pitch == doctest::Approx(settle_deg).epsilon(1e-3));
            CHECK(pitch_max <= kContinuousPeakDeg);
            CHECK(std::abs(rig.rates().q) < 1e-6);
        }
    }
}
