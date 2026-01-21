#pragma once

#include <cmath>

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
