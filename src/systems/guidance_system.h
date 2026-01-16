#pragma once

#include <flecs.h>
#include <cmath>
#include "components/common.h"
#include "components/weapon.h"
#include "systems/control_system.h" // For math helpers

inline void register_guidance_system(flecs::world& ecs) {
    ecs.system<Velocity, const Transform, const Missile>("MissileGuidance")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto v = it.field<Velocity>(0);
                auto p = it.field<const Transform>(1);
                auto missile_comp = it.field<const Missile>(2);
                
                double dt = it.delta_time();

                for (auto i : it) {
                    if (!missile_comp[i].active) continue;

                    // 1. Get Target Info
                    auto target_entity = it.world().entity(missile_comp[i].target_id);
                    if (!target_entity.is_valid()) {
                        // Target lost/destroyed -> Self Destruct or coast
                        continue; 
                    }
                    
                    const Transform* t_pos = target_entity.get<Transform>();
                    const Velocity* t_vel = target_entity.get<Velocity>();
                    
                    if (!t_pos || !t_vel) continue;

                    // 2. Lead Pursuit Guidance (Simplified PN)
                    // Calculate Time to Go (approx)
                    double dx = t_pos->x - p[i].x;
                    double dy = t_pos->y - p[i].y;
                    double dist = std::sqrt(dx*dx + dy*dy);
                    double closing_speed = missile_comp[i].max_speed; // Assume max speed for simplification
                    double tgo = dist / closing_speed;
                    
                    // Predict Target Position
                    double pred_x = t_pos->x + t_vel->vx * tgo;
                    double pred_y = t_pos->y + t_vel->vy * tgo;
                    
                    // Desired Heading to Predicted Point
                    double aim_dx = pred_x - p[i].x;
                    double aim_dy = pred_y - p[i].y;
                    double curr_heading_rad = std::atan2(v[i].vy, v[i].vx);
                    double desired_heading_rad = std::atan2(aim_dy, aim_dx);
                    
                    // Proportional Control on Heading (Turn Rate Limit)
                    double error = desired_heading_rad - curr_heading_rad;
                    
                    // Normalize -PI to PI
                    while (error > M_PI) error -= 2 * M_PI;
                    while (error < -M_PI) error += 2 * M_PI;
                    
                    // Clamp Turn
                    double max_turn_rad = to_radians(missile_comp[i].turn_rate) * dt;
                    double turn = std::clamp(error, -max_turn_rad, max_turn_rad);
                    
                    double new_heading = curr_heading_rad + turn;
                    
                    // Update Velocity (Sustain max speed)
                    v[i].vx = missile_comp[i].max_speed * std::cos(new_heading);
                    v[i].vy = missile_comp[i].max_speed * std::sin(new_heading);
                }
            }
        });
}
