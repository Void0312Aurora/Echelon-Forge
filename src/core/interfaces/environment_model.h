#pragma once

#include "components/basic/environment_data.h"
#include <cmath>
#include <cstdint>
#include <limits>
#include <numbers>
#include <string>

class IEnvironmentModel {
  public:
    // Merge/fallback rule:
    // - configured=false: environment contributes no maritime override and platform defaults remain
    // active.
    // - configured=true: environment fully overrides platform sea_state / wave_heading_deg /
    // wave_period_s,
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

    // Bounded local slope observation shared by Ground movement and training
    // adapters. This is a terrain gradient, not a climbability or physics
    // decision.
    virtual double get_ground_slope_deg(double x, double y) {
        constexpr double kSampleHalfSpanM = 5.0;
        const double east_gradient = (get_terrain_elevation(x + kSampleHalfSpanM, y) -
                                      get_terrain_elevation(x - kSampleHalfSpanM, y)) /
                                     (2.0 * kSampleHalfSpanM);
        const double north_gradient = (get_terrain_elevation(x, y + kSampleHalfSpanM) -
                                       get_terrain_elevation(x, y - kSampleHalfSpanM)) /
                                      (2.0 * kSampleHalfSpanM);
        if (!std::isfinite(east_gradient) || !std::isfinite(north_gradient)) {
            return std::numeric_limits<double>::quiet_NaN();
        }
        return std::atan(std::hypot(east_gradient, north_gradient)) * 180.0 /
               std::numbers::pi_v<double>;
    }

    // Line of Sight Check (true if clear, false if blocked)
    virtual bool check_line_of_sight(double x1, double y1, double z1, double x2, double y2,
                                     double z2) = 0;

    // Weather Query: Returns attenuation factor (0.0=clear, 1.0=blocked) for specific sensor type
    // type: 0=Visual, 1=IR, 2=Radar
    virtual double get_weather_attenuation(double x1, double y1, double z1, double x2, double y2,
                                           double z2, int sensor_type) = 0;

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
        double friction_mult;      // 1.0 = Concrete
        double roughness;          // 0.0 - 1.0
        double vegetation_density; // 0.0 = Clear, 1.0 = Dense Forest
        double runway_heading;     // Degrees (NAV), only valid if type == Concrete
    };

    struct GroundFieldSemanticObservation {
        bool configured = false;
        double nearest_tree_line_distance_m = -1.0;
        double nearest_tree_line_bearing_deg = 0.0;
        double nearest_settlement_distance_m = -1.0;
        double nearest_settlement_bearing_deg = 0.0;
        bool in_tree_line = false;
        bool in_settlement = false;
    };

    struct GroundTransitionObservation {
        bool configured = false;
        bool passable = false;
        SurfaceType destination_surface = SurfaceType::Obstacle;
        bool water_blocked = false;
        bool obstacle_blocked = false;
        bool bridge_admitted = false;
        double distance_m = 0.0;
    };

    // Domain-neutral terrain line of sight over the measured elevation surface.
    // `Unknown` is never a visibility claim: consumers must fail closed on it.
    enum class TerrainLineOfSightStatus : std::uint8_t {
        Unknown = 0,
        Visible = 1,
        Blocked = 2,
    };

    enum class TerrainLineOfSightUnknownReason : std::uint8_t {
        None = 0,
        NoMeasuredElevation = 1,   // no metric raster loaded, or a synthetic profile active
        InvalidInput = 2,          // non-finite coordinate or negative/non-finite height
        EndpointOutsideRaster = 3, // an endpoint has no raster elevation sample
        SampleOutsideRaster = 4,   // an interior sample has no raster elevation sample
    };

    enum class TerrainElevationSource : std::uint8_t {
        None = 0,
        ArnisMetricRaster = 1,
    };

    struct TerrainLineOfSightObservation {
        TerrainLineOfSightStatus status = TerrainLineOfSightStatus::Unknown;
        TerrainLineOfSightUnknownReason unknown_reason =
            TerrainLineOfSightUnknownReason::NoMeasuredElevation;
        TerrainElevationSource elevation_source = TerrainElevationSource::None;
        // Provenance: the raster's metric cell size and the interior samples evaluated.
        double sample_spacing_m = 0.0;
        std::uint32_t sample_count = 0;
        double distance_m = 0.0;
        // Absolute ray endpoints: terrain elevation plus the caller's height.
        double from_absolute_height_m = std::numeric_limits<double>::quiet_NaN();
        double to_absolute_height_m = std::numeric_limits<double>::quiet_NaN();
        // First sample whose terrain is strictly above the ray (Blocked only).
        bool has_blocking_sample = false;
        double blocking_x = 0.0;
        double blocking_y = 0.0;
        double blocking_distance_m = 0.0;
        double blocking_terrain_height_m = 0.0;
        double blocking_ray_height_m = 0.0;
    };

    // Heights are above the local terrain surface at each endpoint. Providers
    // without a measured elevation surface keep this fail-closed default.
    virtual TerrainLineOfSightObservation
    get_terrain_line_of_sight_observation(double /*from_x*/, double /*from_y*/,
                                          double /*from_height_above_terrain_m*/, double /*to_x*/,
                                          double /*to_y*/, double /*to_height_above_terrain_m*/) {
        return {};
    }

    virtual TerrainCell get_terrain_at(double x, double y) = 0;

    // Dynamic Configuration
    virtual void clear_zones() = 0;
    virtual void add_zone(const std::string &name, double x, double y, double width, double height,
                          double heading, SurfaceType surface) = 0;

    // Wind configuration
    // dir_from_deg uses NAV convention: 0=North, CW positive.
    // shear_mps_per_km is applied in the "to" direction (same as the base wind).
    virtual void set_wind(double /*speed_mps*/, double /*dir_from_deg*/,
                          double /*shear_mps_per_km*/) {}

    // Sun configuration (drives get_sun_direction and the optical glare
    // penalty in sensor models). azimuth_deg uses NAV convention: 0=North,
    // CW positive; elevation_deg is above the horizon. Defaults preserve the
    // historical fixed vector (azimuth 0, elevation 45).
    virtual void set_sun_direction(double /*azimuth_deg*/, double /*elevation_deg*/) {}

    // Terrain profile configuration.
    // "flat" means zero-elevation terrain outside explicit zones.
    // "legacy"/"hill"/"gaussian_hill"/"mountain" preserve the historical procedural mountain.
    // Unknown terrain profiles must fail closed instead of falling back to that profile.
    virtual void set_terrain_type(const std::string & /*terrain_type*/) {}

    // Load a verified Arnis continuous raster bundle into the environment
    // provider. Providers that do not support this repository-native bundle
    // remain fail-closed by returning false.
    virtual bool load_arnis_terrain_bundle(const std::string & /*bundle_root*/) { return false; }

    // Load the companion metadata-only overlay. Providers must keep its
    // tree-line/settlement semantics separate from movement, passability,
    // cover, and fire-control authority.
    virtual bool load_arnis_field_overlay(const std::string & /*overlay_path*/) { return false; }

    virtual GroundFieldSemanticObservation get_ground_field_semantic_observation(double /*x*/,
                                                                                 double /*y*/) {
        return {};
    }

    virtual GroundTransitionObservation get_ground_transition_observation(double /*from_x*/,
                                                                          double /*from_y*/,
                                                                          double /*to_x*/,
                                                                          double /*to_y*/) {
        return {};
    }

    // Maritime-state configuration used by surface-ship runtime proxies.
    // set_maritime_state() activates a full environment override; clear_maritime_state() returns
    // control to per-platform fallback values. Partial field merge is intentionally not supported
    // in this MVP.
    virtual void set_maritime_state(double /*sea_state*/, double /*wave_heading_deg*/,
                                    double /*wave_period_s*/) {}
    virtual void clear_maritime_state() {}
    virtual MaritimeState get_maritime_state() const { return {}; }
};

struct EnvironmentModelRef {
    IEnvironmentModel *model;
};

#include <memory>
std::unique_ptr<IEnvironmentModel> make_default_environment_model();
