#pragma once

#include <cstdint>

#include "components/domains/ground/tasking/ground_tasking_enums.h"

struct LeaderIntentGround {
    struct StaticStatusDirective {
        GroundStatusPhase ground_status_phase = GroundStatusPhase::Unspecified;
        GroundTaskMode ground_task_mode = GroundTaskMode::Unspecified;
        std::uint64_t objective_area_id = 0;
        std::uint64_t objective_node_id = 0;
        std::uint64_t ground_commander_id = 0;
        double tactical_cadence_hz = 1.0;

        bool operator==(const StaticStatusDirective&) const = default;
    };

    GroundStatusPhase ground_status_phase = GroundStatusPhase::Unspecified;
    GroundTaskMode ground_task_mode = GroundTaskMode::Unspecified;
    std::uint64_t objective_area_id = 0;
    std::uint64_t objective_node_id = 0;
    std::uint64_t ground_commander_id = 0;
    double tactical_cadence_hz = 1.0;
};

// Maintained ground-domain owner slice projected through LeaderIntent compatibility shells.
using LeaderIntentGroundOwnerSlice = LeaderIntentGround;
inline constexpr bool kLeaderIntentGroundOwnedDomainSlice = true;

[[nodiscard]] inline LeaderIntentGround::StaticStatusDirective
leader_intent_ground_static_status_directive(
    const LeaderIntentGroundOwnerSlice& ground
) noexcept {
    return {
        .ground_status_phase = ground.ground_status_phase,
        .ground_task_mode = ground.ground_task_mode,
        .objective_area_id = ground.objective_area_id,
        .objective_node_id = ground.objective_node_id,
        .ground_commander_id = ground.ground_commander_id,
        .tactical_cadence_hz = ground.tactical_cadence_hz,
    };
}
