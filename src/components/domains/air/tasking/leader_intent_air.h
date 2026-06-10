#pragma once

#include <cstdint>

#include "components/domains/air/tasking/air_tasking_enums.h"

struct LeaderIntentAir {
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

    LeaderPhase phase_id = LeaderPhase::Idle;
    int element_phase_id = 0;
    std::uint64_t route_ref_id = 0;
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
    FormationMode formation_mode_id = FormationMode::Unspecified;
    bool join_required_flag = false;
    bool rejoin_required_flag = false;
    bool split_flag = false;
    double support_anchor_x_m = 0.0;
    double support_anchor_y_m = 0.0;
    double support_slot_offset_x_m = 0.0;
    double support_slot_offset_y_m = 0.0;
    WingmanCommandMode wingman_command_mode = WingmanCommandMode::None;
    bool approach_armed = false;
    bool commit_to_land = false;
    bool abort_flag = false;
};

// Maintained air-domain owner slice projected through LeaderIntent compatibility shells.
using LeaderIntentAirOwnerSlice = LeaderIntentAir;
inline constexpr bool kLeaderIntentAirOwnedDomainSlice = true;

[[nodiscard]] inline LeaderIntentAir::RecoveryDirective
leader_intent_air_recovery_directive(const LeaderIntentAirOwnerSlice& air) noexcept {
    return {
        .recovery_base_id = air.recovery_base_id,
        .recovery_runway_id = air.recovery_runway_id,
        .recovery_approach_type = air.recovery_approach_type,
    };
}

[[nodiscard]] inline LeaderIntentAir::TakeoffDirective
leader_intent_air_takeoff_directive(const LeaderIntentAirOwnerSlice& air) noexcept {
    return {
        .takeoff_procedure_id = air.takeoff_procedure_id,
        .takeoff_clearance_id = air.takeoff_clearance_id,
        .takeoff_interval_s = air.takeoff_interval_s,
        .runway_slot_id = air.runway_slot_id,
    };
}

[[nodiscard]] inline LeaderIntentAir::FormationDirective
leader_intent_air_formation_directive(const LeaderIntentAirOwnerSlice& air) noexcept {
    return {
        .formation_id = air.formation_id,
        .form_offset_x = air.form_offset_x,
        .form_offset_y = air.form_offset_y,
        .form_offset_z = air.form_offset_z,
    };
}
