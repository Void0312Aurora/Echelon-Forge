#pragma once

#include <cstdint>

#include "components/tasking/common/core_tasking_enums.h"

struct TaskOrderCore {
    std::uint64_t task_id = 0;
    ServiceProfile service_profile = ServiceProfile::Unspecified;
    TaskFamily task_family = TaskFamily::Unspecified;
    TacticalUnitType tactical_unit_type = TacticalUnitType::Unspecified;
    int priority = 0;
    std::uint64_t issuer_id = 0;
    std::uint64_t assignee_id = 0;
    CommandRelationship command_relationship = CommandRelationship::None;
    AuthorityScope authority_scope = AuthorityScope::Unspecified;
    std::uint64_t parent_node_id = 0;
    std::uint64_t task_group_id = 0;
    std::uint64_t supported_node_id = 0;
    std::uint64_t supporting_node_id = 0;
    int role_code = 0;
    CoordinationMode coordination_mode = CoordinationMode::Unspecified;
    int relative_slot_code = 0;
    AssigneeKind assignee_kind = AssigneeKind::Aircraft;
    std::uint64_t recovery_site_id = 0;
    bool active = false;
    double issue_time_s = 0.0;
};
