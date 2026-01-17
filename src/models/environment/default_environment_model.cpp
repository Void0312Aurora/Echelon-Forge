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

class DefaultEnvironmentModel : public IEnvironmentModel {
    std::vector<WeatherZoneImpl> weather_zones_;

public:
    DefaultEnvironmentModel() {
        // Initialize with one example cloud
        weather_zones_.push_back({
            {15000.0, 15000.0, 5000.0}, // Center
            3000.0,                     // Radius
            0.8,                        // Vis Att
            0.6                         // IR Att
        });
    }

    AtmosphericData get_atmosphere_at(double x, double y, double z) override {
        AtmosphericData data;
        
        // ISA Model (Troposphere < 11km)
        // Check "U.S. Standard Atmosphere 1976" simplified
        constexpr double kG = 9.80665;
        constexpr double kR = 287.0; // Gas constant for dry air
        constexpr double kL = 0.0065; // Temp lapse rate K/m
        constexpr double kT0 = 288.15; // Sea level temp K
        constexpr double kP0 = 101325.0; // Sea level pressure Pa

        double h = std::max(0.0, z);
        
        if (h < 11000.0) {
            data.temperature = kT0 - kL * h;
            double exponent = (kG / (kR * kL)) - 1.0;
            // Pressure = P0 * (T/T0)^(g/RL) ? 
            // Formula: P = P0 * (1 - L*h/T0)^(g/RL)
            double base = 1.0 - (kL * h / kT0);
            double exponent_p = kG / (kR * kL);
            data.pressure = kP0 * std::pow(base, exponent_p);
        } else {
            // Stratosphere (isothermal up to 20km)
            constexpr double kT11 = 216.65;
            constexpr double kP11 = 22632.1;
            data.temperature = kT11;
            // P = P11 * exp(-g*(h-11000)/(R*T))
            data.pressure = kP11 * std::exp(-kG * (h - 11000.0) / (kR * kT11));
        }

        // Density rho = P / (R * T)
        data.air_density = data.pressure / (kR * data.temperature);
        
        // Speed of Sound a = sqrt(gamma * R * T), gamma = 1.4
        data.speed_of_sound = std::sqrt(1.4 * kR * data.temperature);

        // Simple Global Wind (West to East)
        // Increase with altitude: 10 m/s at SL, 50 m/s at 10km
        double wind_mag = 10.0 + (h / 1000.0) * 4.0;
        data.wind_velocity = {wind_mag, 0.0, 0.0};

        return data;
    }

    double get_terrain_elevation(double x, double y) override {
        // Procedural Terrain: A generic mountain at (25000, 25000)
        constexpr double kPeakX = 25000.0;
        constexpr double kPeakY = 25000.0;
        constexpr double kPeakH = 2000.0;
        constexpr double kSigmaSq = 5000.0 * 5000.0;

        double dx = x - kPeakX;
        double dy = y - kPeakY;
        double dist_sq = dx * dx + dy * dy;
        return kPeakH * std::exp(-dist_sq / (2.0 * kSigmaSq));
    }

    bool check_line_of_sight(double x1, double y1, double z1, double x2, double y2, double z2) override {
        double dist_sq = (x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1) + (z2 - z1) * (z2 - z1);
        double dist = std::sqrt(dist_sq);
        
        if (dist < 1.0) return true; 

        constexpr double kStepSize = 200.0;
        int steps = static_cast<int>(dist / kStepSize);

        double dx = (x2 - x1) / dist * kStepSize;
        double dy = (y2 - y1) / dist * kStepSize;
        double dz = (z2 - z1) / dist * kStepSize;

        double cur_x = x1;
        double cur_y = y1;
        double cur_z = z1;

        for (int i = 1; i < steps; ++i) {
            cur_x += dx;
            cur_y += dy;
            cur_z += dz;
            if (cur_z < get_terrain_elevation(cur_x, cur_y)) {
                 return false; // Blocked
            }
        }
        return true;
    }

    double get_weather_attenuation(double x1, double y1, double z1, double x2, double y2, double z2, int sensor_type) override {
        double total_att = 0.0;
        
        // Ray-Sphere intersection for each zone
        double vx = x2 - x1, vy = y2 - y1, vz = z2 - z1;
        double len = std::sqrt(vx*vx + vy*vy + vz*vz);
        if (len < 1e-3) return 0.0;
        
        double dx = vx/len, dy = vy/len, dz = vz/len;

        for (const auto& zone : weather_zones_) {
            double mx = x1 - zone.center.x;
            double my = y1 - zone.center.y;
            double mz = z1 - zone.center.z;
            
            double b = mx*dx + my*dy + mz*dz;
            double c = (mx*mx + my*my + mz*mz) - zone.radius*zone.radius;
            
            if (c > 0.0 && b > 0.0) continue; // Outside and pointing away
            
            double discr = b*b - c;
            if (discr < 0.0) continue; // Miss
            
            double t1 = -b - std::sqrt(discr);
            if (t1 < len) {
                double t2 = -b + std::sqrt(discr);
                if (t2 > 0) {
                    // Hit
                    if (sensor_type == 0) total_att += zone.visual_attenuation;
                    else if (sensor_type == 1) total_att += zone.ir_attenuation;
                }
            }
        }

        return std::clamp(total_att, 0.0, 1.0);
    }

    Vec3 get_sun_direction() override {
        // South-Up
        return {0.0, 0.7071, 0.7071}; 
    }
};

} // namespace

std::unique_ptr<IEnvironmentModel> make_default_environment_model() {
    return std::make_unique<DefaultEnvironmentModel>();
}
