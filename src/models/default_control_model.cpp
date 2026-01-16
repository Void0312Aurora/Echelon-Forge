#include "core/control_model.h"

#include <algorithm>
#include <cmath>

namespace {

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

double normalize_angle(double angle) {
    while (angle > 180.0) angle -= 360.0;
    while (angle < -180.0) angle += 360.0;
    return angle;
}

double to_degrees(double rad) { return rad * 180.0 / M_PI; }
double to_radians(double deg) { return deg * M_PI / 180.0; }

class DefaultControlModel : public IControlModel {
public:
    void update(flecs::world /*world*/,
                flecs::entity /*entity*/,
                Velocity& velocity,
                Transform& transform,
                const MovementCommand& command,
                const FlightModel& flight_model,
                double dt) override {
        if (!command.active) return;

        double current_speed = std::sqrt(velocity.vx * velocity.vx +
                                         velocity.vy * velocity.vy +
                                         velocity.vz * velocity.vz);

        double current_heading_math = std::atan2(velocity.vy, velocity.vx);
        double current_heading_nav = 90.0 - to_degrees(current_heading_math);
        current_heading_nav = normalize_angle(current_heading_nav);

        double heading_error = normalize_angle(command.target_heading - current_heading_nav);
        double max_turn = flight_model.max_turn_rate * dt;
        double turn = std::clamp(heading_error, -max_turn, max_turn);
        double new_heading_nav = current_heading_nav + turn;

        double safe_target_speed = std::clamp(command.target_speed,
                                              flight_model.min_speed,
                                              flight_model.max_speed);
        double speed_error = safe_target_speed - current_speed;
        double max_accel_step = flight_model.max_accel * dt;
        double accel = std::clamp(speed_error, -max_accel_step, max_accel_step);
        double new_speed = std::max(0.0, current_speed + accel);

        double alt_error = command.target_altitude - transform.z;
        const double climb_tau = 10.0;
        double desired_climb_rate = alt_error / climb_tau;
        double max_climb = flight_model.max_climb_rate;
        double climb_rate = std::clamp(desired_climb_rate, -max_climb, max_climb);

        double pitch_rad = 0.0;
        if (new_speed > 1.0) {
            pitch_rad = std::asin(std::clamp(climb_rate / new_speed, -1.0, 1.0));
        }

        double h_speed = new_speed * std::cos(pitch_rad);
        double new_heading_math_rad = to_radians(90.0 - new_heading_nav);

        velocity.vx = h_speed * std::cos(new_heading_math_rad);
        velocity.vy = h_speed * std::sin(new_heading_math_rad);
        velocity.vz = new_speed * std::sin(pitch_rad);

        transform.heading = new_heading_nav;
        transform.pitch = to_degrees(pitch_rad);
        transform.roll = turn * 2.0;
    }
};

} // namespace

std::unique_ptr<IControlModel> make_default_control_model() {
    return std::make_unique<DefaultControlModel>();
}
