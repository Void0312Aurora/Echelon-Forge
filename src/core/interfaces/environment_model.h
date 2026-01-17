#pragma once

#include "components/basic/environment_data.h"

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
};

struct EnvironmentModelRef {
    IEnvironmentModel* model;
};

#include <memory>
std::unique_ptr<IEnvironmentModel> make_default_environment_model();
