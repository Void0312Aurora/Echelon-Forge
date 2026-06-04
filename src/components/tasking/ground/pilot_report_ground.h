#pragma once

#include <cstdint>

#include "components/tasking/ground/ground_tasking_enums.h"

struct PilotReportGround {
    struct StaticStatusDirective {
        GroundTaskGrade grade = GroundTaskGrade::Unspecified;
        GroundTaskKind task_kind = GroundTaskKind::Unspecified;
        GroundSchemaBoundary schema_boundary = GroundSchemaBoundary::Unspecified;
        std::uint64_t objective_area_id = 0;
        bool movement_released = false;
        bool observation_export_released = false;
        bool fires_released = false;

        bool operator==(const StaticStatusDirective&) const = default;
    };

    GroundTaskGrade ground_task_grade = GroundTaskGrade::Unspecified;
    GroundTaskKind ground_task_kind = GroundTaskKind::Unspecified;
    GroundSchemaBoundary ground_schema_boundary = GroundSchemaBoundary::Unspecified;
    std::uint64_t ground_objective_area_id = 0;
    bool ground_movement_released = false;
    bool ground_observation_export_released = false;
    bool ground_fires_released = false;
};

// Maintained ground-domain owner slice for G0/G1 report/status evidence only.
using PilotReportGroundOwnerSlice = PilotReportGround;
inline constexpr bool kPilotReportGroundOwnedDomainSlice = true;

[[nodiscard]] inline PilotReportGround::StaticStatusDirective
pilot_report_ground_static_status_directive(
    const PilotReportGroundOwnerSlice& ground
) noexcept {
    return {
        .grade = ground.ground_task_grade,
        .task_kind = ground.ground_task_kind,
        .schema_boundary = ground.ground_schema_boundary,
        .objective_area_id = ground.ground_objective_area_id,
        .movement_released = ground.ground_movement_released,
        .observation_export_released = ground.ground_observation_export_released,
        .fires_released = ground.ground_fires_released,
    };
}
