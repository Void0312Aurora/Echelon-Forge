#pragma once

// Test-only writer for a minimal `arnis_cmo_bundle.v1` elevation/landcover
// raster pair, plus optional road vectors, so terrain queries can be exercised
// over exact synthetic relief and features through the provider's real bundle
// loader (no private test seam).

#include <cstdint>
#include <filesystem>
#include <fstream>
#include <functional>
#include <random>
#include <string>
#include <vector>

#include <nlohmann/json.hpp>

namespace terrain_raster_fixture {

struct SyntheticRaster {
    int width = 0;
    int height = 0;
    double origin_x = 0.0;
    double origin_y = 0.0;
    double step_x = 1.0;
    double step_y = -1.0;
    // Elevation by (column, row); row 0 is at origin_y, advancing by step_y.
    std::function<float(int, int)> elevation;
    // ESA WorldCover class by (column, row). Unset means class 30 (grassland)
    // everywhere: open terrain.
    std::function<std::uint8_t(int, int)> landcover;
    // `arnis_cmo_features` road features in the local ENU frame. Empty means
    // the bundle declares no road artifact.
    nlohmann::json road_features = nlohmann::json::array();
};

class ScopedBundle {
  public:
    explicit ScopedBundle(const SyntheticRaster &raster) {
        std::random_device device;
        root_ = std::filesystem::temp_directory_path() /
                ("ef_terrain_los_" + std::to_string(device()) + "_" + std::to_string(device()));
        std::filesystem::create_directories(root_ / "rasters");
        const std::size_t cells =
            static_cast<std::size_t>(raster.width) * static_cast<std::size_t>(raster.height);
        std::vector<float> elevation(cells);
        for (int row = 0; row < raster.height; ++row) {
            for (int col = 0; col < raster.width; ++col) {
                elevation[static_cast<std::size_t>(row) * raster.width + col] =
                    raster.elevation(col, row);
            }
        }
        std::vector<std::uint8_t> landcover(cells, 30);
        if (raster.landcover) {
            for (int row = 0; row < raster.height; ++row) {
                for (int col = 0; col < raster.width; ++col) {
                    landcover[static_cast<std::size_t>(row) * raster.width + col] =
                        raster.landcover(col, row);
                }
            }
        }
        write_bytes("rasters/elevation.f32le", elevation.data(), cells * sizeof(float));
        write_bytes("rasters/landcover.u8", landcover.data(), cells);

        const nlohmann::json metadata = {
            {"origin_xy_m", {raster.origin_x, raster.origin_y}},
            {"step_xy_m", {raster.step_x, raster.step_y}},
        };
        const nlohmann::json shape = {raster.height, raster.width};
        nlohmann::json bundle = {
            {"contract_version", "arnis_cmo_bundle.v1"},
            {"no_held_capability_release", true},
            {"artifacts",
             {
                 {{"kind", "elevation_raster"},
                  {"path", "rasters/elevation.f32le"},
                  {"shape", shape},
                  {"byte_length", cells * sizeof(float)},
                  {"metadata", metadata}},
                 {{"kind", "landcover_raster"},
                  {"path", "rasters/landcover.u8"},
                  {"shape", shape},
                  {"byte_length", cells},
                  {"metadata", metadata}},
             }},
        };
        if (!raster.road_features.empty()) {
            std::filesystem::create_directories(root_ / "vectors");
            const nlohmann::json roads = {{"schema", "arnis_cmo_features"},
                                          {"schema_version", 1},
                                          {"coordinate_frame", "local_enu_m"},
                                          {"feature_class", "road"},
                                          {"features", raster.road_features}};
            std::ofstream(root_ / "vectors/roads.cmo.json") << roads.dump();
            bundle["artifacts"].push_back({{"kind", "vector_features"},
                                           {"feature_class", "road"},
                                           {"path", "vectors/roads.cmo.json"}});
        }
        std::ofstream(root_ / "bundle.json") << bundle.dump();
    }

    ScopedBundle(const ScopedBundle &) = delete;
    ScopedBundle &operator=(const ScopedBundle &) = delete;

    ~ScopedBundle() {
        std::error_code ignored;
        std::filesystem::remove_all(root_, ignored);
    }

    [[nodiscard]] std::string root() const { return root_.string(); }

  private:
    void write_bytes(const char *relative, const void *data, std::size_t size) const {
        std::ofstream file(root_ / relative, std::ios::binary);
        file.write(static_cast<const char *>(data), static_cast<std::streamsize>(size));
    }

    std::filesystem::path root_;
};

// 21 x 21 cells at 1 m: x in [0, 20], y in [0, 20] (row 0 at y = 20).
// `ridge_height_m` is added along the column x = 10; elsewhere the surface
// sits at `base_m`.
[[nodiscard]] inline SyntheticRaster east_west_ridge(float base_m, float ridge_height_m) {
    SyntheticRaster raster;
    raster.width = 21;
    raster.height = 21;
    raster.origin_x = 0.0;
    raster.origin_y = 20.0;
    raster.step_x = 1.0;
    raster.step_y = -1.0;
    raster.elevation = [base_m, ridge_height_m](int col, int) {
        return col == 10 ? base_m + ridge_height_m : base_m;
    };
    return raster;
}

// `width` x `height` cells at `step_m`, laid out like `east_west_ridge`:
// x in [0, (width - 1) * step_m], y in [0, (height - 1) * step_m], row 0 at the
// top. Each cell centre holds the plane
// `base_m + east_gradient * x + north_gradient * y`; choose dyadic values so the
// float32 cells are exact.
[[nodiscard]] inline SyntheticRaster inclined_plane(int width, int height, double step_m,
                                                    double base_m, double east_gradient,
                                                    double north_gradient) {
    SyntheticRaster raster;
    raster.width = width;
    raster.height = height;
    raster.origin_x = 0.0;
    raster.origin_y = static_cast<double>(height - 1) * step_m;
    raster.step_x = step_m;
    raster.step_y = -step_m;
    raster.elevation = [=](int col, int row) {
        const double x = static_cast<double>(col) * step_m;
        const double y = static_cast<double>(height - 1 - row) * step_m;
        return static_cast<float>(base_m + east_gradient * x + north_gradient * y);
    };
    return raster;
}

} // namespace terrain_raster_fixture
