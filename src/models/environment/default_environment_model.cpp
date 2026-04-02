#include "core/interfaces/environment_model.h"
#include "models/environment/default_environment_snapshot.h"

#include <cmath>
#include <vector>
#include <iostream>
#include <algorithm>
#include <cctype>

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
    double width;  // X-size or Diameter
    double length; // Y-size (0 if circle)
    double heading; // Degrees
    int type; // 0=Rect, 1=Circle
    
    // Properties
    IEnvironmentModel::SurfaceType surface;
    double friction;
    double roughness;
    double vegetation_density;
    double runway_heading; // If runway
    int z_order; // Higher = Top (Overlays others)
};

struct RasterGrid {
    Vec3 origin; // Bottom-Left Corner (Min X, Min Y)
    double resolution; // Meters per cell
    int width; // Number of columns (X)
    int height; // Number of rows (Y)
    std::vector<IEnvironmentModel::SurfaceType> data; // Row-major (y * width + x) (Or standard image layout)

    // Helper: World (x,y) -> Grid Index
    bool get_surface(double x, double y, IEnvironmentModel::SurfaceType& out_type) const {
        // Local coords
        double lx = x - origin.x;
        double ly = y - origin.y;
        
        // Check bounds
        if (lx < 0 || ly < 0) return false;
        
        int col = static_cast<int>(lx / resolution);
        int row = static_cast<int>(ly / resolution);
        
        if (col >= width || row >= height) return false;
        
        // Index
        size_t idx = static_cast<size_t>(row * width + col);
        if (idx < data.size()) {
            out_type = data[idx];
            return true;
        }
        return false;
    }
};



class DefaultEnvironmentModel : public IEnvironmentModel {
    std::vector<WeatherZoneImpl> weather_zones_;
    std::vector<Zone> zones_;
    RasterGrid raster_layer_;
    double base_wind_speed_mps_ = 10.0;
    double base_wind_dir_from_deg_ = 270.0;   // Wind "from" West => blowing to East (+X)
    double wind_shear_mps_per_km_ = 4.0;      // Matches legacy (h/250 => +4 m/s per km)
    bool flat_terrain_ = false;

public:
    DefaultEnvironmentModel() {
        // Initialize with default weather
        weather_zones_.push_back({
            {15000.0, 15000.0, 5000.0}, 3000.0, 0.8, 0.6
        });

        // Initialize Raster Base Layer (20km x 20km centered at Origin)
        raster_layer_.origin = {-10000.0, -10000.0, 0.0};
        raster_layer_.resolution = 100.0; // 100m per cell
        raster_layer_.width = 200;
        raster_layer_.height = 200;
        raster_layer_.data.resize(raster_layer_.width * raster_layer_.height);

        // Procedural Generation: Checkerboard Pattern (1km patches)
        for (int y = 0; y < raster_layer_.height; ++y) {
            for (int x = 0; x < raster_layer_.width; ++x) {
                // 1km = 10 cells
                bool patch = ((x / 10) + (y / 10)) % 2 == 0;
                raster_layer_.data[y * raster_layer_.width + x] = patch ? 
                    IEnvironmentModel::SurfaceType::SoftDirt : 
                    IEnvironmentModel::SurfaceType::HardPacked;
            }
        }

        // Initialize Default Zones
        // Zones are now loaded via API (add_zone).
        
        // Raster initialized above.
    }

    AtmosphericData get_atmosphere_at(double x, double y, double z) override {
        AtmosphericData data;
        constexpr double kG=9.80665, kR=287.0, kL=0.0065, kT0=288.15, kP0=101325.0;
        double h = std::max(0.0, z);
        if(h < 11000.0) {
            data.temperature = kT0 - kL*h;
            data.pressure = kP0 * std::pow(1.0 - kL*h/kT0, kG/(kR*kL));
        } else {
            constexpr double kT11=216.65, kP11=22632.1;
            data.temperature = kT11;
            data.pressure = kP11 * std::exp(-kG*(h-11000.0)/(kR*kT11));
        }
        data.air_density = data.pressure / (kR * data.temperature);
        data.speed_of_sound = std::sqrt(1.4 * kR * data.temperature);

        // Wind (world frame). dir_from is NAV: 0=N, CW positive. Convert to a "to" unit vector.
        double dir_to_deg = std::fmod(base_wind_dir_from_deg_ + 180.0, 360.0);
        if (dir_to_deg < 0.0) dir_to_deg += 360.0;
        double dir_to_rad = dir_to_deg * M_PI / 180.0;
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
         constexpr double kPeakX = 25000.0, kPeakY = 25000.0, kPeakH = 2000.0, kSigmaSq = 25000000.0;
         double d2 = (x-kPeakX)*(x-kPeakX) + (y-kPeakY)*(y-kPeakY);
         return kPeakH * std::exp(-d2 / (2.0*kSigmaSq));
    }

    bool check_line_of_sight(double x1, double y1, double z1, double x2, double y2, double z2) override {
        // Simple ground check approximation
        if (z1 < get_terrain_elevation(x1, y1) || z2 < get_terrain_elevation(x2, y2)) return false;
        return true; 
    }

    double get_weather_attenuation(double, double, double, double, double, double, int) override {
        return 0.0; // MVP
    }

    Vec3 get_sun_direction() override { return {0.0, 0.7071, 0.7071}; }

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
        
        for (const auto& zone : zones_) {
            // Transform point to Zone Local Frame
            // Translate to center.
            double dx = x - zone.center.x;
            double dy = y - zone.center.y;

            bool inside = false;

            if (zone.type == 0) { // Rect (rotated by heading)
                // Convert NAV heading (0=N, CW) to math yaw (0=+X, CCW).
                double yaw = std::fmod(90.0 - zone.heading, 360.0) * M_PI / 180.0;
                double c = std::cos(yaw);
                double s = std::sin(yaw);

                // Local axes: length axis points along heading, width axis is perpendicular.
                double local_len = dx * c + dy * s;
                double local_wid = dx * (-s) + dy * c;

                if (std::abs(local_wid) <= zone.width / 2.0 && std::abs(local_len) <= zone.length / 2.0) {
                    inside = true;
                }
            } else if (zone.type == 1) { // Circle
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

    void clear_zones() override {
        zones_.clear();
    }

    void add_zone(const std::string& name, double x, double y, double width, double length, double heading, SurfaceType surface) override {
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
            z.friction = 0.02; z.roughness = 0.0; z.vegetation_density = 0.0; z.z_order = 10;
        } else if (surface == SurfaceType::Asphalt) {
            z.friction = 0.02; z.roughness = 0.0; z.vegetation_density = 0.0; z.z_order = 5;
        } else {
            z.friction = 0.1; z.roughness = 0.5; z.vegetation_density = 0.5; z.z_order = 1;
        }
        
        zones_.push_back(z);
        // Keep sorted
        std::sort(zones_.begin(), zones_.end(), [](const Zone& a, const Zone& b){
            return a.z_order > b.z_order;
        });
    }

    void set_wind(double speed_mps, double dir_from_deg, double shear_mps_per_km) override {
        base_wind_speed_mps_ = std::max(0.0, speed_mps);
        base_wind_dir_from_deg_ = std::fmod(dir_from_deg, 360.0);
        if (base_wind_dir_from_deg_ < 0.0) base_wind_dir_from_deg_ += 360.0;
        wind_shear_mps_per_km_ = shear_mps_per_km;
    }

    void set_terrain_type(const std::string& terrain_type) override {
        std::string key = terrain_type;
        std::transform(key.begin(), key.end(), key.begin(), [](unsigned char c) {
            return static_cast<char>(std::tolower(c));
        });
        if (key.empty() || key == "legacy" || key == "hill" || key == "gaussian_hill" || key == "mountain") {
            flat_terrain_ = false;
            return;
        }
        if (key == "flat") {
            flat_terrain_ = true;
            return;
        }
        // Unknown terrain types fall back to the historical profile for backward compatibility.
        flat_terrain_ = false;
    }

    bool snapshot_to(DefaultEnvironmentSnapshot* out) const {
        if (out == nullptr) {
            return false;
        }
        *out = DefaultEnvironmentSnapshot{};
        out->valid = true;
        out->flat_terrain = flat_terrain_;
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
        for (const auto& zone : zones_) {
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

bool extract_default_environment_snapshot(
    IEnvironmentModel* env,
    DefaultEnvironmentSnapshot* out
) {
    auto* model = dynamic_cast<DefaultEnvironmentModel*>(env);
    return model != nullptr && model->snapshot_to(out);
}
