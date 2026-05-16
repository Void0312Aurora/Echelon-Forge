#pragma once

#include <cstdint>

#include "components/tasking/air/air_tasking_enums.h"

struct LeaderIntentAir {
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
