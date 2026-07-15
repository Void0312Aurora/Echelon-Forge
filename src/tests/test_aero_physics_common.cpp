#include <doctest/doctest.h>

#include "models/physics/aerodynamics_common.h"
#include "models/weapons/missile_guidance_math.h"

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

TEST_SUITE("missile_guidance_coordinates") {

    TEST_CASE("world LOS reconstruction is invariant to equivalent heading and bearing pairs") {
        const missile_guidance::Vec3 expected = missile_guidance::normalize({0.6, 0.8, 0.1});
        const double nav_bearing_deg =
            std::atan2(expected.x, expected.y) * 180.0 / M_PI;
        const double elevation_deg =
            std::atan2(expected.z, std::hypot(expected.x, expected.y)) * 180.0 / M_PI;

        for (const double heading_deg : {0.0, 73.0, -132.0}) {
            const Transform transform{0.0, 0.0, 0.0, heading_deg, 0.0, 0.0};
            const auto reconstructed = missile_guidance::world_los_from_relative_angles(
                nav_bearing_deg - heading_deg, elevation_deg, transform);
            CHECK(reconstructed.x == doctest::Approx(expected.x).epsilon(1.0e-12));
            CHECK(reconstructed.y == doctest::Approx(expected.y).epsilon(1.0e-12));
            CHECK(reconstructed.z == doctest::Approx(expected.z).epsilon(1.0e-12));
        }
    }

    TEST_CASE("world LOS angular rate gives zero for radial motion") {
        const missile_guidance::Vec3 los{0.0, 1.0, 0.0};
        const auto rate = missile_guidance::world_los_angular_rate(los, los, 0.1);
        CHECK(missile_guidance::norm(rate) == doctest::Approx(0.0));
    }

    TEST_CASE("world LOS history PN preserves ENU right left and elevation signs") {
        constexpr double dt_s = 0.1;
        constexpr double angle_rad = 0.01;
        const missile_guidance::Vec3 forward{0.0, 1.0, 0.0};

        const missile_guidance::Vec3 right_los{std::sin(angle_rad), std::cos(angle_rad), 0.0};
        const auto right_rate =
            missile_guidance::world_los_angular_rate(forward, right_los, dt_s);
        const auto right_accel = missile_guidance::transverse_pn_acceleration(
            right_rate, forward, 500.0, 4.0, 1.2);
        CHECK(right_accel.x > 0.0);
        CHECK(right_accel.y == doctest::Approx(0.0).epsilon(1.0e-12));

        const missile_guidance::Vec3 left_los{-std::sin(angle_rad), std::cos(angle_rad), 0.0};
        const auto left_rate =
            missile_guidance::world_los_angular_rate(forward, left_los, dt_s);
        const auto left_accel = missile_guidance::transverse_pn_acceleration(
            left_rate, forward, 500.0, 4.0, 1.2);
        CHECK(left_accel.x < 0.0);
        CHECK(std::abs(left_accel.x) == doctest::Approx(std::abs(right_accel.x)));

        const missile_guidance::Vec3 up_los{0.0, std::cos(angle_rad), std::sin(angle_rad)};
        const auto up_rate = missile_guidance::world_los_angular_rate(forward, up_los, dt_s);
        const auto up_accel = missile_guidance::transverse_pn_acceleration(
            up_rate, forward, 500.0, 4.0, 1.2);
        CHECK(up_accel.z > 0.0);
    }

    TEST_CASE("world LOS history PN is transverse to missile velocity") {
        const missile_guidance::Vec3 previous =
            missile_guidance::normalize({0.1, 0.98, 0.15});
        const missile_guidance::Vec3 current =
            missile_guidance::normalize({0.12, 0.96, 0.19});
        const missile_guidance::Vec3 velocity_dir =
            missile_guidance::normalize({0.2, 0.95, -0.1});
        const auto rate = missile_guidance::world_los_angular_rate(previous, current, 0.05);
        const auto acceleration = missile_guidance::transverse_pn_acceleration(
            rate, velocity_dir, 600.0, 4.0, 1.2);
        CHECK(missile_guidance::dot(acceleration, velocity_dir) ==
              doctest::Approx(0.0).epsilon(1.0e-12));
    }

    TEST_CASE("capture range factors expose the current double inverse-range schedule") {
        constexpr double speed_mps = 900.0;
        constexpr double reference_range_m = 6000.0;
        for (const double range_m : {4000.0, 6000.0, 16000.0}) {
            const double base = missile_guidance::capture_base_range_factor(
                speed_mps, range_m, reference_range_m, 0);
            const double terminal = missile_guidance::capture_terminal_weight(
                range_m, reference_range_m, 0.25, 2.5, 0);
            CHECK(base * terminal ==
                  doctest::Approx(speed_mps * speed_mps * reference_range_m /
                                  (range_m * range_m)));
            CHECK(terminal == doctest::Approx(missile_guidance::capture_terminal_weight(
                                  range_m, reference_range_m, 0.25, 2.5, 2)));
        }
    }

    TEST_CASE("capture clamp breakpoints are continuous and explicit") {
        constexpr double reference_range_m = 6000.0;
        CHECK(missile_guidance::capture_terminal_weight(2400.0, reference_range_m, 0.25, 2.5,
                                                        0) == doctest::Approx(2.5));
        CHECK(missile_guidance::capture_terminal_weight(24000.0, reference_range_m, 0.25, 2.5,
                                                        0) == doctest::Approx(0.25));
        CHECK(missile_guidance::capture_terminal_weight(2399.999, reference_range_m, 0.25, 2.5,
                                                        0) == doctest::Approx(2.5));
        CHECK(missile_guidance::capture_terminal_weight(24000.001, reference_range_m, 0.25, 2.5,
                                                        0) == doctest::Approx(0.25));
        CHECK(missile_guidance::capture_terminal_weight(10000.0, reference_range_m, 0.25, 2.5,
                                                        1) == doctest::Approx(1.0));
    }

    TEST_CASE("reference-range and lead schedule modes remove only their named shaping") {
        constexpr double speed_mps = 900.0;
        constexpr double reference_range_m = 6000.0;
        const double near_base = missile_guidance::capture_base_range_factor(
            speed_mps, 4000.0, reference_range_m, 1);
        const double far_base = missile_guidance::capture_base_range_factor(
            speed_mps, 16000.0, reference_range_m, 1);
        CHECK(near_base == doctest::Approx(far_base));
        CHECK(missile_guidance::lead_blend_range_fraction(16000.0, 8000.0, 0.2, 1) ==
              doctest::Approx(1.0));
        CHECK(missile_guidance::lead_blend_range_fraction(4000.0, 8000.0, 0.2, 2) ==
              doctest::Approx(0.0));
        CHECK(missile_guidance::lead_blend_range_fraction(16000.0, 8000.0, 0.2, 0) ==
              doctest::Approx(0.5));
    }

} // TEST_SUITE("missile_guidance_coordinates")
