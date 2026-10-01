#include "core/interfaces/environment_model.h"
#include "models/environment/default_environment_snapshot.h"

#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <vector>
#include <iostream>
#include <algorithm>
#include <cctype>
#include <limits>
#include <stdexcept>
#include <numbers>

#include <nlohmann/json.hpp>

namespace {

struct WeatherZoneImpl {
    Vec3 center;
    double radius;
    double visual_attenuation;
    double ir_attenuation;
};

struct Zone {
    std::string name;
    Vec3 center;
    double width;   // X-size or Diameter
    double length;  // Y-size (0 if circle)
    double heading; // Degrees
    int type;       // 0=Rect, 1=Circle

    // Properties
    IEnvironmentModel::SurfaceType surface;
    double friction;
    double roughness;
    double vegetation_density;
    double runway_heading; // If runway
    int z_order;           // Higher = Top (Overlays others)
};

struct ArnisFeatureGeometry {
    std::vector<std::pair<double, double>> points;
    double width_m = 0.0;
    bool polygon = false;
};

struct RasterGrid {
    Vec3 origin;       // Bottom-Left Corner (Min X, Min Y)
    double resolution; // Meters per cell
    double step_x = 0.0;
    double step_y = 0.0;
    int width;  // Number of columns (X)
    int height; // Number of rows (Y)
    std::vector<IEnvironmentModel::SurfaceType>
        data; // Row-major (y * width + x) (Or standard image layout)
    std::vector<double> elevation;
    std::vector<std::uint8_t> landcover;
    std::vector<ArnisFeatureGeometry> river_features;
    std::vector<ArnisFeatureGeometry> bridge_features;
    std::vector<ArnisFeatureGeometry> tree_line_features;
    std::vector<ArnisFeatureGeometry> settlement_features;
    bool field_overlay_loaded = false;
    bool arnis_metric_bundle = false;

    static double distance_squared_to_segment(double x, double y, double x1, double y1, double x2,
                                              double y2) {
        const double dx = x2 - x1;
        const double dy = y2 - y1;
        const double length_squared = dx * dx + dy * dy;
        const double projection =
            length_squared > 0.0
                ? std::clamp(((x - x1) * dx + (y - y1) * dy) / length_squared, 0.0, 1.0)
                : 0.0;
        const double nearest_x = x1 + projection * dx;
        const double nearest_y = y1 + projection * dy;
        const double offset_x = x - nearest_x;
        const double offset_y = y - nearest_y;
        return offset_x * offset_x + offset_y * offset_y;
    }

    static bool point_in_polygon(double x, double y,
                                 const std::vector<std::pair<double, double>> &points) {
        bool inside = false;
        if (points.size() < 3) return false;
        for (std::size_t i = 0, j = points.size() - 1; i < points.size(); j = i++) {
            const auto &[xi, yi] = points[i];
            const auto &[xj, yj] = points[j];
            const bool crosses =
                ((yi > y) != (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
            if (crosses) inside = !inside;
        }
        return inside;
    }

    static bool contains(const ArnisFeatureGeometry &feature, double x, double y) {
        if (feature.polygon && point_in_polygon(x, y, feature.points)) return true;
        const double radius = std::max(0.0, feature.width_m * 0.5);
        const double threshold = radius * radius;
        for (std::size_t i = 1; i < feature.points.size(); ++i) {
            if (distance_squared_to_segment(x, y, feature.points[i - 1].first,
                                            feature.points[i - 1].second, feature.points[i].first,
                                            feature.points[i].second) <= threshold) {
                return true;
            }
        }
        return false;
    }

    bool bridge_at(double x, double y) const {
        return std::any_of(bridge_features.begin(), bridge_features.end(),
                           [x, y](const auto &feature) { return contains(feature, x, y); });
    }

    bool river_at(double x, double y) const {
        return std::any_of(river_features.begin(), river_features.end(),
                           [x, y](const auto &feature) { return contains(feature, x, y); });
    }

    double cell_step_x() const { return step_x != 0.0 ? step_x : resolution; }
    double cell_step_y() const { return step_y != 0.0 ? step_y : resolution; }

    // The cell containing (x, y). Every raster lookup (surface, elevation,
    // landcover, slope) resolves through this one cell definition.
    bool cell_for(double x, double y, long long &col, long long &row) const {
        const double sx = cell_step_x();
        const double sy = cell_step_y();
        if (!std::isfinite(sx) || !std::isfinite(sy) || sx == 0.0 || sy == 0.0 || width <= 0 ||
            height <= 0) {
            return false;
        }
        const double col_f = (x - origin.x) / sx;
        const double row_f = (y - origin.y) / sy;
        col = static_cast<long long>(std::llround(col_f));
        row = static_cast<long long>(std::llround(row_f));
        return col >= 0 && row >= 0 && col < width && row < height &&
               std::abs(col_f - static_cast<double>(col)) <= 0.51 &&
               std::abs(row_f - static_cast<double>(row)) <= 0.51;
    }

    bool index_for(double x, double y, std::size_t &index) const {
        long long col = 0;
        long long row = 0;
        if (!cell_for(x, y, col, row)) return false;
        index = static_cast<std::size_t>(row) * static_cast<std::size_t>(width) +
                static_cast<std::size_t>(col);
        return index < static_cast<std::size_t>(width) * static_cast<std::size_t>(height);
    }

    // Elevation gradient (dz/dx, dz/dy) at the cell containing (x, y), read
    // from raster cells only. Per axis the half window is `half_span_m` in
    // whole cells of that axis (at least one, the finest difference the grid
    // holds) and is clamped to the raster, so no sample lies outside it: at an
    // edge cell the difference is one-sided, and the window always contains
    // the query cell. The divisor is the metric distance between the two
    // sampled cell centres. Returns false off the raster, or when an axis
    // holds a single cell, since no in-raster difference then exists.
    bool elevation_gradient(double x, double y, double half_span_m, double &east_gradient,
                            double &north_gradient) const {
        long long col = 0;
        long long row = 0;
        if (!cell_for(x, y, col, row) || !std::isfinite(half_span_m) || half_span_m <= 0.0 ||
            elevation.size() !=
                static_cast<std::size_t>(width) * static_cast<std::size_t>(height)) {
            return false;
        }
        const auto clamped_window = [half_span_m](long long centre, long long count, double step,
                                                  long long &low, long long &high) {
            const long long half =
                std::max<long long>(1, std::llround(half_span_m / std::abs(step)));
            low = std::max<long long>(0, centre - half);
            high = std::min<long long>(count - 1, centre + half);
            return high > low;
        };
        long long west = 0;
        long long east = 0;
        long long first_row = 0;
        long long last_row = 0;
        if (!clamped_window(col, width, cell_step_x(), west, east) ||
            !clamped_window(row, height, cell_step_y(), first_row, last_row)) {
            return false;
        }
        const auto at = [this](long long sample_col, long long sample_row) {
            return elevation[static_cast<std::size_t>(sample_row) *
                                 static_cast<std::size_t>(width) +
                             static_cast<std::size_t>(sample_col)];
        };
        // Rows advance by the signed `step_y`, so this is dz/dy in the world frame.
        east_gradient =
            (at(east, row) - at(west, row)) / (static_cast<double>(east - west) * cell_step_x());
        north_gradient = (at(col, last_row) - at(col, first_row)) /
                         (static_cast<double>(last_row - first_row) * cell_step_y());
        return std::isfinite(east_gradient) && std::isfinite(north_gradient);
    }

    // Helper: World (x,y) -> Grid Index
    bool get_surface(double x, double y, IEnvironmentModel::SurfaceType &out_type) const {
        std::size_t idx = 0;
        if (index_for(x, y, idx) && idx < data.size()) {
            out_type = data[idx];
            return true;
        }
        return false;
    }

    bool get_elevation(double x, double y, double &out_elevation) const {
        std::size_t idx = 0;
        if (index_for(x, y, idx) && idx < elevation.size()) {
            out_elevation = elevation[idx];
            return std::isfinite(out_elevation);
        }
        return false;
    }

    bool get_landcover(double x, double y, std::uint8_t &out_code) const {
        std::size_t idx = 0;
        if (index_for(x, y, idx) && idx < landcover.size()) {
            out_code = landcover[idx];
            return true;
        }
        return false;
    }
};

using Json = nlohmann::json;

bool read_binary_bytes(const std::filesystem::path &path, std::size_t expected_bytes,
                       std::vector<std::uint8_t> &out) {
    std::error_code ec;
    if (!std::filesystem::is_regular_file(path, ec) ||
        std::filesystem::file_size(path, ec) != expected_bytes) {
        return false;
    }
    std::ifstream file(path, std::ios::binary);
    if (!file) return false;
    out.resize(expected_bytes);
    file.read(reinterpret_cast<char *>(out.data()), static_cast<std::streamsize>(expected_bytes));
    return file.good() || file.gcount() == static_cast<std::streamsize>(expected_bytes);
}

bool json_finite_pair(const Json &value, double &first, double &second) {
    if (!value.is_array() || value.size() != 2 || !value[0].is_number() || !value[1].is_number()) {
        return false;
    }
    first = value[0].get<double>();
    second = value[1].get<double>();
    return std::isfinite(first) && std::isfinite(second);
}

bool read_feature_geometries(const std::filesystem::path &path, bool bridges,
                             std::vector<ArnisFeatureGeometry> &out) {
    std::ifstream file(path);
    if (!file) return false;
    Json root;
    file >> root;
    if (root.value("schema", "") != "arnis_cmo_features" ||
        root.value("coordinate_frame", "") != "local_enu_m") {
        return false;
    }
    const auto &features = root.at("features");
    if (!features.is_array()) return false;
    for (const auto &feature : features) {
        if (!feature.is_object()) return false;
        const auto &attributes = feature.at("attributes");
        const bool is_bridge = attributes.value("bridge", false);
        if (bridges != is_bridge) continue;
        const auto &geometry = feature.at("geometry");
        const std::string geometry_type = geometry.value("type", "");
        if (geometry_type != "LineString" && geometry_type != "Polygon") return false;
        const auto &raw_coordinates = geometry.at("coordinates");
        const auto &coordinates =
            geometry_type == "LineString" ? raw_coordinates : raw_coordinates.at(0);
        if (!coordinates.is_array() || coordinates.size() < 2) return false;
        ArnisFeatureGeometry parsed;
        parsed.polygon = geometry_type == "Polygon";
        parsed.width_m = attributes.value("width_m", 0.0);
        if (!std::isfinite(parsed.width_m) || parsed.width_m < 0.0) return false;
        for (const auto &point : coordinates) {
            double x = 0.0;
            double y = 0.0;
            if (!json_finite_pair(point, x, y)) return false;
            parsed.points.emplace_back(x, y);
        }
        if (parsed.polygon && parsed.points.front() != parsed.points.back()) {
            parsed.points.push_back(parsed.points.front());
        }
        if (!parsed.polygon && parsed.width_m <= 0.0) return false;
        out.push_back(std::move(parsed));
    }
    return true;
}

bool field_overlay_evidence_is_held(const Json &evidence) {
    if (!evidence.is_object()) return false;
    for (const char *key :
         {"metadata_only", "no_runtime_setup_application", "no_movement_release",
          "no_passability_release", "no_los_cover_release", "no_fire_control_release"}) {
        if (!evidence.value(key, false)) return false;
    }
    return true;
}

bool read_field_overlay(const std::filesystem::path &path, const RasterGrid &base,
                        std::vector<ArnisFeatureGeometry> &tree_lines,
                        std::vector<ArnisFeatureGeometry> &settlements) {
    std::ifstream file(path);
    if (!file) return false;
    Json root;
    try {
        file >> root;
    } catch (const std::exception &) {
        return false;
    }
    if (root.value("contract_version", "") != "field_overlay.v1" ||
        !field_overlay_evidence_is_held(root.value("evidence", Json{}))) {
        return false;
    }
    const auto &entries = root.value("entries", Json{});
    if (!entries.is_array()) return false;

    const double min_x = std::min(base.origin.x, base.origin.x + (base.width - 1) * base.step_x);
    const double min_y = std::min(base.origin.y, base.origin.y + (base.height - 1) * base.step_y);
    const double extent_x = std::abs(base.step_x) * static_cast<double>(base.width - 1);
    const double extent_y = std::abs(base.step_y) * static_cast<double>(base.height - 1);
    constexpr double kOverlayExtentToleranceM = 2.0;
    auto translated_point = [&](const Json &value, std::pair<double, double> &out) {
        double logical_x = 0.0;
        double logical_y = 0.0;
        if (!json_finite_pair(value, logical_x, logical_y) ||
            logical_x < -kOverlayExtentToleranceM || logical_y < -kOverlayExtentToleranceM ||
            logical_x > extent_x + kOverlayExtentToleranceM ||
            logical_y > extent_y + kOverlayExtentToleranceM) {
            return false;
        }
        out = {min_x + logical_x, min_y + logical_y};
        return true;
    };

    for (const auto &entry : entries) {
        if (!entry.is_object()) return false;
        const std::string kind = entry.value("overlay_kind", "");
        if (kind != "tree_line" && kind != "settlement_anchor" && kind != "settlement_structure") {
            continue;
        }
        if (!field_overlay_evidence_is_held(entry.value("evidence", Json{}))) return false;
        const auto &geometry = entry.value("geometry", Json{});
        if (!geometry.is_object()) return false;
        const std::string geometry_type = geometry.value("geometry_type", "");
        ArnisFeatureGeometry parsed;
        parsed.polygon = geometry_type == "polygon";
        if (geometry_type == "point") {
            std::pair<double, double> point;
            if (!translated_point(geometry.value("point", Json{}), point)) return false;
            parsed.points.push_back(point);
        } else if (geometry_type == "line" || parsed.polygon) {
            const auto &raw_points = geometry.value("points", Json{});
            if (!raw_points.is_array() || raw_points.size() < 2) return false;
            for (const auto &raw_point : raw_points) {
                std::pair<double, double> point;
                if (!translated_point(raw_point, point)) return false;
                parsed.points.push_back(point);
            }
            if (parsed.polygon && parsed.points.front() != parsed.points.back()) {
                parsed.points.push_back(parsed.points.front());
            }
        } else {
            return false;
        }
        if (kind == "tree_line") {
            tree_lines.push_back(std::move(parsed));
        } else {
            settlements.push_back(std::move(parsed));
        }
    }
    return !tree_lines.empty() || !settlements.empty();
}

double distance_squared_to_field_feature(const ArnisFeatureGeometry &feature, double x, double y,
                                         bool &inside, double &nearest_x, double &nearest_y) {
    inside = false;
    if (feature.points.empty()) return std::numeric_limits<double>::infinity();
    if (feature.points.size() == 1) {
        nearest_x = feature.points.front().first;
        nearest_y = feature.points.front().second;
        return RasterGrid::distance_squared_to_segment(x, y, nearest_x, nearest_y, nearest_x,
                                                       nearest_y);
    }
    if (feature.polygon && RasterGrid::point_in_polygon(x, y, feature.points)) {
        inside = true;
        nearest_x = x;
        nearest_y = y;
        return 0.0;
    }
    double best = std::numeric_limits<double>::infinity();
    for (std::size_t i = 1; i < feature.points.size(); ++i) {
        const double x1 = feature.points[i - 1].first;
        const double y1 = feature.points[i - 1].second;
        const double x2 = feature.points[i].first;
        const double y2 = feature.points[i].second;
        const double dx = x2 - x1;
        const double dy = y2 - y1;
        const double length_squared = dx * dx + dy * dy;
        const double projection =
            length_squared > 0.0
                ? std::clamp(((x - x1) * dx + (y - y1) * dy) / length_squared, 0.0, 1.0)
                : 0.0;
        const double candidate_x = x1 + projection * dx;
        const double candidate_y = y1 + projection * dy;
        const double candidate = RasterGrid::distance_squared_to_segment(x, y, x1, y1, x2, y2);
        if (candidate < best) {
            best = candidate;
            nearest_x = candidate_x;
            nearest_y = candidate_y;
        }
    }
    return best;
}

IEnvironmentModel::SurfaceType surface_for_landcover(std::uint8_t code) {
    switch (code) {
    case 80: // permanent water
        return IEnvironmentModel::SurfaceType::Water;
    case 0: // unknown/nodata must not become silently traversable
        return IEnvironmentModel::SurfaceType::Obstacle;
    case 50: // built-up
        return IEnvironmentModel::SurfaceType::HardPacked;
    default:
        return IEnvironmentModel::SurfaceType::SoftDirt;
    }
}

double vegetation_density_for_landcover(std::uint8_t code) {
    switch (code) {
    case 10: // tree cover
        return 0.90;
    case 20: // shrubland
        return 0.70;
    case 30: // grassland
        return 0.35;
    case 40: // cropland
        return 0.45;
    case 90: // herbaceous wetland
    case 95: // mangroves
        return 0.80;
    default:
        return 0.50;
    }
}

class DefaultEnvironmentModel : public IEnvironmentModel {
    std::vector<WeatherZoneImpl> weather_zones_;
    std::vector<Zone> zones_;
    RasterGrid raster_layer_;
    double base_wind_speed_mps_ = 10.0;
    double base_wind_dir_from_deg_ = 270.0; // Wind "from" West => blowing to East (+X)
    double wind_shear_mps_per_km_ = 4.0;    // Matches legacy (h/250 => +4 m/s per km)
    // Defaults match the historical fixed sun vector {0, 0.7071, 0.7071}.
    double sun_azimuth_deg_ = 0.0;    // NAV: 0=North, CW positive
    double sun_elevation_deg_ = 45.0; // above horizon
    MaritimeState maritime_state_{};
    bool flat_terrain_ = false;

  public:
    DefaultEnvironmentModel() {
        // Initialize with default weather
        weather_zones_.push_back({{15000.0, 15000.0, 5000.0}, 3000.0, 0.8, 0.6});

        // Initialize Raster Base Layer (20km x 20km centered at Origin)
        raster_layer_.origin = {-10000.0, -10000.0, 0.0};
        raster_layer_.resolution = 100.0; // 100m per cell
        raster_layer_.step_x = raster_layer_.resolution;
        raster_layer_.step_y = raster_layer_.resolution;
        raster_layer_.width = 200;
        raster_layer_.height = 200;
        raster_layer_.data.resize(raster_layer_.width * raster_layer_.height);

        // Procedural Generation: Checkerboard Pattern (1km patches)
        for (int y = 0; y < raster_layer_.height; ++y) {
            for (int x = 0; x < raster_layer_.width; ++x) {
                // 1km = 10 cells
                bool patch = ((x / 10) + (y / 10)) % 2 == 0;
                raster_layer_.data[y * raster_layer_.width + x] =
                    patch ? IEnvironmentModel::SurfaceType::SoftDirt
                          : IEnvironmentModel::SurfaceType::HardPacked;
            }
        }

        // Initialize Default Zones
        // Zones are now loaded via API (add_zone).

        // Raster initialized above.
    }

    AtmosphericData get_atmosphere_at(double x, double y, double z) override {
        AtmosphericData data;
        constexpr double kG = 9.80665, kR = 287.0, kL = 0.0065, kT0 = 288.15, kP0 = 101325.0;
        double h = std::max(0.0, z);
        if (h < 11000.0) {
            data.temperature = kT0 - kL * h;
            data.pressure = kP0 * std::pow(1.0 - kL * h / kT0, kG / (kR * kL));
        } else {
            constexpr double kT11 = 216.65, kP11 = 22632.1;
            data.temperature = kT11;
            data.pressure = kP11 * std::exp(-kG * (h - 11000.0) / (kR * kT11));
        }
        data.air_density = data.pressure / (kR * data.temperature);
        data.speed_of_sound = std::sqrt(1.4 * kR * data.temperature);

        // Wind (world frame). dir_from is NAV: 0=N, CW positive. Convert to a "to" unit vector.
        double dir_to_deg = std::fmod(base_wind_dir_from_deg_ + 180.0, 360.0);
        if (dir_to_deg < 0.0) dir_to_deg += 360.0;
        double dir_to_rad = dir_to_deg * std::numbers::pi_v<double> / 180.0;
        double ux = std::sin(dir_to_rad);
        double uy = std::cos(dir_to_rad);

        double alt_km = h / 1000.0;
        double speed_mps = base_wind_speed_mps_ + wind_shear_mps_per_km_ * alt_km;
        if (speed_mps < 0.0) speed_mps = 0.0;
        data.wind_velocity = {ux * speed_mps, uy * speed_mps, 0.0};
        return data;
    }

    double get_terrain_elevation(double x, double y) override {
        if (flat_terrain_) {
            return 0.0;
        }
        double raster_elevation = 0.0;
        if (raster_layer_.arnis_metric_bundle &&
            raster_layer_.get_elevation(x, y, raster_elevation)) {
            return raster_elevation;
        }
        constexpr double kPeakX = 25000.0, kPeakY = 25000.0, kPeakH = 2000.0, kSigmaSq = 25000000.0;
        double d2 = (x - kPeakX) * (x - kPeakX) + (y - kPeakY) * (y - kPeakY);
        return kPeakH * std::exp(-d2 / (2.0 * kSigmaSq));
    }

    double get_ground_slope_deg(double x, double y) override {
        // The procedural and `flat` surfaces are defined everywhere, so the
        // interface's central difference never leaves them.
        if (!raster_layer_.arnis_metric_bundle || flat_terrain_) {
            return IEnvironmentModel::get_ground_slope_deg(x, y);
        }
        // Over the measured raster, elevation beyond the edge is the
        // procedural fallback, not terrain, so the gradient is taken from
        // raster cells only. The documented 5 m half span is kept and expressed
        // in whole cells; on the 1 m Arnis grid inland this is the same +/-5
        // cell difference as before.
        double east_gradient = 0.0;
        double north_gradient = 0.0;
        if (!raster_layer_.elevation_gradient(x, y, kGroundSlopeSampleHalfSpanM, east_gradient,
                                              north_gradient)) {
            return std::numeric_limits<double>::quiet_NaN();
        }
        return ground_slope_deg_from_gradient(east_gradient, north_gradient);
    }

    bool check_line_of_sight(double x1, double y1, double z1, double x2, double y2,
                             double z2) override {
        const double terrain1 = get_terrain_elevation(x1, y1);
        const double terrain2 = get_terrain_elevation(x2, y2);

        // Sea-surface LOS uses a small tolerance and sparse land sampling so
        // z=0 maritime contacts are not spuriously blocked by near-zero legacy terrain.
        constexpr double kSurfaceEndpointToleranceM = 2.0;
        constexpr double kLowReliefTerrainToleranceM = 1.0;
        constexpr double kLandObstructionThresholdM = 1.5;
        if (maritime_state_.configured && std::abs(z1) <= kSurfaceEndpointToleranceM &&
            std::abs(z2) <= kSurfaceEndpointToleranceM && terrain1 <= kLowReliefTerrainToleranceM &&
            terrain2 <= kLowReliefTerrainToleranceM) {
            constexpr int kLosSamples = 24;
            for (int i = 1; i < kLosSamples; ++i) {
                const double t = static_cast<double>(i) / static_cast<double>(kLosSamples);
                const double sx = x1 + (x2 - x1) * t;
                const double sy = y1 + (y2 - y1) * t;
                if (get_terrain_elevation(sx, sy) > kLandObstructionThresholdM) {
                    return false;
                }
            }
            return true;
        }

        constexpr double kTerrainContactToleranceM = 0.5;
        if (z1 + kTerrainContactToleranceM < terrain1 ||
            z2 + kTerrainContactToleranceM < terrain2) {
            return false;
        }
        return true;
    }

    double get_weather_attenuation(double, double, double, double, double, double, int) override {
        return 0.0; // MVP
    }

    Vec3 get_sun_direction() override {
        // Unit vector pointing toward the sun. NAV azimuth: 0=North (+Y), CW
        // positive toward East (+X); elevation above the horizon.
        const double az_rad = sun_azimuth_deg_ * std::numbers::pi_v<double> / 180.0;
        const double el_rad = sun_elevation_deg_ * std::numbers::pi_v<double> / 180.0;
        const double horizontal = std::cos(el_rad);
        return {std::sin(az_rad) * horizontal, std::cos(az_rad) * horizontal, std::sin(el_rad)};
    }

    void set_sun_direction(double azimuth_deg, double elevation_deg) override {
        sun_azimuth_deg_ = std::fmod(azimuth_deg, 360.0);
        if (sun_azimuth_deg_ < 0.0) sun_azimuth_deg_ += 360.0;
        sun_elevation_deg_ = std::clamp(elevation_deg, -90.0, 90.0);
    }

    TerrainCell get_terrain_at(double x, double y) override {
        TerrainCell cell;
        cell.elevation = get_terrain_elevation(x, y);

        // Default (Background)
        cell.type = SurfaceType::SoftDirt;
        cell.friction_mult = 0.1;
        cell.roughness = 0.5;
        cell.vegetation_density = 0.5; // Default scrub
        cell.runway_heading = 0.0;

        // Iterate zones (sorted by z_order high->low). First match wins.

        for (const auto &zone : zones_) {
            // Transform point to Zone Local Frame
            // Translate to center.
            double dx = x - zone.center.x;
            double dy = y - zone.center.y;

            bool inside = false;

            if (zone.type == 0) { // Rect (rotated by heading)
                // Convert NAV heading (0=N, CW) to math yaw (0=+X, CCW).
                double yaw =
                    std::fmod(90.0 - zone.heading, 360.0) * std::numbers::pi_v<double> / 180.0;
                double c = std::cos(yaw);
                double s = std::sin(yaw);

                // Local axes: length axis points along heading, width axis is perpendicular.
                double local_len = dx * c + dy * s;
                double local_wid = dx * (-s) + dy * c;

                if (std::abs(local_wid) <= zone.width / 2.0 &&
                    std::abs(local_len) <= zone.length / 2.0) {
                    inside = true;
                }
            } else if (zone.type == 1) {                            // Circle
                if (dx * dx + dy * dy <= zone.width * zone.width) { // width = radius
                    inside = true;
                }
            }

            if (inside) {
                cell.type = zone.surface;
                cell.friction_mult = zone.friction;
                cell.roughness = zone.roughness;
                cell.vegetation_density = zone.vegetation_density;
                cell.runway_heading = zone.runway_heading;
                return cell; // Priority Match
            }
        }

        // 2. Check Raster Base Layer (Grid)
        if (raster_layer_.arnis_metric_bundle) {
            std::uint8_t landcover = 0;
            if (raster_layer_.get_landcover(x, y, landcover)) {
                // Vector semantics take precedence over the source landcover:
                // a declared bridge is traversable, while a declared river
                // corridor remains water even where the raster class is coarse.
                if (raster_layer_.bridge_at(x, y)) {
                    cell.type = SurfaceType::HardPacked;
                } else if (raster_layer_.river_at(x, y)) {
                    cell.type = SurfaceType::Water;
                } else {
                    cell.type = surface_for_landcover(landcover);
                }
                switch (cell.type) {
                case SurfaceType::HardPacked:
                    cell.friction_mult = 0.04;
                    cell.roughness = 0.2;
                    cell.vegetation_density = 0.1;
                    break;
                case SurfaceType::Water:
                    cell.friction_mult = 0.1;
                    cell.roughness = 0.0;
                    cell.vegetation_density = 0.0;
                    break;
                case SurfaceType::Obstacle:
                    cell.friction_mult = 0.0;
                    cell.roughness = 1.0;
                    cell.vegetation_density = 1.0;
                    break;
                default:
                    cell.friction_mult = 0.1;
                    cell.roughness = 0.5;
                    cell.vegetation_density = vegetation_density_for_landcover(landcover);
                    break;
                }
                return cell;
            }
            // Outside the admitted raster, fail closed rather than falling
            // back to the procedural checkerboard.
            cell.type = SurfaceType::Obstacle;
            cell.friction_mult = 0.0;
            cell.roughness = 1.0;
            cell.vegetation_density = 1.0;
            return cell;
        }
        IEnvironmentModel::SurfaceType grid_type;
        if (raster_layer_.get_surface(x, y, grid_type)) {
            cell.type = grid_type;

            // Map Type to Properties (Simple Lookup)
            switch (grid_type) {
            case SurfaceType::HardPacked:
                cell.friction_mult = 0.04;
                cell.roughness = 0.2;
                cell.vegetation_density = 0.1;
                break;
            case SurfaceType::SoftDirt:
                cell.friction_mult = 0.1;
                cell.roughness = 0.5;
                cell.vegetation_density = 0.5;
                break;
            case SurfaceType::Water:
                cell.friction_mult = 0.1;
                cell.roughness = 0.0;
                break;
            default: // Should not happen in this generator
                cell.friction_mult = 0.05;
                cell.roughness = 0.3;
                break;
            }
            return cell;
        }

        return cell; // Fallback to Initial Default (SoftDirt)
    }

    GroundFieldSemanticObservation get_ground_field_semantic_observation(double x,
                                                                         double y) override {
        GroundFieldSemanticObservation observation;
        observation.configured = raster_layer_.field_overlay_loaded;
        if (!observation.configured) return observation;

        auto inspect = [x, y](const std::vector<ArnisFeatureGeometry> &features, double &distance,
                              double &bearing, bool &inside) {
            double best = std::numeric_limits<double>::infinity();
            double best_x = x;
            double best_y = y;
            inside = false;
            for (const auto &feature : features) {
                bool feature_inside = false;
                double candidate_x = x;
                double candidate_y = y;
                const double candidate = distance_squared_to_field_feature(
                    feature, x, y, feature_inside, candidate_x, candidate_y);
                if (feature_inside) inside = true;
                if (candidate < best) {
                    best = candidate;
                    best_x = candidate_x;
                    best_y = candidate_y;
                }
            }
            if (!std::isfinite(best)) {
                distance = -1.0;
                bearing = 0.0;
                return;
            }
            distance = std::sqrt(std::max(0.0, best));
            if (distance > 0.0) {
                bearing = std::fmod(
                    std::atan2(best_x - x, best_y - y) * 180.0 / std::numbers::pi_v<double> + 360.0,
                    360.0);
            } else {
                bearing = 0.0;
            }
        };

        inspect(raster_layer_.tree_line_features, observation.nearest_tree_line_distance_m,
                observation.nearest_tree_line_bearing_deg, observation.in_tree_line);
        inspect(raster_layer_.settlement_features, observation.nearest_settlement_distance_m,
                observation.nearest_settlement_bearing_deg, observation.in_settlement);
        return observation;
    }

    GroundTransitionObservation get_ground_transition_observation(double from_x, double from_y,
                                                                  double to_x,
                                                                  double to_y) override {
        GroundTransitionObservation observation;
        observation.configured = raster_layer_.arnis_metric_bundle;
        observation.distance_m = std::hypot(to_x - from_x, to_y - from_y);
        const std::size_t sample_count = std::max<std::size_t>(
            1, static_cast<std::size_t>(std::ceil(observation.distance_m / 5.0)));
        SurfaceType endpoint_surface = SurfaceType::Obstacle;
        for (std::size_t index = 0; index <= sample_count; ++index) {
            const double fraction = static_cast<double>(index) / static_cast<double>(sample_count);
            const double x = from_x + (to_x - from_x) * fraction;
            const double y = from_y + (to_y - from_y) * fraction;
            const auto terrain = get_terrain_at(x, y);
            endpoint_surface = terrain.type;
            if (raster_layer_.arnis_metric_bundle && raster_layer_.bridge_at(x, y)) {
                observation.bridge_admitted = true;
            }
            if (terrain.type == SurfaceType::Water) {
                observation.water_blocked = true;
            } else if (terrain.type == SurfaceType::Obstacle) {
                observation.obstacle_blocked = true;
            }
        }
        observation.destination_surface =
            observation.water_blocked
                ? SurfaceType::Water
                : (observation.obstacle_blocked ? SurfaceType::Obstacle : endpoint_surface);
        observation.passable = !observation.water_blocked && !observation.obstacle_blocked;
        return observation;
    }

    TerrainLineOfSightObservation
    get_terrain_line_of_sight_observation(double from_x, double from_y, double from_height_m,
                                          double to_x, double to_y, double to_height_m) override {
        using Status = TerrainLineOfSightStatus;
        using Reason = TerrainLineOfSightUnknownReason;
        TerrainLineOfSightObservation observation;
        // Only the measured raster is an elevation authority. The procedural
        // hill and the `flat` profile are synthetic surfaces, so a sight line
        // over them is unknown rather than visible.
        if (!raster_layer_.arnis_metric_bundle || flat_terrain_) {
            return observation;
        }
        observation.elevation_source = TerrainElevationSource::ArnisMetricRaster;
        // Sample at the raster's own metric cell size: finer sampling cannot
        // see more relief than the grid holds, coarser sampling could skip a
        // one-cell crest.
        observation.sample_spacing_m =
            std::min(std::abs(raster_layer_.step_x), std::abs(raster_layer_.step_y));
        const bool finite_input = std::isfinite(from_x) && std::isfinite(from_y) &&
                                  std::isfinite(to_x) && std::isfinite(to_y) &&
                                  std::isfinite(from_height_m) && std::isfinite(to_height_m);
        if (!finite_input || from_height_m < 0.0 || to_height_m < 0.0 ||
            !std::isfinite(observation.sample_spacing_m) || observation.sample_spacing_m <= 0.0) {
            observation.unknown_reason = Reason::InvalidInput;
            return observation;
        }
        observation.distance_m = std::hypot(to_x - from_x, to_y - from_y);
        double from_terrain = 0.0;
        double to_terrain = 0.0;
        if (!raster_layer_.get_elevation(from_x, from_y, from_terrain) ||
            !raster_layer_.get_elevation(to_x, to_y, to_terrain)) {
            observation.unknown_reason = Reason::EndpointOutsideRaster;
            return observation;
        }
        observation.from_absolute_height_m = from_terrain + from_height_m;
        observation.to_absolute_height_m = to_terrain + to_height_m;

        const std::size_t intervals =
            std::max<std::size_t>(1, static_cast<std::size_t>(std::ceil(
                                         observation.distance_m / observation.sample_spacing_m)));
        for (std::size_t index = 1; index < intervals; ++index) {
            const double fraction = static_cast<double>(index) / static_cast<double>(intervals);
            const double x = from_x + (to_x - from_x) * fraction;
            const double y = from_y + (to_y - from_y) * fraction;
            double terrain = 0.0;
            if (!raster_layer_.get_elevation(x, y, terrain)) {
                observation.unknown_reason = Reason::SampleOutsideRaster;
                return observation;
            }
            observation.sample_count += 1;
            const double ray =
                observation.from_absolute_height_m +
                (observation.to_absolute_height_m - observation.from_absolute_height_m) * fraction;
            if (terrain > ray) {
                observation.status = Status::Blocked;
                observation.unknown_reason = Reason::None;
                observation.has_blocking_sample = true;
                observation.blocking_x = x;
                observation.blocking_y = y;
                observation.blocking_distance_m = observation.distance_m * fraction;
                observation.blocking_terrain_height_m = terrain;
                observation.blocking_ray_height_m = ray;
                return observation;
            }
        }
        observation.status = Status::Visible;
        observation.unknown_reason = Reason::None;
        return observation;
    }

    void clear_zones() override { zones_.clear(); }

    void add_zone(const std::string &name, double x, double y, double width, double length,
                  double heading, SurfaceType surface) override {
        Zone z;
        z.name = name;
        z.center = {x, y, 0.0};
        z.width = width;
        z.length = length;
        z.heading = heading;
        z.type = 0; // Rect
        z.surface = surface;
        z.runway_heading = heading; // Assume alignment for now

        // Defaults based on type
        if (surface == SurfaceType::Concrete) {
            z.friction = 0.02;
            z.roughness = 0.0;
            z.vegetation_density = 0.0;
            z.z_order = 10;
        } else if (surface == SurfaceType::Asphalt) {
            z.friction = 0.02;
            z.roughness = 0.0;
            z.vegetation_density = 0.0;
            z.z_order = 5;
        } else {
            z.friction = 0.1;
            z.roughness = 0.5;
            z.vegetation_density = 0.5;
            z.z_order = 1;
        }

        zones_.push_back(z);
        // Keep sorted
        std::sort(zones_.begin(), zones_.end(),
                  [](const Zone &a, const Zone &b) { return a.z_order > b.z_order; });
    }

    void set_wind(double speed_mps, double dir_from_deg, double shear_mps_per_km) override {
        base_wind_speed_mps_ = std::max(0.0, speed_mps);
        base_wind_dir_from_deg_ = std::fmod(dir_from_deg, 360.0);
        if (base_wind_dir_from_deg_ < 0.0) base_wind_dir_from_deg_ += 360.0;
        wind_shear_mps_per_km_ = shear_mps_per_km;
    }

    bool load_arnis_terrain_bundle(const std::string &bundle_root) override {
        namespace fs = std::filesystem;
        try {
            const fs::path root = fs::weakly_canonical(fs::path(bundle_root));
            const fs::path bundle_path = root / "bundle.json";
            std::ifstream bundle_file(bundle_path);
            if (!bundle_file) return false;

            Json bundle;
            bundle_file >> bundle;
            if (bundle.value("contract_version", "") != "arnis_cmo_bundle.v1" ||
                !bundle.value("no_held_capability_release", false)) {
                return false;
            }

            const Json *elevation_artifact = nullptr;
            const Json *landcover_artifact = nullptr;
            const Json *hydrology_artifact = nullptr;
            const Json *road_artifact = nullptr;
            const auto &artifacts = bundle.at("artifacts");
            if (!artifacts.is_array()) return false;
            for (const auto &artifact : artifacts) {
                if (!artifact.is_object()) continue;
                const std::string kind = artifact.value("kind", "");
                if (kind == "elevation_raster") elevation_artifact = &artifact;
                if (kind == "landcover_raster") landcover_artifact = &artifact;
                if (kind == "vector_features" &&
                    artifact.value("feature_class", "") == "hydrology") {
                    hydrology_artifact = &artifact;
                }
                if (kind == "vector_features" && artifact.value("feature_class", "") == "road") {
                    road_artifact = &artifact;
                }
            }
            if (elevation_artifact == nullptr || landcover_artifact == nullptr) return false;

            auto read_shape = [](const Json &artifact, int &height, int &width) {
                const auto &shape = artifact["shape"];
                if (!shape.is_array() || shape.size() != 2 || !shape[0].is_number_integer() ||
                    !shape[1].is_number_integer()) {
                    return false;
                }
                height = shape[0].get<int>();
                width = shape[1].get<int>();
                return height > 0 && width > 0;
            };

            int elevation_height = 0;
            int elevation_width = 0;
            int landcover_height = 0;
            int landcover_width = 0;
            if (!read_shape(*elevation_artifact, elevation_height, elevation_width) ||
                !read_shape(*landcover_artifact, landcover_height, landcover_width) ||
                elevation_height != landcover_height || elevation_width != landcover_width) {
                return false;
            }

            const Json &elevation_metadata = elevation_artifact->at("metadata");
            const Json &landcover_metadata = landcover_artifact->at("metadata");
            double origin_x = 0.0;
            double origin_y = 0.0;
            double step_x = 0.0;
            double step_y = 0.0;
            double landcover_origin_x = 0.0;
            double landcover_origin_y = 0.0;
            double landcover_step_x = 0.0;
            double landcover_step_y = 0.0;
            if (!json_finite_pair(elevation_metadata.at("origin_xy_m"), origin_x, origin_y) ||
                !json_finite_pair(elevation_metadata.at("step_xy_m"), step_x, step_y) ||
                !json_finite_pair(landcover_metadata.at("origin_xy_m"), landcover_origin_x,
                                  landcover_origin_y) ||
                !json_finite_pair(landcover_metadata.at("step_xy_m"), landcover_step_x,
                                  landcover_step_y) ||
                std::abs(step_x - landcover_step_x) > 1.0e-9 ||
                std::abs(step_y - landcover_step_y) > 1.0e-9 ||
                std::abs(origin_x - landcover_origin_x) > 1.0e-6 ||
                std::abs(origin_y - landcover_origin_y) > 1.0e-6 || step_x == 0.0 ||
                step_y == 0.0) {
                return false;
            }

            auto resolve_child = [&root](const Json &artifact) -> fs::path {
                const std::string relative = artifact.value("path", "");
                if (relative.empty()) return {};
                const fs::path candidate = fs::weakly_canonical(root / fs::path(relative));
                const auto root_text = root.generic_string();
                const auto candidate_text = candidate.generic_string();
                if (candidate_text.size() <= root_text.size() ||
                    candidate_text.compare(0, root_text.size(), root_text) != 0 ||
                    candidate_text[root_text.size()] != '/') {
                    return {};
                }
                return candidate;
            };

            const fs::path elevation_path = resolve_child(*elevation_artifact);
            const fs::path landcover_path = resolve_child(*landcover_artifact);
            if (elevation_path.empty() || landcover_path.empty()) return false;

            std::vector<ArnisFeatureGeometry> river_features;
            std::vector<ArnisFeatureGeometry> bridge_features;
            if (hydrology_artifact != nullptr) {
                const fs::path hydrology_path = resolve_child(*hydrology_artifact);
                if (hydrology_path.empty() ||
                    !read_feature_geometries(hydrology_path, false, river_features)) {
                    return false;
                }
            }
            if (road_artifact != nullptr) {
                const fs::path road_path = resolve_child(*road_artifact);
                if (road_path.empty() ||
                    !read_feature_geometries(road_path, true, bridge_features)) {
                    return false;
                }
            }

            const std::size_t cell_count = static_cast<std::size_t>(elevation_height) *
                                           static_cast<std::size_t>(elevation_width);
            const std::size_t elevation_bytes = cell_count * sizeof(float);
            const std::size_t landcover_bytes = cell_count * sizeof(std::uint8_t);
            if (elevation_artifact->value("byte_length", 0u) != elevation_bytes ||
                landcover_artifact->value("byte_length", 0u) != landcover_bytes) {
                return false;
            }

            std::vector<std::uint8_t> elevation_raw;
            std::vector<std::uint8_t> landcover_raw;
            if (!read_binary_bytes(elevation_path, elevation_bytes, elevation_raw) ||
                !read_binary_bytes(landcover_path, landcover_bytes, landcover_raw)) {
                return false;
            }

            RasterGrid candidate;
            candidate.origin = {origin_x, origin_y, 0.0};
            candidate.resolution = std::abs(step_x);
            candidate.step_x = step_x;
            candidate.step_y = step_y;
            candidate.width = elevation_width;
            candidate.height = elevation_height;
            candidate.arnis_metric_bundle = true;
            candidate.river_features = std::move(river_features);
            candidate.bridge_features = std::move(bridge_features);
            candidate.elevation.resize(cell_count);
            candidate.landcover = std::move(landcover_raw);
            candidate.data.resize(cell_count);
            for (std::size_t index = 0; index < cell_count; ++index) {
                float value = 0.0F;
                std::memcpy(&value, elevation_raw.data() + index * sizeof(float), sizeof(float));
                if (!std::isfinite(value)) return false;
                candidate.elevation[index] = static_cast<double>(value);
                candidate.data[index] = surface_for_landcover(candidate.landcover[index]);
            }

            raster_layer_ = std::move(candidate);
            flat_terrain_ = false;
            return true;
        } catch (const std::exception &) {
            return false;
        }
    }

    bool load_arnis_field_overlay(const std::string &overlay_path) override {
        if (!raster_layer_.arnis_metric_bundle) return false;
        std::vector<ArnisFeatureGeometry> tree_lines;
        std::vector<ArnisFeatureGeometry> settlements;
        if (!read_field_overlay(std::filesystem::path(overlay_path), raster_layer_, tree_lines,
                                settlements)) {
            return false;
        }
        raster_layer_.tree_line_features = std::move(tree_lines);
        raster_layer_.settlement_features = std::move(settlements);
        raster_layer_.field_overlay_loaded = true;
        return true;
    }

    void set_terrain_type(const std::string &terrain_type) override {
        std::string key = terrain_type;
        key.erase(key.begin(), std::find_if(key.begin(), key.end(),
                                            [](unsigned char c) { return !std::isspace(c); }));
        key.erase(
            std::find_if(key.rbegin(), key.rend(), [](unsigned char c) { return !std::isspace(c); })
                .base(),
            key.end());
        std::transform(key.begin(), key.end(), key.begin(),
                       [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
        if (key.empty()) {
            key = "flat";
        }
        if (key == "legacy" || key == "hill" || key == "gaussian_hill" || key == "mountain") {
            flat_terrain_ = false;
            return;
        }
        if (key == "flat") {
            flat_terrain_ = true;
            return;
        }
        throw std::invalid_argument(
            "Unknown terrain_type '" + terrain_type +
            "'; expected one of: flat, gaussian_hill, hill, legacy, mountain");
    }

    void set_maritime_state(double sea_state, double wave_heading_deg,
                            double wave_period_s) override {
        maritime_state_.configured = true;
        maritime_state_.sea_state = std::clamp(sea_state, 0.0, 12.0);
        maritime_state_.wave_heading_deg = std::fmod(wave_heading_deg, 360.0);
        if (maritime_state_.wave_heading_deg < 0.0) maritime_state_.wave_heading_deg += 360.0;
        maritime_state_.wave_period_s = std::max(2.0, wave_period_s);
    }

    void clear_maritime_state() override { maritime_state_ = MaritimeState{}; }

    MaritimeState get_maritime_state() const override { return maritime_state_; }

    bool snapshot_to(DefaultEnvironmentSnapshot *out) const {
        if (out == nullptr) {
            return false;
        }
        *out = DefaultEnvironmentSnapshot{};
        out->valid = true;
        out->flat_terrain = flat_terrain_;
        out->maritime_state_configured = maritime_state_.configured;
        out->sea_state = maritime_state_.sea_state;
        out->wave_heading_deg = maritime_state_.wave_heading_deg;
        out->wave_period_s = maritime_state_.wave_period_s;
        out->raster.origin_x = raster_layer_.origin.x;
        out->raster.origin_y = raster_layer_.origin.y;
        out->raster.resolution_m = raster_layer_.resolution;
        out->raster.width = raster_layer_.width;
        out->raster.height = raster_layer_.height;
        out->raster.surface_codes.reserve(raster_layer_.data.size());
        for (const auto surface : raster_layer_.data) {
            out->raster.surface_codes.push_back(static_cast<std::uint8_t>(surface));
        }
        out->zones.reserve(zones_.size());
        for (const auto &zone : zones_) {
            DefaultEnvironmentZoneSnapshot item{};
            item.center_x = zone.center.x;
            item.center_y = zone.center.y;
            item.width = zone.width;
            item.length = zone.length;
            item.heading_deg = zone.heading;
            item.type = zone.type;
            item.surface_code = static_cast<std::uint8_t>(zone.surface);
            out->zones.push_back(item);
        }
        return true;
    }
};

} // namespace

std::unique_ptr<IEnvironmentModel> make_default_environment_model() {
    return std::make_unique<DefaultEnvironmentModel>();
}

bool extract_default_environment_snapshot(IEnvironmentModel *env, DefaultEnvironmentSnapshot *out) {
    auto *model = dynamic_cast<DefaultEnvironmentModel *>(env);
    return model != nullptr && model->snapshot_to(out);
}
