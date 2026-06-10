#pragma once

#include <cstdint>

#include "components/domains/ground/tasking/ground_tasking_enums.h"

struct PilotReportGround {
    struct StaticStatusDirective {
        GroundStatusPhase ground_status_phase = GroundStatusPhase::Unspecified;
        GroundTaskMode ground_task_mode = GroundTaskMode::Unspecified;
        std::uint64_t objective_area_id = 0;
        std::uint64_t objective_node_id = 0;
        std::uint64_t ground_commander_id = 0;
        double tactical_cadence_hz = 1.0;
        double readiness_ratio = 0.0;

        bool operator==(const StaticStatusDirective &) const = default;
    };

    GroundStatusPhase ground_status_phase = GroundStatusPhase::Unspecified;
    GroundTaskMode ground_task_mode = GroundTaskMode::Unspecified;
    std::uint64_t objective_area_id = 0;
    std::uint64_t objective_node_id = 0;
    std::uint64_t ground_commander_id = 0;
    double tactical_cadence_hz = 1.0;
    double readiness_ratio = 0.0;
};

// Maintained ground-domain owner slice projected through PilotReport compatibility shells.
using PilotReportGroundOwnerSlice = PilotReportGround;
inline constexpr bool kPilotReportGroundOwnedDomainSlice = true;

[[nodiscard]] inline PilotReportGround::StaticStatusDirective
pilot_report_ground_static_status_directive(const PilotReportGroundOwnerSlice &ground) noexcept {
    return {
        .ground_status_phase = ground.ground_status_phase,
        .ground_task_mode = ground.ground_task_mode,
        .objective_area_id = ground.objective_area_id,
        .objective_node_id = ground.objective_node_id,
        .ground_commander_id = ground.ground_commander_id,
        .tactical_cadence_hz = ground.tactical_cadence_hz,
        .readiness_ratio = ground.readiness_ratio,
    };
}
