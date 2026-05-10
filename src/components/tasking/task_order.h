#pragma once

#include <cstdint>

#include "components/tasking/tasking_enums.h"

/**
 * TaskOrder
 * Implements task_order_leader_standard.md: the C2 -> Leader task object.
 */
struct TaskOrder {
    std::uint64_t task_id = 0;
    TaskType task_type = TaskType::Idle;
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
    std::uint64_t element_id = 0;
    std::uint64_t package_id = 0;
    std::uint64_t lead_aircraft_id = 0;
    bool active = false;
    double issue_time_s = 0.0;

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
    std::uint64_t formation_template_id = 0;
    std::uint64_t formation_contract_id = 0;
    FormationRole formation_role_id = FormationRole::Unspecified;
    WingmanSlot wingman_slot_id = WingmanSlot::Unspecified;
    int join_policy_id = 0;
    int rejoin_policy_id = 0;
    int mutual_support_mode = 0;
    std::uint64_t support_sector_id = 0;
};
