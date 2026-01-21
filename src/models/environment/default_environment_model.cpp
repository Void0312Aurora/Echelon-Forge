#include "core/interfaces/environment_model.h"

#include <cmath>
#include <vector>
#include <iostream>
#include <algorithm>

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
        data.wind_velocity = {10.0 + h/250.0, 0.0, 0.0}; // Simplified
        return data;
    }

    double get_terrain_elevation(double x, double y) override {
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
            // 1. Translate
            double dx = x - zone.center.x;
            double dy = y - zone.center.y;
            
            // NOTE: Zones are currently axis-aligned for MVP terrain.
            bool inside = false;
            
            if (zone.type == 0) { // Rect
                if (std::abs(dx) <= zone.width / 2.0 && std::abs(dy) <= zone.length / 2.0) {
                     inside = true;
                }
            } else if (zone.type == 1) { // Circle
                if (dx*dx + dy*dy <= zone.width * zone.width) { // width = radius
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
};

} // namespace

std::unique_ptr<IEnvironmentModel> make_default_environment_model() {
    return std::make_unique<DefaultEnvironmentModel>();
}
