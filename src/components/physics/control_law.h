#pragma once

// Persistent state for control laws (SAS/FBW) that need memory across frames.
// This lives in the simulation ECS so the control model can apply realistic
// filtering/rate limiting without relying on any external (god) information.
struct ControlLawState {
    double stick_roll_filt = 0.0;
    double stick_pitch_filt = 0.0;
    double stick_yaw_filt = 0.0;
    double stick_yaw_cmd = 0.0;

    // Diagnostics-only mirror of the most recent pitch g-command outer loop.
    // These let a probe read the actual internal values (instead of inferring
    // them from downstream motion) so loop sign/gain issues can be isolated
    // decisively rather than by reasoning about sign conventions. Not used by
    // any control logic; safe to ignore outside diagnostics.
    double dbg_g_cmd = 0.0;
    double dbg_measured_nz = 0.0;
    double dbg_q_cmd = 0.0;
    // Final pitch-rate command actually fed to the elevator inner loop, after
    // all ground/airborne attitude and AoA protections have been applied.
    double dbg_q_cmd_final = 0.0;
    double dbg_elevator_cmd = 0.0;
    double dbg_g_branch_active = 0.0;
};
