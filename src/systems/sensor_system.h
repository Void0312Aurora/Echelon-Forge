#pragma once
#include <flecs.h>
#include <vector>
#include <cmath>
#include <algorithm>
#include "components/common.h"
#include "components/sensor.h"
#include "core/simulation_kernel.h" // For SimObject tag if needed, but safe to just use components usually

#include <spdlog/spdlog.h>

// Helper to normalize angle to [-180, 180]
inline double normalize_angle_deg(double angle) {
    while (angle > 180.0) angle -= 360.0;
    while (angle < -180.0) angle += 360.0;
    return angle;
}

void register_sensor_system(flecs::world& ecs) {
    // Create the target query ONCE outside the loop if possible
    // But inside run is cleaner for lambda capture.
    auto target_query = ecs.query<Transform, SimObject>();

    ecs.system<Transform, Sensor, ContactList>("SensorSystem")
        .run([=](flecs::iter& it) {
            while (it.next()) {
                auto t = it.field<Transform>(0);
                auto s = it.field<Sensor>(1);
                auto c = it.field<ContactList>(2);

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

                    int target_count = 0;
                    
                    // Iterate using the cached query
                    target_query.each([&](flecs::entity target_e, const Transform& target_t, const SimObject& /*tag*/) {
                        target_count++;
                        if (target_e == it.entity(i)) return; // Don't detect self

                        double dx = target_t.x - t[i].x;
                        double dy = target_t.y - t[i].y;
                        double dz = target_t.z - t[i].z;
                        double dist_sq = dx*dx + dy*dy + dz*dz;
                        double max_sq = s[i].max_range * s[i].max_range;

                        if (dist_sq <= max_sq) {
                            double dist = std::sqrt(dist_sq);
                            double bearing_rad = std::atan2(dy, dx); // ENU bearing (East=0, North=90)
                            double bearing_deg = bearing_rad * 180.0 / M_PI;
                            double rel_bearing = normalize_angle_deg(bearing_deg - t[i].heading);
                            
                            // Debug log
                            // spdlog::info("Target {} D:{:.0f} B:{:.0f}", target_e.id(), dist, rel_bearing);

                            if (std::abs(rel_bearing) <= s[i].fov_deg / 2.0) {
                                c[i].contacts.push_back({
                                    target_e.id(),
                                    dist,
                                    bearing_deg,
                                    current_time
                                });
                            }
                        }
                    });
                }
            }
        });
}
