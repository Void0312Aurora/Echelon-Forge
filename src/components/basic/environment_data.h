#pragma once

struct Vec3 { 
    double x, y, z; 
};

struct AtmosphericData {
    double air_density;      // kg/m^3
    double speed_of_sound;   // m/s
    double pressure;         // Pa
    double temperature;      // Kelvin
    Vec3 wind_velocity;      // m/s
};

struct WeatherZone {
    Vec3 center;
    double radius;
    double visual_attenuation; // 0.0 (clear) to 1.0 (blocked)
    double ir_attenuation;     // 0.0 (clear) to 1.0 (blocked)
};

