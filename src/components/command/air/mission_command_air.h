#pragma once

#include <cstdint>

#include "components/tasking/air/air_tasking_enums.h"

struct MissionCommandAir {
    struct RecoveryDirective {
        std::uint64_t recovery_base_id = 0;
        std::uint64_t recovery_runway_id = 0;
        RecoveryApproachType recovery_approach_type = RecoveryApproachType::None;

        bool operator==(const RecoveryDirective&) const = default;
    };

    struct TakeoffDirective {
        TakeoffProcedureType takeoff_procedure_id = TakeoffProcedureType::Unspecified;
        TakeoffClearanceState takeoff_clearance_id = TakeoffClearanceState::Unspecified;
        double takeoff_interval_s = 0.0;
        RunwaySlotPosition runway_slot_id = RunwaySlotPosition::Unspecified;

        bool operator==(const TakeoffDirective&) const = default;
    };

    struct FormationDirective {
        int formation_id = 0;
        double form_offset_x = 0.0;
        double form_offset_y = 0.0;
        double form_offset_z = 0.0;

        bool operator==(const FormationDirective&) const = default;
    };

    std::uint64_t recovery_base_id = 0;
    std::uint64_t recovery_runway_id = 0;
    RecoveryApproachType recovery_approach_type = RecoveryApproachType::None;
    TakeoffProcedureType takeoff_procedure_id = TakeoffProcedureType::Unspecified;
    TakeoffClearanceState takeoff_clearance_id = TakeoffClearanceState::Unspecified;
    double takeoff_interval_s = 0.0;
    RunwaySlotPosition runway_slot_id = RunwaySlotPosition::Unspecified;

    int formation_id = 0;
    double form_offset_x = 0.0;
    double form_offset_y = 0.0;
    double form_offset_z = 0.0;
};

// Maintained air-domain owner slice projected through MissionCommand compatibility shells.
using MissionCommandAirOwnerSlice = MissionCommandAir;
inline constexpr bool kMissionCommandAirOwnedDomainSlice = true;

[[nodiscard]] inline MissionCommandAir::RecoveryDirective
mission_command_air_recovery_directive(const MissionCommandAirOwnerSlice& air) noexcept {
    return {
        .recovery_base_id = air.recovery_base_id,
        .recovery_runway_id = air.recovery_runway_id,
        .recovery_approach_type = air.recovery_approach_type,
    };
}

[[nodiscard]] inline MissionCommandAir::TakeoffDirective
mission_command_air_takeoff_directive(const MissionCommandAirOwnerSlice& air) noexcept {
    return {
        .takeoff_procedure_id = air.takeoff_procedure_id,
        .takeoff_clearance_id = air.takeoff_clearance_id,
        .takeoff_interval_s = air.takeoff_interval_s,
        .runway_slot_id = air.runway_slot_id,
    };
}

[[nodiscard]] inline MissionCommandAir::FormationDirective
mission_command_air_formation_directive(const MissionCommandAirOwnerSlice& air) noexcept {
    return {
        .formation_id = air.formation_id,
        .form_offset_x = air.form_offset_x,
        .form_offset_y = air.form_offset_y,
        .form_offset_z = air.form_offset_z,
    };
}
