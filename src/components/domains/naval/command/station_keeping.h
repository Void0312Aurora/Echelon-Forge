#pragma once

// Station keeping relative to a moving reference ship (CSG-S1-A).
//
// A station is a point at a true bearing and range from the reference ship's
// position. Formation axis and stations are true-bearing referenced, so a
// course change of the guide does not rotate the screen; rotating the
// formation axis is a separate C2 order.
//
// The law commands an over-ground velocity
//     v_c = v_ref + k (p_station - p_own),     k = 1 / tau_close,
// i.e. the reference ship's velocity as feed-forward plus a bounded closing
// velocity toward the station. Its magnitude and direction become the ordered
// speed and heading for the hull's maneuvering law. Far from station the
// closing term saturates at `max_closing_speed_mps`, so the ship transits back
// at a bounded speed difference; on station it degenerates to the guide's
// course and speed, so there is no steering chatter from the bearing to a
// nearby point. A guide at rest with the ship on station leaves no command:
// heading and speed are then held (the fallback).

#include <algorithm>
#include <cmath>
#include <numbers>

namespace naval_station_keeping {

struct StationCommand {
    double heading_deg = 0.0;
    double speed_mps = 0.0;
    double station_x_m = 0.0;
    double station_y_m = 0.0;
    double range_error_m = 0.0;
};

// Closing time constant of the position loop. It must be long against the hull
// yaw time constant (tens of seconds for warship hulls) so the inner heading
// loop tracks it; 300 s closes a 1 km offset at about 3.3 m/s.
inline constexpr double kClosingTimeConstantS = 300.0;
// Highest closing (or opening) speed relative to the guide.
inline constexpr double kMaxClosingSpeedMps = 4.0;
// Below this commanded speed the direction of v_c is not meaningful.
inline constexpr double kHeadingSpeedFloorMps = 0.25;

[[nodiscard]] inline StationCommand
station_keeping_command(double reference_x_m, double reference_y_m, double reference_vx_mps,
                        double reference_vy_mps, double station_bearing_deg,
                        double station_radius_m, double own_x_m, double own_y_m,
                        double fallback_heading_deg) noexcept {
    StationCommand command{};
    const double bearing_rad = station_bearing_deg * std::numbers::pi_v<double> / 180.0;
    command.station_x_m = reference_x_m + std::sin(bearing_rad) * station_radius_m;
    command.station_y_m = reference_y_m + std::cos(bearing_rad) * station_radius_m;
    const double ex = command.station_x_m - own_x_m;
    const double ey = command.station_y_m - own_y_m;
    command.range_error_m = std::hypot(ex, ey);

    double closing_x = ex / kClosingTimeConstantS;
    double closing_y = ey / kClosingTimeConstantS;
    const double closing_speed = std::hypot(closing_x, closing_y);
    if (closing_speed > kMaxClosingSpeedMps) {
        closing_x *= kMaxClosingSpeedMps / closing_speed;
        closing_y *= kMaxClosingSpeedMps / closing_speed;
    }
    const double vx = reference_vx_mps + closing_x;
    const double vy = reference_vy_mps + closing_y;
    command.speed_mps = std::hypot(vx, vy);
    command.heading_deg = fallback_heading_deg;
    if (command.speed_mps > kHeadingSpeedFloorMps) {
        double heading = std::atan2(vx, vy) * 180.0 / std::numbers::pi_v<double>;
        if (heading < 0.0) {
            heading += 360.0;
        }
        command.heading_deg = heading;
    }
    return command;
}

} // namespace naval_station_keeping
