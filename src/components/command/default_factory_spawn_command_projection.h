#pragma once

#include "components/command/common/mission_command_control_state.h"
#include "components/command/common/mission_command_core.h"
#include "components/command/legacy_command.h"

namespace default_unit_factory_detail {

// Default-factory spawn command projection seam.
// MissionCommandControlState is the maintained spawn-default owner here;
// MovementCommand/LaggedCommand remain projected mirrors for still-live mirror
// consumers until their readers move to typed control state.
struct SpawnCommandProjectionControlStateSeed {
    ActionCommand action_command = make_action_command();
    MissionCommandControlState control_state = make_mission_command_control_state(0.0, 0.0, 0.0);
};

struct SpawnCommandProjectionActionSeed {
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

inline MovementCommand project_spawn_command_projection_movement_mirror(
    const MissionCommandControlState& control_state
) {
    return make_legacy_autopilot_movement_command(
        control_state.target_heading_deg,
        control_state.target_speed_mps,
        control_state.target_altitude_m,
        control_state.active);
}

inline LaggedCommand project_spawn_command_projection_lagged_mirror(
    const MissionCommandControlState& control_state
) {
    return make_lagged_command(
        control_state.lagged_heading_deg,
        control_state.lagged_speed_mps,
        control_state.lagged_altitude_m,
        control_state.lagged_active);
}

inline SpawnCommandProjectionControlStateSeed make_spawn_command_projection_control_state_seed(
    const MissionCommandCore& mission_seed
) {
    SpawnCommandProjectionControlStateSeed seed;
    seed.control_state = make_mission_command_control_state(mission_seed, true);
    return seed;
}

inline SpawnCommandProjectionControlStateSeed make_spawn_command_projection_control_state_seed(
    double heading_deg,
    double speed_mps,
    double altitude_m
) {
    return make_spawn_command_projection_control_state_seed(
        make_spawn_default_mission_command_core_seed(
            heading_deg,
            speed_mps,
            altitude_m));
}

template <typename EntityT>
inline void apply_spawn_command_projection_action_seed(
    EntityT& entity,
    const SpawnCommandProjectionActionSeed& seed = {}
) {
    entity.template set<ActionCommand>(seed.action_command);
}

template <typename EntityT>
inline void apply_spawn_command_projection_control_state_seed(
    EntityT& entity,
    const SpawnCommandProjectionControlStateSeed& seed
) {
    apply_spawn_command_projection_action_seed(
        entity,
        SpawnCommandProjectionActionSeed{seed.action_command});
    entity.template set<MissionCommandControlState>(seed.control_state);
    entity.template set<MovementCommand>(
        project_spawn_command_projection_movement_mirror(seed.control_state));
    entity.template set<LaggedCommand>(
        project_spawn_command_projection_lagged_mirror(seed.control_state));
}

} // namespace default_unit_factory_detail
