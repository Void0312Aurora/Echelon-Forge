#pragma once

#include <cstdint>

#include "components/tasking/air/air_tasking_enums.h"

struct TaskOrderAir {
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

    TaskType task_type = TaskType::Idle;
    std::uint64_t element_id = 0;
    std::uint64_t package_id = 0;
    std::uint64_t lead_aircraft_id = 0;

    double anchor_x_m = 0.0;
    double anchor_y_m = 0.0;
    double anchor_z_m = 0.0;
    StationType station_type = StationType::Orbit;
    double station_radius_m = 0.0;
    double station_leg_length_m = 0.0;
    double station_heading_deg = 0.0;

    double altitude_block_min_m = 0.0;
    double altitude_block_max_m = 0.0;
    double target_altitude_m = 0.0;
    double speed_min_mps = 0.0;
    double speed_max_mps = 0.0;
    double target_speed_mps = 0.0;

    int entry_condition_code = 0;
    int exit_condition_code = 0;
    double on_station_time_s = 0.0;
    double fuel_bingo_override_kg = 0.0;
    std::uint64_t recovery_base_id = 0;
    std::uint64_t recovery_runway_id = 0;
    RecoveryApproachType recovery_approach_type = RecoveryApproachType::None;
    TakeoffProcedureType takeoff_procedure_id = TakeoffProcedureType::Unspecified;
    TakeoffClearanceState takeoff_clearance_id = TakeoffClearanceState::Unspecified;
    double takeoff_interval_s = 0.0;
    RunwaySlotPosition runway_slot_id = RunwaySlotPosition::Unspecified;
    std::uint64_t formation_template_id = 0;
    std::uint64_t formation_contract_id = 0;
    FormationRole formation_role_id = FormationRole::Unspecified;
    WingmanSlot wingman_slot_id = WingmanSlot::Unspecified;
    int join_policy_id = 0;
    int rejoin_policy_id = 0;
    int mutual_support_mode = 0;
    std::uint64_t support_sector_id = 0;
};

// Maintained air-domain owner slice projected through TaskOrder compatibility shells.
using TaskOrderAirOwnerSlice = TaskOrderAir;
inline constexpr bool kTaskOrderAirOwnedDomainSlice = true;

[[nodiscard]] inline TaskOrderAir::RecoveryDirective
task_order_air_recovery_directive(const TaskOrderAirOwnerSlice& air) noexcept {
    return {
        .recovery_base_id = air.recovery_base_id,
        .recovery_runway_id = air.recovery_runway_id,
        .recovery_approach_type = air.recovery_approach_type,
    };
}

[[nodiscard]] inline TaskOrderAir::TakeoffDirective
task_order_air_takeoff_directive(const TaskOrderAirOwnerSlice& air) noexcept {
    return {
        .takeoff_procedure_id = air.takeoff_procedure_id,
        .takeoff_clearance_id = air.takeoff_clearance_id,
        .takeoff_interval_s = air.takeoff_interval_s,
        .runway_slot_id = air.runway_slot_id,
    };
}
