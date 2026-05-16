#pragma once

#include <cmath>

#include "components/basic/common.h"

struct EGI {
    // INS/GPS Blended Solution (What the pilot sees)
    double lat_deg;
    double lon_deg;
    double alt_baro_m; // Barometric Altitude
    double alt_radar_m; // Radar Altimeter (AGL)

    double vn_mps; // Velocity North
    double ve_mps; // Velocity East
    double vd_mps; // Velocity Down

    double heading_deg;
    double pitch_deg;
    double roll_deg;

    // Wind Estimation
    double wind_speed_mps;
    double wind_dir_deg;

    // System Status / Error States
    double drift_lat_m;
    double drift_lon_m;
    double drift_alt_m;
    
    double position_uncertainty_m; // EPE (Estimated Position Error)
    double time_since_last_gps_fix;
    
    // Configuration / Constants (could be in proper config later)
    double ins_drift_rate_mps; // e.g., 0.5 m/s per hour (bad INS) or better
    bool gps_available;
};

struct InstrumentNavigationProjection {
    double lat_deg = 0.0;
    double lon_deg = 0.0;
    double vn_mps = 0.0;
    double ve_mps = 0.0;
    double vd_mps = 0.0;
    double ground_speed_mps = 0.0;
    double ground_track_deg = 0.0;
    bool gps_available = false;
    double position_uncertainty_m = 1000.0;
};

inline InstrumentNavigationProjection project_egi_to_instrument_navigation(
    const EGI& egi,
    double fallback_heading_deg
) {
    InstrumentNavigationProjection out;
    out.lat_deg = egi.lat_deg;
    out.lon_deg = egi.lon_deg;
    out.vn_mps = egi.vn_mps;
    out.ve_mps = egi.ve_mps;
    out.vd_mps = egi.vd_mps;
    out.ground_speed_mps = std::hypot(egi.vn_mps, egi.ve_mps);
    out.ground_track_deg = Math::ground_track_deg_from_velocity(
        egi.ve_mps,
        egi.vn_mps,
        fallback_heading_deg
    );
    out.gps_available = egi.gps_available;
    out.position_uncertainty_m = egi.position_uncertainty_m;
    return out;
}
