#pragma once

#include <cstdint>

#include "components/command/common/comm_message.h"
#include "components/tasking/common/core_tasking_enums.h"

struct PilotReportCore {
    CommMsgType report_type = CommMsgType::None;
    std::uint64_t sender_id = 0;
    std::uint64_t task_id = 0;
    ServiceProfile service_profile = ServiceProfile::Unspecified;
    TaskFamily task_family = TaskFamily::Unspecified;
    TacticalUnitType tactical_unit_type = TacticalUnitType::Unspecified;
    std::uint64_t tactical_unit_id = 0;
    std::uint64_t task_group_id = 0;
    int role_code = 0;
    CoordinationMode coordination_mode = CoordinationMode::Unspecified;
    double timestamp_s = 0.0;
    double status_value = 0.0;
    std::uint64_t entity_ref = 0;
    double location_x_m = 0.0;
    double location_y_m = 0.0;
    double location_z_m = 0.0;
    bool active = false;
};
