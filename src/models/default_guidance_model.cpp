#include "core/guidance_model.h"

#include <algorithm>
#include <cmath>

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
                flecs::entity /*missile_entity*/,
                Velocity& velocity,
                const Transform& transform,
                Missile& missile,
                double dt) override {
        if (!missile.active) return;

        auto target_entity = world.entity(missile.target_id);
        if (!target_entity.is_valid()) {
            return;
        }

        const Transform* t_pos = target_entity.get<Transform>();
        const Velocity* t_vel = target_entity.get<Velocity>();
        if (!t_pos || !t_vel) return;

        const ecs_world_info_t* info = ecs_get_world_info(world.c_ptr());
        double current_time = info ? (double)info->world_time_total : 0.0;
        if (missile.launch_time <= 0.0) {
            missile.launch_time = current_time;
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

        double dx = t_pos->x - transform.x;
        double dy = t_pos->y - transform.y;
        double dist_sq = dx * dx + dy * dy;
        if (dist_sq < 1e-6) return;
        double dist = std::sqrt(dist_sq);
        if (missile.seeker_lock_range > 0.0 && dist > missile.seeker_lock_range) {
            return;
        }

        double bearing_math_deg = std::atan2(dy, dx) * 180.0 / M_PI;
        double bearing_nav_deg = math_deg_to_nav_deg(bearing_math_deg);
        double rel_bearing = normalize_angle_deg(bearing_nav_deg - transform.heading);
        if (missile.seeker_fov_deg > 0.0 &&
            std::abs(rel_bearing) > missile.seeker_fov_deg * 0.5) {
            return;
        }

        double rel_vx = t_vel->vx - velocity.vx;
        double rel_vy = t_vel->vy - velocity.vy;
        double los_rate = (dx * rel_vy - dy * rel_vx) / dist_sq;
        double nav_gain = (missile.nav_gain > 0.0) ? missile.nav_gain : 3.0;
        double desired_turn_rate = nav_gain * los_rate;

        double max_turn_rate = to_radians(missile.turn_rate);
        desired_turn_rate = std::clamp(desired_turn_rate, -max_turn_rate, max_turn_rate);

        double curr_heading_rad = std::atan2(velocity.vy, velocity.vx);
        double new_heading = curr_heading_rad + desired_turn_rate * dt;
        double speed = missile.max_speed;
        velocity.vx = speed * std::cos(new_heading);
        velocity.vy = speed * std::sin(new_heading);
    }
};

} // namespace

std::unique_ptr<IGuidanceModel> make_default_guidance_model() {
    return std::make_unique<DefaultGuidanceModel>();
}
