#include "core/interfaces/environment_model.h"

#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <limits>
#include <random>
#include <string>
#include <vector>

namespace {

using Availability = IEnvironmentModel::TerrainPointAvailability;
using Source = IEnvironmentModel::TerrainPointSource;
using Surface = IEnvironmentModel::TerrainSurfaceClass;
using Observation = IEnvironmentModel::TerrainPointObservation;
using Json = nlohmann::json;

// Feed exact synthetic cells through the real bundle loader, including metadata
// and malformed replacement attempts. This test never uses a private provider seam.
struct ScopedBundle {
    std::filesystem::path root;
    Json manifest;

    ScopedBundle(int width = 21, int height = 21, double step_x = 1.0, double step_y = -1.0) {
        std::random_device random;
        root = std::filesystem::temp_directory_path() /
               ("ef_terrain_point_" + std::to_string(random()) + "_" + std::to_string(random()));
        std::filesystem::create_directories(root);
        const std::size_t count = static_cast<std::size_t>(width) * height;
        std::vector<float> elevation(count);
        std::vector<std::uint8_t> landcover(count, 30);
        for (int row = 0; row < height; ++row) {
            for (int col = 0; col < width; ++col) {
                elevation[static_cast<std::size_t>(row) * width + col] =
                    100.0F + static_cast<float>(col) * 0.25F + static_cast<float>(row) * 0.5F;
            }
        }
        write("elevation.f32le", elevation.data(), count * sizeof(float));
        write("landcover.u8", landcover.data(), count);
        Json metadata = {{"origin_xy_m", {0.0, 0.0}}, {"step_xy_m", {step_x, step_y}}};
        manifest = {
            {"contract_version", "arnis_cmo_bundle.v1"},
            {"coordinate_frame", "local_enu_m"},
            {"no_held_capability_release", true},
            {"tile_scheme", {{"tile_id", "tile:synthetic-point"}}},
            {"artifacts",
             {{{"kind", "elevation_raster"},
               {"path", "elevation.f32le"},
               {"shape", {height, width}},
               {"byte_length", count * sizeof(float)},
               {"metadata", metadata}},
              {{"kind", "landcover_raster"},
               {"path", "landcover.u8"},
               {"shape", {height, width}},
               {"byte_length", count},
               {"metadata", metadata}}}},
        };
        manifest["artifacts"][0]["metadata"]["vertical_datum"] =
            "source_provider_native_unspecified";
        manifest["artifacts"][0]["metadata"]["source_provider"] = "synthetic_dem_fixture";
        manifest["artifacts"][1]["metadata"]["classification_scheme"] = "ESA_WorldCover_2021_v200";
        save();
    }

    ScopedBundle(const ScopedBundle &) = delete;
    ScopedBundle &operator=(const ScopedBundle &) = delete;

    ~ScopedBundle() {
        std::error_code ignored;
        std::filesystem::remove_all(root, ignored);
    }

    void write(const char *name, const void *data, std::size_t size) const {
        std::ofstream stream(root / name, std::ios::binary);
        stream.write(static_cast<const char *>(data), static_cast<std::streamsize>(size));
        REQUIRE(stream.good());
    }

    void save() const {
        std::ofstream stream(root / "bundle.json");
        stream << manifest.dump();
        REQUIRE(stream.good());
    }
};

struct LegacyEnvironment final : IEnvironmentModel {
    AtmosphericData get_atmosphere_at(double, double, double) override { return {}; }
    double get_terrain_elevation(double, double) override { return 123.0; }
    bool check_line_of_sight(double, double, double, double, double, double) override {
        return true;
    }
    double get_weather_attenuation(double, double, double, double, double, double, int) override {
        return 0.0;
    }
    Vec3 get_sun_direction() override { return {}; }
    TerrainCell get_terrain_at(double, double) override {
        return {123.0, SurfaceType::Concrete, 1.0, 0.0, 0.0, 0.0};
    }
    void clear_zones() override {}
    void add_zone(const std::string &, double, double, double, double, double,
                  SurfaceType) override {}
};

void check_no_sample(const Observation &observation) {
    CHECK_FALSE(std::isfinite(observation.elevation_m));
    CHECK_FALSE(observation.surface.has_value());
}

void check_same_sample(const Observation &left, const Observation &right) {
    CHECK(left.availability == right.availability);
    CHECK(left.elevation_m == doctest::Approx(right.elevation_m));
    CHECK(left.surface == right.surface);
    CHECK(left.landcover_code == right.landcover_code);
    CHECK(left.source == right.source);
    CHECK(left.horizontal_frame == right.horizontal_frame);
    CHECK(left.vertical_datum == right.vertical_datum);
    CHECK(left.elevation_source == right.elevation_source);
    CHECK(left.surface_source == right.surface_source);
    CHECK(left.tile_id == right.tile_id);
    CHECK(left.grid_step_x_m == right.grid_step_x_m);
    CHECK(left.grid_step_y_m == right.grid_step_y_m);
}

} // namespace

TEST_SUITE("environment_terrain_point") {
    TEST_CASE("unsupported and synthetic scalar providers do not fabricate a typed raster sample") {
        LegacyEnvironment legacy;
        const auto inherited = legacy.get_terrain_point_observation(0.0, 0.0);
        CHECK(inherited.availability == Availability::Unavailable);
        CHECK(inherited.source == Source::None);
        check_no_sample(inherited);

        auto model = make_default_environment_model();
        for (const auto *profile : {"legacy", "flat"}) {
            model->set_terrain_type(profile);
            const auto observation = model->get_terrain_point_observation(0.0, 0.0);
            CHECK(observation.availability == Availability::Unavailable);
            CHECK(observation.source == Source::None);
            check_no_sample(observation);
        }
    }

    TEST_CASE("all raster cells and their edge interiors pair elevation with the source surface") {
        ScopedBundle bundle;
        auto model = make_default_environment_model();
        REQUIRE(model->load_arnis_terrain_bundle(bundle.root.string()));
        for (int row = 0; row < 21; ++row) {
            for (int col = 0; col < 21; ++col) {
                for (const double offset : {0.0, -0.4, 0.4}) {
                    const double x = static_cast<double>(col) + offset;
                    const double y = -static_cast<double>(row) + offset;
                    INFO("x=" << x << " y=" << y);
                    const auto observation = model->get_terrain_point_observation(x, y);
                    CHECK(observation.availability == Availability::Available);
                    CHECK(observation.elevation_m ==
                          doctest::Approx(100.0 + col * 0.25 + row * 0.5));
                    CHECK(observation.surface == Surface::Grassland);
                    CHECK(observation.landcover_code == 30);
                    CHECK(observation.elevation_m == model->get_terrain_elevation(x, y));
                }
            }
        }
        const auto observation = model->get_terrain_point_observation(2.0, -3.0);
        CHECK(observation.source == Source::ArnisMetricRaster);
        CHECK(observation.horizontal_frame == "local_enu_m");
        CHECK(observation.vertical_datum == "source_provider_native_unspecified");
        CHECK(observation.elevation_source == "synthetic_dem_fixture");
        CHECK(observation.surface_source == "ESA_WorldCover_2021_v200");
        CHECK(observation.tile_id == "tile:synthetic-point");
        CHECK(observation.grid_step_x_m == 1.0);
        CHECK(observation.grid_step_y_m == -1.0);
    }

    TEST_CASE("out of coverage retains provenance without a hill or obstacle fallback") {
        ScopedBundle bundle;
        auto model = make_default_environment_model();
        REQUIRE(model->load_arnis_terrain_bundle(bundle.root.string()));
        for (const auto &[x, y] :
             {std::pair{-1.0, -10.0}, std::pair{21.0, -10.0}, std::pair{10.0, 1.0},
              std::pair{10.0, -21.0}, std::pair{-0.5, 0.0}, std::pair{20.5, 0.0},
              std::pair{std::numeric_limits<double>::max(), 0.0}}) {
            const auto observation = model->get_terrain_point_observation(x, y);
            CHECK(observation.availability == Availability::OutOfCoverage);
            CHECK(observation.source == Source::ArnisMetricRaster);
            CHECK(observation.vertical_datum == "source_provider_native_unspecified");
            check_no_sample(observation);
        }
        // Compatibility callers retain their existing scalar fallback.
        CHECK(std::isfinite(model->get_terrain_elevation(-1.0, -10.0)));
        CHECK(model->get_terrain_at(-1.0, -10.0).type == IEnvironmentModel::SurfaceType::Obstacle);
    }

    TEST_CASE("nonfinite inputs are invalid before any raster lookup") {
        ScopedBundle bundle;
        auto model = make_default_environment_model();
        for (const bool load_raster : {false, true}) {
            if (load_raster) REQUIRE(model->load_arnis_terrain_bundle(bundle.root.string()));
            for (const double invalid :
                 {std::numeric_limits<double>::quiet_NaN(), std::numeric_limits<double>::infinity(),
                  -std::numeric_limits<double>::infinity()}) {
                for (const auto &[x, y] : {std::pair{invalid, 0.0}, std::pair{0.0, invalid}}) {
                    const auto observation = model->get_terrain_point_observation(x, y);
                    CHECK(observation.availability == Availability::InvalidInput);
                    check_no_sample(observation);
                }
            }
        }
    }

    TEST_CASE("non-square signed metric steps and a single-cell raster remain queryable") {
        ScopedBundle bundle(3, 2, -2.0, 4.0);
        auto model = make_default_environment_model();
        REQUIRE(model->load_arnis_terrain_bundle(bundle.root.string()));
        const auto observation = model->get_terrain_point_observation(-4.0, 4.0);
        CHECK(observation.availability == Availability::Available);
        CHECK(observation.elevation_m == doctest::Approx(101.0));
        CHECK(observation.grid_step_x_m == -2.0);
        CHECK(observation.grid_step_y_m == 4.0);
        CHECK(model->get_terrain_point_observation(-6.0, 4.0).availability ==
              Availability::OutOfCoverage);

        ScopedBundle single(1, 1);
        REQUIRE(model->load_arnis_terrain_bundle(single.root.string()));
        CHECK(model->get_terrain_point_observation(0.0, 0.0).availability ==
              Availability::Available);
    }

    TEST_CASE("declared unspecified empty missing and null datums retain their original meaning") {
        ScopedBundle bundle;
        auto model = make_default_environment_model();
        auto &metadata = bundle.manifest["artifacts"][0]["metadata"];
        for (const auto *datum :
             {"fixture_local_datum", "source_provider_native_unspecified", ""}) {
            metadata["vertical_datum"] = datum;
            bundle.save();
            REQUIRE(model->load_arnis_terrain_bundle(bundle.root.string()));
            const auto observation = model->get_terrain_point_observation(0.0, 0.0);
            CHECK(observation.availability == Availability::Available);
            CHECK(observation.vertical_datum == datum);
            CHECK(observation.elevation_m == 100.0);
        }
        for (const bool missing : {true, false}) {
            if (missing)
                metadata.erase("vertical_datum");
            else
                metadata["vertical_datum"] = nullptr;
            bundle.save();
            REQUIRE(model->load_arnis_terrain_bundle(bundle.root.string()));
            CHECK(model->get_terrain_point_observation(0.0, 0.0).vertical_datum.empty());
        }
    }

    TEST_CASE("raw WorldCover classes are not movement policy or scenario overlays") {
        ScopedBundle bundle(13, 1);
        const std::array<std::uint8_t, 13> codes = {10, 20, 30, 40,  50, 60, 70,
                                                    80, 90, 95, 100, 0,  255};
        const std::array<Surface, 11> surfaces = {
            Surface::TreeCover, Surface::Shrubland,  Surface::Grassland, Surface::Cropland,
            Surface::BuiltUp,   Surface::BareGround, Surface::SnowIce,   Surface::Water,
            Surface::Wetland,   Surface::Mangroves,  Surface::MossLichen};
        bundle.write("landcover.u8", codes.data(), codes.size());
        auto model = make_default_environment_model();
        REQUIRE(model->load_arnis_terrain_bundle(bundle.root.string()));
        model->add_zone("compatibility_runway", 0.0, 0.0, 100.0, 100.0, 0.0,
                        IEnvironmentModel::SurfaceType::Concrete);
        for (std::size_t index = 0; index < codes.size(); ++index) {
            const auto observation =
                model->get_terrain_point_observation(static_cast<double>(index), 0.0);
            CHECK(observation.landcover_code == codes[index]);
            if (index < surfaces.size()) {
                CHECK(observation.availability == Availability::Available);
                CHECK(observation.surface == surfaces[index]);
                CHECK(observation.elevation_m ==
                      doctest::Approx(100.0 + static_cast<double>(index) * 0.25));
            } else {
                CHECK(observation.availability == Availability::NoData);
                check_no_sample(observation);
            }
        }
        CHECK(model->get_terrain_at(0.0, 0.0).type == IEnvironmentModel::SurfaceType::Concrete);
    }

    TEST_CASE("unknown frames and classification schemes are not silently relabeled") {
        ScopedBundle bundle;
        auto model = make_default_environment_model();
        bundle.manifest["coordinate_frame"] = "fixture_source_local_grid";
        bundle.save();
        REQUIRE(model->load_arnis_terrain_bundle(bundle.root.string()));
        CHECK(model->get_terrain_point_observation(0.0, 0.0).horizontal_frame ==
              "fixture_source_local_grid");
        bundle.manifest.erase("coordinate_frame");
        auto &metadata = bundle.manifest["artifacts"][1]["metadata"];
        for (const auto *scheme : {"undeclared_fixture_classification", ""}) {
            metadata["classification_scheme"] = scheme;
            bundle.save();
            REQUIRE(model->load_arnis_terrain_bundle(bundle.root.string()));
            const auto observation = model->get_terrain_point_observation(0.0, 0.0);
            CHECK(observation.horizontal_frame.empty());
            CHECK(observation.surface_source == scheme);
            CHECK(observation.landcover_code == 30);
            CHECK(observation.availability == Availability::NoData);
            check_no_sample(observation);
        }
        metadata.erase("classification_scheme");
        bundle.manifest["coordinate_frame"] = nullptr;
        bundle.save();
        REQUIRE(model->load_arnis_terrain_bundle(bundle.root.string()));
        const auto observation = model->get_terrain_point_observation(0.0, 0.0);
        CHECK(observation.horizontal_frame.empty());
        CHECK(observation.surface_source.empty());
        CHECK(observation.availability == Availability::NoData);
        check_no_sample(observation);
    }

    TEST_CASE("failed replacement loads preserve the active sample and its provenance") {
        ScopedBundle good;
        auto model = make_default_environment_model();
        REQUIRE(model->load_arnis_terrain_bundle(good.root.string()));
        const auto before = model->get_terrain_point_observation(2.0, -3.0);
        ScopedBundle bad;
        SUBCASE("byte count mismatch") {
            bad.manifest["artifacts"][0]["byte_length"] = 1;
        }
        SUBCASE("invalid datum type") {
            bad.manifest["artifacts"][0]["metadata"]["vertical_datum"] = 42;
        }
        SUBCASE("invalid frame type") {
            bad.manifest["coordinate_frame"] = 42;
        }
        SUBCASE("inconsistent grids") {
            bad.manifest["artifacts"][1]["metadata"]["step_xy_m"] = {2.0, -1.0};
        }
        SUBCASE("missing raster") {
            bad.manifest["artifacts"][0]["path"] = "missing.f32le";
        }
        bad.save();
        CHECK_FALSE(model->load_arnis_terrain_bundle(bad.root.string()));
        check_same_sample(before, model->get_terrain_point_observation(2.0, -3.0));
    }
}
