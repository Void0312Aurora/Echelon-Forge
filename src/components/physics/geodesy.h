#pragma once

// Geodetic frame and curvature geometry (Geodetic Frame package, P2-A/P2-B).
//
// Owner: systems/physics. This header is the single authority for the earth
// model, the relation between the simulation's local frame and geodetic
// coordinates, and curvature-aware geometry queries. It is a pure, stateless
// header in `components/` so that every layer allowed to read components
// (models, systems, core/engine, content) can use the same queries without an
// upward include.
//
// Frame contract:
//   * The simulation frame (`Transform` x, y, z) is a map projection anchored at
//     a scenario geodetic anchor: x = east, y = north, z = height above the
//     reference sphere. It is NOT a strict tangent plane: at 500 km a tangent
//     plane would sit 19.6 km above the sea, while z-as-height keeps gravity
//     and flight dynamics correct.
//   * Horizontal coordinates are azimuthal-equidistant about the anchor:
//     distance and bearing from the anchor are exact on the sphere. Distances
//     between two arbitrary points differ from great-circle distance by
//     well under 0.1 % inside the declared frame extent, which is why local
//     range and bearing math may stay flat (see the P1-A inventory).
//   * Horizon and line-of-sight queries must use the curvature functions below;
//     flat math is wrong by kilometres at hundreds of kilometres.
//
// Earth model: a sphere of mean radius. WGS-84 ellipsoidal geometry is a
// planned follow-on; sphere vs ellipsoid moves horizons by <= 0.3 %, which is
// smaller than the uncertainty in the atmospheric refraction factor.
//
// Units: metres, radians internally; degrees only at the API edge where named.

#include <cmath>
#include <numbers>

namespace geodesy {

// IUGG mean earth radius R1 = (2a + b) / 3 for WGS-84, rounded to the metre.
inline constexpr double kMeanEarthRadiusM = 6371009.0;

// Standard-atmosphere effective-earth-radius factor for radar/radio horizons
// (ITU-R P.834 median value). Declared, not tuned: sensing or environment may
// pass a different factor for anomalous propagation.
inline constexpr double kStandardRefractionFactor = 4.0 / 3.0;

// Standard terrestrial refraction for the visible sea horizon: NGA Pub. No. 9
// (Bowditch), Table 12 "Distance of the Horizon", computes
// D = sqrt(2 r0 h / beta0) with beta0 = 0.8321, i.e. an effective-radius factor
// of 1 / 0.8321 (the familiar 1.17 nmi * sqrt(h[ft])). Visual and infrared
// sensors use this factor; radio-frequency sensors use the 4/3 factor above.
inline constexpr double kStandardOpticalRefractionFactor = 1.0 / 0.8321;

struct EarthModel {
    double radius_m = kMeanEarthRadiusM;
};

// Geodetic anchor of a scenario's local frame.
//
// A scenario that does not declare an anchor inherits `kDefaultGeodeticAnchor`:
// the Nellis AFB reference (36.24 N, 115.05 W) that the navigation system used
// as a hard-coded anchor before the geodetic frame existed. Keeping it as the
// documented default leaves every undeclared scenario at the same latitude and
// longitude it always had near the origin.
struct GeodeticAnchor {
    double latitude_deg = 0.0;
    double longitude_deg = 0.0;
    // Height of the local frame's z = 0 above the reference sphere. Scenarios
    // at sea use 0; a land tile may declare its datum offset here.
    double height_m = 0.0;
};

inline constexpr GeodeticAnchor kDefaultGeodeticAnchor{36.24, -115.05, 0.0};

// An anchor is usable when every field is finite and the latitude lies strictly
// inside (-90, 90): the azimuthal-equidistant frame is undefined at a pole
// anchor's own meridian. Longitude may be any finite value; it is wrapped.
[[nodiscard]] inline bool is_valid_anchor(const GeodeticAnchor &anchor) noexcept {
    return std::isfinite(anchor.latitude_deg) && std::isfinite(anchor.longitude_deg) &&
           std::isfinite(anchor.height_m) && anchor.latitude_deg > -90.0 &&
           anchor.latitude_deg < 90.0;
}

struct GeodeticPosition {
    double latitude_deg = 0.0;
    double longitude_deg = 0.0;
    double height_m = 0.0;
};

struct LocalPosition {
    double east_m = 0.0;
    double north_m = 0.0;
    double up_m = 0.0;
};

[[nodiscard]] inline constexpr double deg_to_rad(double deg) noexcept {
    return deg * std::numbers::pi_v<double> / 180.0;
}

[[nodiscard]] inline constexpr double rad_to_deg(double rad) noexcept {
    return rad * 180.0 / std::numbers::pi_v<double>;
}

// Normalise a longitude to [-180, 180).
[[nodiscard]] inline double wrap_longitude_deg(double lon_deg) noexcept {
    double wrapped = std::fmod(lon_deg + 180.0, 360.0);
    if (wrapped < 0.0) {
        wrapped += 360.0;
    }
    return wrapped - 180.0;
}

// Great-circle central angle between two geodetic points (haversine form,
// numerically stable for short and long separations).
[[nodiscard]] inline double central_angle_rad(double lat1_deg, double lon1_deg, double lat2_deg,
                                              double lon2_deg) noexcept {
    const double phi1 = deg_to_rad(lat1_deg);
    const double phi2 = deg_to_rad(lat2_deg);
    const double dphi = phi2 - phi1;
    const double dlambda = deg_to_rad(lon2_deg - lon1_deg);
    const double s_dphi = std::sin(dphi * 0.5);
    const double s_dlambda = std::sin(dlambda * 0.5);
    const double h = s_dphi * s_dphi + std::cos(phi1) * std::cos(phi2) * s_dlambda * s_dlambda;
    return 2.0 * std::asin(std::sqrt(std::fmin(1.0, std::fmax(0.0, h))));
}

// Great-circle surface distance on the model sphere.
[[nodiscard]] inline double great_circle_distance_m(const EarthModel &earth, double lat1_deg,
                                                    double lon1_deg, double lat2_deg,
                                                    double lon2_deg) noexcept {
    return earth.radius_m * central_angle_rad(lat1_deg, lon1_deg, lat2_deg, lon2_deg);
}

// Initial great-circle bearing from point 1 to point 2, degrees clockwise from
// true north in [0, 360).
[[nodiscard]] inline double initial_bearing_deg(double lat1_deg, double lon1_deg, double lat2_deg,
                                                double lon2_deg) noexcept {
    const double phi1 = deg_to_rad(lat1_deg);
    const double phi2 = deg_to_rad(lat2_deg);
    const double dlambda = deg_to_rad(lon2_deg - lon1_deg);
    const double y = std::sin(dlambda) * std::cos(phi2);
    const double x =
        std::cos(phi1) * std::sin(phi2) - std::sin(phi1) * std::cos(phi2) * std::cos(dlambda);
    double bearing = rad_to_deg(std::atan2(y, x));
    if (bearing < 0.0) {
        bearing += 360.0;
    }
    return bearing;
}

// Local frame -> geodetic (inverse azimuthal-equidistant projection).
[[nodiscard]] inline GeodeticPosition local_to_geodetic(const EarthModel &earth,
                                                        const GeodeticAnchor &anchor,
                                                        const LocalPosition &local) noexcept {
    const double phi0 = deg_to_rad(anchor.latitude_deg);
    const double lambda0 = deg_to_rad(anchor.longitude_deg);
    const double rho = std::hypot(local.east_m, local.north_m);
    GeodeticPosition out;
    out.height_m = anchor.height_m + local.up_m;
    if (rho == 0.0) {
        out.latitude_deg = anchor.latitude_deg;
        out.longitude_deg = wrap_longitude_deg(anchor.longitude_deg);
        return out;
    }
    const double c = rho / earth.radius_m; // central angle
    const double sin_c = std::sin(c);
    const double cos_c = std::cos(c);
    const double sin_phi0 = std::sin(phi0);
    const double cos_phi0 = std::cos(phi0);
    const double phi = std::asin(
        std::fmin(1.0, std::fmax(-1.0, cos_c * sin_phi0 + local.north_m * sin_c * cos_phi0 / rho)));
    const double lambda =
        lambda0 +
        std::atan2(local.east_m * sin_c, rho * cos_phi0 * cos_c - local.north_m * sin_phi0 * sin_c);
    out.latitude_deg = rad_to_deg(phi);
    out.longitude_deg = wrap_longitude_deg(rad_to_deg(lambda));
    return out;
}

// Geodetic -> local frame (forward azimuthal-equidistant projection).
[[nodiscard]] inline LocalPosition geodetic_to_local(const EarthModel &earth,
                                                     const GeodeticAnchor &anchor,
                                                     const GeodeticPosition &geo) noexcept {
    const double c = central_angle_rad(anchor.latitude_deg, anchor.longitude_deg, geo.latitude_deg,
                                       geo.longitude_deg);
    LocalPosition out;
    out.up_m = geo.height_m - anchor.height_m;
    if (c == 0.0) {
        return out;
    }
    const double rho = earth.radius_m * c;
    const double azimuth = deg_to_rad(initial_bearing_deg(anchor.latitude_deg, anchor.longitude_deg,
                                                          geo.latitude_deg, geo.longitude_deg));
    out.east_m = rho * std::sin(azimuth);
    out.north_m = rho * std::cos(azimuth);
    return out;
}

// Effective earth radius for propagation over the curved surface.
[[nodiscard]] inline constexpr double effective_radius_m(const EarthModel &earth,
                                                         double refraction_factor) noexcept {
    return earth.radius_m * refraction_factor;
}

// Distance to the horizon from one height above the surface, using an
// effective earth radius. Heights below the surface clamp to zero. Uses the
// exact tangent length sqrt(2 R h + h^2), which reduces to sqrt(2 R h) for
// h << R.
[[nodiscard]] inline double horizon_distance_m(double effective_radius_m,
                                               double height_m) noexcept {
    const double h = std::fmax(0.0, height_m);
    return std::sqrt(2.0 * effective_radius_m * h + h * h);
}

// Maximum surface-to-surface separation at which two points at the given
// heights can see each other over a smooth sphere of the given effective
// radius. This is the two-ended radar/radio horizon.
[[nodiscard]] inline double two_way_horizon_distance_m(double effective_radius_m, double height_a_m,
                                                       double height_b_m) noexcept {
    return horizon_distance_m(effective_radius_m, height_a_m) +
           horizon_distance_m(effective_radius_m, height_b_m);
}

// Largest surface separation (arc length on the effective sphere) at which two
// points at the given heights still have a clear smooth-earth line of sight:
// Re * (alpha_a + alpha_b), where alpha is the central angle from each point to
// its horizon, tan(alpha) = sqrt(2 Re h + h^2) / Re. This is the exact boundary
// of `smooth_earth_line_of_sight` and is the form sensing and data links compare
// against a horizontal separation in the local frame.
[[nodiscard]] inline double two_way_horizon_arc_m(double effective_radius_m, double height_a_m,
                                                  double height_b_m) noexcept {
    const double alpha_a =
        std::atan2(horizon_distance_m(effective_radius_m, height_a_m), effective_radius_m);
    const double alpha_b =
        std::atan2(horizon_distance_m(effective_radius_m, height_b_m), effective_radius_m);
    return effective_radius_m * (alpha_a + alpha_b);
}

// Whether two points at heights above the surface and a given surface
// separation have a clear line of sight over a smooth sphere of the given
// effective radius. The test is the exact one: the straight segment between the
// two points clears the sphere iff its minimum distance to the sphere centre is
// at least the radius, or the closest point lies outside the segment.
[[nodiscard]] inline bool smooth_earth_line_of_sight(double effective_radius_m, double height_a_m,
                                                     double height_b_m,
                                                     double surface_separation_m) noexcept {
    const double r = effective_radius_m;
    const double ra = r + std::fmax(0.0, height_a_m);
    const double rb = r + std::fmax(0.0, height_b_m);
    const double theta = surface_separation_m / r;
    if (theta <= 0.0) {
        return true;
    }
    if (theta >= std::numbers::pi_v<double>) {
        return false;
    }
    // Points in the plane of the great circle: A = (ra, 0), B = (rb cos t, rb sin t).
    const double bx = rb * std::cos(theta);
    const double by = rb * std::sin(theta);
    const double dx = bx - ra;
    const double dy = by;
    const double seg_len_sq = dx * dx + dy * dy;
    // Parameter of the closest point to the origin along A + t (B - A).
    const double t = -(ra * dx) / seg_len_sq;
    if (t <= 0.0 || t >= 1.0) {
        return true;
    }
    const double cx = ra + t * dx;
    const double cy = t * dy;
    return (cx * cx + cy * cy) >= r * r;
}

// Height of the smooth-earth bulge above the chord between two surface points
// at the given separation, at the midpoint: b = R (1 - cos(d / 2R)), which is
// d^2 / (8 R) for d << R. Useful for terrain-profile line-of-sight tests that
// sample along a straight segment in the local frame.
[[nodiscard]] inline double earth_bulge_m(double effective_radius_m, double distance_from_a_m,
                                          double distance_from_b_m) noexcept {
    // Bulge at a point splitting the chord into d1 and d2: d1 * d2 / (2 R).
    return std::fmax(0.0, distance_from_a_m) * std::fmax(0.0, distance_from_b_m) /
           (2.0 * effective_radius_m);
}

} // namespace geodesy
