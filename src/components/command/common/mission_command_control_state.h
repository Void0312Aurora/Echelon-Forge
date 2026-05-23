#pragma once

#include "components/command/common/mission_command_core.h"

struct MissionCommandTypedAirControlState {
    double throttle_command = 0.0;
    double brake_amount = 0.0;
    double nose_wheel_yaw_command = 0.0;

    float flaps_pos = 0.0f;
    float speedbrake_pos = 0.0f;

    bool throttle_active = false;
    bool throttle_idle = false;
    bool ground_active = false;
    bool instrument_active = false;
    bool nose_wheel_steering_active = false;
    bool manual_input_active = false;
    bool action_semantics_active = false;
    bool master_arm = false;

    int weapon_selected = 0;
};

struct MissionCommandControlState {
    double target_heading_deg = 0.0;
    double target_altitude_m = 0.0;
    double target_speed_mps = 0.0;

    double lagged_heading_deg = 0.0;
    double lagged_altitude_m = 0.0;
    double lagged_speed_mps = 0.0;

    bool active = false;
    bool lagged_active = false;

    // Minimal typed ownership seam for air-control semantics that still need
    // compatibility projection out of legacy MovementCommand/ActionCommand.
    MissionCommandTypedAirControlState typed_air_control{};
};

inline MissionCommandControlState make_mission_command_control_state(
    double heading_deg,
    double speed_mps,
    double altitude_m,
    bool active = true
) {
    MissionCommandControlState state{};
    state.target_heading_deg = heading_deg;
    state.target_altitude_m = altitude_m;
    state.target_speed_mps = speed_mps;
    state.lagged_heading_deg = heading_deg;
    state.lagged_altitude_m = altitude_m;
    state.lagged_speed_mps = speed_mps;
    state.active = active;
    state.lagged_active = active;
    return state;
}

inline MissionCommandControlState make_mission_command_control_state(
    const MissionCommandCore& core,
    bool active
) {
    return make_mission_command_control_state(
        core.cmd_heading_deg,
        core.cmd_speed_mps,
        core.cmd_altitude_m,
        active
    );
}

inline MissionCommandControlState make_mission_command_control_state(
    const MissionCommandCore& core
) {
    return make_mission_command_control_state(core, core.active);
}

inline void set_mission_command_control_target(
    MissionCommandControlState& state,
    double heading_deg,
    double speed_mps,
    double altitude_m,
    bool active = true
) {
    state.target_heading_deg = heading_deg;
    state.target_speed_mps = speed_mps;
    state.target_altitude_m = altitude_m;
    state.active = active;
}

inline void set_mission_command_control_target(
    MissionCommandControlState& state,
    const MissionCommandCore& core,
    bool active
) {
    set_mission_command_control_target(
        state,
        core.cmd_heading_deg,
        core.cmd_speed_mps,
        core.cmd_altitude_m,
        active
    );
}

inline void set_mission_command_control_lagged(
    MissionCommandControlState& state,
    double heading_deg,
    double speed_mps,
    double altitude_m,
    bool active = true
) {
    state.lagged_heading_deg = heading_deg;
    state.lagged_speed_mps = speed_mps;
    state.lagged_altitude_m = altitude_m;
    state.lagged_active = active;
}

inline bool mission_command_typed_air_control_active(
    const MissionCommandTypedAirControlState& typed_air_control
) {
    return typed_air_control.throttle_active ||
        typed_air_control.ground_active ||
        typed_air_control.instrument_active ||
        typed_air_control.nose_wheel_steering_active ||
        typed_air_control.manual_input_active ||
        typed_air_control.action_semantics_active;
}

inline void reset_mission_command_typed_air_control_state(
    MissionCommandControlState& state
) {
    state.typed_air_control = MissionCommandTypedAirControlState{};
}

inline void set_mission_command_typed_air_control_state(
    MissionCommandControlState& state,
    const MissionCommandTypedAirControlState& typed_air_control
) {
    state.typed_air_control = typed_air_control;
}
