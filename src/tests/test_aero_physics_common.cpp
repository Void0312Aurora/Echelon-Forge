#include <doctest/doctest.h>

#include "models/physics/aerodynamics_common.h"

TEST_SUITE("aero_physics_common") {

TEST_CASE("lookup_1d_or keeps aircraft-style fallback semantics") {
    CHECK(aero_physics::lookup_1d_or({}, {}, 0.5, 42.0) == doctest::Approx(42.0));

    const std::vector<double> breakpoints{0.0, 1.0, 2.0};
    const std::vector<double> values{10.0, 20.0, 30.0};
    CHECK(aero_physics::lookup_1d_or(breakpoints, values, -1.0, 42.0) ==
          doctest::Approx(10.0));
    CHECK(aero_physics::lookup_1d_or(breakpoints, values, 1.5, 42.0) ==
          doctest::Approx(25.0));
    CHECK(aero_physics::lookup_1d_or(breakpoints, values, 3.0, 42.0) ==
          doctest::Approx(30.0));
}

TEST_CASE("positive strict lookup validates missile Mach tables") {
    const aero_physics::LookupTableValidation strict =
        aero_physics::positive_strict_lookup_validation();

    const std::vector<double> breakpoints{0.0, 1.0, 2.0};
    const std::vector<double> values{0.2, 0.6, 0.4};
    REQUIRE(aero_physics::lookup_1d_optional(breakpoints, values, 0.5, strict).has_value());
    CHECK(*aero_physics::lookup_1d_optional(breakpoints, values, 0.5, strict) ==
          doctest::Approx(0.4));

    CHECK_FALSE(aero_physics::lookup_1d_optional({0.0, 0.8, 0.8}, values, 0.5, strict)
                    .has_value());
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
