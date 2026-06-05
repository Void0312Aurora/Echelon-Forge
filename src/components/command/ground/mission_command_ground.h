#pragma once

#include <cstdint>

#include "components/tasking/ground/ground_tasking_enums.h"

struct MissionCommandGround {
    struct StaticTaskDirective {
        GroundTaskMode ground_task_mode = GroundTaskMode::Unspecified;
        std::uint64_t objective_area_id = 0;
        std::uint64_t objective_node_id = 0;
        std::uint64_t ground_commander_id = 0;
        double tactical_cadence_hz = 1.0;

        bool operator==(const StaticTaskDirective&) const = default;
    };

    GroundTaskMode ground_task_mode = GroundTaskMode::Unspecified;
    std::uint64_t objective_area_id = 0;
    std::uint64_t objective_node_id = 0;
    std::uint64_t ground_commander_id = 0;
    double tactical_cadence_hz = 1.0;
};

// Maintained ground-domain owner slice projected through MissionCommand compatibility shells.
using MissionCommandGroundOwnerSlice = MissionCommandGround;
inline constexpr bool kMissionCommandGroundOwnedDomainSlice = true;

[[nodiscard]] inline MissionCommandGround::StaticTaskDirective
mission_command_ground_static_task_directive(
    const MissionCommandGroundOwnerSlice& ground
) noexcept {
    return {
        .ground_task_mode = ground.ground_task_mode,
        .objective_area_id = ground.objective_area_id,
        .objective_node_id = ground.objective_node_id,
        .ground_commander_id = ground.ground_commander_id,
        .tactical_cadence_hz = ground.tactical_cadence_hz,
    };
}
