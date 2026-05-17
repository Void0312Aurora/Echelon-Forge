#pragma once

#include <algorithm>
#include <string>
#include <unordered_map>

#include "content/unit_definition.h"

#include <vector>

inline Sensor make_unit_definition_default_sensor_preset(
    double max_range,
    double fov_deg,
    double scan_period,
    double detection_prob,
    double bearing_noise_std,
    double range_noise_std,
    double track_memory_s,
    double aspect_influence,
    int sensor_type
) {
    Sensor sensor = make_unit_definition_default_sensor();
    sensor.max_range = max_range;
    sensor.fov_deg = fov_deg;
    sensor.scan_period = scan_period;
    sensor.detection_prob = detection_prob;
    sensor.bearing_noise_std = bearing_noise_std;
    sensor.range_noise_std = range_noise_std;
    sensor.track_memory_s = track_memory_s;
    sensor.aspect_influence = aspect_influence;
    sensor.doppler_notch_width = 20.0;
    sensor.reference_range_m = std::max(1000.0, max_range);
    sensor.type = sensor_type;
    return sensor;
}

bool load_unit_definitions_json(const std::string& path,
                                std::vector<UnitDefinition>& out_definitions,
                                std::string* error);
