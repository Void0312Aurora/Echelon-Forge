#pragma once

#include <flecs.h>
#include <spdlog/spdlog.h>
#include "components/basic/common.h"
#include "components/physics/action.h"
#include "components/physics/performance.h"
#include "core/interfaces/control_model.h"

inline void register_control_system(flecs::world& ecs) {
    ecs.system<Velocity, Transform, const LaggedCommand, const FlightModel>("FlightControl")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto v = it.field<Velocity>(0);
                auto p = it.field<Transform>(1);
                auto cmd = it.field<const LaggedCommand>(2);
                auto fm = it.field<const FlightModel>(3);
                const ControlModelRef* model_ref = it.world().get<ControlModelRef>();
                double dt = it.delta_time();
                
                for (auto i : it) {
                    if (!model_ref || !model_ref->model) {
                        spdlog::warn("Control model not configured; skipping control update.");
                        continue;
                    }

                    MovementCommand lagged_cmd{
                        cmd[i].target_heading,
                        cmd[i].target_speed,
                        cmd[i].target_altitude,
                        cmd[i].active
                    };
                    model_ref->model->update(it.world(),
                                             it.entity(i),
                                             v[i],
                                             p[i],
                                             lagged_cmd,
                                             fm[i],
                                             dt);
                }
            }
        });
}
