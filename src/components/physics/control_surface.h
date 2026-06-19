#pragma once

#include <algorithm>

// ControlSurfaceState
//
// Physical intermediary between the flight-control law (FBW/SAS) and the
// aerodynamic moment model. The control law writes normalized surface
// *commands* (`*_cmd`, in [-1, 1]); the actuator system advances the actual
// surface *positions* (`*_pos`, in [-1, 1]) toward those commands subject to
// first-order actuator lag and finite travel. The aerodynamics system then
// converts actual positions into control moments via control-effectiveness
// derivatives, so control authority scales naturally with dynamic pressure and
// Mach instead of being synthesized as a raw rate-command torque.
//
// Sign conventions (normalized, before mapping to physical deflection):
// - elevator_cmd/pos > 0 commands nose-up pitch (positive pitch moment).
// - aileron_cmd/pos  > 0 commands right roll.
// - rudder_cmd/pos   > 0 commands the sim's positive yaw moment
//   (which corresponds to a left/decreasing-heading turn; the control law owns
//   the PilotAction.rudder -> internal-sign mapping).
//
// Positions are normalized; the aerodynamics tuning owns the per-axis maximum
// physical deflection used to scale the control derivatives. Keeping the state
// normalized lets the actuator model stay airframe-agnostic while the tuning
// carries the platform-specific travel and effectiveness.
struct ControlSurfaceState {
    double elevator_cmd = 0.0;
    double aileron_cmd = 0.0;
    double rudder_cmd = 0.0;

    double elevator_pos = 0.0;
    double aileron_pos = 0.0;
    double rudder_pos = 0.0;

    void clamp_positions() {
        elevator_pos = std::clamp(elevator_pos, -1.0, 1.0);
        aileron_pos = std::clamp(aileron_pos, -1.0, 1.0);
        rudder_pos = std::clamp(rudder_pos, -1.0, 1.0);
    }
};
