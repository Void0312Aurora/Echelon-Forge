#pragma once

#include <cstdint>

#include "components/tasking/air/air_tasking_enums.h"

struct MissionCommandAir {
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
