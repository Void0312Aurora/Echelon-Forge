#pragma once

#include "components/basic/environment_data.h"
#include <cstdint>
#include <string>

class IEnvironmentModel {
public:
    // Merge/fallback rule:
    // - configured=false: environment contributes no maritime override and platform defaults remain active.
    // - configured=true: environment fully overrides platform sea_state / wave_heading_deg / wave_period_s,
    //   including the explicit "calm sea" case where sea_state == 0.
    struct MaritimeState {
        bool configured = false;
        double sea_state = 0.0;
        double wave_heading_deg = 0.0;
        double wave_period_s = 8.0;
    };

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

    // Wind configuration
    // dir_from_deg uses NAV convention: 0=North, CW positive.
    // shear_mps_per_km is applied in the "to" direction (same as the base wind).
    virtual void set_wind(double /*speed_mps*/, double /*dir_from_deg*/, double /*shear_mps_per_km*/) {}

    // Sun configuration (drives get_sun_direction and the optical glare
    // penalty in sensor models). azimuth_deg uses NAV convention: 0=North,
    // CW positive; elevation_deg is above the horizon. Defaults preserve the
    // historical fixed vector (azimuth 0, elevation 45).
    virtual void set_sun_direction(double /*azimuth_deg*/, double /*elevation_deg*/) {}

    // Terrain profile configuration.
    // "flat" means zero-elevation terrain outside explicit zones.
    // "legacy"/"hill"/"gaussian_hill"/"mountain" preserve the historical procedural mountain.
    // Unknown terrain profiles must fail closed instead of falling back to that profile.
    virtual void set_terrain_type(const std::string& /*terrain_type*/) {}

    // Maritime-state configuration used by surface-ship runtime proxies.
    // set_maritime_state() activates a full environment override; clear_maritime_state() returns control to
    // per-platform fallback values. Partial field merge is intentionally not supported in this MVP.
    virtual void set_maritime_state(double /*sea_state*/, double /*wave_heading_deg*/, double /*wave_period_s*/) {}
    virtual void clear_maritime_state() {}
    virtual MaritimeState get_maritime_state() const { return {}; }
};

struct EnvironmentModelRef {
    IEnvironmentModel* model;
};

#include <memory>
std::unique_ptr<IEnvironmentModel> make_default_environment_model();
