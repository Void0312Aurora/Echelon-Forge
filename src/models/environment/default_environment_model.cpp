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

struct RasterGrid {
    Vec3 origin;       // Bottom-Left Corner (Min X, Min Y)
    double resolution; // Meters per cell
    double step_x = 0.0;
    double step_y = 0.0;
    int width;         // Number of columns (X)
    int height;        // Number of rows (Y)
    std::vector<IEnvironmentModel::SurfaceType>
        data; // Row-major (y * width + x) (Or standard image layout)
    std::vector<double> elevation;
    std::vector<std::uint8_t> landcover;
    bool arnis_metric_bundle = false;

    bool index_for(double x, double y, std::size_t &index) const {
        const double sx = step_x != 0.0 ? step_x : resolution;
        const double sy = step_y != 0.0 ? step_y : resolution;
        if (!std::isfinite(sx) || !std::isfinite(sy) || sx == 0.0 || sy == 0.0 || width <= 0 ||
            height <= 0) {
            return false;
        }
        const double col_f = (x - origin.x) / sx;
        const double row_f = (y - origin.y) / sy;
        const auto col = static_cast<long long>(std::llround(col_f));
        const auto row = static_cast<long long>(std::llround(row_f));
        if (col < 0 || row < 0 || col >= width || row >= height ||
            std::abs(col_f - static_cast<double>(col)) > 0.51 ||
            std::abs(row_f - static_cast<double>(row)) > 0.51) {
            return false;
        }
        index = static_cast<std::size_t>(row) * static_cast<std::size_t>(width) +
                static_cast<std::size_t>(col);
        return index < static_cast<std::size_t>(width) * static_cast<std::size_t>(height);
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
    if (!value.is_array() || value.size() != 2 || !value[0].is_number() ||
        !value[1].is_number()) {
        return false;
    }
    first = value[0].get<double>();
    second = value[1].get<double>();
    return std::isfinite(first) && std::isfinite(second);
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
        if (raster_layer_.arnis_metric_bundle && raster_layer_.get_elevation(x, y, raster_elevation)) {
            return raster_elevation;
        }
        constexpr double kPeakX = 25000.0, kPeakY = 25000.0, kPeakH = 2000.0, kSigmaSq = 25000000.0;
        double d2 = (x - kPeakX) * (x - kPeakX) + (y - kPeakY) * (y - kPeakY);
        return kPeakH * std::exp(-d2 / (2.0 * kSigmaSq));
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
                cell.type = surface_for_landcover(landcover);
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
                    cell.vegetation_density = 0.5;
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
            const auto &artifacts = bundle.at("artifacts");
            if (!artifacts.is_array()) return false;
            for (const auto &artifact : artifacts) {
                if (!artifact.is_object()) continue;
                const std::string kind = artifact.value("kind", "");
                if (kind == "elevation_raster") elevation_artifact = &artifact;
                if (kind == "landcover_raster") landcover_artifact = &artifact;
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
