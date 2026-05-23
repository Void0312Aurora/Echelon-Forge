#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <type_traits>

#include "components/command/command_link.h"
#include "components/command/common/mission_command_control_state.h"
#include "components/command/air/control_input_resolution.h"
#include "components/basic/common.h"

// Compatibility-only bridge seam for quarantined legacy command DTO consumers
// outside the maintained air-control physics path.

struct ResolvedCompatibilityCountermeasureCommand {
    bool release_chaff = false;
    bool release_flare = false;
};

struct ResolvedCompatibilityMessageCommand {
    bool send = false;
    int msg_type = 0;
    std::uint64_t recipient = 0;
    std::uint64_t arg = 0;
};

inline double resolved_compatibility_damage_evasion(
    const ActionCommand* legacy_action
) {
    const ActionCommand* action = active_legacy_action_command(legacy_action);
    if (!action) {
        return 0.0;
    }
    return std::clamp(std::abs(action->turn_rate_cmd), 0.0, 1.0);
}

template <typename EntityT>
requires (!std::is_pointer_v<std::remove_reference_t<EntityT>>)
inline double resolved_compatibility_damage_evasion(const EntityT& entity) {
    return resolved_compatibility_damage_evasion(
        entity.template get<ActionCommand>()
    );
}

inline ResolvedCompatibilityCountermeasureCommand resolve_compatibility_countermeasure_command(
    const PilotAction* pilot,
    const ActionCommand* legacy_action
) {
    ResolvedCompatibilityCountermeasureCommand resolved;
    if (const PilotAction* active_pilot = active_pilot_action(pilot)) {
        resolved.release_chaff = active_pilot->program_chaff;
        resolved.release_flare = active_pilot->program_flare;
    }

    if (const ActionCommand* action = active_legacy_action_command(legacy_action)) {
        resolved.release_chaff = resolved.release_chaff || action->release_chaff;
        resolved.release_flare = resolved.release_flare || action->release_flare;
    }
    return resolved;
}

template <typename EntityT>
requires (!std::is_pointer_v<std::remove_reference_t<EntityT>>)
inline ResolvedCompatibilityCountermeasureCommand resolve_compatibility_countermeasure_command(
    const EntityT& entity
) {
    return resolve_compatibility_countermeasure_command(
        entity.template get<PilotAction>(),
        entity.template get<ActionCommand>()
    );
}

inline bool resolved_compatibility_jettison_tanks(const ActionCommand* legacy_action) {
    const ActionCommand* action = active_legacy_action_command(legacy_action);
    return action && action->jettison_tanks;
}

template <typename EntityT>
requires (!std::is_pointer_v<std::remove_reference_t<EntityT>>)
inline bool resolved_compatibility_jettison_tanks(const EntityT& entity) {
    return resolved_compatibility_jettison_tanks(
        entity.template get<ActionCommand>()
    );
}

inline ResolvedCompatibilityMessageCommand resolve_compatibility_message_command(
    const ActionCommand* legacy_action
) {
    const ActionCommand* action = active_legacy_action_command(legacy_action);
    if (!action) {
        return {};
    }
    return {
        action->send_msg,
        action->msg_type,
        action->msg_recipient,
        action->msg_arg,
    };
}

template <typename EntityT>
requires (!std::is_pointer_v<std::remove_reference_t<EntityT>>)
inline ResolvedCompatibilityMessageCommand resolve_compatibility_message_command(
    const EntityT& entity
) {
    return resolve_compatibility_message_command(
        entity.template get<ActionCommand>()
    );
}

inline void set_compatibility_autopilot_movement_command(
    MovementCommand& legacy_movement,
    double heading_deg,
    double speed_mps,
    double altitude_m
) {
    legacy_movement = make_legacy_autopilot_movement_command(
        heading_deg,
        speed_mps,
        altitude_m
    );
}

template <typename EntityT>
requires (!std::is_pointer_v<std::remove_reference_t<EntityT>>)
inline MissionCommandControlState& ensure_mission_command_control_state(
    EntityT& entity
) {
    if (MissionCommandControlState* state =
            entity.template get_mut<MissionCommandControlState>()) {
        return *state;
    }
    entity.template set<MissionCommandControlState>(
        make_mission_command_control_state(0.0, 0.0, 0.0, false)
    );
    return *entity.template get_mut<MissionCommandControlState>();
}

template <typename EntityT>
requires (!std::is_pointer_v<std::remove_reference_t<EntityT>>)
inline MovementCommand& ensure_compatibility_movement_command(
    EntityT& entity
) {
    if (MovementCommand* legacy_movement =
            entity.template get_mut<MovementCommand>()) {
        return *legacy_movement;
    }
    entity.template set<MovementCommand>(
        make_legacy_autopilot_movement_command(0.0, 0.0, 0.0, false)
    );
    return *entity.template get_mut<MovementCommand>();
}

template <typename EntityT>
requires (!std::is_pointer_v<std::remove_reference_t<EntityT>>)
inline LaggedCommand& ensure_compatibility_lagged_command(
    EntityT& entity
) {
    if (LaggedCommand* lagged = entity.template get_mut<LaggedCommand>()) {
        return *lagged;
    }
    entity.template set<LaggedCommand>(make_lagged_command(0.0, 0.0, 0.0, false));
    return *entity.template get_mut<LaggedCommand>();
}

template <typename EntityT>
requires (!std::is_pointer_v<std::remove_reference_t<EntityT>>)
inline void ensure_compatibility_control_mirrors(EntityT& entity) {
    (void)ensure_mission_command_control_state(entity);
    (void)ensure_compatibility_movement_command(entity);
    (void)ensure_compatibility_lagged_command(entity);
}

inline void refresh_compatibility_autopilot_movement_command_from_control_state(
    MovementCommand& legacy_movement,
    const MissionCommandControlState& state
) {
    legacy_movement.target_heading = state.target_heading_deg;
    legacy_movement.target_speed = state.target_speed_mps;
    legacy_movement.target_altitude = state.target_altitude_m;
    legacy_movement.use_stick_control = false;
    legacy_movement.stick_roll = 0.0;
    legacy_movement.stick_pitch = 0.0;
    legacy_movement.throttle_cmd = 0.0;
    legacy_movement.gear_handle = true;
    legacy_movement.active = state.active;
}

inline void refresh_compatibility_lagged_command_mirror_from_control_state(
    LaggedCommand& lagged,
    const MissionCommandControlState& state
) {
    lagged.target_heading = state.lagged_heading_deg;
    lagged.target_speed = state.lagged_speed_mps;
    lagged.target_altitude = state.lagged_altitude_m;
    lagged.active = state.lagged_active;
}

inline void refresh_optional_compatibility_autopilot_movement_command_from_control_state(
    MovementCommand* legacy_movement,
    const MissionCommandControlState& state
) {
    if (!legacy_movement) {
        return;
    }
    refresh_compatibility_autopilot_movement_command_from_control_state(
        *legacy_movement,
        state
    );
}

inline void refresh_optional_compatibility_lagged_command_mirror_from_control_state(
    LaggedCommand* lagged,
    const MissionCommandControlState& state
) {
    if (!lagged) {
        return;
    }
    refresh_compatibility_lagged_command_mirror_from_control_state(
        *lagged,
        state
    );
}

inline double compatibility_wrap_angle_360(double angle) {
    while (angle < 0.0) angle += 360.0;
    while (angle >= 360.0) angle -= 360.0;
    return angle;
}

inline double compatibility_speed_from_velocity(const Velocity& velocity) {
    return std::sqrt(
        velocity.vx * velocity.vx +
        velocity.vy * velocity.vy +
        velocity.vz * velocity.vz
    );
}

inline MissionCommandControlState make_compatibility_control_state_seed(
    const Transform& transform,
    const Velocity& velocity
) {
    return make_mission_command_control_state(
        compatibility_wrap_angle_360(transform.heading),
        compatibility_speed_from_velocity(velocity),
        transform.z
    );
}

inline MissionCommandTypedAirControlState
make_compatibility_typed_air_control_from_legacy_movement(
    const MovementCommand& legacy_movement
) {
    MissionCommandTypedAirControlState typed_air_control{};
    typed_air_control.throttle_command = std::clamp(legacy_movement.throttle_cmd, 0.0, 1.0);
    typed_air_control.throttle_active = legacy_movement.active;
    typed_air_control.throttle_idle = legacy_movement.throttle_cmd < 0.01;
    typed_air_control.brake_amount = typed_air_control.throttle_idle ? 1.0 : 0.0;
    typed_air_control.ground_active = legacy_movement.active;
    typed_air_control.manual_input_active =
        legacy_movement.active && legacy_movement.use_stick_control;
    return typed_air_control;
}

inline MissionCommandTypedAirControlState
make_compatibility_typed_air_control_from_legacy_action(
    const ActionCommand& legacy_action
) {
    MissionCommandTypedAirControlState typed_air_control{};
    typed_air_control.throttle_command = std::clamp((legacy_action.accel_cmd + 1.0) * 0.5, 0.0, 1.0);
    typed_air_control.throttle_active = legacy_action.active;
    typed_air_control.throttle_idle = typed_air_control.throttle_command < 0.01;
    typed_air_control.ground_active = legacy_action.active;
    typed_air_control.action_semantics_active = legacy_action.active;
    return typed_air_control;
}

inline void refresh_compatibility_typed_air_control_from_legacy_movement(
    MissionCommandControlState& state,
    const MovementCommand& legacy_movement
) {
    MissionCommandTypedAirControlState typed_air_control =
        state.typed_air_control;
    const MissionCommandTypedAirControlState legacy_projection =
        make_compatibility_typed_air_control_from_legacy_movement(legacy_movement);

    typed_air_control.throttle_command = legacy_projection.throttle_command;
    typed_air_control.throttle_active = legacy_projection.throttle_active;
    typed_air_control.throttle_idle = legacy_projection.throttle_idle;
    typed_air_control.brake_amount = legacy_projection.brake_amount;
    typed_air_control.ground_active = legacy_projection.ground_active;
    typed_air_control.manual_input_active = legacy_projection.manual_input_active;

    set_mission_command_typed_air_control_state(state, typed_air_control);
}

inline void refresh_compatibility_typed_air_control_from_legacy_action(
    MissionCommandControlState& state,
    const ActionCommand& legacy_action
) {
    MissionCommandTypedAirControlState typed_air_control =
        state.typed_air_control;
    const MissionCommandTypedAirControlState legacy_projection =
        make_compatibility_typed_air_control_from_legacy_action(legacy_action);

    if (!typed_air_control.throttle_active) {
        typed_air_control.throttle_command = legacy_projection.throttle_command;
        typed_air_control.throttle_active = legacy_projection.throttle_active;
        typed_air_control.throttle_idle = legacy_projection.throttle_idle;
    }
    if (!typed_air_control.ground_active) {
        typed_air_control.throttle_idle = legacy_projection.throttle_idle;
        typed_air_control.brake_amount = legacy_projection.brake_amount;
        typed_air_control.ground_active = legacy_projection.ground_active;
    }
    typed_air_control.action_semantics_active = legacy_projection.action_semantics_active;

    set_mission_command_typed_air_control_state(state, typed_air_control);
}

inline void refresh_compatibility_typed_air_control_from_pending_action_bridge(
    MissionCommandControlState& state,
    const MissionCommandTypedAirControlState& pending_action_bridge
) {
    MissionCommandTypedAirControlState typed_air_control =
        state.typed_air_control;

    if (!typed_air_control.throttle_active) {
        typed_air_control.throttle_command = pending_action_bridge.throttle_command;
        typed_air_control.throttle_active = pending_action_bridge.throttle_active;
        typed_air_control.throttle_idle = pending_action_bridge.throttle_idle;
    }
    if (!typed_air_control.ground_active) {
        typed_air_control.throttle_idle = pending_action_bridge.throttle_idle;
        typed_air_control.brake_amount = pending_action_bridge.brake_amount;
        typed_air_control.ground_active = pending_action_bridge.ground_active;
    }
    typed_air_control.action_semantics_active =
        pending_action_bridge.action_semantics_active;

    set_mission_command_typed_air_control_state(state, typed_air_control);
}

template <typename EntityT>
requires (!std::is_pointer_v<std::remove_reference_t<EntityT>>)
inline void refresh_compatibility_control_mirrors_from_state(EntityT& entity) {
    const MissionCommandControlState& state =
        ensure_mission_command_control_state(entity);
    refresh_compatibility_autopilot_movement_command_from_control_state(
        ensure_compatibility_movement_command(entity),
        state
    );
    refresh_compatibility_lagged_command_mirror_from_control_state(
        ensure_compatibility_lagged_command(entity),
        state
    );
}

template <typename EntityT>
requires (!std::is_pointer_v<std::remove_reference_t<EntityT>>)
inline void set_compatibility_autopilot_control_target(
    EntityT& entity,
    double heading_deg,
    double speed_mps,
    double altitude_m
) {
    MissionCommandControlState& state = ensure_mission_command_control_state(entity);
    set_mission_command_control_target(
        state,
        heading_deg,
        speed_mps,
        altitude_m,
        true
    );
    if (!state.lagged_active) {
        set_mission_command_control_lagged(
            state,
            heading_deg,
            speed_mps,
            altitude_m,
            true
        );
    }
    refresh_compatibility_control_mirrors_from_state(entity);
}

template <typename EntityT>
requires (!std::is_pointer_v<std::remove_reference_t<EntityT>>)
inline void set_compatibility_autopilot_movement_command(
    EntityT& entity,
    double heading_deg,
    double speed_mps,
    double altitude_m
) {
    MissionCommandControlState& state = ensure_mission_command_control_state(entity);
    set_mission_command_control_target(
        state,
        heading_deg,
        speed_mps,
        altitude_m,
        true
    );
    set_mission_command_control_lagged(
        state,
        heading_deg,
        speed_mps,
        altitude_m,
        true
    );
    refresh_compatibility_control_mirrors_from_state(entity);
}

template <typename EntityT>
requires (!std::is_pointer_v<std::remove_reference_t<EntityT>>)
inline void set_quarantined_compatibility_stick_movement_command(
    EntityT& entity,
    double stick_roll,
    double stick_pitch,
    double throttle_cmd,
    bool gear_down
) {
    // Compatibility-only stick DTO write: this does not express a typed
    // autopilot target and must not mutate MissionCommandControlState.
    MovementCommand& legacy_movement = ensure_compatibility_movement_command(entity);
    legacy_movement = make_legacy_stick_movement_command(
        stick_roll,
        stick_pitch,
        throttle_cmd,
        gear_down
    );
    refresh_compatibility_typed_air_control_from_legacy_movement(
        ensure_mission_command_control_state(entity),
        legacy_movement
    );
}

inline void deactivate_compatibility_movement_command(MovementCommand& legacy_movement) {
    legacy_movement.active = false;
    legacy_movement.use_stick_control = false;
}

template <typename EntityT>
requires (!std::is_pointer_v<std::remove_reference_t<EntityT>>)
inline void deactivate_compatibility_movement_command(EntityT& entity) {
    ensure_compatibility_control_mirrors(entity);
    MissionCommandControlState& state = ensure_mission_command_control_state(entity);
    state.active = false;
    state.lagged_active = false;
    reset_mission_command_typed_air_control_state(state);
    refresh_compatibility_control_mirrors_from_state(entity);
}

template <typename EntityT>
requires (!std::is_pointer_v<std::remove_reference_t<EntityT>>)
inline void refresh_compatibility_typed_air_control_from_action_command(
    EntityT& entity,
    const ActionCommand& legacy_action
) {
    refresh_compatibility_typed_air_control_from_legacy_action(
        ensure_mission_command_control_state(entity),
        legacy_action
    );
}

template <typename EntityT>
requires (!std::is_pointer_v<std::remove_reference_t<EntityT>>)
inline void refresh_optional_compatibility_typed_air_control_from_action_command(
    EntityT& entity,
    const ActionCommand& legacy_action
) {
    if (MissionCommandControlState* state =
            entity.template get_mut<MissionCommandControlState>()) {
        refresh_compatibility_typed_air_control_from_legacy_action(
            *state,
            legacy_action
        );
    }
}

template <typename EntityT>
requires (!std::is_pointer_v<std::remove_reference_t<EntityT>>)
inline void refresh_optional_pending_action_typed_air_control_bridge(
    EntityT& entity,
    const PendingActionCommand& pending_action
) {
    if (MissionCommandControlState* state =
            entity.template get_mut<MissionCommandControlState>()) {
        refresh_compatibility_typed_air_control_from_pending_action_bridge(
            *state,
            pending_action.typed_air_control_bridge
        );
    }
}
