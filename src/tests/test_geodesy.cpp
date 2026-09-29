// Geodetic frame tests (Geodetic Frame package, P2-A/P2-B).
//
// Expected values come from closed forms or published references, not from the
// implementation under test:
//   * horizon distance sqrt(2 R h + h^2) and the 4/3 effective radius
//     (ITU-R P.834);
//   * the optical sea horizon of NGA Pub. No. 9 (Bowditch), Table 12;
//   * one degree of arc on the IUGG mean sphere = R * pi / 180;
//   * quarter, third, and half great circles (pi R / 2, pi R / 3, pi R);
//   * azimuthal-equidistant identity: distance and bearing from the anchor are
//     preserved exactly.

#include "components/physics/geodesy.h"

#include <doctest/doctest.h>

#include <cmath>
#include <initializer_list>
#include <numbers>
#include <utility>

namespace {

constexpr double kPi = std::numbers::pi_v<double>;

} // namespace

TEST_SUITE("geodesy") {
    TEST_CASE("one degree of arc on the mean sphere matches R*pi/180") {
        const geodesy::EarthModel earth;
        const double expected = geodesy::kMeanEarthRadiusM * kPi / 180.0; // ~111195 m
        CHECK(geodesy::great_circle_distance_m(earth, 0.0, 0.0, 0.0, 1.0) ==
              doctest::Approx(expected).epsilon(1e-12));
        CHECK(geodesy::great_circle_distance_m(earth, 10.0, 20.0, 11.0, 20.0) ==
              doctest::Approx(expected).epsilon(1e-12));
    }

    TEST_CASE("great-circle distance matches closed-form arcs") {
        geodesy::EarthModel earth;
        earth.radius_m = 6371000.0;
        // Equator to pole along a meridian: a quarter great circle, pi R / 2.
        CHECK(geodesy::great_circle_distance_m(earth, 0.0, 30.0, 90.0, 30.0) ==
              doctest::Approx(kPi * earth.radius_m / 2.0).epsilon(1e-12));
        // Antipodes on the equator: half a great circle, pi R.
        CHECK(geodesy::great_circle_distance_m(earth, 0.0, 0.0, 0.0, 180.0) ==
              doctest::Approx(kPi * earth.radius_m).epsilon(1e-12));
        // 60 degrees of longitude on the equator: R * pi / 3.
        CHECK(geodesy::great_circle_distance_m(earth, 0.0, -30.0, 0.0, 30.0) ==
              doctest::Approx(kPi * earth.radius_m / 3.0).epsilon(1e-12));
    }

    TEST_CASE("initial bearing along cardinal directions") {
        CHECK(geodesy::initial_bearing_deg(0.0, 0.0, 1.0, 0.0) == doctest::Approx(0.0));
        CHECK(geodesy::initial_bearing_deg(0.0, 0.0, 0.0, 1.0) == doctest::Approx(90.0));
        CHECK(geodesy::initial_bearing_deg(0.0, 0.0, -1.0, 0.0) == doctest::Approx(180.0));
        CHECK(geodesy::initial_bearing_deg(0.0, 0.0, 0.0, -1.0) == doctest::Approx(270.0));
    }

    TEST_CASE("local and geodetic conversions round-trip inside a 500 km frame") {
        const geodesy::EarthModel earth;
        const geodesy::GeodeticAnchor anchor{18.2, 109.5, 0.0}; // South China Sea
        const double offsets[][3] = {
            {0.0, 0.0, 0.0},           {250000.0, 0.0, 30.0},       {0.0, -250000.0, 9000.0},
            {354000.0, 354000.0, 0.0}, {-500000.0, 120000.0, 12.0},
        };
        for (const auto &o : offsets) {
            const geodesy::LocalPosition local{o[0], o[1], o[2]};
            const auto geo = geodesy::local_to_geodetic(earth, anchor, local);
            const auto back = geodesy::geodetic_to_local(earth, anchor, geo);
            CHECK(back.east_m == doctest::Approx(local.east_m).epsilon(1e-9).scale(1.0));
            CHECK(back.north_m == doctest::Approx(local.north_m).epsilon(1e-9).scale(1.0));
            CHECK(back.up_m == doctest::Approx(local.up_m));
            // Sub-millimetre agreement in absolute terms.
            CHECK(std::abs(back.east_m - local.east_m) < 1e-3);
            CHECK(std::abs(back.north_m - local.north_m) < 1e-3);
        }
    }

    TEST_CASE("azimuthal-equidistant frame preserves distance and bearing from the anchor") {
        const geodesy::EarthModel earth;
        const geodesy::GeodeticAnchor anchor{36.0, -120.0, 0.0};
        const geodesy::LocalPosition local{300000.0, 400000.0, 0.0}; // 500 km at 36.87 deg
        const auto geo = geodesy::local_to_geodetic(earth, anchor, local);
        const double d = geodesy::great_circle_distance_m(
            earth, anchor.latitude_deg, anchor.longitude_deg, geo.latitude_deg, geo.longitude_deg);
        CHECK(d == doctest::Approx(500000.0).epsilon(1e-9));
        const double bearing = geodesy::initial_bearing_deg(
            anchor.latitude_deg, anchor.longitude_deg, geo.latitude_deg, geo.longitude_deg);
        CHECK(bearing ==
              doctest::Approx(std::atan2(300000.0, 400000.0) * 180.0 / kPi).epsilon(1e-9));
    }

    TEST_CASE("anchor height offsets the local up axis") {
        const geodesy::EarthModel earth;
        const geodesy::GeodeticAnchor anchor{0.0, 0.0, 120.0};
        const auto geo = geodesy::local_to_geodetic(earth, anchor, {0.0, 0.0, 30.0});
        CHECK(geo.height_m == doctest::Approx(150.0));
        CHECK(geodesy::geodetic_to_local(earth, anchor, geo).up_m == doctest::Approx(30.0));
    }

    TEST_CASE("horizon distance matches sqrt(2Rh + h^2) with the 4/3 effective radius") {
        const geodesy::EarthModel earth;
        const double re = geodesy::effective_radius_m(earth, geodesy::kStandardRefractionFactor);
        CHECK(re == doctest::Approx(geodesy::kMeanEarthRadiusM * 4.0 / 3.0));
        for (double h : {1.0, 20.0, 32.0, 10000.0}) {
            CHECK(geodesy::horizon_distance_m(re, h) ==
                  doctest::Approx(std::sqrt(2.0 * re * h + h * h)));
        }
        // Small-height form used in radar practice: 4.12 km * sqrt(h[m]).
        CHECK(geodesy::horizon_distance_m(re, 25.0) / 1000.0 ==
              doctest::Approx(4.1218 * 5.0).epsilon(2e-4));
        CHECK(geodesy::horizon_distance_m(re, -5.0) == doctest::Approx(0.0));
    }

    TEST_CASE("two-way horizon for a 20 m antenna and a 10 km target is about 431 km at 4/3") {
        const geodesy::EarthModel earth;
        const double re = geodesy::effective_radius_m(earth, geodesy::kStandardRefractionFactor);
        const double d = geodesy::two_way_horizon_distance_m(re, 20.0, 10000.0);
        CHECK(d / 1000.0 == doctest::Approx(430.6).epsilon(2e-3));
    }

    TEST_CASE("smooth-earth line of sight agrees with the two-way horizon") {
        const geodesy::EarthModel earth;
        const double re = geodesy::effective_radius_m(earth, geodesy::kStandardRefractionFactor);
        const double h_a = 32.0;
        const double h_b = 25.0;
        const double horizon = geodesy::two_way_horizon_distance_m(re, h_a, h_b);
        // The horizon distance is measured along the tangents; the arc is
        // marginally shorter than the tangent sum, so test either side of it.
        CHECK(geodesy::smooth_earth_line_of_sight(re, h_a, h_b, horizon * 0.99));
        CHECK_FALSE(geodesy::smooth_earth_line_of_sight(re, h_a, h_b, horizon * 1.01));
        CHECK(geodesy::smooth_earth_line_of_sight(re, h_a, h_b, 0.0));
        // Surface to surface is blocked at any positive separation.
        CHECK_FALSE(geodesy::smooth_earth_line_of_sight(re, 0.0, 0.0, 1000.0));
    }

    TEST_CASE("two-way horizon arc is the exact boundary of smooth-earth line of sight") {
        const geodesy::EarthModel earth;
        const double re = geodesy::effective_radius_m(earth, geodesy::kStandardRefractionFactor);
        for (const auto &h : {std::pair{32.0, 25.0}, std::pair{5.0, 45.0}, std::pair{20.0, 10000.0},
                              std::pair{0.0, 30.0}}) {
            const double arc = geodesy::two_way_horizon_arc_m(re, h.first, h.second);
            // One metre either side of the boundary; a relative step would fall
            // below double resolution at the tangent point when one height is 0.
            CHECK(geodesy::smooth_earth_line_of_sight(re, h.first, h.second, arc - 1.0));
            CHECK_FALSE(geodesy::smooth_earth_line_of_sight(re, h.first, h.second, arc + 1.0));
            // The arc and the tangent-length sum differ only at second order in h / Re.
            CHECK(arc == doctest::Approx(geodesy::two_way_horizon_distance_m(re, h.first, h.second))
                             .epsilon(1e-3));
        }
        CHECK(geodesy::two_way_horizon_arc_m(re, 0.0, 0.0) == doctest::Approx(0.0));
    }

    TEST_CASE("optical refraction factor reproduces Bowditch Table 12 sea-horizon distances") {
        // NGA Pub. No. 9, Table 12 "Distance of the Horizon": 100 ft -> 11.7 nmi,
        // 120 ft -> 12.8 nmi, 200 ft -> 16.5 nmi (tabulated to 0.1 nmi).
        const geodesy::EarthModel earth;
        const double re =
            geodesy::effective_radius_m(earth, geodesy::kStandardOpticalRefractionFactor);
        constexpr double kFootM = 0.3048;
        constexpr double kNauticalMileM = 1852.0;
        for (const auto &row :
             {std::pair{100.0, 11.7}, std::pair{120.0, 12.8}, std::pair{200.0, 16.5}}) {
            const double d_nmi =
                geodesy::horizon_distance_m(re, row.first * kFootM) / kNauticalMileM;
            CHECK(std::abs(d_nmi - row.second) <= 0.05);
        }
        // The optical horizon is shorter than the 4/3 radio horizon.
        CHECK(geodesy::kStandardOpticalRefractionFactor < geodesy::kStandardRefractionFactor);
    }

    TEST_CASE("earth bulge at the midpoint equals d^2 / (8 R)") {
        const geodesy::EarthModel earth;
        const double re = geodesy::effective_radius_m(earth, geodesy::kStandardRefractionFactor);
        for (double d : {100000.0, 300000.0, 500000.0}) {
            CHECK(geodesy::earth_bulge_m(re, d * 0.5, d * 0.5) ==
                  doctest::Approx(d * d / (8.0 * re)));
        }
        // 100 km at 4/3: about 147 m (P1-A inventory reference value).
        CHECK(geodesy::earth_bulge_m(re, 50000.0, 50000.0) == doctest::Approx(147.2).epsilon(5e-3));
    }

    TEST_CASE("longitude wraps into [-180, 180)") {
        CHECK(geodesy::wrap_longitude_deg(190.0) == doctest::Approx(-170.0));
        CHECK(geodesy::wrap_longitude_deg(-190.0) == doctest::Approx(170.0));
        CHECK(geodesy::wrap_longitude_deg(180.0) == doctest::Approx(-180.0));
        CHECK(geodesy::wrap_longitude_deg(0.0) == doctest::Approx(0.0));
    }
}
