#pragma once

// Persistent state for control laws (SAS/FBW) that need memory across frames.
// This lives in the simulation ECS so the control model can apply realistic
// filtering/rate limiting without relying on any external (god) information.
struct ControlLawState {
    double stick_roll_filt = 0.0;
    double stick_pitch_filt = 0.0;
    double stick_yaw_filt = 0.0;
    double stick_yaw_cmd = 0.0;
};
