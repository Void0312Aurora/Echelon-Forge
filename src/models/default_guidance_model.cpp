#include "core/guidance_model.h"

#include <algorithm>
#include <cmath>

namespace {

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

double to_radians(double deg) { return deg * M_PI / 180.0; }

class DefaultGuidanceModel : public IGuidanceModel {
public:
    void update(flecs::world world,
                flecs::entity /*missile_entity*/,
                Velocity& velocity,
                const Transform& transform,
                const Missile& missile,
                double dt) override {
        if (!missile.active) return;

        auto target_entity = world.entity(missile.target_id);
        if (!target_entity.is_valid()) {
            return;
        }

        const Transform* t_pos = target_entity.get<Transform>();
        const Velocity* t_vel = target_entity.get<Velocity>();
        if (!t_pos || !t_vel) return;

        double dx = t_pos->x - transform.x;
        double dy = t_pos->y - transform.y;
        double dist = std::sqrt(dx * dx + dy * dy);
        double closing_speed = missile.max_speed;
        double tgo = dist / closing_speed;

        double pred_x = t_pos->x + t_vel->vx * tgo;
        double pred_y = t_pos->y + t_vel->vy * tgo;

        double aim_dx = pred_x - transform.x;
        double aim_dy = pred_y - transform.y;
        double curr_heading_rad = std::atan2(velocity.vy, velocity.vx);
        double desired_heading_rad = std::atan2(aim_dy, aim_dx);

        double error = desired_heading_rad - curr_heading_rad;
        while (error > M_PI) error -= 2 * M_PI;
        while (error < -M_PI) error += 2 * M_PI;

        double max_turn_rad = to_radians(missile.turn_rate) * dt;
        double turn = std::clamp(error, -max_turn_rad, max_turn_rad);

        double new_heading = curr_heading_rad + turn;
        velocity.vx = missile.max_speed * std::cos(new_heading);
        velocity.vy = missile.max_speed * std::sin(new_heading);
    }
};

} // namespace

std::unique_ptr<IGuidanceModel> make_default_guidance_model() {
    return std::make_unique<DefaultGuidanceModel>();
}
