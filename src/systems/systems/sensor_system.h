#pragma once
#include <flecs.h>
#include <vector>
#include <cmath>
#include <algorithm>
#include <unordered_set>
#include "components/basic/common.h"
#include "components/systems/sensor.h"
#include "components/basic/tags.h"
#include "core/interfaces/sensor_model.h"

#include <spdlog/spdlog.h>

void register_sensor_system(flecs::world& ecs) {
    ecs.system<Transform, Sensor, ContactList>("SensorSystem")
        .kind(flecs::OnUpdate)
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
                        if (s[i].track_memory_s > 0.0 && !c[i].contacts.empty()) {
                            auto& contacts = c[i].contacts;
                            contacts.erase(
                                std::remove_if(contacts.begin(),
                                               contacts.end(),
                                               [&](const Detection& det) {
                                                   return (current_time - det.timestamp) >
                                                          s[i].track_memory_s;
                                               }),
                                contacts.end());
                        }
                        continue; 
                    }
                    s[i].last_scan_time = current_time;
                    std::vector<Detection> previous_contacts = c[i].contacts;

                    if (!model_ref || !model_ref->model) {
                        spdlog::warn("Sensor model not configured; skipping scan.");
                        continue;
                    }

                    ContactList fresh_contacts;
                    model_ref->model->scan(it.world(),
                                           it.entity(i),
                                           t[i],
                                           s[i],
                                           fresh_contacts,
                                           current_time);

                    std::unordered_set<uint64_t> seen;
                    std::vector<Detection> merged;
                    merged.reserve(fresh_contacts.contacts.size() + previous_contacts.size());
                    for (const auto& det : fresh_contacts.contacts) {
                        merged.push_back(det);
                        seen.insert(det.target_id);
                    }
                    if (s[i].track_memory_s > 0.0) {
                        for (const auto& det : previous_contacts) {
                            if (seen.find(det.target_id) != seen.end()) continue;
                            if ((current_time - det.timestamp) <= s[i].track_memory_s) {
                                merged.push_back(det);
                            }
                        }
                    }
                    c[i].contacts.swap(merged);
                }
            }
        });
}
