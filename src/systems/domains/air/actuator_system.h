#pragma once

#include <algorithm>
#include <cmath>

#include <flecs.h>

#include "components/basic/common.h"
#include "components/domains/air/combat/damage_air.h"
#include "components/domains/air/platform/flight_dynamics_tuning.h"
#include "components/physics/control_surface.h"

namespace flight_dynamics {

// ActuatorSystem
//
// Physical intermediary between the flight-control law and the aerodynamic
// moment model. The control law writes normalized surface commands
// (ControlSurfaceState::*_cmd in [-1, 1]); this system advances the actual
// surface positions (*_pos) toward those commands with first-order actuator
// lag and finite travel. The aerodynamics system then converts the actual
// positions into control moments.
//
// Running surface dynamics here (rather than folding them into the control law
// or the aero step) keeps a single owner for actuator behavior and makes the
// "command vs. realized deflection" distinction observable for diagnostics.
inline double actuator_first_order_step(double pos, double cmd, double dt, double tau_s) {
    if (!std::isfinite(pos)) {
        pos = 0.0;
    }
    if (!std::isfinite(cmd)) {
        return pos;
    }
    if (tau_s <= 1.0e-6 || dt <= 0.0) {
        return cmd;
    }
    const double gain = std::clamp(dt / (tau_s + dt), 0.0, 1.0);
    return pos + gain * (cmd - pos);
}

inline void register_actuator_system(flecs::world &ecs) {
    ecs.system<ControlSurfaceState>("AdvanceControlSurfaces")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter &it) {
            double dt = it.delta_time();
            if (dt <= 0.0) {
                dt = 0.05;
            }
            while (it.next()) {
                auto surfaces = it.field<ControlSurfaceState>(0);
                for (auto i : it) {
                    const flecs::entity entity = it.entity(i);
                    const AeroTuning *attached = entity.get<AeroTuning>();
                    const AeroTuning &tuning =
                        (attached && attached->enabled) ? *attached : default_aero_tuning();

                    ControlSurfaceState &s = surfaces[i];
                    s.elevator_cmd = std::clamp(s.elevator_cmd, -1.0, 1.0);
                    s.aileron_cmd = std::clamp(s.aileron_cmd, -1.0, 1.0);
                    s.rudder_cmd = std::clamp(s.rudder_cmd, -1.0, 1.0);

                    s.elevator_pos = actuator_first_order_step(s.elevator_pos, s.elevator_cmd, dt,
                                                               tuning.actuator_tau_elevator_s);
                    s.aileron_pos = actuator_first_order_step(s.aileron_pos, s.aileron_cmd, dt,
                                                              tuning.actuator_tau_aileron_s);
                    s.rudder_pos = actuator_first_order_step(s.rudder_pos, s.rudder_cmd, dt,
                                                             tuning.actuator_tau_rudder_s);
                    s.clamp_positions();
                }
            }
        });
}

} // namespace flight_dynamics
