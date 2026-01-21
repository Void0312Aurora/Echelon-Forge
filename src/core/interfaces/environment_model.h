#pragma once

#include "components/basic/environment_data.h"
#include <cstdint>
#include <string>

class IEnvironmentModel {
public:
    virtual ~IEnvironmentModel() = default;

    // Core lookup: Get atmospheric conditions at specific position
    virtual AtmosphericData get_atmosphere_at(double x, double y, double z) = 0;

    // Terrain Query
    virtual double get_terrain_elevation(double x, double y) = 0;

    // Line of Sight Check (true if clear, false if blocked)
    virtual bool check_line_of_sight(double x1, double y1, double z1, double x2, double y2, double z2) = 0;

    // Weather Query: Returns attenuation factor (0.0=clear, 1.0=blocked) for specific sensor type
    // type: 0=Visual, 1=IR, 2=Radar
    virtual double get_weather_attenuation(double x1, double y1, double z1, double x2, double y2, double z2, int sensor_type) = 0;

    virtual Vec3 get_sun_direction() = 0;

    enum class SurfaceType : uint8_t {
        Concrete = 0, // Paved Runway
        Asphalt,      // Road / Taxiway
        HardPacked,   // Dirt Strip / Austere
        SoftDirt,     // General Off-road
        Water,        // Ocean / Lake
        Obstacle      // Rock / Tree
    };

    struct TerrainCell {
        double elevation;
        SurfaceType type;
        double friction_mult; // 1.0 = Concrete
        double roughness;     // 0.0 - 1.0
        double vegetation_density; // 0.0 = Clear, 1.0 = Dense Forest
        double runway_heading; // Degrees (NAV), only valid if type == Concrete
    };

    virtual TerrainCell get_terrain_at(double x, double y) = 0;

    // Dynamic Configuration
    virtual void clear_zones() = 0;
    virtual void add_zone(const std::string& name, double x, double y, double width, double height, double heading, SurfaceType surface) = 0;
};

struct EnvironmentModelRef {
    IEnvironmentModel* model;
};

#include <memory>
std::unique_ptr<IEnvironmentModel> make_default_environment_model();
