#pragma once

#include <algorithm>
#include <unordered_set>
#include <vector>

#include <flecs.h>

#include "components/systems/sensor.h"
#include "components/systems/sonar.h"
#include "core/interfaces/acoustic_model.h"

inline void register_sonar_system(flecs::world& ecs) {
    ecs.system<ContactList>("SonarSystem")
        .kind(flecs::OnUpdate)
        .run([=](flecs::iter& it) {
            const AcousticModelRef* model_ref = it.world().get<AcousticModelRef>();
            if (!model_ref || !model_ref->model) {
                return;
            }
            const ecs_world_info_t* info = ecs_get_world_info(it.world().c_ptr());
            const double current_time = info ? static_cast<double>(info->world_time_total) : 0.0;

            while (it.next()) {
                auto contacts = it.field<ContactList>(0);
                for (auto i : it) {
                    flecs::entity entity = it.entity(i);
                    const Transform* transform = entity.get<Transform>();
                    if (!transform) {
                        continue;
                    }

                    Sonar* inline_sonar = entity.get_mut<Sonar>();
                    MountedSonars* mounted_sonars = entity.get_mut<MountedSonars>();
                    const bool has_inline = inline_sonar != nullptr;
                    const bool has_mounted = mounted_sonars != nullptr && !mounted_sonars->mounts.empty();
                    if (!has_inline && !has_mounted) {
                        continue;
                    }

                    std::vector<Detection> sonar_hits;
                    auto scan_one = [&](Sonar& sonar_state) {
                        const double elapsed = current_time - sonar_state.last_scan_time_s;
                        if (sonar_state.last_scan_time_s >= 0.0 && elapsed < sonar_state.scan_period_s) {
                            return;
                        }
                        sonar_state.last_scan_time_s = current_time;
                        ContactList local{};
                        model_ref->model->scan(it.world(), entity, *transform, sonar_state, local, current_time);
                        for (const auto& det : local.contacts) {
                            sonar_hits.push_back(det);
                        }
                    };

                    if (has_inline) {
                        scan_one(*inline_sonar);
                    }
                    if (has_mounted) {
                        for (auto& mount : mounted_sonars->mounts) {
                            scan_one(mount.sonar);
                        }
                    }

                    std::unordered_set<std::uint64_t> replaced;
                    for (const auto& det : sonar_hits) {
                        auto existing = std::find_if(
                            contacts[i].contacts.begin(),
                            contacts[i].contacts.end(),
                            [&](const Detection& current) { return current.target_id == det.target_id; }
                        );
                        if (existing == contacts[i].contacts.end()) {
                            contacts[i].contacts.push_back(det);
                        } else if (existing->range <= 0.0 && det.range > 0.0) {
                            *existing = det;
                        } else if (existing->sensor_type != static_cast<int>(SensorType::Radar)) {
                            *existing = det;
                        }
                        replaced.insert(det.target_id);
                    }

                    double max_memory = 0.0;
                    if (has_inline) {
                        max_memory = std::max(max_memory, inline_sonar->track_memory_s);
                    }
                    if (has_mounted) {
                        for (const auto& mount : mounted_sonars->mounts) {
                            max_memory = std::max(max_memory, mount.sonar.track_memory_s);
                        }
                    }
                    if (max_memory > 0.0) {
                        auto& merged = contacts[i].contacts;
                        merged.erase(
                            std::remove_if(
                                merged.begin(),
                                merged.end(),
                                [&](const Detection& det) {
                                    if (det.sensor_type != static_cast<int>(SensorType::Sonar)) {
                                        return false;
                                    }
                                    if (replaced.find(det.target_id) != replaced.end()) {
                                        return false;
                                    }
                                    return (current_time - det.timestamp) > max_memory;
                                }
                            ),
                            merged.end()
                        );
                    }
                }
            }
        });
}
