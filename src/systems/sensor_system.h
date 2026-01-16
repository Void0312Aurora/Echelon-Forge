#pragma once
#include <flecs.h>
#include <vector>
#include <cmath>
#include <algorithm>
#include "components/common.h"
#include "components/sensor.h"
#include "components/tags.h"
#include "core/sensor_model.h"

#include <spdlog/spdlog.h>

void register_sensor_system(flecs::world& ecs) {
    ecs.system<Transform, Sensor, ContactList>("SensorSystem")
        .run([=](flecs::iter& it) {
            while (it.next()) {
                auto t = it.field<Transform>(0);
                auto s = it.field<Sensor>(1);
                auto c = it.field<ContactList>(2);
                const SensorModelRef* model_ref = it.world().get<SensorModelRef>();

                // Use world_time_total via C API if C++ wrapper misses it
                const ecs_world_info_t* info = ecs_get_world_info(it.world().c_ptr());
                double current_time = info ? (double)info->world_time_total : 0.0;

                for (auto i : it) {
                    double time_since_last = current_time - s[i].last_scan_time;
                    if (time_since_last < s[i].scan_period) {
                        continue; 
                    }
                    s[i].last_scan_time = current_time;
                    c[i].contacts.clear();

                    if (!model_ref || !model_ref->model) {
                        spdlog::warn("Sensor model not configured; skipping scan.");
                        continue;
                    }

                    model_ref->model->scan(it.world(),
                                           it.entity(i),
                                           t[i],
                                           s[i],
                                           c[i],
                                           current_time);
                }
            }
        });
}
