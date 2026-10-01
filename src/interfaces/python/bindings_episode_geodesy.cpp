#include "interfaces/python/bindings_episode_detail.h"

#include "components/physics/geodesy.h"

#include <tuple>

// Geodetic frame projection (Geodetic Frame P2-A) for scenario compilation.
//
// Scenario tooling that places entities by latitude and longitude calls the
// same azimuthal-equidistant projection the runtime uses for EGI and the sensing
// horizon, instead of re-deriving it in Python. Stateless: the caller passes the
// scenario anchor it resolved.
void bind_episode_geodesy(nb::module_ &m) {
    m.def(
        "geodesy_geodetic_to_local",
        [](double anchor_latitude_deg, double anchor_longitude_deg, double anchor_height_m,
           double latitude_deg, double longitude_deg, double height_m) {
            const geodesy::GeodeticAnchor anchor{anchor_latitude_deg, anchor_longitude_deg,
                                                 anchor_height_m};
            if (!geodesy::is_valid_anchor(anchor)) {
                throw nb::value_error("geodetic anchor latitude must lie inside (-90, 90)");
            }
            const geodesy::LocalPosition local = geodesy::geodetic_to_local(
                geodesy::EarthModel{}, anchor, {latitude_deg, longitude_deg, height_m});
            return std::make_tuple(local.east_m, local.north_m, local.up_m);
        },
        nb::arg("anchor_latitude_deg"), nb::arg("anchor_longitude_deg"), nb::arg("anchor_height_m"),
        nb::arg("latitude_deg"), nb::arg("longitude_deg"), nb::arg("height_m") = 0.0,
        "Project a geodetic point into the local frame (east, north, up metres) of an anchor.");
    m.def(
        "geodesy_local_to_geodetic",
        [](double anchor_latitude_deg, double anchor_longitude_deg, double anchor_height_m,
           double east_m, double north_m, double up_m) {
            const geodesy::GeodeticAnchor anchor{anchor_latitude_deg, anchor_longitude_deg,
                                                 anchor_height_m};
            if (!geodesy::is_valid_anchor(anchor)) {
                throw nb::value_error("geodetic anchor latitude must lie inside (-90, 90)");
            }
            const geodesy::GeodeticPosition geo =
                geodesy::local_to_geodetic(geodesy::EarthModel{}, anchor, {east_m, north_m, up_m});
            return std::make_tuple(geo.latitude_deg, geo.longitude_deg, geo.height_m);
        },
        nb::arg("anchor_latitude_deg"), nb::arg("anchor_longitude_deg"), nb::arg("anchor_height_m"),
        nb::arg("east_m"), nb::arg("north_m"), nb::arg("up_m") = 0.0,
        "Map a local-frame point (east, north, up metres) of an anchor to latitude, longitude, "
        "height.");
    m.def(
        "geodesy_great_circle_distance_m",
        [](double lat1_deg, double lon1_deg, double lat2_deg, double lon2_deg) {
            return geodesy::great_circle_distance_m(geodesy::EarthModel{}, lat1_deg, lon1_deg,
                                                    lat2_deg, lon2_deg);
        },
        nb::arg("lat1_deg"), nb::arg("lon1_deg"), nb::arg("lat2_deg"), nb::arg("lon2_deg"),
        "Great-circle surface distance on the mean-earth sphere, metres.");
    m.def(
        "geodesy_initial_bearing_deg",
        [](double lat1_deg, double lon1_deg, double lat2_deg, double lon2_deg) {
            return geodesy::initial_bearing_deg(lat1_deg, lon1_deg, lat2_deg, lon2_deg);
        },
        nb::arg("lat1_deg"), nb::arg("lon1_deg"), nb::arg("lat2_deg"), nb::arg("lon2_deg"),
        "Initial great-circle bearing from point 1 to point 2, degrees clockwise from true north.");
}
