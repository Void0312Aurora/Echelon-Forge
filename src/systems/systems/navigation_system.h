#pragma once

#include <flecs.h>
#include <algorithm>
#include "components/basic/common.h"
#include "components/physics/dynamics.h"
#include "components/systems/navigation.h"
#include "core/interfaces/environment_model.h"

inline void register_navigation_system(flecs::world &ecs) {
    ecs.system<EGI, const Transform, const Velocity>("NavigationSystem")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter &it) {
            // The world's geodetic anchor (Geodetic Frame P3-B); the documented
            // default anchor applies when no environment is bound.
            const EnvironmentModelRef *env_ref = it.world().get<EnvironmentModelRef>();
            const IEnvironmentModel *env = env_ref ? env_ref->model : nullptr;
            while (it.next()) {
                auto egi = it.field<EGI>(0);
                auto trans = it.field<const Transform>(1);
                auto vel = it.field<const Velocity>(2);

                double dt = it.delta_time();

                for (auto i : it) {
                    // Training-oriented, deterministic navigation solution:
                    // treat EGI as truth-aligned (no stochastic drift).
                    egi[i].drift_lat_m = 0.0;
                    egi[i].drift_lon_m = 0.0;
                    egi[i].drift_alt_m = 0.0;

                    if (egi[i].gps_available) {
                        egi[i].time_since_last_gps_fix = 0.0;
                        egi[i].position_uncertainty_m =
                            std::min(egi[i].position_uncertainty_m, 5.0);
                    } else {
                        egi[i].time_since_last_gps_fix += dt;
                        egi[i].position_uncertainty_m =
                            std::max(egi[i].position_uncertainty_m, 50.0);
                    }

                    double nav_x = trans[i].x;
                    double nav_y = trans[i].y;
                    double nav_z = trans[i].z;

                    // Inverse azimuthal-equidistant projection about the anchor.
                    const geodesy::GeodeticPosition geo =
                        environment_local_to_geodetic(env, nav_x, nav_y, nav_z);
                    egi[i].lat_deg = geo.latitude_deg;
                    egi[i].lon_deg = geo.longitude_deg;

                    // Velocities (World ENU -> NED)
                    egi[i].vn_mps = vel[i].vy;  // Y is North
                    egi[i].ve_mps = vel[i].vx;  // X is East
                    egi[i].vd_mps = -vel[i].vz; // Z Up -> D Down

                    egi[i].alt_baro_m = nav_z;
                    egi[i].alt_radar_m = std::max(0.0, nav_z); // Flat-ground fallback

                    // Attitude
                    egi[i].heading_deg = trans[i].heading;
                    egi[i].pitch_deg = trans[i].pitch;
                    egi[i].roll_deg = trans[i].roll;

                    // Wrap Heading [0, 360)
                    while (egi[i].heading_deg < 0.0)
                        egi[i].heading_deg += 360.0;
                    while (egi[i].heading_deg >= 360.0)
                        egi[i].heading_deg -= 360.0;
                }
            }
        });
}
