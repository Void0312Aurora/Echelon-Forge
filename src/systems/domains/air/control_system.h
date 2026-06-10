#pragma once

#include <flecs.h>
#include <spdlog/spdlog.h>
#include <iostream>
#include "components/basic/common.h"
#include "components/command/command_link.h"
#include "components/command/common/mission_command_control_state.h"
#include "components/physics/performance.h"
#include "core/interfaces/control_model.h"
#include "core/interfaces/environment_model.h"

inline void register_control_system(flecs::world &ecs) {
    ecs.system<Velocity, Transform, const MissionCommandControlState, const FlightModel>(
           "FlightControl")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter &it) {
            while (it.next()) {
                auto v = it.field<Velocity>(0);
                auto p = it.field<Transform>(1);
                auto control_state = it.field<const MissionCommandControlState>(2);
                auto fm = it.field<const FlightModel>(3);

                const ControlModelRef *model_ref = it.world().get<ControlModelRef>();
                const EnvironmentModelRef *env_ref = it.world().get<EnvironmentModelRef>();
                double dt = it.delta_time();

                for (auto i : it) {
                    if (!model_ref || !model_ref->model) {
                        continue;
                    }
                    (void)control_state;

                    // We now just pass the entity. The model is responsible for fetching
                    // PilotAction/MissionCommand.
                    model_ref->model->update(it.world(), it.entity(i), v[i], p[i], fm[i], dt,
                                             env_ref ? env_ref->model : nullptr);
                }
            }
        });
}
