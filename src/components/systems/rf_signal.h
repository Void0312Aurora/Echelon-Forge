#pragma once

#include <algorithm>
#include <cmath>
#include <limits>
#include <numbers>

// Isotropic free-space reference, ITU-R P.525-5 equation (5). EIRP is
// separately authored: the historical jammer ERP/proxy is not silently EIRP.
inline bool rf_emission_valid(double eirp_watts, double frequency_mhz, double bandwidth_mhz) {
    return std::isfinite(eirp_watts) && eirp_watts > 0.0 &&
           std::isfinite(frequency_mhz) && frequency_mhz > 0.0 &&
           std::isfinite(bandwidth_mhz) && bandwidth_mhz > 0.0;
}

inline double rf_received_power_dbm(double eirp_watts, double frequency_mhz, double distance_m) {
    if (!std::isfinite(eirp_watts) || eirp_watts <= 0.0 ||
        !std::isfinite(frequency_mhz) || frequency_mhz <= 0.0 ||
        !std::isfinite(distance_m) || distance_m < 0.0) {
        return -std::numeric_limits<double>::infinity();
    }
    constexpr double speed_of_light_mps = 299792458.0;
    const double loss_db = 20.0 * (std::log10(4.0 * std::numbers::pi_v<double>) +
        std::log10(std::max(1.0, distance_m)) + std::log10(frequency_mhz) + 6.0 -
        std::log10(speed_of_light_mps));
    return 10.0 * std::log10(eirp_watts) + 30.0 - loss_db;
}

inline double rf_band_overlap(double center_a, double width_a, double center_b, double width_b) {
    if (!std::isfinite(center_a) || !std::isfinite(center_b) ||
        !std::isfinite(width_a) || !std::isfinite(width_b) ||
        center_a <= 0.0 || center_b <= 0.0 || width_a <= 0.0 || width_b <= 0.0) return 0.0;
    return std::max(0.0, std::min(center_a + width_a * 0.5, center_b + width_b * 0.5) -
                            std::max(center_a - width_a * 0.5, center_b - width_b * 0.5));
}
