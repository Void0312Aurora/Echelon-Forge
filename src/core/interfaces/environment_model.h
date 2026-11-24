#pragma once

#include "components/basic/environment_data.h"
#include "components/physics/geodesy.h"
#include <cmath>
#include <cstdint>
#include <limits>
#include <numbers>
#include <optional>
#include <string>
#include <vector>

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

    // Bathymetry is an environment observation, not a naval movement or
    // grounding decision.  A valid segment observation reports the shallowest
    // water column along the proposed horizontal step in one declared vertical
    // datum.  Providers must report coverage and datum provenance explicitly;
    // consumers must not treat an unavailable result as deep water.
    enum class BathymetryAvailability : uint8_t {
        Unavailable = 0,
        Valid = 1,
        OutOfCoverage = 2,
        Dry = 3,
        InvalidDatum = 4,
    };

    struct BathymetrySegmentObservation {
        BathymetryAvailability availability = BathymetryAvailability::Unavailable;
        double minimum_water_depth_m = std::numeric_limits<double>::quiet_NaN();
        // The frame in which the horizontal segment coordinates are expressed.
        // Consumers must reject observations with no declared frame.
        std::string horizontal_frame{};
        std::string vertical_datum{};
        std::string source{};
        // This slice requires the water surface to coincide with Transform.z
        // zero. A nonzero tide/elevation must not be silently discarded.
        double water_surface_elevation_m = std::numeric_limits<double>::quiet_NaN();
        // The first admitted slice is static over a simulation step. Providers
        // must say so explicitly; time-varying tide data needs a later contract
        // that carries query time and validity bounds.
        bool time_invariant_for_step = false;
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

    virtual TerrainCell get_terrain_at(double x, double y) = 0;

    // P2-A additive contract; legacy methods above keep their existing behavior.
    // See environment_runtime_p2a_contract_20261124.md. No default below infers
    // coverage, datum, time, or a clear line of sight from legacy scalar queries.
    enum class QueryStatus : uint8_t {
        Unavailable = 0,
        Valid,
        OutOfCoverage,
        NoData,
        InvalidDatum,
        InvalidFrame,
        InvalidTime,
        Unsupported
    };

    enum class EnvironmentLayer : uint8_t {
        TerrainElevation,
        TerrainSurface,
        Bathymetry,
        WaterBody,
        Coastline,
        Atmosphere,
        Wind,
        SeaState,
        Illumination,
        OceanAcoustics
    };

    struct QueryContext {
        std::string horizontal_frame{};
        std::string vertical_datum{};
        double simulation_time_s = std::numeric_limits<double>::quiet_NaN();
        // Optional absolute clock value, tied to the same scenario clock.
        std::optional<double> utc_unix_time_s{};
    };

    struct QueryPoint {
        double x_m = std::numeric_limits<double>::quiet_NaN();
        double y_m = std::numeric_limits<double>::quiet_NaN();
        double z_m = std::numeric_limits<double>::quiet_NaN();
    };

    struct QueryMetadata {
        QueryStatus status = QueryStatus::Unavailable;
        std::string horizontal_frame{};
        std::string vertical_datum{};
        std::string source{};
        std::string snapshot_id{};
        std::vector<std::string> tile_ids{};
        std::optional<double> resolution_x_m{};
        std::optional<double> resolution_y_m{};
        std::optional<double> valid_from_simulation_s{};
        std::optional<double> valid_until_simulation_s{};
    };

    struct EnvironmentLayerDescriptor {
        EnvironmentLayer layer = EnvironmentLayer::TerrainElevation;
        QueryMetadata metadata{};
        std::string layer_id{};
        int32_t priority = 0;
        // Half-open horizontal bounds in metadata.horizontal_frame.
        double min_x_m = std::numeric_limits<double>::quiet_NaN();
        double min_y_m = std::numeric_limits<double>::quiet_NaN();
        double max_x_m = std::numeric_limits<double>::quiet_NaN();
        double max_y_m = std::numeric_limits<double>::quiet_NaN();
    };

    struct TerrainObservation {
        QueryMetadata metadata{};
        // Valid requires BOTH elevation and surface from one coherent snapshot.
        std::optional<double> elevation_m{};
        std::optional<SurfaceType> surface{};
        std::optional<uint32_t> landcover_code{};
        std::optional<double> slope_deg{};
    };

    enum class WaterBodyKind : uint8_t { Unknown = 0, Sea, River, Lake, Reservoir };

    struct WaterBodyObservation {
        QueryMetadata metadata{};
        std::string water_body_id{};
        WaterBodyKind kind = WaterBodyKind::Unknown;
        std::optional<double> surface_elevation_m{};
        std::optional<double> bottom_elevation_m{};
        std::optional<double> depth_m{};
        std::optional<Vec3> flow_to_mps{};
        std::optional<double> salinity_psu{};
        std::optional<double> temperature_c{};
    };

    struct CoastlineObservation {
        QueryMetadata metadata{};
        std::string water_body_id{};
        WaterBodyKind kind = WaterBodyKind::Unknown;
        // Nonnegative horizontal distance; wet_side is independent of distance.
        std::optional<double> distance_m{};
        std::optional<QueryPoint> nearest_point{};
        std::optional<bool> wet_side{};
    };

    enum class VariationMode : uint8_t { Unspecified = 0, Constant, SeededField };

    struct VariationDescriptor {
        VariationMode mode = VariationMode::Unspecified;
        uint64_t seed = 0;
        std::string algorithm_version{};
        std::string parameters_id{};
        std::optional<double> spatial_scale_m{};
        std::optional<double> temporal_scale_s{};
    };

    struct WeatherObservation {
        QueryMetadata metadata{};
        VariationDescriptor variation{};
        std::optional<AtmosphericData> atmosphere{};
        std::optional<Vec3> wind_to_mps{};
        std::optional<double> visibility_m{};
        std::optional<double> precipitation_mm_per_hour{};
    };

    struct WaveComponent {
        double significant_height_m = std::numeric_limits<double>::quiet_NaN();
        double period_s = std::numeric_limits<double>::quiet_NaN();
        double heading_to_deg = std::numeric_limits<double>::quiet_NaN();
    };

    struct SeaStateObservation {
        QueryMetadata metadata{};
        VariationDescriptor variation{};
        std::optional<double> sea_state{};
        std::optional<WaveComponent> wind_sea{};
        std::optional<WaveComponent> swell{};
    };

    enum class IlluminationSource : uint8_t { Unspecified = 0, ScenarioFixed, ScenarioClock };

    struct IlluminationObservation {
        QueryMetadata metadata{};
        IlluminationSource source = IlluminationSource::Unspecified;
        std::optional<Vec3> sun_direction_to{};
        std::optional<double> solar_elevation_deg{};
    };

    enum class OceanBottomClass : uint8_t { Unknown = 0, Mud, Sand, Gravel, Rock };

    struct OceanAcousticSample {
        double depth_below_surface_m = std::numeric_limits<double>::quiet_NaN();
        std::optional<double> sound_speed_mps{};
        std::optional<double> temperature_c{};
        std::optional<double> salinity_psu{};
    };

    struct AmbientNoiseSample {
        double frequency_hz = std::numeric_limits<double>::quiet_NaN();
        double spectral_level_db_re_1_upa2_per_hz = std::numeric_limits<double>::quiet_NaN();
    };

    struct OceanAcousticObservation {
        QueryMetadata metadata{};
        std::optional<double> water_surface_elevation_m{};
        std::vector<OceanAcousticSample> profile{};
        std::optional<double> mixed_layer_depth_m{};
        OceanBottomClass bottom_class = OceanBottomClass::Unknown;
        std::vector<AmbientNoiseSample> ambient_noise{};
    };

    enum class HeightReference : uint8_t { Unspecified = 0, AbsoluteDatum, AboveTerrain };
    enum class CurvatureMode : uint8_t { Unspecified = 0, LocalFlat, GeodeticEarth };
    enum class TerrainVisibility : uint8_t { Unknown = 0, Clear, Occluded };

    struct TerrainSightQuery {
        QueryContext context{};
        QueryPoint from{};
        QueryPoint to{};
        HeightReference from_height = HeightReference::Unspecified;
        HeightReference to_height = HeightReference::Unspecified;
        CurvatureMode curvature = CurvatureMode::Unspecified;
    };

    struct TerrainSightObservation {
        QueryMetadata metadata{};
        TerrainVisibility visibility = TerrainVisibility::Unknown;
        CurvatureMode curvature = CurvatureMode::Unspecified;
    };

    struct TimedBathymetrySegmentObservation {
        QueryMetadata metadata{};
        // Minimum over the WHOLE horizontal segment at context.simulation_time_s.
        std::optional<double> minimum_water_depth_m{};
    };

    // All seams are optional overrides. Empty means unavailable, never clear,
    // dry land, calm water, zero altitude, or permission to move.
    virtual std::vector<EnvironmentLayerDescriptor> get_environment_layers() const { return {}; }
    virtual TerrainObservation query_terrain(const QueryContext &, const QueryPoint &) {
        return {};
    }
    virtual WaterBodyObservation query_water_body(const QueryContext &, const QueryPoint &) {
        return {};
    }
    virtual CoastlineObservation query_coastline(const QueryContext &, const QueryPoint &) {
        return {};
    }
    virtual WeatherObservation query_weather(const QueryContext &, const QueryPoint &) {
        return {};
    }
    virtual SeaStateObservation query_sea_state(const QueryContext &, const QueryPoint &) {
        return {};
    }
    virtual IlluminationObservation query_illumination(const QueryContext &, const QueryPoint &) {
        return {};
    }
    virtual OceanAcousticObservation query_ocean_acoustics(const QueryContext &,
                                                           const QueryPoint &) {
        return {};
    }
    virtual TerrainSightObservation query_terrain_visibility(const TerrainSightQuery &) {
        return {};
    }
    virtual TimedBathymetrySegmentObservation
    query_bathymetry_segment(const QueryContext &, const QueryPoint &, const QueryPoint &) {
        return {};
    }

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

    // Shared environment owner seam for the first bathymetry-aware naval
    // slice.  The default provider has no admitted bathymetry and therefore
    // returns Unavailable.  The segment result is conservative by contract:
    // minimum_water_depth_m covers the complete proposed horizontal step.
    virtual BathymetrySegmentObservation get_bathymetry_along_segment(double /*from_x*/,
                                                                      double /*from_y*/,
                                                                      double /*to_x*/,
                                                                      double /*to_y*/) {
        return {};
    }

    // Geodetic frame of this world (Geodetic Frame P3-B): the scenario anchor of
    // the local frame and the reference earth. A world whose scenario declares no
    // anchor keeps `geodesy::kDefaultGeodeticAnchor`. Like the other environment
    // settings, the anchor survives kernel reset.
    virtual void set_geodetic_anchor(const geodesy::GeodeticAnchor & /*anchor*/) {}
    virtual geodesy::GeodeticAnchor get_geodetic_anchor() const {
        return geodesy::kDefaultGeodeticAnchor;
    }
    virtual geodesy::EarthModel get_earth_model() const { return {}; }

    // Scenario settings applied through the setters above, for state
    // transfer. Loaded terrain content (raster and Arnis bundles) is not part
    // of it. Zones keep their stored order: replaying add_zone could reorder
    // zones of equal z_order.
    struct ZoneSettings {
        std::string name;
        double center_x = 0.0;
        double center_y = 0.0;
        double center_z = 0.0;
        double width = 0.0;
        double length = 0.0;
        double heading_deg = 0.0;
        int type = 0;
        SurfaceType surface = SurfaceType::Concrete;
        double friction = 0.0;
        double roughness = 0.0;
        double vegetation_density = 0.0;
        double runway_heading_deg = 0.0;
        int z_order = 0;
    };
    struct Settings {
        double wind_speed_mps = 0.0;
        double wind_dir_from_deg = 0.0;
        double wind_shear_mps_per_km = 0.0;
        double sun_azimuth_deg = 0.0;
        double sun_elevation_deg = 0.0;
        MaritimeState maritime_state{};
        geodesy::GeodeticAnchor geodetic_anchor{};
        bool flat_terrain = false;
        std::vector<ZoneSettings> zones;
    };
    // Providers that cannot reproduce their settings exactly return false;
    // state transfer then fails closed instead of copying a partial state.
    virtual bool export_settings(Settings * /*out*/) const { return false; }
    virtual bool restore_settings(const Settings & /*settings*/) { return false; }
};

// Geodetic position of a local-frame point in the world that owns `env`; falls
// back to the documented default anchor when no environment is bound.
inline geodesy::GeodeticPosition environment_local_to_geodetic(const IEnvironmentModel *env,
                                                               double x_m, double y_m, double z_m) {
    const geodesy::GeodeticAnchor anchor =
        env ? env->get_geodetic_anchor() : geodesy::kDefaultGeodeticAnchor;
    const geodesy::EarthModel earth = env ? env->get_earth_model() : geodesy::EarthModel{};
    return geodesy::local_to_geodetic(earth, anchor, {x_m, y_m, z_m});
}

struct EnvironmentModelRef {
    IEnvironmentModel *model;
};

#include <memory>
std::unique_ptr<IEnvironmentModel> make_default_environment_model();
