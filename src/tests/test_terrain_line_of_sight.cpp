// Terrain line-of-sight query on the default environment provider
// (docs/systems/environment/work/active/terrain_line_of_sight_v1/README.md).

#include "core/interfaces/environment_model.h"
#include "tests/terrain_raster_fixture.h"

#include <doctest/doctest.h>

#include <cmath>
#include <memory>

namespace {

using Status = IEnvironmentModel::TerrainLineOfSightStatus;
using Reason = IEnvironmentModel::TerrainLineOfSightUnknownReason;
using Source = IEnvironmentModel::TerrainElevationSource;

std::unique_ptr<IEnvironmentModel> model_over(const terrain_raster_fixture::ScopedBundle &bundle) {
    auto model = make_default_environment_model();
    REQUIRE(model->load_arnis_terrain_bundle(bundle.root()));
    return model;
}

} // namespace

TEST_SUITE("terrain_line_of_sight") {
    TEST_CASE("no measured raster is unknown, never visible") {
        auto model = make_default_environment_model();
        const auto procedural =
            model->get_terrain_line_of_sight_observation(0.0, 0.0, 1.6, 100.0, 0.0, 1.0);
        CHECK(procedural.status == Status::Unknown);
        CHECK(procedural.unknown_reason == Reason::NoMeasuredElevation);
        CHECK(procedural.elevation_source == Source::None);

        model->set_terrain_type("flat");
        const auto flat =
            model->get_terrain_line_of_sight_observation(0.0, 0.0, 1.6, 100.0, 0.0, 1.0);
        CHECK(flat.status == Status::Unknown);
        CHECK(flat.unknown_reason == Reason::NoMeasuredElevation);
    }

    TEST_CASE("flat raster is visible with raster-derived sampling provenance") {
        const terrain_raster_fixture::ScopedBundle bundle(
            terrain_raster_fixture::east_west_ridge(100.0F, 0.0F));
        auto model = model_over(bundle);
        const auto los =
            model->get_terrain_line_of_sight_observation(2.0, 10.0, 1.6, 18.0, 10.0, 1.0);
        CHECK(los.status == Status::Visible);
        CHECK(los.unknown_reason == Reason::None);
        CHECK(los.elevation_source == Source::ArnisMetricRaster);
        CHECK(los.sample_spacing_m == doctest::Approx(1.0));
        CHECK(los.distance_m == doctest::Approx(16.0));
        // 16 m at the 1 m cell size: 16 intervals, 15 interior samples.
        CHECK(los.sample_count == 15);
        CHECK(los.from_absolute_height_m == doctest::Approx(101.6));
        CHECK(los.to_absolute_height_m == doctest::Approx(101.0));
        CHECK_FALSE(los.has_blocking_sample);
    }

    TEST_CASE("a ridge above the ray blocks and reports the first blocking sample") {
        const terrain_raster_fixture::ScopedBundle bundle(
            terrain_raster_fixture::east_west_ridge(100.0F, 3.0F));
        auto model = model_over(bundle);
        const auto los =
            model->get_terrain_line_of_sight_observation(2.0, 10.0, 1.6, 18.0, 10.0, 1.0);
        CHECK(los.status == Status::Blocked);
        CHECK(los.unknown_reason == Reason::None);
        REQUIRE(los.has_blocking_sample);
        CHECK(los.blocking_x == doctest::Approx(10.0));
        CHECK(los.blocking_y == doctest::Approx(10.0));
        CHECK(los.blocking_distance_m == doctest::Approx(8.0));
        CHECK(los.blocking_terrain_height_m == doctest::Approx(103.0));
        CHECK(los.blocking_ray_height_m == doctest::Approx(101.3));
        // Seven interior samples precede the crest at 1 m spacing.
        CHECK(los.sample_count == 8);
        // The same crest is symmetric: the reverse sight line is blocked too.
        CHECK(
            model->get_terrain_line_of_sight_observation(18.0, 10.0, 1.0, 2.0, 10.0, 1.6).status ==
            Status::Blocked);
    }

    TEST_CASE("endpoint heights decide a low ridge: stand clears, prone does not") {
        const terrain_raster_fixture::ScopedBundle bundle(
            terrain_raster_fixture::east_west_ridge(100.0F, 0.5F));
        auto model = model_over(bundle);
        CHECK(
            model->get_terrain_line_of_sight_observation(2.0, 10.0, 1.6, 18.0, 10.0, 1.0).status ==
            Status::Visible);
        CHECK(
            model->get_terrain_line_of_sight_observation(2.0, 10.0, 0.3, 18.0, 10.0, 0.15).status ==
            Status::Blocked);
    }

    TEST_CASE("raster edge: last cell is measured, one cell beyond is unknown") {
        const terrain_raster_fixture::ScopedBundle bundle(
            terrain_raster_fixture::east_west_ridge(100.0F, 0.0F));
        auto model = model_over(bundle);
        const auto on_edge =
            model->get_terrain_line_of_sight_observation(12.0, 10.0, 1.6, 20.0, 10.0, 1.0);
        CHECK(on_edge.status == Status::Visible);
        const auto beyond =
            model->get_terrain_line_of_sight_observation(12.0, 10.0, 1.6, 21.0, 10.0, 1.0);
        CHECK(beyond.status == Status::Unknown);
        CHECK(beyond.unknown_reason == Reason::EndpointOutsideRaster);
        CHECK(beyond.elevation_source == Source::ArnisMetricRaster);
    }

    TEST_CASE("non-finite coordinates and negative heights are invalid input") {
        const terrain_raster_fixture::ScopedBundle bundle(
            terrain_raster_fixture::east_west_ridge(100.0F, 0.0F));
        auto model = model_over(bundle);
        CHECK(model->get_terrain_line_of_sight_observation(2.0, 10.0, -0.1, 18.0, 10.0, 1.0)
                  .unknown_reason == Reason::InvalidInput);
        CHECK(model->get_terrain_line_of_sight_observation(2.0, std::nan(""), 1.6, 18.0, 10.0, 1.0)
                  .unknown_reason == Reason::InvalidInput);
    }

    TEST_CASE("coincident endpoints are visible with no interior samples") {
        const terrain_raster_fixture::ScopedBundle bundle(
            terrain_raster_fixture::east_west_ridge(100.0F, 0.0F));
        auto model = model_over(bundle);
        const auto los = model->get_terrain_line_of_sight_observation(5.0, 5.0, 1.6, 5.0, 5.0, 1.0);
        CHECK(los.status == Status::Visible);
        CHECK(los.sample_count == 0);
    }
}
