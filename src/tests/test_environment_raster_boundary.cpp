// Raster-boundary behaviour of the default environment provider's terrain
// queries (docs/systems/environment/work/active/terrain_line_of_sight_v1/README.md,
// "Raster edge"). A query over a measured raster must never read elevation from
// outside it: near an edge the slope window is clamped to the raster, and where
// an axis holds fewer than two cells the slope is unavailable (NaN).

#include "core/interfaces/environment_model.h"
#include "tests/terrain_raster_fixture.h"

#include <doctest/doctest.h>

#include <cmath>
#include <memory>
#include <numbers>
#include <utility>

namespace {

using Surface = IEnvironmentModel::SurfaceType;

std::unique_ptr<IEnvironmentModel> model_over(const terrain_raster_fixture::ScopedBundle &bundle) {
    auto model = make_default_environment_model();
    REQUIRE(model->load_arnis_terrain_bundle(bundle.root()));
    return model;
}

double slope_deg_for(double east_gradient, double north_gradient) {
    return std::atan(std::hypot(east_gradient, north_gradient)) * 180.0 /
           std::numbers::pi_v<double>;
}

} // namespace

TEST_SUITE("environment_raster_boundary") {
    TEST_CASE("an inclined plane has its exact slope on every cell, edges and corners included") {
        // 21 x 21 cells at 1 m: x and y in [0, 20]. Dyadic gradients keep the
        // float32 cells exact, so every in-raster difference is exact.
        constexpr double kEast = 0.25;
        constexpr double kNorth = 0.125;
        const terrain_raster_fixture::ScopedBundle bundle(
            terrain_raster_fixture::inclined_plane(21, 21, 1.0, 100.0, kEast, kNorth));
        auto model = model_over(bundle);
        const double expected = slope_deg_for(kEast, kNorth);
        // Every cell, at its centre and off-centre inside the cell: the query
        // resolves to the containing cell exactly as `get_terrain_at` does.
        for (int east_m = 0; east_m <= 20; ++east_m) {
            for (int north_m = 0; north_m <= 20; ++north_m) {
                for (const double offset : {0.0, 0.4, -0.4}) {
                    const double x = static_cast<double>(east_m) + offset;
                    const double y = static_cast<double>(north_m) - offset;
                    INFO("x=" << x << " y=" << y);
                    CHECK(model->get_ground_slope_deg(x, y) == doctest::Approx(expected));
                }
            }
        }
    }

    TEST_CASE("the slope window clamps to the raster instead of reading past the edge") {
        // A 1 m cliff of 6 m between x = 5 and x = 6, flat on either side.
        terrain_raster_fixture::SyntheticRaster raster;
        raster.width = 21;
        raster.height = 21;
        raster.origin_x = 0.0;
        raster.origin_y = 20.0;
        raster.step_x = 1.0;
        raster.step_y = -1.0;
        raster.elevation = [](int col, int) { return col >= 6 ? 106.0F : 100.0F; };
        const terrain_raster_fixture::ScopedBundle bundle(raster);
        auto model = model_over(bundle);
        // At the west edge cell the window is one-sided, cells 0..5: flat.
        CHECK(model->get_ground_slope_deg(0.0, 10.0) == doctest::Approx(0.0));
        // One cell in, the west half-window holds one cell: cells 0..6, so the
        // 6 m rise is spread over the 6 m actually spanned (45 degrees).
        CHECK(model->get_ground_slope_deg(1.0, 10.0) == doctest::Approx(45.0));
        // Inland the window is symmetric, cells 0..10 at x = 5: 6 m over 10 m.
        CHECK(model->get_ground_slope_deg(5.0, 10.0) == doctest::Approx(slope_deg_for(0.6, 0.0)));
        // Far from the cliff and from the edges the window sees flat ground.
        CHECK(model->get_ground_slope_deg(15.0, 10.0) == doctest::Approx(0.0));
        CHECK(model->get_ground_slope_deg(20.0, 10.0) == doctest::Approx(0.0));
    }

    TEST_CASE("off the raster the slope is unavailable and movement still blocks") {
        const terrain_raster_fixture::ScopedBundle bundle(
            terrain_raster_fixture::inclined_plane(21, 21, 1.0, 100.0, 0.25, 0.125));
        auto model = model_over(bundle);
        for (const auto &[x, y] : {std::pair{-1.0, 10.0}, std::pair{21.0, 10.0},
                                   std::pair{10.0, -1.0}, std::pair{10.0, 21.0}}) {
            INFO("x=" << x << " y=" << y);
            CHECK(std::isnan(model->get_ground_slope_deg(x, y)));
            CHECK(model->get_terrain_at(x, y).type == Surface::Obstacle);
        }
        // Moving out across the west edge still fails closed as an obstacle.
        const auto outbound = model->get_ground_transition_observation(5.0, 10.0, -5.0, 10.0);
        CHECK(outbound.configured);
        CHECK_FALSE(outbound.passable);
        CHECK(outbound.obstacle_blocked);
        CHECK(outbound.destination_surface == Surface::Obstacle);
        // Moving along the edge row stays passable.
        const auto along = model->get_ground_transition_observation(0.0, 2.0, 0.0, 18.0);
        CHECK(along.passable);
    }

    TEST_CASE("an axis with a single cell cannot support a slope estimate") {
        // One column, 21 rows: no east-west difference exists inside the raster.
        const terrain_raster_fixture::ScopedBundle bundle(
            terrain_raster_fixture::inclined_plane(1, 21, 1.0, 100.0, 0.0, 0.125));
        auto model = model_over(bundle);
        CHECK(std::isnan(model->get_ground_slope_deg(0.0, 10.0)));
        CHECK(model->get_terrain_at(0.0, 10.0).type != Surface::Obstacle);
    }
}
