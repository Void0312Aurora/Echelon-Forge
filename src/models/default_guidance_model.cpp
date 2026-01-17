#include "core/guidance_model.h"

#include <algorithm>
#include <cmath>

#include "components/sensor.h"

namespace {

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

double to_radians(double deg) { return deg * M_PI / 180.0; }

double wrap_angle_360(double angle) {
    while (angle < 0.0) angle += 360.0;
    while (angle >= 360.0) angle -= 360.0;
    return angle;
}

double normalize_angle_deg(double angle) {
    while (angle > 180.0) angle -= 360.0;
    while (angle < -180.0) angle += 360.0;
    return angle;
}

double math_deg_to_nav_deg(double math_deg) {
    return wrap_angle_360(90.0 - math_deg);
}

class DefaultGuidanceModel : public IGuidanceModel {
public:
    void update(flecs::world world,
                flecs::entity missile_entity,
                Velocity& velocity,
                const Transform& transform,
                Missile& missile,
                double dt) override {
        if (!missile.active) return;

        const ecs_world_info_t* info = ecs_get_world_info(world.c_ptr());
        double current_time = info ? (double)info->world_time_total : 0.0;
        if (missile.launch_time <= 0.0) {
            missile.launch_time = current_time;
        }
        if (missile.max_flight_time_s > 0.0 &&
            (current_time - missile.launch_time) > missile.max_flight_time_s) {
            missile.active = false;
            missile_entity.destruct();
            return;
        }
        if (current_time - missile.launch_time < missile.guidance_delay_s) {
            return;
        }
        if (missile.guidance_update_period_s > 0.0) {
            if (current_time - missile.last_guidance_time < missile.guidance_update_period_s) {
                return;
            }
        }
        missile.last_guidance_time = current_time;

        // Use seeker track only (no access to target truth here).
        const ContactList* contacts = missile_entity.get<ContactList>();
        if (!contacts) {
            return;
        }
        const Detection* det = nullptr;
        for (const auto& c : contacts->contacts) {
            if (c.target_id == missile.target_id) {
                det = &c;
                break;
            }
        }
        if (!det) {
            return;
        }

        double dist = det->range;
        if (missile.seeker_lock_range > 0.0 && dist > missile.seeker_lock_range) {
            return;
        }
        double rel_bearing = det->bearing;
        if (missile.seeker_fov_deg > 0.0 &&
            std::abs(rel_bearing) > missile.seeker_fov_deg * 0.5) {
            return;
        }

        double max_turn_deg = std::abs(missile.turn_rate) * dt;
        double heading_step_deg = std::clamp(rel_bearing, -max_turn_deg, max_turn_deg);
        double new_nav_heading = wrap_angle_360(transform.heading + heading_step_deg);
        double new_math_deg = 90.0 - new_nav_heading;
        double new_heading = to_radians(new_math_deg);

        double speed = missile.max_speed;
        velocity.vx = speed * std::cos(new_heading);
        velocity.vy = speed * std::sin(new_heading);
    }
};

} // namespace

std::unique_ptr<IGuidanceModel> make_default_guidance_model() {
    return std::make_unique<DefaultGuidanceModel>();
}
