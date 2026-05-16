#pragma once

#include <cstdint>
#include <vector>

#include "core/interfaces/environment_model.h"

struct DefaultEnvironmentZoneSnapshot {
    double center_x = 0.0;
    double center_y = 0.0;
    double width = 0.0;
    double length = 0.0;
    double heading_deg = 0.0;
    int type = 0;  // 0=rect, 1=circle
    std::uint8_t surface_code = 0;
};

struct DefaultEnvironmentRasterSnapshot {
    double origin_x = 0.0;
    double origin_y = 0.0;
    double resolution_m = 0.0;
    int width = 0;
    int height = 0;
    std::vector<std::uint8_t> surface_codes;
};

struct DefaultEnvironmentSnapshot {
    bool valid = false;
    bool flat_terrain = false;
    bool maritime_state_configured = false;
    double sea_state = 0.0;
    double wave_heading_deg = 0.0;
    double wave_period_s = 8.0;
    DefaultEnvironmentRasterSnapshot raster;
    std::vector<DefaultEnvironmentZoneSnapshot> zones;
};

bool extract_default_environment_snapshot(
    IEnvironmentModel* env,
    DefaultEnvironmentSnapshot* out
);
