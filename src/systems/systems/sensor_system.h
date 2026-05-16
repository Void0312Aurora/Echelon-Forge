#pragma once
#include <flecs.h>
#include <vector>
#include <cmath>
#include <algorithm>
#include <unordered_map>
#include <unordered_set>
#include "components/basic/common.h"
#include "components/systems/sensor.h"
#include "components/basic/tags.h"
#include "core/interfaces/sensor_model.h"

#include <spdlog/spdlog.h>

inline bool prefer_detection_over_existing(const Detection& candidate, const Detection& existing) {
    const bool candidate_has_range = candidate.range > 1.0;
    const bool existing_has_range = existing.range > 1.0;
    if (candidate_has_range != existing_has_range) {
        return candidate_has_range;
    }
    if (candidate.sensor_type != existing.sensor_type) {
        if (candidate.sensor_type == static_cast<int>(SensorType::Radar)) return true;
        if (existing.sensor_type == static_cast<int>(SensorType::Radar)) return false;
    }
    if (std::abs(candidate.signal_strength - existing.signal_strength) > 1.0e-9) {
        return candidate.signal_strength > existing.signal_strength;
    }
    return candidate.timestamp >= existing.timestamp;
}

void register_sensor_system(flecs::world& ecs) {
    ecs.system<Transform, ContactList>("SensorSystem")
        .kind(flecs::OnUpdate)
        .run([=](flecs::iter& it) {
            while (it.next()) {
                auto t = it.field<Transform>(0);
                auto c = it.field<ContactList>(1);
                const SensorModelRef* model_ref = it.world().get<SensorModelRef>();

                // Use world_time_total via C API if C++ wrapper misses it
                const ecs_world_info_t* info = ecs_get_world_info(it.world().c_ptr());
                double current_time = info ? (double)info->world_time_total : 0.0;

                for (auto i : it) {
                    flecs::entity entity = it.entity(i);
                    Sensor* inline_sensor = entity.get_mut<Sensor>();
                    MountedSensors* mounted_sensors = entity.get_mut<MountedSensors>();
                    const bool has_inline_sensor = inline_sensor != nullptr;
                    const bool has_mounted_sensors =
                        mounted_sensors != nullptr && !mounted_sensors->mounts.empty();
                    if (!has_inline_sensor && !has_mounted_sensors) {
                        continue;
                    }

                    double max_track_memory_s = 0.0;
                    if (has_inline_sensor) {
                        max_track_memory_s = std::max(max_track_memory_s, inline_sensor->track_memory_s);
                    }
                    if (has_mounted_sensors) {
                        for (const auto& mount : mounted_sensors->mounts) {
                            max_track_memory_s = std::max(max_track_memory_s, mount.sensor.track_memory_s);
                        }
                    }

                    std::vector<Detection> previous_contacts = c[i].contacts;

                    if (!model_ref || !model_ref->model) {
                        spdlog::warn("Sensor model not configured; skipping scan.");
                        continue;
                    }

                    std::vector<Detection> fresh_contacts;
                    bool any_sensor_scanned = false;

                    auto scan_one_sensor = [&](Sensor& sensor_state) {
                        const double time_since_last = current_time - sensor_state.last_scan_time;
                        const bool first_scan_ready = sensor_state.last_scan_time < 0.0;
                        if (!first_scan_ready && time_since_last < sensor_state.scan_period) {
                            return;
                        }

                        sensor_state.last_scan_time = current_time;
                        ContactList sensor_contacts;
                        model_ref->model->scan(
                            it.world(),
                            entity,
                            t[i],
                            sensor_state,
                            sensor_contacts,
                            current_time
                        );
                        any_sensor_scanned = true;
                        for (const auto& det : sensor_contacts.contacts) {
                            auto existing_it = std::find_if(
                                fresh_contacts.begin(),
                                fresh_contacts.end(),
                                [&](const Detection& existing) {
                                    return existing.target_id == det.target_id;
                                }
                            );
                            if (existing_it == fresh_contacts.end()) {
                                fresh_contacts.push_back(det);
                            } else if (prefer_detection_over_existing(det, *existing_it)) {
                                *existing_it = det;
                            }
                        }
                    };

                    if (has_inline_sensor) {
                        scan_one_sensor(*inline_sensor);
                    }
                    if (has_mounted_sensors) {
                        for (auto& mount : mounted_sensors->mounts) {
                            scan_one_sensor(mount.sensor);
                        }
                    }

                    if (!any_sensor_scanned) {
                        if (max_track_memory_s > 0.0 && !c[i].contacts.empty()) {
                            auto& contacts = c[i].contacts;
                            contacts.erase(
                                std::remove_if(
                                    contacts.begin(),
                                    contacts.end(),
                                    [&](const Detection& det) {
                                        return (current_time - det.timestamp) > max_track_memory_s;
                                    }
                                ),
                                contacts.end()
                            );
                        }
                        continue;
                    }

                    std::unordered_set<uint64_t> seen;
                    std::vector<Detection> merged;
                    merged.reserve(fresh_contacts.size() + previous_contacts.size());
                    for (const auto& det : fresh_contacts) {
                        merged.push_back(det);
                        seen.insert(det.target_id);
                    }
                    if (max_track_memory_s > 0.0) {
                        for (const auto& det : previous_contacts) {
                            if (seen.find(det.target_id) != seen.end()) continue;
                            if ((current_time - det.timestamp) <= max_track_memory_s) {
                                merged.push_back(det);
                            }
                        }
                    }
                    c[i].contacts.swap(merged);
                }
            }
        });
}
