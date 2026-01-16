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

        constexpr double kGravity = 9.80665;
        double current_speed = std::sqrt(velocity.vx * velocity.vx +
                                         velocity.vy * velocity.vy +
                                         velocity.vz * velocity.vz);

        double current_heading_nav = transform.heading;
        if (current_speed > 1e-3) {
            double current_heading_math = std::atan2(velocity.vy, velocity.vx);
            current_heading_nav = 90.0 - to_degrees(current_heading_math);
            current_heading_nav = normalize_angle(current_heading_nav);
        }

        double heading_error = normalize_angle(command.target_heading - current_heading_nav);
        double max_turn_rate = flight_model.max_turn_rate;
        if (current_speed > 1.0 && flight_model.max_g > 1.0) {
            double max_turn_rate_g = kGravity *
                                     std::sqrt(flight_model.max_g * flight_model.max_g - 1.0) /
                                     current_speed;
            max_turn_rate = std::min(max_turn_rate, to_degrees(max_turn_rate_g));
        }
        double max_turn_step = max_turn_rate * dt;
        double turn_step = std::clamp(heading_error, -max_turn_step, max_turn_step);
        double turn_rate_deg = (dt > 0.0) ? (turn_step / dt) : 0.0;
        double new_heading_nav = normalize_angle(current_heading_nav + turn_step);

        double turn_rate_rad = to_radians(turn_rate_deg);
        double bank_rad = 0.0;
        if (current_speed > 1.0 && std::abs(turn_rate_rad) > 1e-6) {
            bank_rad = std::atan2(current_speed * turn_rate_rad, kGravity);
        }
        double cos_bank = std::max(0.1, std::abs(std::cos(bank_rad)));
        double load_factor = 1.0 / cos_bank;
        double effective_min_speed = flight_model.min_speed * std::sqrt(load_factor);

        double alt_error = command.target_altitude - transform.z;
        const double climb_tau = 10.0;
        double desired_climb_rate = alt_error / climb_tau;
        double climb_rate = std::clamp(desired_climb_rate,
                                       -flight_model.max_climb_rate,
                                       flight_model.max_climb_rate);
        if (climb_rate > 0.0 && current_speed > 1.0) {
            double max_climb_rate_energy =
                current_speed * std::clamp(flight_model.max_accel / kGravity, 0.0, 1.0);
            climb_rate = std::min(climb_rate, max_climb_rate_energy);
        }

        double pitch_rad_energy = 0.0;
        if (current_speed > 1.0) {
            pitch_rad_energy =
                std::asin(std::clamp(climb_rate / current_speed, -0.99, 0.99));
        }

        double safe_target_speed = std::clamp(command.target_speed,
                                              effective_min_speed,
                                              flight_model.max_speed);
        double speed_error = safe_target_speed - current_speed;
        double max_accel_step = flight_model.max_accel * dt;
        double speed_step = std::clamp(speed_error, -max_accel_step, max_accel_step);
        double gravity_step = kGravity * std::sin(pitch_rad_energy) * dt;
        double new_speed = current_speed + speed_step - gravity_step;
        new_speed = std::clamp(new_speed, effective_min_speed, flight_model.max_speed);

        double pitch_rad = 0.0;
        if (new_speed > 1.0) {
            pitch_rad = std::asin(std::clamp(climb_rate / new_speed, -0.99, 0.99));
        }

        double h_speed = new_speed * std::cos(pitch_rad);
        double new_heading_math_rad = to_radians(90.0 - new_heading_nav);

        velocity.vx = h_speed * std::cos(new_heading_math_rad);
        velocity.vy = h_speed * std::sin(new_heading_math_rad);
        velocity.vz = new_speed * std::sin(pitch_rad);

        transform.heading = new_heading_nav;
        transform.pitch = to_degrees(pitch_rad);
        transform.roll = to_degrees(bank_rad);
    }
};

} // namespace

std::unique_ptr<IControlModel> make_default_control_model() {
    return std::make_unique<DefaultControlModel>();
}
