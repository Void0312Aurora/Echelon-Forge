#pragma once

#include <algorithm>

#include "components/command/common/mission_command_control_state.h"
#include "components/command/legacy_command.h"
#include "components/command/pilot_action.h"

// Bridge-owned compatibility seam for maintained air-control consumers.
// New maintained systems should resolve legacy fallback through this header
// instead of re-implementing MovementCommand/ActionCommand probing inline.
struct ResolvedAirCommandInputSources {
    const PilotAction *pilot = nullptr;
    const MissionCommandControlState *control_state = nullptr;
    const MovementCommand *legacy_movement = nullptr;
    const ActionCommand *legacy_action = nullptr;
};

struct ResolvedGroundControlInput {
    bool throttle_idle = false;
    double brake_amount = 0.0;
};

struct ResolvedAirInstrumentControlInput {
    float flaps_pos = 0.0f;
    float speedbrake_pos = 0.0f;
    bool master_arm = false;
    int weapon_selected = 0;
};

struct ResolvedAirNoseWheelSteeringInput {
    bool available = false;
    double yaw_command = 0.0;
};

struct ResolvedAirControlInput {
    bool has_primary_flight_control_input = false;
    bool has_manual_pilot_input = false;
    bool has_command_control_state = false;
    double throttle_command = 0.0;
    ResolvedGroundControlInput ground_control{};
    ResolvedAirInstrumentControlInput instrument_control{};
    ResolvedAirNoseWheelSteeringInput nose_wheel_steering{};
};

inline const PilotAction *active_pilot_action(const PilotAction *pilot) {
    return (pilot && pilot->active) ? pilot : nullptr;
}

inline const MovementCommand *active_legacy_movement_command(const MovementCommand *legacy) {
    return (legacy && legacy->active) ? legacy : nullptr;
}

inline const ActionCommand *active_legacy_action_command(const ActionCommand *legacy_action) {
    return (legacy_action && legacy_action->active) ? legacy_action : nullptr;
}

inline const MissionCommandControlState *
active_mission_command_control_state(const MissionCommandControlState *control_state) {
    return (control_state &&
            (control_state->active || control_state->lagged_active ||
             mission_command_typed_air_control_active(control_state->typed_air_control)))
               ? control_state
               : nullptr;
}

inline const MovementCommand *
active_compatibility_legacy_movement_command(const MovementCommand *legacy_movement) {
    return active_legacy_movement_command(legacy_movement);
}

inline const ActionCommand *
active_compatibility_legacy_action_command(const ActionCommand *legacy_action) {
    return active_legacy_action_command(legacy_action);
}

inline ResolvedAirCommandInputSources resolve_air_command_input_sources(
    const PilotAction *pilot, const MissionCommandControlState *control_state,
    const MovementCommand *legacy_movement, const ActionCommand *legacy_action = nullptr) {
    return {
        active_pilot_action(pilot),
        active_mission_command_control_state(control_state),
        active_compatibility_legacy_movement_command(legacy_movement),
        active_compatibility_legacy_action_command(legacy_action),
    };
}

inline ResolvedAirCommandInputSources
resolve_air_command_input_sources(const PilotAction *pilot, const MovementCommand *legacy_movement,
                                  const ActionCommand *legacy_action = nullptr) {
    return resolve_air_command_input_sources(pilot, nullptr, legacy_movement, legacy_action);
}

inline bool
has_resolved_primary_flight_control_input(const ResolvedAirCommandInputSources &inputs) {
    return inputs.pilot != nullptr || inputs.control_state != nullptr ||
           inputs.legacy_movement != nullptr;
}

inline const MissionCommandTypedAirControlState *
active_typed_air_control_state(const MissionCommandControlState *control_state) {
    if (!control_state) {
        return nullptr;
    }
    return mission_command_typed_air_control_active(control_state->typed_air_control)
               ? &control_state->typed_air_control
               : nullptr;
}

inline double resolved_air_command_throttle(const ResolvedAirCommandInputSources &inputs,
                                            double fallback_throttle = 0.0) {
    if (inputs.pilot) {
        return std::clamp(inputs.pilot->throttle, 0.0, 1.0);
    }
    if (const MissionCommandTypedAirControlState *typed_air_control =
            active_typed_air_control_state(inputs.control_state);
        typed_air_control && typed_air_control->throttle_active) {
        return std::clamp(typed_air_control->throttle_command, 0.0, 1.0);
    }
    if (inputs.legacy_movement) {
        return std::clamp(inputs.legacy_movement->throttle_cmd, 0.0, 1.0);
    }
    if (inputs.legacy_action) {
        return std::clamp((inputs.legacy_action->accel_cmd + 1.0) * 0.5, 0.0, 1.0);
    }
    return std::clamp(fallback_throttle, 0.0, 1.0);
}

inline double resolved_pilot_or_legacy_throttle(const PilotAction *pilot,
                                                const MissionCommandControlState *control_state,
                                                const MovementCommand *legacy,
                                                double fallback_throttle = 0.0) {
    return resolved_air_command_throttle(
        resolve_air_command_input_sources(pilot, control_state, legacy), fallback_throttle);
}

inline double resolved_pilot_or_legacy_throttle(const PilotAction *pilot,
                                                const MovementCommand *legacy,
                                                double fallback_throttle = 0.0) {
    return resolved_pilot_or_legacy_throttle(pilot, nullptr, legacy, fallback_throttle);
}

inline ResolvedGroundControlInput
resolved_pilot_or_legacy_ground_control(const ResolvedAirCommandInputSources &inputs) {
    ResolvedGroundControlInput out;
    if (inputs.pilot) {
        out.throttle_idle = (inputs.pilot->throttle < 0.01);
        out.brake_amount = std::clamp(inputs.pilot->brake, 0.0, 1.0);
        if (inputs.pilot->brake_left || inputs.pilot->brake_right) {
            out.brake_amount = 1.0;
        }
        return out;
    }
    if (const MissionCommandTypedAirControlState *typed_air_control =
            active_typed_air_control_state(inputs.control_state);
        typed_air_control && typed_air_control->ground_active) {
        out.throttle_idle = typed_air_control->throttle_idle;
        out.brake_amount = std::clamp(typed_air_control->brake_amount, 0.0, 1.0);
        return out;
    }
    if (inputs.legacy_movement) {
        out.throttle_idle = (inputs.legacy_movement->throttle_cmd < 0.01);
        if (out.throttle_idle) {
            out.brake_amount = 1.0;
        }
    }
    return out;
}

inline ResolvedAirInstrumentControlInput
resolved_air_instrument_control(const ResolvedAirCommandInputSources &inputs) {
    if (inputs.pilot) {
        return {
            std::clamp(inputs.pilot->flaps, 0.0f, 1.0f),
            std::clamp(inputs.pilot->speedbrake, 0.0f, 1.0f),
            inputs.pilot->master_arm,
            inputs.pilot->weapon_select_id,
        };
    }
    if (const MissionCommandTypedAirControlState *typed_air_control =
            active_typed_air_control_state(inputs.control_state);
        typed_air_control && typed_air_control->instrument_active) {
        return {
            std::clamp(typed_air_control->flaps_pos, 0.0f, 1.0f),
            std::clamp(typed_air_control->speedbrake_pos, 0.0f, 1.0f),
            typed_air_control->master_arm,
            typed_air_control->weapon_selected,
        };
    }
    return {};
}

inline ResolvedAirNoseWheelSteeringInput
resolved_air_nose_wheel_steering_input(const ResolvedAirCommandInputSources &inputs) {
    if (inputs.pilot) {
        return {
            true,
            std::clamp(inputs.pilot->rudder, -1.0, 1.0),
        };
    }
    if (const MissionCommandTypedAirControlState *typed_air_control =
            active_typed_air_control_state(inputs.control_state);
        typed_air_control && typed_air_control->nose_wheel_steering_active) {
        return {
            true,
            std::clamp(typed_air_control->nose_wheel_yaw_command, -1.0, 1.0),
        };
    }
    return {};
}

inline ResolvedAirControlInput
resolve_air_control_input(const ResolvedAirCommandInputSources &inputs,
                          double fallback_throttle = 0.0) {
    return {
        has_resolved_primary_flight_control_input(inputs),
        inputs.pilot != nullptr,
        inputs.control_state != nullptr,
        resolved_air_command_throttle(inputs, fallback_throttle),
        resolved_pilot_or_legacy_ground_control(inputs),
        resolved_air_instrument_control(inputs),
        resolved_air_nose_wheel_steering_input(inputs),
    };
}

inline ResolvedAirControlInput
resolve_air_control_input(const PilotAction *pilot, const MissionCommandControlState *control_state,
                          const MovementCommand *legacy_movement,
                          const ActionCommand *legacy_action = nullptr,
                          double fallback_throttle = 0.0) {
    return resolve_air_control_input(
        resolve_air_command_input_sources(pilot, control_state, legacy_movement, legacy_action),
        fallback_throttle);
}

inline ResolvedAirControlInput
resolve_air_control_input(const PilotAction *pilot, const MovementCommand *legacy_movement,
                          const ActionCommand *legacy_action = nullptr,
                          double fallback_throttle = 0.0) {
    return resolve_air_control_input(pilot, nullptr, legacy_movement, legacy_action,
                                     fallback_throttle);
}

inline ResolvedGroundControlInput
resolve_pilot_or_legacy_ground_control(const PilotAction *pilot,
                                       const MissionCommandControlState *control_state,
                                       const MovementCommand *legacy) {
    return resolved_pilot_or_legacy_ground_control(
        resolve_air_command_input_sources(pilot, control_state, legacy));
}

inline ResolvedGroundControlInput
resolve_pilot_or_legacy_ground_control(const PilotAction *pilot, const MovementCommand *legacy) {
    return resolve_pilot_or_legacy_ground_control(pilot, nullptr, legacy);
}
