#pragma once

#include "components/command/common/mission_command_control_state.h"
#include "components/command/common/mission_command_core.h"
#include "components/command/legacy_command.h"

namespace default_unit_factory_detail {

// Compatibility-only spawn seam for default unit factory legacy command bootstrap.
// MissionCommandControlState is the maintained spawn-default owner here; legacy
// MovementCommand/LaggedCommand remain projected mirrors only for still-live
// compatibility consumers. It is not a retired seam.
struct SpawnCompatibilityControlStateSeed {
    ActionCommand action_command = make_action_command();
    MissionCommandControlState control_state = make_mission_command_control_state(0.0, 0.0, 0.0);
};

using SpawnCompatibilityLegacyCommandSeed = SpawnCompatibilityControlStateSeed;

struct SpawnCompatibilityActionCommandSeed {
    ActionCommand action_command = make_action_command();
};

inline MissionCommandCore make_spawn_default_mission_command_core_seed(
    double heading_deg,
    double speed_mps,
    double altitude_m
) {
    MissionCommandCore seed{};
    seed.cmd_heading_deg = heading_deg;
    seed.cmd_speed_mps = speed_mps;
    seed.cmd_altitude_m = altitude_m;
    return seed;
}

inline MovementCommand project_spawn_compatibility_movement_command_mirror(
    const MissionCommandControlState& control_state
) {
    return make_legacy_autopilot_movement_command(
        control_state.target_heading_deg,
        control_state.target_speed_mps,
        control_state.target_altitude_m,
        control_state.active);
}

inline LaggedCommand project_spawn_compatibility_lagged_command_mirror(
    const MissionCommandControlState& control_state
) {
    return make_lagged_command(
        control_state.lagged_heading_deg,
        control_state.lagged_speed_mps,
        control_state.lagged_altitude_m,
        control_state.lagged_active);
}

inline SpawnCompatibilityControlStateSeed make_spawn_compatibility_control_state_seed(
    const MissionCommandCore& mission_seed
) {
    SpawnCompatibilityControlStateSeed seed;
    seed.control_state = make_mission_command_control_state(mission_seed, true);
    return seed;
}

inline SpawnCompatibilityControlStateSeed make_spawn_compatibility_control_state_seed(
    double heading_deg,
    double speed_mps,
    double altitude_m
) {
    return make_spawn_compatibility_control_state_seed(
        make_spawn_default_mission_command_core_seed(
            heading_deg,
            speed_mps,
            altitude_m));
}

inline SpawnCompatibilityLegacyCommandSeed make_spawn_compatibility_legacy_command_seed(
    const MissionCommandCore& mission_seed
) {
    return make_spawn_compatibility_control_state_seed(mission_seed);
}

inline SpawnCompatibilityLegacyCommandSeed make_spawn_compatibility_legacy_command_seed(
    double heading_deg,
    double speed_mps,
    double altitude_m
) {
    return make_spawn_compatibility_control_state_seed(
        heading_deg,
        speed_mps,
        altitude_m);
}

template <typename EntityT>
inline void apply_spawn_compatibility_action_command_seed(
    EntityT& entity,
    const SpawnCompatibilityActionCommandSeed& seed = {}
) {
    entity.template set<ActionCommand>(seed.action_command);
}

template <typename EntityT>
inline void apply_spawn_compatibility_control_state_seed(
    EntityT& entity,
    const SpawnCompatibilityControlStateSeed& seed
) {
    apply_spawn_compatibility_action_command_seed(
        entity,
        SpawnCompatibilityActionCommandSeed{seed.action_command});
    entity.template set<MissionCommandControlState>(seed.control_state);
    entity.template set<MovementCommand>(
        project_spawn_compatibility_movement_command_mirror(seed.control_state));
    entity.template set<LaggedCommand>(
        project_spawn_compatibility_lagged_command_mirror(seed.control_state));
}

template <typename EntityT>
inline void apply_spawn_compatibility_legacy_command_seed(
    EntityT& entity,
    const SpawnCompatibilityLegacyCommandSeed& seed
) {
    apply_spawn_compatibility_control_state_seed(entity, seed);
}

} // namespace default_unit_factory_detail
